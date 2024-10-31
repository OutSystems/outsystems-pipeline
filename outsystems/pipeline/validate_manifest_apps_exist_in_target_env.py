# Python Modules
import sys
import os
import argparse
import json

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
# Variables
from outsystems.vars.file_vars import ARTIFACT_FOLDER
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS, MANIFEST_FLAG_IS_TEST_APPLICATION, MANIFEST_APPLICATION_NAME
# Functions
from outsystems.lifetime.lifetime_applications import get_applications
from outsystems.lifetime.lifetime_environments import get_environment_key
from outsystems.file_helpers.file import load_data
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.vars.vars_base import load_configuration_file
# Exceptions
from outsystems.exceptions.app_does_not_exist import AppDoesNotExistError
from outsystems.exceptions.manifest_does_not_exist import ManifestDoesNotExistError


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, env_label: str, include_test_apps: bool, trigger_manifest: dict):

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Gets the environment key for the target environment
    env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, env_label)

    # Get Applications without extra data
    apps = get_applications(artifact_dir, lt_endpoint, lt_token, True)
    print("OS Applications data retrieved successfully.", flush=True)

    app_names_to_validate = [app[MANIFEST_APPLICATION_NAME] for app in trigger_manifest.get(MANIFEST_APPLICATION_VERSIONS, []) if include_test_apps or not app.get(MANIFEST_FLAG_IS_TEST_APPLICATION)]

    # Check if all manifest application names exist in the infra
    if not all(any(app["Name"] == app_name for app in apps) for app_name in app_names_to_validate):
        raise AppDoesNotExistError("One or more applications not found in this infra.")

    # Check if the each manifest application exists in the provided environment
    for app_info in apps:
        if app_info["Name"] in app_names_to_validate:
            app_status_in_envs = app_info.get("AppStatusInEnvs", [])
            environment_keys = [env["EnvironmentKey"] for env in app_status_in_envs]
            if env_key not in environment_keys:
                raise AppDoesNotExistError("Application '{}' does not exist in '{}' Environment .".format(app_info['Name'], env_key))

    print("All Trigger Manifest Applications exist in the {} Environment.".format(env_label), flush=True)

# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="(Optional) Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-u", "--lt_url", type=str, required=True,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
    parser.add_argument("-t", "--lt_token", type=str, required=True,
                        help="Token for LifeTime API calls.")
    parser.add_argument("-v", "--lt_api_version", type=int, default=LIFETIME_API_VERSION,
                        help="(Optional) LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
    parser.add_argument("-e", "--lt_endpoint", type=str, default=LIFETIME_API_ENDPOINT,
                        help="(Optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-s", "--env_label", type=str, required=True,
                        help="Label, as configured in the manifest, of the source environment where the apps are.")
    parser.add_argument("-i", "--include_test_apps", action='store_true',
                        help="Flag that indicates if applications marked as \"Test Application\" in the manifest are included in the deployment plan.")
    parser.add_argument("-m", "--trigger_manifest", type=str,
                        help="Manifest artifact (in JSON format) received when the pipeline is triggered. Contains required data used throughout the pipeline execution.")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="Manifest file (with JSON format). Contains required data used throughout the pipeline execution.")
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
    lt_version = args.lt_api_version
    # Parse the LT Token
    lt_token = args.lt_token
    # Parse Environment
    env_label = args.env_label
    # Parse Include Test Apps flag
    include_test_apps = args.include_test_apps

    # Validate Manifest is being passed either as JSON or as file
    if not args.trigger_manifest and not args.manifest_file:
        raise ManifestDoesNotExistError("The manifest was not provided as JSON or as a file. Aborting!")

    # Parse Trigger Manifest artifact
    if args.manifest_file:
        trigger_manifest_path = os.path.split(args.manifest_file)
        trigger_manifest = load_data(trigger_manifest_path[0], trigger_manifest_path[1])
    else:
        trigger_manifest = json.loads(args.trigger_manifest)

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, env_label, include_test_apps, trigger_manifest)
