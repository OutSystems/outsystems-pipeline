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
from outsystems.vars.pipeline_vars import MAX_VERSIONS_TO_RETURN, TAG_APP_MAX_RETRIES
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS

# Functions
from outsystems.lifetime.lifetime_applications import get_applications, get_running_app_version, get_application_versions
from outsystems.lifetime.lifetime_environments import get_environment_key
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.lifetime.lifetime_applications import set_application_version
from outsystems.file_helpers.file import load_data

# Exceptions
from outsystems.exceptions.manifest_does_not_exist import ManifestDoesNotExistError

# ############################################################# SCRIPT ##############################################################


def generate_new_version_number(base_version: str):
    # Split tag version digits
    base_version = base_version.split('.')  # type: ignore

    # Default values for Major.Minor.Revison
    maj = base_version[0]
    min = "0"
    rev = "1"

    if not len(base_version) < 2:
        min = base_version[1]

    if not len(base_version) < 3:
        # Increment revision number
        rev = str(int(base_version[2]) + 1)

    return "{}.{}.{}".format(maj, min, rev)


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, dest_env: str, trigger_manifest: dict, log_msg: str):
    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Get the environment key
    env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, dest_env)

    # Get all applications info
    all_apps = get_applications(artifact_dir, lt_endpoint, lt_token, True)

    for app_name in trigger_manifest[MANIFEST_APPLICATION_VERSIONS]:
        # Gets application specific details
        app_detail = list(filter(lambda x: x["Name"] == app_name["ApplicationName"], all_apps))

        if len(app_detail):
            # Checks if application is modified in target env
            app_env_detail = list(filter(lambda x: x["EnvironmentKey"] == env_key and x["IsModified"], app_detail[0]["AppStatusInEnvs"]))

            if len(app_env_detail):
                current_tag = get_running_app_version(artifact_dir, lt_endpoint, lt_token, env_key, app_name=app_name)
                generated_tag = generate_new_version_number(current_tag["Version"])

                # List of the last application tags
                tag_history_list = [d["Version"] for d in get_application_versions(artifact_dir, lt_endpoint, lt_token, MAX_VERSIONS_TO_RETURN, app_name=app_name)]

                # Finds next available tag number
                retries = 0
                while retries < TAG_APP_MAX_RETRIES:
                    if generated_tag in tag_history_list:
                        generated_tag = generate_new_version_number(generated_tag)
                    else:
                        # Checks if app is mobile and gets mobile info
                        app_mobile_detail = list(filter(lambda x: x["IsModified"], app_env_detail[0]["MobileAppsStatus"]))

                        # Will contain the List of mobile versions to tag
                        native_shell_versions = []

                        # Generate new version number for each native shell
                        if app_mobile_detail:
                            for native_shell in app_mobile_detail:
                                native_shell_versions.append({"NativePlatform": native_shell["NativePlatform"], "VersionNumber": generate_new_version_number(native_shell["VersionNumber"]), "VersionDescription": log_msg})

                        set_application_version(lt_endpoint, lt_token, env_key, current_tag["ApplicationKey"], log_msg, generated_tag, native_shell_versions)
                        print("Application '{}' successfully tagged to version {} on environment '{}'".format(current_tag["ApplicationName"], generated_tag, dest_env), flush=True)
                        break

                    retries += 1
                    if retries == TAG_APP_MAX_RETRIES:
                        print("Could not find available tag for Application '{}' ".format(current_tag["ApplicationName"]), flush=True)

# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-u", "--lt_url", type=str, required=True,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
    parser.add_argument("-t", "--lt_token", type=str, required=True,
                        help="Token for LifeTime API calls.")
    parser.add_argument("-v", "--lt_api_version", type=int, default=LIFETIME_API_VERSION,
                        help="LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
    parser.add_argument("-e", "--lt_endpoint", type=str, default=LIFETIME_API_ENDPOINT,
                        help="(optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-d", "--dest_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the environment where you want to tag the apps.")
    parser.add_argument("-m", "--trigger_manifest", type=str,
                        help="Manifest artifact (in JSON format) received when the pipeline is triggered. Contains required data used throughout the pipeline execution.")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="Manifest file (with JSON format). Contains required data used throughout the pipeline execution.")
    parser.add_argument("-l", "--log_msg", type=str, default="Version created automatically using outsystems-pipeline package.",
                        help="(optional) log message to be added to the new tags")
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
    # Parse Destination Environment
    dest_env = args.dest_env
    # Validate Manifest is being passed either as JSON or as file
    if not args.trigger_manifest and not args.manifest_file:
        raise ManifestDoesNotExistError("The manifest was not provided as JSON or as a file. Aborting!")
    # Parse Trigger Manifest artifact
    if args.manifest_file:
        trigger_manifest_path = os.path.split(args.manifest_file)
        trigger_manifest = load_data(trigger_manifest_path[0], trigger_manifest_path[1])
    else:
        trigger_manifest = json.loads(args.trigger_manifest)
    # Parse Log Message
    log_msg = args.log_msg
    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, dest_env, trigger_manifest, log_msg)
