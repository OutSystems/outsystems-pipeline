# Python Modules
import sys
import os
import argparse
from pkg_resources import parse_version
from time import sleep
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
from outsystems.vars.file_vars import ARTIFACT_FOLDER, DEPLOYMENT_FOLDER, DEPLOYMENT_MANIFEST_FILE
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS, MANIFEST_FLAG_IS_TEST_APPLICATION, MANIFEST_CONFIG_ITEM_KEY, \
    MANIFEST_CONFIG_ITEM_NAME, MANIFEST_CONFIG_ITEM_TARGET_VALUE, MANIFEST_CONFIG_ITEM_TYPE, MANIFEST_ENVIRONMENT_NAME, MANIFEST_MODULE_KEY 
from outsystems.vars.properties_vars import PROPERTY_TYPE_SITE_PROPERTY
from outsystems.vars.pipeline_vars import QUEUE_TIMEOUT_IN_SECS, SLEEP_PERIOD_IN_SECS, CONFLICTS_FILE, \
    REDEPLOY_OUTDATED_APPS, DEPLOYMENT_TIMEOUT_IN_SECS, DEPLOYMENT_RUNNING_STATUS, DEPLOYMENT_WAITING_STATUS, \
    DEPLOYMENT_ERROR_STATUS_LIST, DEPLOY_ERROR_FILE
# Functions
from outsystems.lifetime.lifetime_environments import get_environment_app_version
from outsystems.lifetime.lifetime_applications import get_running_app_version, get_application_version
from outsystems.lifetime.lifetime_deployments import get_deployment_status, get_deployment_info, \
    send_deployment, delete_deployment, start_deployment, continue_deployment, get_running_deployment
from outsystems.file_helpers.file import store_data, load_data
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.manifest.manifest_base import get_environment_details, get_deployment_notes, get_configuration_items_for_environment
from outsystems.properties.properties_set_value import set_site_property_value
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
def generate_deployment_based_on_manifest(artifact_dir: str, lt_endpoint: str, lt_token: str, src_env_key: str, src_env_name: str, manifest: list, include_test_apps: bool):
    app_data_list = []  # will contain the applications details from the manifest

    for deployed_app in manifest[MANIFEST_APPLICATION_VERSIONS]:      
        if not(include_test_apps) and deployed_app[MANIFEST_FLAG_IS_TEST_APPLICATION]:
            continue   
        try:
            get_application_version(artifact_dir, lt_endpoint, lt_token, False, deployed_app["VersionKey"], app_name=deployed_app["ApplicationName"])
        except AppDoesNotExistError:
            print("Application {} with version {} no longer exists in {}. The manifest no longer reflects the current state of the environment. Aborting!".format(deployed_app["ApplicationName"], deployed_app["VersionNumber"], src_env_name), flush=True)
            sys.exit(1)
        except Exception as error:
            print("Error trying to validate if the application {} exists in the {} environment.\nError: {}".format(deployed_app["ApplicationName"], src_env_name, error), flush=True)
            sys.exit(1)

        # Add it to the app data list
        app_data_list.append({'Name': deployed_app["ApplicationName"], 'Key': deployed_app["ApplicationKey"], 'Version': deployed_app["VersionNumber"], 'VersionKey': deployed_app["VersionKey"]})

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
                        # If the version in the environment is higher than the one in the manifest -> stale pipeline -> abort
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
            print("App {} with version {} does not exist in {} environment. Ignoring check and deploy it.".format(app["Name"], app["Version"], env_name), flush=True)
    return app_keys


# Function to apply configuration values to a target environment
def apply_configuration_values_to_target_env(artifact_dir: str, lt_url: str, lt_token: str, target_env_label: str, trigger_manifest: dict):
    
    # Tuple with (EnvName, EnvKey): target_env_tuple[0] = EnvName; target_env_tuple[1] = EnvKey
    target_env_tuple = get_environment_details(trigger_manifest, target_env_label)
    
    # Get configuration items defined in the manifest for target environment
    config_items = get_configuration_items_for_environment(trigger_manifest, target_env_tuple[1])

    # Check if there are any configuration item values to apply for target environment 
    if config_items:
        print("Applying new values to configuration items in {} (Label: {})...".format(target_env_tuple[0], target_env_label), flush=True)
    else:
        print("No configuration item values were found in the manifest for {} (Label: {}).".format(target_env_tuple[0], target_env_label), flush=True)      

    # Apply target value for each configuration item according to its type
    for cfg_item in config_items:
        if cfg_item[MANIFEST_CONFIG_ITEM_TYPE] == PROPERTY_TYPE_SITE_PROPERTY:
            result = set_site_property_value(
                lt_url, lt_token, cfg_item[MANIFEST_MODULE_KEY], target_env_tuple[1], cfg_item[MANIFEST_CONFIG_ITEM_KEY], cfg_item[MANIFEST_CONFIG_ITEM_TARGET_VALUE])
            if result["Success"]:
                print("New value successfully applied to configuration item '{}' ({}).".format(cfg_item[MANIFEST_CONFIG_ITEM_NAME], cfg_item[MANIFEST_CONFIG_ITEM_TYPE]), flush=True)
            else:
                print("Unable to apply new value to configuration item '{}' ({}).\nReason: {}".format(cfg_item[MANIFEST_CONFIG_ITEM_NAME], cfg_item[MANIFEST_CONFIG_ITEM_TYPE], result["Message"]), flush=True)            
        else:
            raise NotImplementedError("Configuration item type '{}' not supported.".format(cfg_item[MANIFEST_CONFIG_ITEM_TYPE]))

def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, source_env_label: str, dest_env_label: str, include_test_apps: bool, trigger_manifest: dict):

    app_data_list = []  # will contain the applications to deploy details from LT
    to_deploy_app_keys = []  # will contain the app keys for the apps tagged

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Tuple with (EnvName, EnvKey): src_env_tuple[0] = EnvName; src_env_tuple[1] = EnvKey
    src_env_tuple = get_environment_details(trigger_manifest, source_env_label)
    # Tuple with (EnvName, EnvKey): dest_env_tuple[0] = EnvName; dest_env_tuple[1] = EnvKey
    dest_env_tuple = get_environment_details(trigger_manifest, dest_env_label)

    # Retrive the app versions to deploy from the manifest content
    app_data_list = generate_deployment_based_on_manifest(artifact_dir, lt_endpoint, lt_token, src_env_tuple[1], src_env_tuple[0], trigger_manifest, include_test_apps)
    
    # Check if which application versions have not been deployed to destination environment
    to_deploy_app_keys = check_if_can_deploy(artifact_dir, lt_endpoint, lt_api_version, lt_token, dest_env_tuple[1], dest_env_tuple[0], app_data_list)

    # Check if there are apps to be deployed
    if len(to_deploy_app_keys) == 0:
        print("Deployment skipped because {} environment already has the target application deployed with the same tags.".format(dest_env_tuple[0]), flush=True)
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
    print("Creating deployment plan from {} (Label: {}) to {} (Label: {}) including applications: {} ({}).".format(src_env_tuple[0], source_env_label, dest_env_tuple[0], dest_env_label, to_deploy_app_names, to_deploy_app_info), flush=True)

    wait_counter = 0
    deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_tuple[1])
    while len(deployments) > 0:
        if wait_counter >= QUEUE_TIMEOUT_IN_SECS:
            print("Timeout occurred while waiting for LifeTime to be free, to create the new deployment plan.", flush=True)
            sys.exit(1)
        sleep(SLEEP_PERIOD_IN_SECS)
        wait_counter += SLEEP_PERIOD_IN_SECS
        print("Waiting for LifeTime to be free. Elapsed time: {} seconds...".format(wait_counter), flush=True)
        deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_tuple[1])

    # LT is free to deploy
    # Send the deployment plan and grab the key
    dep_plan_key = send_deployment(artifact_dir, lt_endpoint, lt_token, lt_api_version, to_deploy_app_keys, get_deployment_notes(trigger_manifest), src_env_tuple[0], dest_env_tuple[0])
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
                        help="(Optional) Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-u", "--lt_url", type=str, required=True,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
    parser.add_argument("-t", "--lt_token", type=str, required=True,
                        help="Token for LifeTime API calls.")
    parser.add_argument("-v", "--lt_api_version", type=int, default=LIFETIME_API_VERSION,
                        help="(Optional) LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
    parser.add_argument("-e", "--lt_endpoint", type=str, default=LIFETIME_API_ENDPOINT,
                        help="(Optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-s", "--source_env_label", type=str, required=True,
                        help="Label, as configured in the manifest, of the source environment where the apps are.")
    parser.add_argument("-d", "--destination_env_label", type=str, required=True,
                        help="Label, as configured in the manifest, of the destination environment where you want to deploy the apps.")
    parser.add_argument("-i", "--include_test_apps", type=bool, required=True,
                        help="Flag that indicates if applications marked as \"Test Application\" in the manifest are included in the deployment plan.")
    parser.add_argument("-m", "--trigger_manifest", type=str, required=True,
                        help=" Manifest artifact (in JSON format) received when the pipeline is triggered. Contains required data used throughout the pipeline execution.")

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
    source_env_label = args.source_env_label
    # Parse Destination Environment
    dest_env_label = args.destination_env_label
    # Parse Include Test Apps flag
    include_test_apps = args.include_test_apps
    # Parse Manifest artifact
    # TODO: Isolate in separate funtion to store manifest as a file
    trigger_manifest = json.loads(args.manifest_file) 
    
    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, source_env_label, dest_env_label, include_test_apps, trigger_manifest)
