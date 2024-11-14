# Python Modules
import sys
import os
import argparse
from packaging.version import Version
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
from outsystems.vars.file_vars import ARTIFACT_FOLDER
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS, MANIFEST_FLAG_IS_TEST_APPLICATION
from outsystems.vars.pipeline_vars import QUEUE_TIMEOUT_IN_SECS, SLEEP_PERIOD_IN_SECS, CONFLICTS_FILE, \
    REDEPLOY_OUTDATED_APPS, DEPLOYMENT_TIMEOUT_IN_SECS, DEPLOYMENT_RUNNING_STATUS, DEPLOYMENT_WAITING_STATUS, \
    DEPLOYMENT_ERROR_STATUS_LIST, DEPLOY_ERROR_FILE, ALLOW_CONTINUE_WITH_ERRORS
# Functions
from outsystems.lifetime.lifetime_environments import get_environment_app_version, get_environment_deployment_zones
from outsystems.lifetime.lifetime_applications import get_application_version
from outsystems.lifetime.lifetime_deployments import get_deployment_status, get_deployment_info, \
    send_deployment, delete_deployment, start_deployment, continue_deployment, get_running_deployment, \
    check_deployment_two_step_deploy_status
from outsystems.file_helpers.file import store_data, load_data
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.manifest.manifest_base import get_environment_details, get_deployment_notes
from outsystems.vars.vars_base import get_configuration_value, load_configuration_file
# Exceptions
from outsystems.exceptions.app_does_not_exist import AppDoesNotExistError
from outsystems.exceptions.manifest_does_not_exist import ManifestDoesNotExistError


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
def generate_deployment_based_on_manifest(artifact_dir: str, lt_endpoint: str, lt_token: str, src_env_key: str, src_env_name: str, manifest: list, include_test_apps: bool, include_deployment_zones: bool):
    app_data_list = []  # will contain the applications details from the manifest

    for deployed_app in manifest[MANIFEST_APPLICATION_VERSIONS]:  # type: ignore
        if not include_test_apps and deployed_app[MANIFEST_FLAG_IS_TEST_APPLICATION]:
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
        app_data = {'Name': deployed_app["ApplicationName"], 'Key': deployed_app["ApplicationKey"], 'Version': deployed_app["VersionNumber"], 'VersionKey': deployed_app["VersionKey"]}
        if include_deployment_zones:
            app_data['DeploymentZone'] = deployed_app["DeploymentZoneName"]
        app_data_list.append(app_data)

    return app_data_list


# Function to check if target environment already has the application versions to be deployed
def check_if_can_deploy(artifact_dir: str, lt_endpoint: str, lt_api_version: str, lt_token: str, env_key: str, env_name: str, app_data_list: list, include_deployment_zones: bool):
    app_keys = []  # will contain the application keys to create the deployment plan
    deploy_zones = []  # will contain the deployment zones available in the target environment

    # Get information about the deployment zones in the target environment
    if include_deployment_zones:
        deploy_zones = get_environment_deployment_zones(artifact_dir, lt_endpoint, lt_token, env_key=env_key)

    for app in app_data_list:
        deploy_zone_key = ""
        # Get the target deployment zone based on the name provided in the manifest
        target_deploy_zone = next(filter(lambda x: x["Name"] == app["DeploymentZone"], deploy_zones), None)
        try:
            # Get the status of the app in the target env, to check if they were deployed
            app_status = get_environment_app_version(artifact_dir, lt_endpoint, lt_token, True, env_name=env_name, app_key=app["Key"])
            # Check if the app version is already deployed in the target environment
            for app_in_env in app_status["AppStatusInEnvs"]:
                if app_in_env["EnvironmentKey"] == env_key:
                    # Check if the target environment has the version deployed
                    if app_in_env["BaseApplicationVersionKey"] != app["VersionKey"]:
                        # The version is not the one deployed -> need to compare the version tag
                        app_in_env_data = get_application_version(artifact_dir, lt_endpoint, lt_token, False, app_in_env["BaseApplicationVersionKey"], app_key=app["Key"])
                        # If the version in the target environment has the same version number -> skip deployment
                        if Version(app_in_env_data["Version"]) == Version(app["Version"]):
                            print("Skipping application {} with version {}, since it's already deployed in {} environment.\nReason: VersionTag is equal.".format(app["Name"], app["Version"], env_name), flush=True)
                        else:
                            # Generated app_keys for deployment plan based on the target version
                            if target_deploy_zone:
                                # Check if target deployment zone is different from the current one being used
                                if target_deploy_zone["Key"] != app_in_env["DeploymentZoneKey"]:
                                    deploy_zone_key = target_deploy_zone["Key"]
                            elif include_deployment_zones and app["DeploymentZone"]:
                                print("Deployment zone with name {} not found in {} environment.".format(app["DeploymentZone"], env_name), flush=True)
                            app_keys.append(generate_deploy_app_key(lt_api_version, app["VersionKey"], deploy_zone_key))
                            if deploy_zone_key:
                                print("Adding application {} with version {}, to be deployed in {} environment using {} deployment zone.".format(app["Name"], app["Version"], env_name, target_deploy_zone["Name"]), flush=True)
                            else:
                                print("Adding application {} with version {}, to be deployed in {} environment.".format(app["Name"], app["Version"], env_name), flush=True)
                    else:
                        print("Skipping application {} with version {}, since it's already deployed in {} environment.\nReason: VersionKey is equal.".format(app["Name"], app["Version"], env_name), flush=True)
        except AppDoesNotExistError:
            if target_deploy_zone:
                deploy_zone_key = target_deploy_zone["Key"]
            elif include_deployment_zones and app["DeploymentZone"]:
                print("Deployment zone with name {} not found in {} environment.".format(app["DeploymentZone"], env_name), flush=True)
            app_keys.append(generate_deploy_app_key(lt_api_version, app["VersionKey"], deploy_zone_key))  # type: ignore
            if deploy_zone_key:
                print("App {} with version {} does not exist in {} environment. Ignoring check and deploying it using {} deployment zone.".format(app["Name"], app["Version"], env_name, target_deploy_zone["Name"]), flush=True)
            else:
                print("App {} with version {} does not exist in {} environment. Ignoring check and deploying it.".format(app["Name"], app["Version"], env_name), flush=True)
    return app_keys


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, source_env_label: str, dest_env_label: str, include_test_apps: bool, trigger_manifest: dict, force_two_step_deployment: bool, include_deployment_zones: bool, allow_parallel_deployments: bool):

    app_data_list = []  # will contain the applications to deploy details from LT
    to_deploy_app_keys = []  # will contain the app keys for the apps tagged

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Tuple with (EnvName, EnvKey): src_env_tuple[0] = EnvName; src_env_tuple[1] = EnvKey
    src_env_tuple = get_environment_details(trigger_manifest, source_env_label)
    # Tuple with (EnvName, EnvKey): dest_env_tuple[0] = EnvName; dest_env_tuple[1] = EnvKey
    dest_env_tuple = get_environment_details(trigger_manifest, dest_env_label)

    # Retrive the app versions to deploy from the manifest content
    app_data_list = generate_deployment_based_on_manifest(artifact_dir, lt_endpoint, lt_token, src_env_tuple[1], src_env_tuple[0], trigger_manifest, include_test_apps, include_deployment_zones)

    # Check if which application versions have not been deployed to destination environment
    to_deploy_app_keys = check_if_can_deploy(artifact_dir, lt_endpoint, lt_api_version, lt_token, dest_env_tuple[1], dest_env_tuple[0], app_data_list, include_deployment_zones)

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

    if not allow_parallel_deployments:
        wait_counter = 0
        deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_tuple[1])
        while len(deployments) > 0:
            if wait_counter >= get_configuration_value("QUEUE_TIMEOUT_IN_SECS", QUEUE_TIMEOUT_IN_SECS):
                print("Timeout occurred while waiting for LifeTime to be free, to create the new deployment plan.", flush=True)
                sys.exit(1)
            sleep_value = get_configuration_value("SLEEP_PERIOD_IN_SECS", SLEEP_PERIOD_IN_SECS)
            sleep(sleep_value)
            wait_counter += sleep_value
            print("Waiting for LifeTime to be free. Elapsed time: {} seconds...".format(wait_counter), flush=True)
            deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_tuple[1])

    # LT is free to deploy
    # Send the deployment plan and grab the key
    dep_plan_key = send_deployment(artifact_dir, lt_endpoint, lt_token, lt_api_version, to_deploy_app_keys, get_deployment_notes(trigger_manifest), src_env_tuple[0], dest_env_tuple[0])
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
    parser.add_argument("-s", "--source_env_label", type=str, required=True,
                        help="Label, as configured in the manifest, of the source environment where the apps are.")
    parser.add_argument("-d", "--destination_env_label", type=str, required=True,
                        help="Label, as configured in the manifest, of the destination environment where you want to deploy the apps.")
    parser.add_argument("-i", "--include_test_apps", action='store_true',
                        help="Flag that indicates if applications marked as \"Test Application\" in the manifest are included in the deployment plan.")
    parser.add_argument("-m", "--trigger_manifest", type=str,
                        help="Manifest artifact (in JSON format) received when the pipeline is triggered. Contains required data used throughout the pipeline execution.")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="Manifest file (with JSON format). Contains required data used throughout the pipeline execution.")
    parser.add_argument("-c", "--force_two_step_deployment", action='store_true',
                        help="Force the execution of the 2-Step deployment.")
    parser.add_argument("-z", "--include_deployment_zones", action='store_true',
                        help="Flag that indicates if deployment zone selection is included in the deployment plan. Applicable to self-managed environments only.")
    parser.add_argument("-cf", "--config_file", type=str,
                        help="Config file path. Contains configuration values to override the default ones.")
    parser.add_argument("-p", "--allow_parallel_deployments", action='store_true',
                        help="Skip LifeTime validation for active deployment plans.")

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
    # Parse Source Environment
    source_env_label = args.source_env_label
    # Parse Destination Environment
    dest_env_label = args.destination_env_label
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

    # Parse Force Two-step Deployment flag
    force_two_step_deployment = args.force_two_step_deployment
    # Parse Include Deployment Zones flag
    include_deployment_zones = args.include_deployment_zones

    # Parse Allow Parallel Deployments
    allow_parallel_deployments = args.allow_parallel_deployments

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, source_env_label, dest_env_label, include_test_apps, trigger_manifest, force_two_step_deployment, include_deployment_zones, allow_parallel_deployments)
