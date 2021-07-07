# Python Modules
import sys
import os
import argparse
import shutil

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
from outsystems.vars.os_vars import LOCAL_DRIVE, BINARY_DIRECTORY

# Functions
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.lifetime.lifetime_applications import _get_application_info
from outsystems.lifetime.lifetime_environments import get_environment_key, _find_environment_url
from outsystems.lifetime.lifetime_modules import get_modules
from outsystems.file_helpers.file import load_data
from outsystems.infrastructure.infrastructure_base import connect_shared_drive, disconnect_shared_drive


# ############################################################# SCRIPT ##############################################################
def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, fileshare_user: str, fileshare_pass: str, target_env: str, apps: list, dep_manifest: list, inc_pattern: str, exc_pattern: str):

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
                    if module_status["ApplicationKey"] == app[1] and module_status["EnvironmentKey"] == target_env_key and module["Name"] not in exc_pattern:  # EXC_PATTERN : CasesSampleData excludes Cases moodule
                        module_list.append(module)
                    elif module_status["EnvironmentKey"] == target_env_key and module["Name"] in inc_pattern:  # INC_PATTERN : CasesSampleData include Cases module
                        module_list.append(module)

    # Show final module list
    print("Module scope for code analysis:", flush=True)
    for module in module_list:
        print(" - {}".format(module["Name"]))
    print("", flush=True)

    # Get target environment hostname
    target_env_hostname = _find_environment_url(artifact_dir, lt_endpoint, lt_token, target_env)

    # Create file share to Deployment Controller root folder
    connect_shared_drive(target_env_hostname, fileshare_user, fileshare_pass)

    # Copy located files to target location (keep file hierarchy)
    for module in module_list:
        dst_dir = os.path.join(artifact_dir, MODULES_FOLDER, module["Name"])
        src_dir = r'{}\{}'.format(LOCAL_DRIVE, os.path.join(BINARY_DIRECTORY, "share", module["Name"], "full"))
        print("Fetching resources for module '{}'...".format(module["Name"]), flush=True)

        # Recursively copy the entire directory tree
        # The contents and metadata of the linked files are copied to the new tree
        shutil.copytree(src_dir, dst_dir, symlinks=False)

    # Remove file share network directory
    disconnect_shared_drive()

    sys.exit(0)
# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-u", "--lt_url", type=str, required=True,
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
    parser.add_argument("-m", "--manifest_file", type=str,
                        help="(optional) Manifest file path, to be used instead of to app_list.")
    parser.add_argument("-fu", "--fileshare_user", type=str, required=True,
                        help="Username with priveleges to connect to target environemnt DC")
    parser.add_argument("-fp", "--fileshare_pass", type=str, required=True,
                        help="Password to connect to target environemnt DC")
    parser.add_argument("-in", "--inc_pattern", type=str,
                        help="(optional) Include pattern for module scope")
    parser.add_argument("-ex", "--exc_pattern", type=str,
                        help="(optional) Exclude pattern for module scope")

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
    # Parse Manifest file if it exists
    if args.manifest_file:
        manifest_file = load_data("", args.manifest_file)
    else:
        manifest_file = None
    # Parse Fileshare User
    fileshare_user = args.fileshare_user
    # Parse Fileshare Pass
    fileshare_pass = args.fileshare_pass
    # Parse Include Pattern
    inc_pattern = args.inc_pattern
    # Parse Exclude Pattern
    exc_pattern = args.exc_pattern

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, fileshare_user, fileshare_pass, target_env, apps, manifest_file, inc_pattern, exc_pattern)
