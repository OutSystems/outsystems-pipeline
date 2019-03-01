# Python Modules
import datetime, sys, os, argparse
from time import sleep

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
  sys.path.append(os.environ['WORKSPACE'])

# Custom Modules
# Functions
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.file_helpers.file import store_data
from outsystems.lifetime.lifetime_deployments import get_deployments, get_deployment_status, get_deployment_info, \
  send_deployment, delete_deployment, start_deployment, continue_deployment
from outsystems.lifetime.lifetime_applications import get_application_versions
from outsystems.lifetime.lifetime_environments import get_environment_app_version
# Variables
from outsystems.vars.pipeline_vars import DEPLOYMENT_STATUS_LIST, QUEUE_TIMEOUT_IN_SECS, SLEEP_PERIOD_IN_SECS, CONFLICTS_FILE, \
  REDEPLOY_OUTDATED_APPS, DEPLOYMENT_TIMEOUT_IN_SECS, DEPLOYMENT_RUNNING_STATUS, DEPLOYMENT_WAITING_STATUS, \
  DEPLOYMENT_ERROR_STATUS_LIST, DEPLOY_ERROR_FILE
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION, DEPLOYMENT_MESSAGE
from outsystems.vars.file_vars import ARTIFACT_FOLDER

############################################################## VARS ##############################################################
# Set script local variables
app_data_list = [] # will contain the applications to deploy details from LT
app_keys = [] # will contain the application keys to deploy from LT
to_deploy_app_keys = [] # will contain the app keys for the apps tagged

############################################################## SCRIPT ##############################################################
def main(artifact_dir :str, lt_http_proto :str, lt_url :str, lt_api_endpoint :str, lt_api_version :int, lt_token :str, source_env :str, dest_env :str, apps :list, dep_note :str):
  # Builds the LifeTime endpoint
  lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

  # Creates a list with the details for the apps you want to deploy
  for app_name in apps:
    # Removes whitespaces in the beginning and end of the string
    app_name = app_name.strip()
    # Get the application with version details (for one version = the latest)
    app_with_versions = get_application_versions(artifact_dir, lt_endpoint, lt_token, 1, app_name=app_name)
    # Grab the App key
    app_key = app_with_versions[0]["ApplicationKey"]
    # Grab the Version ID from the latest version of the app
    app_version = app_with_versions[0]["Version"]
    # Grab the Version Key from the latest version of the app
    app_version_key = app_with_versions[0]["Key"]
    if lt_api_version == 1: # LT for OS version < 11
      app_keys.append(app_version_key)
    elif lt_api_version == 2: # LT for OS v11
      app_keys.append({"ApplicationVersionKey": app_version_key, "DeploymentZoneKey": ""})
    else:
      raise NotImplementedError("Please make sure the API version is compatible with the module.")
    # Add it to the app data listapp_version
    app_data_list.append({'Name': app_name, 'Key': app_key, 'Version': app_version, 'VersionKey': app_version_key})

  # Check if target environment already has the application versions to be deployed
  for app in app_data_list:
    app_status = get_environment_app_version(artifact_dir, lt_endpoint, lt_token, True, env_name=dest_env, app_key=app["Key"]) # get the status of the app in the target env, to check if they were deployed
    # Check if the app version is already deployed in the target environment
    if app_status["AppStatusInEnvs"][0]["BaseApplicationVersionKey"] != app["VersionKey"]:
      # If it's not, save the key of the tagged app, to deploy later
      to_deploy_app_keys.append(app["VersionKey"]) 
    else:
      print("Skipping app {} with version {}, since it's already deployed in {} environment.".format(app["Name"], app["Version"], dest_env))
 
  # Check if there are apps to be deployed
  if len(to_deploy_app_keys) == 0:
    print("Deployment skipped because {} environment already has the target application deployed with the same tags.".format(dest_env))
    sys.exit(0)

  # Write the names and keys of the application versions to be deployed
  print("Creating deployment plan from {} to {} including applications: {} ({}).".format(source_env, dest_env, apps, app_data_list))

  wait_counter = 0
  while True:
    # Get list of deployments ordered by creation date (from newest to oldest).
    date = datetime.date.today()
    deployments = get_deployments(artifact_dir, lt_endpoint, lt_token, date)
    if deployments != {}:
      for deployment in deployments:
        # Check status for each retrieved deployment record
        dep_status = get_deployment_status(artifact_dir, lt_endpoint, lt_token, deployment["Key"])
        if dep_status["DeploymentStatus"] in DEPLOYMENT_STATUS_LIST: # If there's a deployment active
          if wait_counter >= QUEUE_TIMEOUT_IN_SECS:
            print("Timeout occurred while queuing for creating a new deployment plan.")
            sys.exit(1)
          sleep(SLEEP_PERIOD_IN_SECS)
          wait_counter += SLEEP_PERIOD_IN_SECS
          print("{} secs have passed while waiting for ongoing deployment to end...".format(wait_counter))
    break

  # LT is free to deploy
  # Send the deployment plan and grab the key
  dep_plan_key = send_deployment(artifact_dir, lt_endpoint, lt_api_version, lt_token, app_keys, dep_note, source_env, dest_env)
  print("Deployment plan {} created successfully.".format(dep_plan_key))

  # Check if created deployment plan has conflicts
  dep_details = get_deployment_info(artifact_dir, lt_endpoint, lt_token, dep_plan_key)
  if len(dep_details["ApplicationConflicts"]) > 0:
    store_data(artifact_dir, CONFLICTS_FILE, dep_details["ApplicationConflicts"])
    print("Deployment plan {} has conflicts and will be aborted. Check {} artifact for more details.".format(dep_plan_key, CONFLICTS_FILE))
    # Abort previously created deployment plan to target environment
    delete_deployment(lt_endpoint, lt_token, dep_plan_key)
    print("Deployment plan {} was deleted successfully.".format(dep_plan_key))
    sys.exit(1)

  # Check if outdated consumer applications (outside of deployment plan) should be redeployed and start the deployment plan execution  
  if lt_api_version == 1: # LT for OS version < 11
    start_deployment(lt_endpoint, lt_token, dep_plan_key)
  elif lt_api_version == 2: # LT for OS v11
    start_deployment(lt_endpoint, lt_token, dep_plan_key, redeploy_outdated=REDEPLOY_OUTDATED_APPS)
  else:
    raise NotImplementedError("Please make sure the API version is compatible with the module.")
  print("Deployment plan {} started being executed.".format(dep_plan_key))

  # Sleep thread until deployment has finished
  wait_counter = 0
  while wait_counter < DEPLOYMENT_TIMEOUT_IN_SECS:
    # Check Deployment Plan status. 
    dep_status = get_deployment_status(artifact_dir, lt_endpoint, lt_token, dep_plan_key)
    if dep_status["DeploymentStatus"] != DEPLOYMENT_RUNNING_STATUS:
      # Check deployment status is pending approval. Force it to continue (if 2-Step deployment is enabled)
      if dep_status["DeploymentStatus"] == DEPLOYMENT_WAITING_STATUS:
        continue_deployment(lt_endpoint, lt_token, dep_plan_key)
        print("Deployment plan {} resumed execution.".format(dep_plan_key))
      elif dep_status["DeploymentStatus"] in DEPLOYMENT_ERROR_STATUS_LIST:
        print("Deployment plan finished with status {}.".format(dep_status["DeploymentStatus"]))
        store_data(artifact_dir, DEPLOY_ERROR_FILE, dep_status)
        sys.exit(1)
      else:
        # If it reaches here, it means the deployment was successful
        print("Deployment plan finished with status {}.".format(dep_status["DeploymentStatus"]))
        # Exit the script to continue with the pipeline
        sys.exit(0)
    # Deployment status is still running. Go back to sleep.
    sleep(SLEEP_PERIOD_IN_SECS)
    wait_counter += SLEEP_PERIOD_IN_SECS
    print("{} secs have passed since the deployment started...".format(wait_counter))

  # Deployment timeout reached. Exit script with error  
  print("Timeout occurred while deployment plan is still in {} status.".format(DEPLOYMENT_RUNNING_STATUS))
  sys.exit(1)

# End of main()

if __name__ == "__main__":
  # Argument menu / parsing
  parser = argparse.ArgumentParser()
  parser.add_argument("-a", "--artifacts", type=str, help="Name of the artifacts folder. Default: \"Artifacts\"")
  parser.add_argument("-u", "--lt_url", type=str, help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
  parser.add_argument("-t", "--lt_token", type=str, help="Token for LifeTime API calls.")
  parser.add_argument("-v", "--lt_api_version", type=int, help="LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
  parser.add_argument("-e", "--lt_endpoint", type=str, help="(optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
  parser.add_argument("-s", "--source_env", type=str, help="Name, as displayed in LifeTime, of the source environment where the apps are.")
  parser.add_argument("-d", "--destination_env", type=str, help="Name, as displayed in LifeTime, of the destination environment where you want to deploy the apps.")
  parser.add_argument("-l", "--app_list", type=str, help="Comma separated list of apps you want to deploy. Example: \"App1,App2 With Spaces,App3_With_Underscores\"")
  parser.add_argument("-m", "--deploy_msg", type=str, help="Message you want to show on the deployment plans in LifeTime. Default: \"Automated deploy using OS Pipelines\".")  
  
  args = parser.parse_args()
  # Parse the artifact directory
  # Assumes the default dir = Artifacts
  artifact_dir = ARTIFACT_FOLDER
  if args.artifacts: artifact_dir = args.artifacts
  # Parse the API endpoint
  # Assumes the default endpoint = lifetimeapi/rest
  lt_api_endpoint = LIFETIME_API_ENDPOINT
  if args.lt_endpoint: lt_api_endpoint = args.lt_endpoint
  # Parse the LT Url and split the LT hostname from the HTTP protocol
  # Assumes the default HTTP protocol = https
  lt_http_proto = LIFETIME_HTTP_PROTO
  lt_url = args.lt_url
  if lt_url:
    if lt_url.startswith("http://"): 
      lt_http_proto = "http"
      lt_url = lt_url.replace("http://","")
    else:
      lt_url = lt_url.replace("https://","")
    if lt_url.endswith("/"): lt_url = lt_url[:-1]
  else:
    print("You need to set the LifeTime URL.")
    exit(1)
  # Parte LT API Version
  # Assumes the default version = 2
  lt_version = LIFETIME_API_VERSION
  if args.lt_api_version: lt_version = args.lt_api_version
  # Parse the LT Token
  lt_token = args.lt_token
  if not lt_token: 
    print("You need to set the LifeTime Token or else you won't be able to authenticate.")
    exit(1)
  # Parse Source Environment
  source_env = args.source_env
  if not source_env:
    print("You need to set the source environment in order to fetch the applications to deploy.")
    exit(1)
  # Parse Destination Environment
  dest_env = args.destination_env
  if not dest_env:
    print("You need to set the destination environment in order to deploy the applications there.")
    exit(1)
  # Parse App list
  _apps = args.app_list
  if not _apps:
    print("You need to set the apps you want to deploy.")
    exit(1)
  apps = _apps.split(',')
  # Parse Deployment Message
  # Assumes default message = "Automated deploy via OutSystems Pipeline"
  dep_note = DEPLOYMENT_MESSAGE
  if args.deploy_msg: dep_note = args.deploy_msg
  
  # Calls the main script
  main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, source_env, dest_env, apps, dep_note)