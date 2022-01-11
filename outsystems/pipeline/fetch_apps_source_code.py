# Python Modules
import sys
import os
import argparse
import shutil
import subprocess
import xml.etree.ElementTree as ET

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
# Variables
from outsystems.vars.file_vars import ARTIFACT_FOLDER, MODULES_FOLDER
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION
from outsystems.vars.os_vars import REMOTE_DRIVE, OUTSYSTEMS_DIR, PLAT_SERVER_DIR, SHARE_DIR, FULL_DIR, \
    REPOSITORY_DIR, CUSTOM_HANDLERS_DIR
from outsystems.vars.msbuild_vars import MS_BUILD_NAMESPACE, ASSEMBLY_BLACKLIST

# Functions
from outsystems.lifetime.lifetime_applications import _get_application_info
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.lifetime.lifetime_environments import get_environment_key, _find_environment_url
from outsystems.lifetime.lifetime_modules import get_modules


# ############################################################# SCRIPT ##############################################################

# Recursively copy the entire directory tree
# Symbolic links in the source tree result in symbolic links in the destination tree
def get_module_resources(module_name: str, network_dir: str, local_dir: str):
    network_dir += os.sep + os.path.join(SHARE_DIR, module_name, FULL_DIR)
    shutil.copytree(network_dir, local_dir, symlinks=True)


# The contents of the files pointed to by symbolic links are copied
# Keeping the original file name
def replace_local_symlinks(network_dir: str, local_dir: str):
    for subdir, dirs, files in os.walk(local_dir):
        for filename in files:
            filepath = os.path.join(local_dir, subdir, filename)

            # CustomHandlers symlink file starts with upercase leter
            # CustomHandlers folder starts with lowercase
            if filename == CUSTOM_HANDLERS_DIR:
                dst_dir = os.path.join(local_dir, CUSTOM_HANDLERS_DIR)
                src_dir = os.path.join(network_dir, CUSTOM_HANDLERS_DIR[0].lower() + CUSTOM_HANDLERS_DIR[1:])

                os.remove(filepath)
                shutil.copytree(src_dir, dst_dir, symlinks=True)

            elif os.path.islink(filepath):
                src_dir = os.path.join(network_dir, REPOSITORY_DIR)

                # Get symbolic link file name (which includes .dll version id)
                head, tail = os.path.split(os.readlink(filepath))
                src_file = os.path.join(src_dir, tail)

                # Replace local (symbolic link) file by the content of the file pointed to by symbolic link
                # maintaining the original local file name
                os.remove(filepath)
                shutil.copy2(src_file, filepath)


# Connect to shared drive, use given credentials
def connect_network_dir(network_path: str, network_user: str, network_pass: str):
    subprocess.call(r'net use "{}" /user:{} {}'.format(network_path, network_user, network_pass), shell=True)


# Disconnect shared drive
def diconnect_network_dir(network_path: str):
    subprocess.call(r'net use {} /delete'.format(network_path), shell=True)


# Return the list of csprojs relative path found in the module solution file
def csproj_files(module_name: str, local_dir: str):

    # Builds the solution full path
    sln_file = os.path.join(local_dir, "{}.sln".format(module_name))

    # Final list of csprojs relative path found in the solution file
    csprojs = []

    # Read module solution file
    with open(sln_file, 'rb') as f:
        line = f.readline()
        while line:
            line = f.readline().decode('utf-8')
            if line.startswith("Project"):
                # Gets line's second object (i.e: csproj relative path)
                # Trim spaces and double quotes
                csproj = line.split(",")[1].strip().strip('\"')

                # Ignore if module's default csproj
                if(csproj == "{}.csproj".format(module_name)):
                    continue

                csprojs.append(csproj)

    return csprojs


# Adds to a csproj file all the references (dll) existing in the module bin folder
def include_references(local_dir: str, csproj_dir: str):

    # Builds bin directory full path
    bin_dir = os.path.join(local_dir, "bin")

    # Builds csproj file full path
    csproj_file = os.path.join(local_dir, csproj_dir)

    # Read csproj file and identifies first ItemGroup element
    ET.register_namespace('', MS_BUILD_NAMESPACE)
    tree = ET.parse(csproj_file)
    itemgroup_elem = tree.find("./{val}ItemGroup".format(val='{' + MS_BUILD_NAMESPACE + '}'))

    # Iterate through all dlls found in the bin directory
    for file in os.listdir(bin_dir):
        if file.endswith(".dll"):
            dll_name = os.path.splitext(file)[0]

            # Validate if dll already exists in the csproj
            dll_exists = (len(tree.findall('./{val}ItemGroup/{val}Reference/[@Include="{dll}"]'.format(val='{' + MS_BUILD_NAMESPACE + '}', dll=dll_name))) > 0)

            # Continue if module's default csproj 
            # Continue if dll already exists in csproj
            # Continue if dll exists in blacklist
            if dll_name == os.path.splitext(os.path.basename(csproj_file))[0] or dll_exists or dll_name in ASSEMBLY_BLACKLIST:
                continue

            # Create Reference structure
            ref = ET.Element("Reference")
            ref.set("Include", dll_name)

            # Create Name structure
            ref_name = ET.Element("Name")
            ref_name.text = dll_name
            ref.append(ref_name)

            # Create HintPath structure
            ref_hintpath = ET.Element("HintPath")
            # Identify the relative path between the module's full dir and csproj file full dir
            # Adds to the element text the dll relative path
            ref_hintpath.text = "{}{}".format(os.path.relpath(local_dir, os.path.split(csproj_file)[0]), '\\bin\\' + dll_name + '.dll')
            ref.append(ref_hintpath)

            # Create Private structure
            ref_private = ET.Element("Private")
            ref_private.text = "False"
            ref.append(ref_private)

            # Append new element to ItemGroup element
            itemgroup_elem.append(ref)

    tree.write(csproj_file)


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, target_env_hostname: str, installation_dir: str, network_user: str, network_pass: str, target_env: str, apps: list, inc_pattern: str, exc_pattern: str, include_all_refs: bool):

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Gets the environment key for the target environment
    target_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, target_env)

    # Tuple with (AppName, AppKey): app_tuple[0] = AppName; app_tuple[1] = AppKey
    app_list = []
    for app in apps:
        app_list.append(_get_application_info(artifact_dir, lt_endpoint, lt_token, app_name=app))

    # Get factory modules info
    all_modules = get_modules(artifact_dir, lt_endpoint, lt_token, True)

    # Get list of corresponding Modules (eSpaces only) that match 'ApplicationScope' in 'TargetEnvironment'
    module_list = []
    for module in all_modules:
        if module["Kind"] == "eSpace":
            for module_status in module["ModuleStatusInEnv"]:
                for app in app_list:
                    if module_status["ApplicationKey"] == app[1] and module_status["EnvironmentKey"] == target_env_key and module["Name"] not in exc_pattern:
                        module_list.append(module)
                    elif module_status["EnvironmentKey"] == target_env_key and module["Name"] in inc_pattern:
                        module_list.append(module)

    # Show final module list
    print("Module scope for code analysis:", flush=True)
    for module in module_list:
        print(" - {}".format(module["Name"]))
    print("", flush=True)

    # Parse target environment hostname
    if not target_env_hostname:
        target_env_hostname = _find_environment_url(artifact_dir, lt_endpoint, lt_token, target_env)

    # Set network root path
    network_dir = os.path.join(target_env_hostname, installation_dir.replace(":", "$"))

    # Set network root path for different local OS
    if os.name == 'nt':
        network_dir = r'\\{}'.format(network_dir)
    elif os.name == 'posix':
        network_dir = r'//{}'.format(network_dir)
    else:
        sys.exit(1)

    print('network_dir: {}'.format(network_dir), flush=True)
    if network_user and network_pass:
        connect_network_dir(network_dir, network_user, network_pass)

    # Copy located files to target location (keep file hierarchy)
    for module in module_list:
        # Set local full path direcory
        local_dir = os.path.join(os.getcwd(), artifact_dir, MODULES_FOLDER, module["Name"])

        print("[{}] Fetching module resources...".format(module["Name"]), flush=True)
        get_module_resources(module["Name"], network_dir, local_dir)

        print("[{}] Replacing local symbolic links...".format(module["Name"]), flush=True)
        replace_local_symlinks(network_dir, local_dir)

        if include_all_refs:
            print("[{}] Including all assembly references...".format(module["Name"]), flush=True)
            for csproj in csproj_files(module["Name"], local_dir):
                include_references(local_dir, csproj)

    if network_user and network_pass:
        diconnect_network_dir(network_dir)

    sys.exit(0)
# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-lu", "--lt_url", type=str, required=True,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
    parser.add_argument("-lt", "--lt_token", type=str, required=True,
                        help="Token for LifeTime API calls.")
    parser.add_argument("-v", "--lt_api_version", type=int, default=LIFETIME_API_VERSION,
                        help="LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
    parser.add_argument("-e", "--lt_endpoint", type=str, default=LIFETIME_API_ENDPOINT,
                        help="(optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-t", "--target_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the target environment where you want to fetch the apps.")
    parser.add_argument("-l", "--app_list", type=str, required=True,
                        help="Comma separated list of apps you want to fetch. Example: \"App1,App2 With Spaces,App3_With_Underscores\"")
    parser.add_argument("-th", "--target_env_hostname", type=str,
                        help=r'(optional) Target environemnt hostname. Example: "<environemnt_hostname>"')
    parser.add_argument("-i", "--installation_dir", type=str, default=os.path.join(REMOTE_DRIVE + ":", os.sep, OUTSYSTEMS_DIR, PLAT_SERVER_DIR),
                        help=r'(optional) OutSystems Platform Installation directory. Example: "E:\OutSystems\Platform Server"')
    parser.add_argument("-u", "--network_user", type=str,
                        help=r'(optional) Network connection Username.')
    parser.add_argument("-p", "--network_pass", type=str,
                        help=r'(optional) Network connection Password')
    parser.add_argument("-in", "--inc_pattern", type=str,
                        help="(optional) Include pattern for module scope")
    parser.add_argument("-ex", "--exc_pattern", type=str,
                        help="(optional) Exclude pattern for module scope")
    parser.add_argument("-ref", "--include_all_refs", action='store_true',
                        help="Flag that indicates if all references need to be added to the csproj file.")

    args = parser.parse_args()

    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse the API endpoint
    lt_api_endpoint = args.lt_endpoint
    # Parse the LT Url and split the LT hostname from the HTTP protocol
    # Assumes the default HTTP protocol = https
    lt_http_proto = LIFETIME_HTTP_PROTO
    lt_url = args.lt_url
    if lt_url.startswith("http://"):
        lt_http_proto = "http"
        lt_url = lt_url.replace("http://", "")
    else:
        lt_url = lt_url.replace("https://", "")
    if lt_url.endswith("/"):
        lt_url = lt_url[:-1]
    # Parte LT API Version
    lt_version = args.lt_api_version
    # Parse the LT Token
    lt_token = args.lt_token
    # Parse Target Environment
    target_env = args.target_env
    # Parse App list
    _apps = args.app_list
    apps = _apps.split(',')
    # Parse Hostname dir
    target_env_hostname = args.target_env_hostname
    # Parse Installation dir
    installation_dir = args.installation_dir
    # Parse Network Username
    network_user = args.network_user
    # Parse Network Password
    network_pass = args.network_pass
    # Parse Include Pattern
    inc_pattern = args.inc_pattern
    # Parse Exclude Pattern
    exc_pattern = args.exc_pattern
    # Parse Include All References
    include_all_refs = args.include_all_refs

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, target_env_hostname, installation_dir, network_user, network_pass, target_env, apps, inc_pattern, exc_pattern, include_all_refs)
