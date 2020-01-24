# Python Modules
import sys
import os
import argparse
from pkg_resources import parse_version
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
from outsystems.vars.file_vars import ARTIFACT_FOLDER, DEPLOYMENT_FOLDER, DEPLOYMENT_MANIFEST_FILE
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION, DEPLOYMENT_MESSAGE
from outsystems.vars.pipeline_vars import QUEUE_TIMEOUT_IN_SECS, SLEEP_PERIOD_IN_SECS, CONFLICTS_FILE, \
    REDEPLOY_OUTDATED_APPS, DEPLOYMENT_TIMEOUT_IN_SECS, DEPLOYMENT_RUNNING_STATUS, DEPLOYMENT_WAITING_STATUS, \
    DEPLOYMENT_ERROR_STATUS_LIST, DEPLOY_ERROR_FILE
# Functions
from outsystems.lifetime.lifetime_environments import get_environment_app_version, get_environment_key
from outsystems.lifetime.lifetime_applications import get_running_app_version, get_application_version
from outsystems.lifetime.lifetime_deployments import get_deployment_status, get_deployment_info, \
    send_deployment, delete_deployment, start_deployment, continue_deployment, get_running_deployment
from outsystems.file_helpers.file import store_data, load_data
from outsystems.lifetime.lifetime_base import build_lt_endpoint
# Exceptions
from outsystems.exceptions.app_does_not_exist import AppDoesNotExistError


# ############################################################# SCRIPT ##############################################################
# Function that will generate the app key portion of the deployment for LifeTime, based on the API level
def generate_deploy_app_key(lt_api_version: int, app_version_key: str, deploy_zone=""):
    if lt_api_version == 1:  # LT for OS version < 11
        return app_version_key
    elif lt_api_version == 2:  # LT for OS v11
        return {"ApplicationVersionKey": app_version_key, "DeploymentZoneKey": deploy_zone}
    else:
        raise NotImplementedError("Please make sure the API version is compatible with the module.")


# Function that will build the info required for a deployment based on a manifest file
def generate_deployment_based_on_manifest(artifact_dir: str, lt_endpoint: str, lt_token: str, src_env_key: str, src_env_name: str, app_list: list, manifest: list):
    app_data_list = []  # will contain the applications details from the manifest

    for deployed_app in manifest:
        if deployed_app["ApplicationName"] in app_list:
            try:
                get_application_version(artifact_dir, lt_endpoint, lt_token, False, deployed_app["VersionKey"], app_name=deployed_app["ApplicationName"])
            except AppDoesNotExistError:
                print("Application {} with version {} no longer exists in {}. The manifest no longer reflects the current state of the environment. Aborting!".format(deployed_app["ApplicationName"], deployed_app["Version"], src_env_name), flush=True)
                sys.exit(1)
            except Exception as error:
                print("Error trying to validate if the application {} exists in the {} environment.\nError: {}".format(deployed_app["ApplicationName"], src_env_name, error), flush=True)
                sys.exit(1)

            # Add it to the app data list
            app_data_list.append({'Name': deployed_app["ApplicationName"], 'Key': deployed_app["ApplicationKey"], 'Version': deployed_app["Version"], 'VersionKey': deployed_app["VersionKey"]})

    return app_data_list


# Function that will build the info required for a deployment based on the latest versions of the apps in the src environment
def generate_regular_deployment(artifact_dir: str, lt_endpoint: str, lt_token: str, src_env_key: str, app_list: list):
    app_data_list = []  # will contain the applications to deploy details from LT
    deployment_manifest = []  # will store the deployment plan, that may be used in later stages of the pipeline

    # Creates a list with the details for the apps you want to deploy
    for app_name in app_list:
        # Removes whitespaces in the beginning and end of the string
        app_name = app_name.strip()

        # Get the app running version on the source environment. It will only retrieve tagged applications
        deployed = get_running_app_version(artifact_dir, lt_endpoint, lt_token, src_env_key, app_name=app_name)

        # Add it to the app data list
        app_data_list.append({'Name': app_name, 'Key': deployed["ApplicationKey"], 'Version': deployed["Version"], 'VersionKey': deployed["VersionKey"]})

        # Add app to manifest, since this is a regular deployment
        deployment_manifest.append(deployed)

    # Store the manifest to be used in other stages of the pipeline
    filename = "{}/{}".format(DEPLOYMENT_FOLDER, DEPLOYMENT_MANIFEST_FILE)
    store_data(ARTIFACT_FOLDER, filename, deployment_manifest)

    return app_data_list


# Function to check if target environment already has the application versions to be deployed
def check_if_can_deploy(artifact_dir: str, lt_endpoint: str, lt_api_version: str, lt_token: str, env_key: str, env_name: str, app_data_list: list):
    app_keys = []  # will contain the application keys to create the deployment plan
    for app in app_data_list:
        # get the status of the app in the target env, to check if they were deployed
        try:
            app_status = get_environment_app_version(artifact_dir, lt_endpoint, lt_token, True, env_name=env_name, app_key=app["Key"])
            # Check if the app version is already deployed in the target environment
            for app_in_env in app_status["AppStatusInEnvs"]:
                if app_in_env["EnvironmentKey"] == env_key:
                    # Check if the target environment has the version deployed
                    if app_in_env["BaseApplicationVersionKey"] != app["VersionKey"]:
                        # The version is not the one deployed -> need to compare the version tag
                        app_in_env_data = get_application_version(artifact_dir, lt_endpoint, lt_token, False, app_in_env["BaseApplicationVersionKey"], app_key=app["Key"])
                        # If the version in the environment is bigger than the one in the manifest -> stale pipeline -> abort
                        if parse_version(app_in_env_data["Version"]) > parse_version(app["Version"]):
                            print("The deployment manifest is stale. The Application {} needs to be deployed with version {} but then environment {} has the version {}.\nReason: VersionTag is inferior to the VersionTag already deployed.\nAborting the pipeline.".format(app["Name"], app["Version"], env_name, app_in_env_data["Version"]), flush=True)
                            sys.exit(1)
                        elif parse_version(app_in_env_data["Version"]) == parse_version(app["Version"]):
                            print("Skipping application {} with version {}, since it's already deployed in {} environment.\nReason: VersionTag is equal.".format(app["Name"], app["Version"], env_name), flush=True)
                        else:
                            # Generated app_keys for deployment plan based on the running version
                            app_keys.append(generate_deploy_app_key(lt_api_version, app["VersionKey"]))
                            print("Adding application {} with version {}, to be deployed in {} environment.".format(app["Name"], app["Version"], env_name), flush=True)
                    else:
                        print("Skipping application {} with version {}, since it's already deployed in {} environment.\nReason: VersionKey is equal.".format(app["Name"], app["Version"], env_name), flush=True)
        except AppDoesNotExistError:
            app_keys.append(generate_deploy_app_key(lt_api_version, app["VersionKey"]))
            print("App {} with version {} does not exist in {} environment. Ignoring check and deploy it.".format(app["Name"], app["Version"], dest_env), flush=True)
    return app_keys


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, source_env: str, dest_env: str, apps: list, dep_manifest: list, dep_note: str):

    app_data_list = []  # will contain the applications to deploy details from LT
    to_deploy_app_keys = []  # will contain the app keys for the apps tagged

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Gets the environment key for the source environment
    src_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, source_env)
    # Gets the environment key for the destination environment
    dest_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, dest_env)

    # If the manifest file is being used, the app versions MUST come from that file
    # Or else you might not be deploying the same app versions that were deployed in
    # previous pipeline steps
    if dep_manifest:
        app_data_list = generate_deployment_based_on_manifest(artifact_dir, lt_endpoint, lt_token, src_env_key, source_env, apps, dep_manifest)
    else:
        app_data_list = generate_regular_deployment(artifact_dir, lt_endpoint, lt_token, src_env_key, apps)

    to_deploy_app_keys = check_if_can_deploy(artifact_dir, lt_endpoint, lt_api_version, lt_token, dest_env_key, dest_env, app_data_list)

    # Check if there are apps to be deployed
    if len(to_deploy_app_keys) == 0:
        print("Deployment skipped because {} environment already has the target application deployed with the same tags.".format(dest_env), flush=True)
        sys.exit(0)

    # Write the names and keys of the application versions to be deployed
    to_deploy_app_names = []
    to_deploy_app_info = []
    for app in app_data_list:
        for deploying_apps in to_deploy_app_keys:
            if lt_api_version == 1:  # LT for OS version < 11
                if deploying_apps == app["VersionKey"]:
                    to_deploy_app_names.append(app["Name"])
                    to_deploy_app_info.append(app)
            elif lt_api_version == 2:  # LT for OS v11
                if deploying_apps["ApplicationVersionKey"] == app["VersionKey"]:
                    to_deploy_app_names.append(app["Name"])
                    to_deploy_app_info.append(app)
            else:
                raise NotImplementedError("Please make sure the API version is compatible with the module.")
    print("Creating deployment plan from {} to {} including applications: {} ({}).".format(source_env, dest_env, to_deploy_app_names, to_deploy_app_info), flush=True)

    wait_counter = 0
    deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_key)
    while len(deployments) > 0:
        if wait_counter >= QUEUE_TIMEOUT_IN_SECS:
            print("Timeout occurred while waiting for LifeTime to be free, to create the new deployment plan.", flush=True)
            sys.exit(1)
        sleep(SLEEP_PERIOD_IN_SECS)
        wait_counter += SLEEP_PERIOD_IN_SECS
        print("Waiting for LifeTime to be free. Elapsed time: {} seconds...".format(wait_counter), flush=True)
        deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_key)

    # LT is free to deploy
    # Send the deployment plan and grab the key
    dep_plan_key = send_deployment(artifact_dir, lt_endpoint, lt_token, lt_api_version, to_deploy_app_keys, dep_note, source_env, dest_env)
    print("Deployment plan {} created successfully.".format(dep_plan_key), flush=True)

    # Check if created deployment plan has conflicts
    dep_details = get_deployment_info(artifact_dir, lt_endpoint, lt_token, dep_plan_key)
    if len(dep_details["ApplicationConflicts"]) > 0:
        store_data(artifact_dir, CONFLICTS_FILE, dep_details["ApplicationConflicts"])
        print("Deployment plan {} has conflicts and will be aborted. Check {} artifact for more details.".format(dep_plan_key, CONFLICTS_FILE), flush=True)
        # Abort previously created deployment plan to target environment
        delete_deployment(lt_endpoint, lt_token, dep_plan_key)
        print("Deployment plan {} was deleted successfully.".format(dep_plan_key), flush=True)
        sys.exit(1)

    # Check if outdated consumer applications (outside of deployment plan) should be redeployed and start the deployment plan execution
    if lt_api_version == 1:  # LT for OS version < 11
        start_deployment(lt_endpoint, lt_token, dep_plan_key)
    elif lt_api_version == 2:  # LT for OS v11
        start_deployment(lt_endpoint, lt_token, dep_plan_key, redeploy_outdated=REDEPLOY_OUTDATED_APPS)
    else:
        raise NotImplementedError("Please make sure the API version is compatible with the module.")
    print("Deployment plan {} started being executed.".format(dep_plan_key), flush=True)

    # Sleep thread until deployment has finished
    wait_counter = 0
    while wait_counter < DEPLOYMENT_TIMEOUT_IN_SECS:
        # Check Deployment Plan status.
        dep_status = get_deployment_status(
            artifact_dir, lt_endpoint, lt_token, dep_plan_key)
        if dep_status["DeploymentStatus"] != DEPLOYMENT_RUNNING_STATUS:
            # Check deployment status is pending approval. Force it to continue (if 2-Step deployment is enabled)
            if dep_status["DeploymentStatus"] == DEPLOYMENT_WAITING_STATUS:
                continue_deployment(lt_endpoint, lt_token, dep_plan_key)
                print("Deployment plan {} resumed execution.".format(dep_plan_key), flush=True)
            elif dep_status["DeploymentStatus"] in DEPLOYMENT_ERROR_STATUS_LIST:
                print("Deployment plan finished with status {}.".format(dep_status["DeploymentStatus"]), flush=True)
                store_data(artifact_dir, DEPLOY_ERROR_FILE, dep_status)
                sys.exit(1)
            else:
                # If it reaches here, it means the deployment was successful
                print("Deployment plan finished with status {}.".format(dep_status["DeploymentStatus"]), flush=True)
                # Exit the script to continue with the pipeline
                sys.exit(0)
        # Deployment status is still running. Go back to sleep.
        sleep(SLEEP_PERIOD_IN_SECS)
        wait_counter += SLEEP_PERIOD_IN_SECS
        print("{} secs have passed since the deployment started...".format(wait_counter), flush=True)

    # Deployment timeout reached. Exit script with error
    print("Timeout occurred while deployment plan is still in {} status.".format(DEPLOYMENT_RUNNING_STATUS), flush=True)
    sys.exit(1)


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
    parser.add_argument("-d", "--destination_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the destination environment where you want to deploy the apps.")
    parser.add_argument("-m", "--deploy_msg", type=str, default=DEPLOYMENT_MESSAGE,
                        help="Message you want to show on the deployment plans in LifeTime. Default: \"Automated deploy using OS Pipelines\".")
    parser.add_argument("-l", "--app_list", type=str, required=True,
                        help="Comma separated list of apps you want to deploy. Example: \"App1,App2 With Spaces,App3_With_Underscores\"")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="(optional) Manifest file path, used to promote the same application versions throughout the pipeline execution.")

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
    # Parse Destination Environment
    dest_env = args.destination_env
    # Parse App list
    _apps = args.app_list
    apps = _apps.split(',')
    # Parse Manifest file if it exists
    if args.manifest_file:
        manifest_file = load_data("", args.manifest_file)
    else:
        manifest_file = None
    # Parse Deployment Message
    dep_note = args.deploy_msg

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, source_env, dest_env, apps, manifest_file, dep_note)
