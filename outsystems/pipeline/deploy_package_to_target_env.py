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
from outsystems.vars.file_vars import ARTIFACT_FOLDER
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION
from outsystems.vars.pipeline_vars import QUEUE_TIMEOUT_IN_SECS, SLEEP_PERIOD_IN_SECS, CONFLICTS_FILE, \
    REDEPLOY_OUTDATED_APPS, DEPLOYMENT_TIMEOUT_IN_SECS, DEPLOYMENT_RUNNING_STATUS, DEPLOYMENT_WAITING_STATUS, \
    DEPLOYMENT_ERROR_STATUS_LIST, DEPLOY_ERROR_FILE, ALLOW_CONTINUE_WITH_ERRORS
# Functions
from outsystems.lifetime.lifetime_environments import get_environment_key
from outsystems.lifetime.lifetime_deployments import get_deployment_status, get_deployment_info, \
    send_binary_deployment, delete_deployment, start_deployment, continue_deployment, get_running_deployment, \
    check_deployment_two_step_deploy_status
from outsystems.file_helpers.file import store_data, is_valid_os_package
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.vars.vars_base import get_configuration_value, load_configuration_file
# Exceptions
from outsystems.exceptions.invalid_os_package import InvalidOutSystemsPackage


# ############################################################# SCRIPT ##############################################################
def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, dest_env_label: str, force_two_step_deployment: bool, package_path: str):

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Gets the environment key for the destination environment
    dest_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, dest_env_label)

    wait_counter = 0
    deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_key)
    while len(deployments) > 0:
        if wait_counter >= get_configuration_value("QUEUE_TIMEOUT_IN_SECS", QUEUE_TIMEOUT_IN_SECS):
            print("Timeout occurred while waiting for LifeTime to be free, to create the new deployment plan.", flush=True)
            sys.exit(1)
        sleep_value = get_configuration_value("SLEEP_PERIOD_IN_SECS", SLEEP_PERIOD_IN_SECS)
        sleep(sleep_value)
        wait_counter += sleep_value
        print("Waiting for LifeTime to be free. Elapsed time: {} seconds...".format(wait_counter), flush=True)
        deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_key)

    # LT is free to deploy
    # Validate if file has OutSystems package extension
    if not is_valid_os_package(package_path):
        raise InvalidOutSystemsPackage("Binary file is not an OutSystems package. Expected 'osp' or 'oap' as file extension.")

    # Send the deployment plan and grab the key
    dep_plan_key = send_binary_deployment(artifact_dir, lt_endpoint, lt_token, lt_api_version, dest_env_key, package_path)
    print("Deployment plan {} created successfully.".format(dep_plan_key), flush=True)

    # Check if created deployment plan has conflicts
    dep_details = get_deployment_info(artifact_dir, lt_endpoint, lt_token, dep_plan_key)
    has_conflicts = len(dep_details["ApplicationConflicts"]) > 0
    if has_conflicts:
        store_data(artifact_dir, CONFLICTS_FILE, dep_details["ApplicationConflicts"])
        if not get_configuration_value("ALLOW_CONTINUE_WITH_ERRORS", ALLOW_CONTINUE_WITH_ERRORS) or lt_api_version == 1:
            print("Deployment plan {} has conflicts and will be aborted. Check {} artifact for more details.".format(dep_plan_key, CONFLICTS_FILE), flush=True)
            # Abort previously created deployment plan to target environment
            delete_deployment(lt_endpoint, lt_token, dep_plan_key)
            print("Deployment plan {} was deleted successfully.".format(dep_plan_key), flush=True)
            sys.exit(1)
        else:
            print("Deployment plan {} has conflicts but will continue with errors. Check {} artifact for more details.".format(dep_plan_key, CONFLICTS_FILE), flush=True)

    # Check if outdated consumer applications (outside of deployment plan) should be redeployed and start the deployment plan execution
    if lt_api_version == 1:  # LT for OS version < 11
        start_deployment(lt_endpoint, lt_token, dep_plan_key)
    elif lt_api_version == 2:  # LT for OS v11
        if has_conflicts:
            start_deployment(lt_endpoint, lt_token, dep_plan_key, redeploy_outdated=False, continue_with_errors=True)
        else:
            start_deployment(lt_endpoint, lt_token, dep_plan_key, redeploy_outdated=get_configuration_value("REDEPLOY_OUTDATED_APPS", REDEPLOY_OUTDATED_APPS))
    else:
        raise NotImplementedError("Please make sure the API version is compatible with the module.")
    print("Deployment plan {} started being executed.".format(dep_plan_key), flush=True)

    # Flag to only alert the user once
    alert_user = False
    # Sleep thread until deployment has finished
    wait_counter = 0
    while wait_counter < get_configuration_value("DEPLOYMENT_TIMEOUT_IN_SECS", DEPLOYMENT_TIMEOUT_IN_SECS):
        # Check Deployment Plan status.
        dep_status = get_deployment_status(
            artifact_dir, lt_endpoint, lt_token, dep_plan_key)
        if dep_status["DeploymentStatus"] != DEPLOYMENT_RUNNING_STATUS:
            # Check deployment status is pending approval.
            if dep_status["DeploymentStatus"] == DEPLOYMENT_WAITING_STATUS:
                # Check if deployment waiting status is due to 2-Step
                if check_deployment_two_step_deploy_status(dep_status):
                    # Force it to continue in case of force_two_step_deployment parameter
                    if force_two_step_deployment:
                        continue_deployment(lt_endpoint, lt_token, dep_plan_key)
                        print("Deployment plan {} resumed execution.".format(dep_plan_key), flush=True)
                    else:
                        # Exit the script to continue with the pipeline execution
                        print("Deployment plan {} first step finished successfully.".format(dep_plan_key), flush=True)
                        sys.exit(0)
                # Send notification to alert deployment manual intervention.
                elif not alert_user:
                    alert_user = True
                    print("A manual intervention is required to continue the execution of the deployment plan {}.".format(dep_plan_key), flush=True)
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
        sleep_value = get_configuration_value("SLEEP_PERIOD_IN_SECS", SLEEP_PERIOD_IN_SECS)
        sleep(sleep_value)
        wait_counter += sleep_value
        print("{} secs have passed since the deployment started...".format(wait_counter), flush=True)

    # Deployment timeout reached. Exit script with error
    print("Timeout occurred while deployment plan is still in {} status.".format(DEPLOYMENT_RUNNING_STATUS), flush=True)
    sys.exit(1)


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
    parser.add_argument("-d", "--destination_env_label", type=str, required=True,
                        help="Label, as configured in the manifest, of the destination environment where you want to deploy the apps.")
    parser.add_argument("-p", "--package_path", type=str, required=True,
                        help="Package file path")
    parser.add_argument("-c", "--force_two_step_deployment", action='store_true',
                        help="Force the execution of the 2-Step deployment.")
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
    dest_env_label = args.destination_env_label
    # Parse the package directory
    package_path = args.package_path
    # Parse Force Two-step Deployment flag
    force_two_step_deployment = args.force_two_step_deployment

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, dest_env_label, force_two_step_deployment, package_path)
