# Python Modules
import sys
import os
import argparse
import re
from time import sleep
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from io import BytesIO

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
# Variables
from outsystems.vars.file_vars import ARTIFACT_FOLDER, ENVIRONMENT_SOURCECODE_FOLDER, ENVIRONMENT_SOURCECODE_DOWNLOAD_FILE
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS, MANIFEST_FLAG_IS_TEST_APPLICATION, \
    MANIFEST_APPLICATION_NAME
from outsystems.vars.pipeline_vars import SOURCECODE_SLEEP_PERIOD_IN_SECS, SOURCECODE_TIMEOUT_IN_SECS, SOURCECODE_ONGOING_STATUS, \
    SOURCECODE_FINISHED_STATUS
from outsystems.vars.dotnet_vars import MS_BUILD_NAMESPACE, ASSEMBLY_BLACKLIST

# Functions
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.lifetime.lifetime_environments import get_environment_app_source_code, get_environment_app_source_code_status, \
    get_environment_app_source_code_link, get_environment_key
from outsystems.lifetime.lifetime_applications import get_running_app_version
from outsystems.lifetime.lifetime_downloads import download_package
from outsystems.file_helpers.file import load_data
from outsystems.vars.vars_base import get_configuration_value, load_configuration_file

# ############################################################# SCRIPT ##############################################################


# Extract content of downloaded source code package (one folder per application module)
def extract_package_content(file_path: str, include_all_refs: bool, remove_resources_files: bool):
    module_count = 0
    with ZipFile(file_path, 'r') as zf:
        # Iterate through the content of the source code package
        for archive_name in zf.namelist():
            match = re.search(r'(.*)\.v\d+.zip$', archive_name)
            # Each package will have one .zip file per module
            if match:
                module_name = match.group(1)
                module_folder = os.path.join(os.path.dirname(file_path), "modules", module_name)
                file_data = BytesIO(zf.read(archive_name))
                with ZipFile(file_data) as zf2:
                    # Extract generated source code of each module to a subfolder
                    zf2.extractall(path=module_folder)

                # Check if any post-processing action is needed over the extracted resources
                if (include_all_refs or remove_resources_files):
                    process_csproj_files(module_name, module_folder, include_all_refs, remove_resources_files)

                # Update package modules count
                module_count += 1

    # Return number of modules inside the source code package
    return module_count


# Return the list of .csproj relative paths referenced in the module .sln file
def find_csproj_files(module_name: str, module_folder: str):

    # Builds the solution full path
    sln_file = os.path.join(module_folder, "{}.sln".format(module_name))

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
                # Check if module's main csproj
                is_main = csproj == "{}.csproj".format(module_name)
                # Check if module's referencesProxy csproj
                is_referencesProxy = csproj.startswith("referencesProxy")
                # Append csproj details
                csprojs.append({"RelativePath": csproj, "IsMain": is_main, "IsReferencesProxy": is_referencesProxy})

    return csprojs


# Post-processing of .csproj files according to provided flags:
# --include_all_refs: Ensures that references proxy .csproj file reference all assemblies (.dll) available in the module bin folder
# --remove_resources_files: Removes embedded .resources files from main .csproj file (if existing)
def process_csproj_files(module_name: str, module_folder: str, include_all_refs: bool, remove_resources_files: bool):

    # Find .csproj files available in the provided module folder
    csprojs = find_csproj_files(module_name, module_folder)

    # Build bin directory full path
    bin_folder = os.path.join(module_folder, "bin")

    # Iterate through all csproj files for the current module
    for csproj in csprojs:
        # Build csproj file full path
        csproj_file = os.path.join(module_folder, csproj["RelativePath"])

        # Check if csproj is for the module's references proxy assembly
        if csproj["IsReferencesProxy"] and include_all_refs:
            # Read csproj file and identify first ItemGroup element
            ET.register_namespace('', MS_BUILD_NAMESPACE)
            tree = ET.parse(csproj_file)
            itemgroup_elem = tree.find("./{val}ItemGroup".format(val='{' + MS_BUILD_NAMESPACE + '}'))

            # Iterate through all dlls found in the bin directory
            for file in os.listdir(bin_folder):
                if file.endswith(".dll"):
                    dll_name = os.path.splitext(file)[0]
                    # TODO: Use os.path.join instead
                    dll_relpath = os.path.join(os.path.relpath(module_folder, os.path.dirname(csproj_file)), 'bin', file)

                    # Validate if dll already exists in the csproj
                    dll_exists = tree.find("./{val}ItemGroup/{val}Reference/{val}HintPath[.='{dll}']".format(val='{' + MS_BUILD_NAMESPACE + '}', dll=dll_relpath)) is not None

                    # Continue if dll is csproj target assembly
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
                    ref_hintpath.text = dll_relpath
                    ref.append(ref_hintpath)

                    # Create Private structure
                    ref_private = ET.Element("Private")
                    ref_private.text = "False"
                    ref.append(ref_private)

                    # Append new element to ItemGroup element
                    itemgroup_elem.append(ref)

            # Save newly added references to csproj file
            tree.write(csproj_file)

        # Check if csproj is for the module's main assembly
        elif csproj["IsMain"] and remove_resources_files:
            # Read csproj file and find all ItemGroup elements
            ET.register_namespace('', MS_BUILD_NAMESPACE)
            tree = ET.parse(csproj_file)
            itemgroup_elems = tree.findall("./{val}ItemGroup".format(val='{' + MS_BUILD_NAMESPACE + '}'))

            # Iterate through all ItemGroups to find out which has embedded resource files
            for itemgroup in itemgroup_elems:
                emb_resource_elems = itemgroup.findall("./{val}EmbeddedResource".format(val='{' + MS_BUILD_NAMESPACE + '}'))
                if emb_resource_elems:
                    for emb_resource in emb_resource_elems:
                        # Remove every embedded resource element found
                        itemgroup.remove(emb_resource)
                    break
            # Save changes to csproj file
            tree.write(csproj_file)


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, target_env: str, apps: list, trigger_manifest: dict, include_test_apps: bool, friendly_package_names: bool, include_all_refs: bool, remove_resources_files: bool):

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # List of application names to fetch the source code from target environment
    app_list = []

    # Extract names from manifest file (when available)
    if trigger_manifest:
        for app in trigger_manifest[MANIFEST_APPLICATION_VERSIONS]:
            if include_test_apps or not app[MANIFEST_FLAG_IS_TEST_APPLICATION]:
                app_list.append(app[MANIFEST_APPLICATION_NAME])
    else:
        app_list = apps

    for app_name in app_list:
        # Request source code package creation
        pkg_details = get_environment_app_source_code(artifact_dir, lt_endpoint, lt_token, env_name=target_env, app_name=app_name)
        pkg_key = pkg_details["PackageKey"]
        print("Source code package {} started being created for application {} deployed in {} environment.".format(pkg_key, app_name, target_env), flush=True)

        # Wait for package creation to finish
        wait_counter = 0
        link_available = False
        while wait_counter < get_configuration_value("SOURCECODE_TIMEOUT_IN_SECS", SOURCECODE_TIMEOUT_IN_SECS):
            # Check current package status
            pkg_status = get_environment_app_source_code_status(artifact_dir, lt_endpoint, lt_token,
                                                                env_name=target_env, app_name=app_name, pkg_key=pkg_key)
            if pkg_status["Status"] == SOURCECODE_FINISHED_STATUS:
                # Package was created successfully
                link_available = True
                break
            elif pkg_status["Status"] == SOURCECODE_ONGOING_STATUS:
                # Package is still being created. Go back to sleep.
                sleep_value = get_configuration_value("SOURCECODE_SLEEP_PERIOD_IN_SECS", SOURCECODE_SLEEP_PERIOD_IN_SECS)
                sleep(sleep_value)
                wait_counter += sleep_value
                print("{} secs have passed while source code package is being created...".format(wait_counter), flush=True)
            else:
                raise NotImplementedError("Unknown source code package status: {}.".format(pkg_status["Status"]))

        # When the package is created, download it using the provided key
        if link_available:
            print("Source code package {} created successfully.".format(pkg_key), flush=True)
            pkg_link = get_environment_app_source_code_link(artifact_dir, lt_endpoint, lt_token,
                                                            env_name=target_env, app_name=app_name, pkg_key=pkg_key)
            if friendly_package_names:
                target_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, target_env)
                running_version = get_running_app_version(artifact_dir, lt_endpoint, lt_token, target_env_key, app_name=app_name)
                file_name = "{}_v{}".format(app_name.replace(" ", "_"), running_version["Version"].replace(".", "_"))
                if running_version["IsModified"]:
                    file_name += "+"
            else:
                file_name = pkg_key
            file_name += ENVIRONMENT_SOURCECODE_DOWNLOAD_FILE
            file_path = os.path.join(artifact_dir, ENVIRONMENT_SOURCECODE_FOLDER, file_name)

            download_package(file_path, lt_token, pkg_link["url"])
            print("Source code package {} downloaded successfully.".format(pkg_key), flush=True)

            # Extract source code for each module from downloaded package, applying post-processing actions (if requested)
            module_count = extract_package_content(file_path, include_all_refs, remove_resources_files)
            print("{} application modules processed successfully.".format(module_count), flush=True)
        else:
            print("Timeout expired while generating source code package {}. Unable to download source code for application {}.".format(pkg_key, app_name), flush=True)


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
    parser.add_argument("-e", "--lt_endpoint", type=str, default=LIFETIME_API_ENDPOINT,
                        help="(optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-t", "--target_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the target environment where to fetch the source code from.")
    parser.add_argument("-l", "--app_list", type=str,
                        help="Comma separated list of apps you want to fetch. Example: \"App1,App2 With Spaces,App3_With_Underscores\"")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="Manifest file (with JSON format). Contains required data used throughout the pipeline execution.")
    parser.add_argument("-i", "--include_test_apps", action='store_true',
                        help="Flag that indicates if applications marked as \"Test Application\" in the manifest are fetched as well.")
    parser.add_argument("-n", "--friendly_package_names", action='store_true',
                        help="Flag that indicates if downloaded source code packages should have a user-friendly name. Example: \"<AppName>_v1_2_1\"")
    parser.add_argument("-ref", "--include_all_refs", action='store_true',
                        help="Flag that indicates if all assemblies in the \"bin\" folder should be added as references in the .csproj file.")
    parser.add_argument("-res", "--remove_resources_files", action='store_true',
                        help="Flag that indicates if embedded resources files should be removed from the .csproj file.")
    parser.add_argument("-cf", "--config_file", type=str,
                        help="Config file path. Contains configuration values to override the default ones.")

    args = parser.parse_args()

    # Load config file if exists
    if args.config_file:
        load_configuration_file(args.config_file)
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
    lt_version = LIFETIME_API_VERSION
    # Parse the LT Token
    lt_token = args.lt_token
    # Parse Target Environment
    target_env = args.target_env
    # Check if either an app list or a manifest file is being provided
    if not args.app_list and not args.manifest_file:
        parser.error("either --app_list or --manifest_file must be provided as arguments")
    # Use Trigger Manifest (if available)
    if args.manifest_file:
        # Parse Trigger Manifest artifact
        trigger_manifest = load_data("", args.manifest_file)
        apps = None
    else:
        trigger_manifest = None
        # Parse App list
        _apps = args.app_list
        apps = _apps.split(',')
    # Parse Include Test Apps flag
    include_test_apps = args.include_test_apps
    # Parse Friendly Package Names flag
    friendly_package_names = args.friendly_package_names
    # Parse Include All References flag
    include_all_refs = args.include_all_refs
    # Parse Remove Resources Files flag
    remove_resources_files = args.remove_resources_files

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, target_env, apps, trigger_manifest, include_test_apps, friendly_package_names, include_all_refs, remove_resources_files)  # type: ignore
