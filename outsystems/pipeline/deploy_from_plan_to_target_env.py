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

sys.path.append("C:\\Users\\jfg\\source\\repos\\OutSystems\\outsystems-pipeline")

# Custom Modules
# Variables
from outsystems.vars.file_vars import ARTIFACT_FOLDER, DEPLOYMENT_FOLDER, DEPLOYMENT_MANIFEST_FILE
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION, DEPLOYMENT_MESSAGE
from outsystems.vars.pipeline_vars import QUEUE_TIMEOUT_IN_SECS, SLEEP_PERIOD_IN_SECS, CONFLICTS_FILE, \
    REDEPLOY_OUTDATED_APPS, DEPLOYMENT_TIMEOUT_IN_SECS, DEPLOYMENT_RUNNING_STATUS, DEPLOYMENT_WAITING_STATUS, \
    DEPLOYMENT_ERROR_STATUS_LIST, DEPLOY_ERROR_FILE
# Functions
from outsystems.lifetime.lifetime_environments import get_environment_app_version, get_environment_key
from outsystems.lifetime.lifetime_applications import get_application_version, get_application_data
from outsystems.lifetime.lifetime_deployments import get_deployment_status, get_deployment_info, \
    delete_deployment, start_deployment, continue_deployment, get_running_deployment
from outsystems.file_helpers.file import store_data, load_data
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.pipeline.deploy_latest_tags_to_target_env import generate_deploy_app_key, check_if_can_deploy, generate_regular_deployment
# Exceptions
from outsystems.exceptions.app_does_not_exist import AppDoesNotExistError


# ############################################################# SCRIPT ##############################################################


# Function that will build the info required for a deployment based on the latest versions of the apps in the src environment
def generate_manifest_based_on_deployment(artifact_dir: str, lt_endpoint: str, lt_token: str, src_env_key: str, deployment_plan_key: str):
    app_data_list = []  # will contain the applications to deploy details from LT
    deployment_manifest = []  # will store the deployment plan, that may be used in later stages of the pipeline

    # Get the details of the Deployment Plan (we're interested in the list of applications and versions)
    dep_details = get_deployment_info(artifact_dir, lt_endpoint, lt_token, deployment_plan_key)
    app_list = dep_details["Deployment"]["ApplicationOperations"]
    print(dep_details)
    # Creates a list with the details for the apps you want to deploy
    for app_oper in app_list:
        
        # Gather applications and version details required for the manifest
        app_key = app_oper["ApplicationKey"]
        app_name = get_application_data(artifact_dir, lt_endpoint, lt_token, False, app_key=app_key)["Name"]
        version_key = app_oper["ApplicationVersionKey"]
        version_name = get_application_version(artifact_dir, lt_endpoint, lt_token, False, version_key, app_key=app_key)["Version"]

        # Add it to the app data list
        app_data_list.append({'Name': app_name, 'Key': app_key, 'Version': version_name, 'VersionKey': version_key})

        app_data = {
                "ApplicationName": app_name,
                "ApplicationKey": app_key,
                "Version": version_name,
                "VersionKey": version_key
            }
        #print(app_data)
        # Add app to manifest, since this is a regular deployment
        deployment_manifest.append(app_data)

    # Store the manifest to be used in other stages of the pipeline
    filename = "{}/{}".format(DEPLOYMENT_FOLDER, DEPLOYMENT_MANIFEST_FILE)
    store_data(ARTIFACT_FOLDER, filename, deployment_manifest)

    return app_data_list



def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, source_env: str, dest_env: str, apps: list, deployment_plan_key: str, dep_note: str):

    app_data_list = []  # will contain the applications to deploy details from LT
    to_deploy_app_keys = []  # will contain the app keys for the apps tagged

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Gets the environment key for the source environment
    src_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, source_env)
    # Gets the environment key for the destination environment
    dest_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, dest_env)

    # Generate the Manifest file based on the information
    # contained within the deployment plan.
    # app_data_list = generate_manifest_based_on_deployment(artifact_dir, lt_endpoint, lt_token, src_env_key, deployment_plan_key)

    # to_deploy_app_keys = check_if_can_deploy(artifact_dir, lt_endpoint, lt_api_version, lt_token, dest_env_key, dest_env, app_data_list)
    
    # Check if there are apps to be deployed
    # if len(to_deploy_app_keys) == 0:
    #    print("Deployment skipped because {} environment already has the target application deployed with the same tags.".format(dest_env), flush=True)
    #    sys.exit(0)

    # Wait until the LifeTime server is ready to deploy
    # wait_counter = 0
    # deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_key)
    # while len(deployments) > 0:
    #     if wait_counter >= QUEUE_TIMEOUT_IN_SECS:
    #         print("Timeout occurred while waiting for LifeTime to be free, to create the new deployment plan.", flush=True)
    #         sys.exit(1)
    #     sleep(SLEEP_PERIOD_IN_SECS)
    #     wait_counter += SLEEP_PERIOD_IN_SECS
    #     print("Waiting for LifeTime to be free. Elapsed time: {} seconds...".format(wait_counter), flush=True)
    #     deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_key)

    # LT is free to deploy.
    # Initiate the process.
    dep_plan_key = deployment_plan_key

    # Check if created deployment plan has conflicts.
    # It should have already been validated when the
    # the Team Lead created it in LifeTime, but we
    # can double check it here.
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
	            # Create the manifest file based on the running versions of source environment, after tagging.
                generate_regular_deployment(artifact_dir, lt_endpoint, lt_token, src_env_key, apps)
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
                        help="Comma separated list of apps in the scope of the pipeline. Example: \"App1,App2 With Spaces,App3_With_Underscores\"")
    parser.add_argument("-p", "--deployment_plan_key", type=str, required=True,
                        help="Key of the deployment plan created in LifeTime that defines the scope of applications to be deployed.")


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
    # Parse Deployment Plan Key
    deployment_plan_key = args.deployment_plan_key
    # Parse Deployment Message
    dep_note = args.deploy_msg
    # Parse App list
    _apps = args.app_list
    apps = _apps.split(',')

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, source_env, dest_env, apps, deployment_plan_key, dep_note)
