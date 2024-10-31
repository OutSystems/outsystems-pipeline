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
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION, DEPLOYMENT_MESSAGE
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS, MANIFEST_ENVIRONMENT_DEFINITIONS, MANIFEST_DEPLOYMENT_NOTES, \
    MANIFEST_APPLICATION_KEY, MANIFEST_APPLICATION_NAME, MANIFEST_APPLICATION_VERSION_KEY, MANIFEST_APPLICATION_VERSION_NUMBER, \
    MANIFEST_ENVIRONMENT_KEY, MANIFEST_ENVIRONMENT_NAME, MANIFEST_ENVIRONMENT_LABEL, MANIFEST_FLAG_IS_TEST_APPLICATION, \
    MANIFEST_FOLDER, MANIFEST_FILE

# Functions
from outsystems.lifetime.lifetime_environments import get_environments, get_environment_deployment_zones
from outsystems.lifetime.lifetime_applications import get_running_app_version, get_application_data
from outsystems.file_helpers.file import store_data
from outsystems.lifetime.lifetime_base import build_lt_endpoint


# Function that will build the info required for the environments
def generate_manifest_env_info(artifact_dir: str, lt_endpoint: str, lt_token: str):
    # Gets all infra environments information
    infra_envs = get_environments(artifact_dir, lt_endpoint, lt_token)

    # Trims info to include only the desired env info (Name and Key)
    env_info = [{MANIFEST_ENVIRONMENT_KEY: env["Key"], MANIFEST_ENVIRONMENT_NAME: env["Name"], MANIFEST_ENVIRONMENT_LABEL: env["Name"]} for env in infra_envs if "Name" in env and "Key" in env]

    return env_info


# Function that will build the info required for a deployment based on the latest versions of the apps in the src environment
def generate_manifest_app_info(artifact_dir: str, lt_endpoint: str, lt_token: str, src_env_key: str, app_list: list):
    app_data_list = []  # will contain the applications to deploy details from LT

    deployment_zones = get_environment_deployment_zones(artifact_dir, lt_endpoint, lt_token, env_key=src_env_key)

    # Creates a list with the details for the apps you want to deploy
    for app_name in app_list:
        # Removes whitespaces in the beginning and end of the string
        app_name = app_name.strip()

        # Get the app running version on the source environment. It will only retrieve tagged applications
        app_info = get_running_app_version(artifact_dir, lt_endpoint, lt_token, src_env_key, app_name=app_name)

        # Get the module info
        app_module_data = get_application_data(artifact_dir, lt_endpoint, lt_token, True, app_key=app_info[MANIFEST_APPLICATION_KEY])

        # Get deployment zone info
        deployment_zone_key = next((item['DeploymentZoneKey'] for item in app_module_data['AppStatusInEnvs'] if item['EnvironmentKey'] == src_env_key), None)
        deployment_zone_name = next((item['Name'] for item in deployment_zones if item['Key'] == deployment_zone_key), None)

        # Add it to the app data list
        app_data_list.append({MANIFEST_APPLICATION_KEY: app_info[MANIFEST_APPLICATION_KEY], MANIFEST_APPLICATION_NAME: app_info[MANIFEST_APPLICATION_NAME],
                              MANIFEST_APPLICATION_VERSION_KEY: app_info[MANIFEST_APPLICATION_VERSION_KEY], MANIFEST_APPLICATION_VERSION_NUMBER: app_info["Version"],
                              'CreatedOn': app_info["CreatedOn"], 'ChangeLog': app_info["ChangeLog"], MANIFEST_FLAG_IS_TEST_APPLICATION: False,
                              'DeploymentZoneKey': deployment_zone_key, 'DeploymentZoneName': deployment_zone_name})

    return app_data_list


# Function that will generate and save the manifest file
def generate_manifest_file(artifact_dir: str, app_details: list, env_details: list, dep_note: str):

    manifest_data = {
        MANIFEST_APPLICATION_VERSIONS: app_details,
        MANIFEST_ENVIRONMENT_DEFINITIONS: env_details,
        MANIFEST_DEPLOYMENT_NOTES: dep_note
    }

    # Store the manifest to be used in other stages of the pipeline
    filename = "{}/{}".format(MANIFEST_FOLDER, MANIFEST_FILE)
    store_data(artifact_dir, filename, manifest_data)
    return manifest_data


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, source_env: str, apps: list, dep_note: str):

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Save environments info structure for manifest
    env_details = generate_manifest_env_info(artifact_dir, lt_endpoint, lt_token)

    # Gets the environment key for the source environment
    src_env_key = next((env["EnvironmentKey"] for env in env_details if env.get("EnvironmentName") == source_env), None)

    # Save applications info structure for manifest
    app_details = generate_manifest_app_info(artifact_dir, lt_endpoint, lt_token, src_env_key, apps)

    generate_manifest_file(artifact_dir, app_details, env_details, dep_note)

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
    parser.add_argument("-s", "--source_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the source environment where the apps are.")
    parser.add_argument("-l", "--app_list", type=str, required=True,
                        help="Comma separated list of apps you want to deploy. Example: \"App1,App2 With Spaces,App3_With_Underscores\"")
    parser.add_argument("-m", "--deploy_msg", type=str, default=DEPLOYMENT_MESSAGE,
                        help="Message you want to show on the deployment plans in LifeTime. Default: \"Automated deploy using OS Pipelines\".")
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
    # Parse Source Environment
    source_env = args.source_env
    # Parse App list
    _apps = args.app_list
    apps = _apps.split(',')
    # Parse Deployment Message
    dep_note = args.deploy_msg

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, source_env, apps, dep_note)
