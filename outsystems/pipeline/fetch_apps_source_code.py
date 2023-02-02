# Python Modules
import sys
import os
import argparse
from time import sleep

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
# Variables
from outsystems.vars.file_vars import ARTIFACT_FOLDER, ENVIRONMENT_FOLDER, ENVIRONMENT_SOURCECODE_FOLDER, \
    ENVIRONMENT_SOURCECODE_DOWNLOAD_FILE
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS, MANIFEST_FLAG_IS_TEST_APPLICATION, \
    MANIFEST_APPLICATION_NAME
from outsystems.vars.pipeline_vars import SOURCECODE_SLEEP_PERIOD_IN_SECS, SOURCECODE_TIMEOUT_IN_SECS, SOURCECODE_ONGOING_STATUS, \
    SOURCECODE_FINISHED_STATUS

# Functions
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.lifetime.lifetime_environments import get_environment_app_source_code, get_environment_app_source_code_status, \
    get_environment_app_source_code_link
from outsystems.file_helpers.file import load_data, download_source_code
# Exceptions


# ############################################################# SCRIPT ##############################################################


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, target_env: str, apps: list, trigger_manifest: dict, include_test_apps: bool):

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
        print("Source code package {} started being created for application {}.".format(pkg_key, app_name), flush=True)

        # Wait for package creation to finish
        wait_counter = 0
        link_available = False
        while wait_counter < SOURCECODE_TIMEOUT_IN_SECS:
            # Check current package status
            pkg_status = get_environment_app_source_code_status(artifact_dir, lt_endpoint, lt_token,
                                                                env_name=target_env, app_name=app_name, pkg_key=pkg_key)
            if pkg_status["Status"] == SOURCECODE_FINISHED_STATUS:
                # Package was created successfully
                link_available = True
                break
            elif pkg_status["Status"] == SOURCECODE_ONGOING_STATUS:
                # Package is still being created. Go back to sleep.
                sleep(SOURCECODE_SLEEP_PERIOD_IN_SECS)
                wait_counter += SOURCECODE_SLEEP_PERIOD_IN_SECS
                print("{} secs have passed while source code package is being created...".format(wait_counter), flush=True)
            else:
                raise NotImplementedError("Unknown source code package status: {}.".format(pkg_status["Status"]))

        # When the package is created, download it using the provided key
        if link_available:
            print("Source code package {} created successfully.".format(pkg_key), flush=True)
            pkg_link = get_environment_app_source_code_link(artifact_dir, lt_endpoint, lt_token,
                                                            env_name=target_env, app_name=app_name, pkg_key=pkg_key)
            file_name = pkg_key + ENVIRONMENT_SOURCECODE_DOWNLOAD_FILE
            file_path = os.path.join(artifact_dir, ENVIRONMENT_FOLDER, ENVIRONMENT_SOURCECODE_FOLDER, file_name)
            download_source_code(file_path, lt_token, pkg_link["url"])
            print("Source code package {} downloaded successfully.".format(pkg_key), flush=True)
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

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, target_env, apps, trigger_manifest, include_test_apps)  # type: ignore
