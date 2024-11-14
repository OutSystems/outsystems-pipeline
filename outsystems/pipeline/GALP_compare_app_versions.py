# Python Modules
import sys
import os
import argparse

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
from outsystems.lifetime.lifetime_applications import get_running_app_version
from outsystems.lifetime.lifetime_environments import get_environment_key
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.file_helpers.file import store_data
# Exceptions
from outsystems.exceptions.app_does_not_exist import AppDoesNotExistError


# Retrieves the running versions of specified applications in a given environment.
# Returns a list of application details, or None if an application does not exist.
def get_running_app_versions(artifact_dir: str, lt_endpoint: str, lt_token: str, env_key: str, app_list: list):

    app_data_list = []

    for app_name in app_list:
        app_name = app_name.strip()

        try:
            # Attempt to get the running version of the application
            deployed = get_running_app_version(artifact_dir, lt_endpoint, lt_token, env_key, app_name=app_name)
            app_data_list.append({
                'Name': app_name,
                'Key': deployed["ApplicationKey"],
                'Version': deployed["Version"],
                'VersionKey': deployed["VersionKey"]
            })
        except AppDoesNotExistError:
            # If the app does not exist, append None with the app name
            app_data_list.append({
                'Name': app_name,
                'Key': None,
                'Version': None,
                'VersionKey': None
            })

    return app_data_list


# Compares application versions between two environments and checks for both
# version mismatches and missing applications in each environment.
def compare_app_versions(src_apps: list, tgt_apps: list, src_env_label: str, tgt_env_label: str):

    discrepancies = []

    # Create dictionaries for quick lookup by app name
    src_apps_dict = {app["Name"]: app for app in src_apps}
    tgt_apps_dict = {app["Name"]: app for app in tgt_apps}

    # Check each app in the source environment
    for src_app in src_apps:
        tgt_app = tgt_apps_dict.get(src_app["Name"])

        # If the app is missing in the target environment
        if not tgt_app or tgt_app["Version"] is None:
            discrepancies.append("'{}' is missing in {}".format(src_app['Name'], tgt_env_label))
        # If the app exists in both environments but has a version mismatch
        elif src_app["Version"] != tgt_app["Version"]:
            discrepancies.append("'{}' has different versions in {} ({}) and {} ({})".format(src_app['Name'], src_env_label, src_app['Version'], tgt_env_label, tgt_app['Version']))

    # Check each app in the target environment to find if any are missing in the source environment
    for tgt_app in tgt_apps:
        if tgt_app["Name"] not in src_apps_dict or src_apps_dict[tgt_app["Name"]]["Version"] is None:
            discrepancies.append("'{}' is missing in {}".format(tgt_app['Name'], src_env_label))

    return discrepancies


# Main function to compare application versions between two environments.
def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, src_env_label: str, tgt_env_label: str, apps: list):

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Gets the environment key for the source and target environments
    src_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, src_env_label)
    tgt_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, tgt_env_label)

    # Retrieve application versions for both environments
    src_apps = get_running_app_versions(artifact_dir, lt_endpoint, lt_token, src_env_key, apps)
    tgt_apps = get_running_app_versions(artifact_dir, lt_endpoint, lt_token, tgt_env_key, apps)

    # Compare the application versions and check for discrepancies
    discrepancies = compare_app_versions(src_apps, tgt_apps, src_env_label, tgt_env_label)

    # Output results and exit with error if there are discrepancies
    if discrepancies:
        for msg in discrepancies:
            print(msg, flush=True)
        store_data(artifact_dir, "discrepancies.cache", discrepancies)
        sys.exit(1)

    print("All provided apps between {} and {} have matching versions.".format(src_env_label, tgt_env_label), flush=True)


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
    parser.add_argument("-src", "--source_env", type=str, required=True,
                        help="Label of the source environment, as displayed in LifeTime.")
    parser.add_argument("-tgt", "--target_env", type=str, required=True,
                        help="Label of the target environment, as displayed in LifeTime.")
    parser.add_argument("-l", "--app_list", type=str, required=True,
                        help="Comma-separated list of apps you want to check. Example: \"App1,App2 With Spaces,App3_With_Underscores\"")

    args = parser.parse_args()

    # Parse arguments
    artifact_dir = args.artifacts
    lt_api_endpoint = args.lt_endpoint
    lt_http_proto = LIFETIME_HTTP_PROTO
    lt_url = args.lt_url
    if lt_url.startswith("http://"):
        lt_http_proto = "http"
        lt_url = lt_url.replace("http://", "")
    else:
        lt_url = lt_url.replace("https://", "")
    if lt_url.endswith("/"):
        lt_url = lt_url[:-1]
    lt_version = args.lt_api_version
    lt_token = args.lt_token
    source_env = args.source_env
    target_env = args.target_env
    apps = args.app_list.split(',')

    # Calls the main function
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, source_env, target_env, apps)
