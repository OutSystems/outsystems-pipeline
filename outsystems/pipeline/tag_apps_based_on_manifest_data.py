# Python Modules
import sys
import os
import argparse
from packaging.version import Version

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

# Functions
from outsystems.file_helpers.file import load_data
from outsystems.lifetime.lifetime_environments import get_environment_key
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.lifetime.lifetime_applications import set_application_version, get_running_app_version
from outsystems.vars.vars_base import load_configuration_file
# Exceptions
from outsystems.exceptions.invalid_parameters import InvalidParametersError


# ############################################################# SCRIPT ##############################################################
def valid_tag_number(artifact_dir: str, lt_endpoint: str, lt_token: str, env_name: str, env_key: str, app: dict):
    # Get the app running version on the source environment. It will only retrieve tagged applications
    running_app = get_running_app_version(artifact_dir, lt_endpoint, lt_token, env_key, app_name=app["ApplicationName"])

    if Version(running_app["Version"]) < Version(app["VersionNumber"]):
        return True

    print("Skipping tag! Application '{}' current tag ({}) on {} is greater than or equal to the manifest data ({}). ".format(app["ApplicationName"], running_app["Version"], env_name, app["VersionNumber"]), flush=True)
    return False


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, dest_env: str, app_list: list, dep_manifest: list, trigger_manifest: dict, include_test_apps: bool):
    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)
    # Get the environment keys
    dest_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, dest_env)

    # the app versions MUST come from that a file
    # either deployment or trigger manifest file
    if dep_manifest:
        for deployed_app in dep_manifest:
            if deployed_app["ApplicationName"] in app_list:
                set_application_version(lt_endpoint, lt_token, dest_env_key, deployed_app["ApplicationKey"], deployed_app["ChangeLog"], deployed_app["Version"], None)
                print("{} application successuflly tagged as {} on {}".format(deployed_app["ApplicationName"], deployed_app["Version"], dest_env), flush=True)
    elif trigger_manifest:
        for deployed_app in trigger_manifest["ApplicationVersions"]:
            if not deployed_app["IsTestApplication"] or (deployed_app["IsTestApplication"] and include_test_apps):
                if valid_tag_number(artifact_dir, lt_endpoint, lt_token, dest_env, dest_env_key, deployed_app):
                    set_application_version(lt_endpoint, lt_token, dest_env_key, deployed_app["ApplicationKey"], deployed_app["ChangeLog"], deployed_app["VersionNumber"], None)
                    print("{} application successuflly tagged as {} on {}".format(deployed_app["ApplicationName"], deployed_app["VersionNumber"], dest_env), flush=True)
                else:
                    continue

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
                        help="(Optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-d", "--destination_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the destination environment where you want to deploy the apps. (if in Airgap mode should be the hostname of the destination environment where you want to deploy the apps)")
    parser.add_argument("-l", "--app_list", type=str,
                        help="(Optional) Comma separated list of apps you want to tag. Example: \"App1,App2 With Spaces,App3_With_Underscores\"")
    parser.add_argument("-f", "--manifest_file", type=str, required=True,
                        help="Manifest file path (either deployment or trigger).")
    parser.add_argument("-i", "--include_test_apps", action='store_true',
                        help="(Optional) Flag that indicates if applications marked as \"Test Application\" in the trigger manifest are included for tagging.")
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
    # Parse Destination Environment
    dest_env = args.destination_env

    # Parse Manifest file if it exists
    # Based on the file content it can be a deployment manifest (list-based) or trigger manifest (dict-based)
    manifest_file = None
    if args.manifest_file:
        manifest_path = os.path.split(args.manifest_file)
        manifest_file = load_data(manifest_path[0], manifest_path[1])

    dep_manifest = manifest_file if type(manifest_file) is list else None
    trigger_manifest = manifest_file if type(manifest_file) is dict else None

    if dep_manifest and not args.app_list:
        raise InvalidParametersError("--app_list parameter is required for Deployment Manifest operation")

    # Parse App list
    apps = None
    if args.app_list:
        _apps = args.app_list
        apps = _apps.split(',')

    # Parse Include Test Apps flag
    include_test_apps = args.include_test_apps
    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, dest_env, apps, dep_manifest, trigger_manifest, include_test_apps)  # type: ignore
