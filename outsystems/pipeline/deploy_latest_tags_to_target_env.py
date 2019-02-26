# Python Modules
import datetime
import sys
from time import sleep
import os

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
  sys.path.append(os.environ['WORKSPACE'])

# Custom Modules
from outsystems.file_helpers.file import store_data
from outsystems.vars.pipeline_vars import DEPLOYMENT_STATUS_LIST, QUEUE_TIMEOUT_IN_SECS, SLEEP_PERIOD_IN_SECS, CONFLICTS_FILE, \
  REDEPLOY_OUTDATED_APPS, DEPLOYMENT_TIMEOUT_IN_SECS, DEPLOYMENT_RUNNING_STATUS, DEPLOYMENT_WAITING_STATUS, \
  DEPLOYMENT_ERROR_STATUS_LIST, DEPLOY_ERROR_FILE
from outsystems.vars.lifetime_vars import LIFETIME_API_VERSION
from outsystems.lifetime.lifetime_applications import get_application_versions
from outsystems.lifetime.lifetime_environments import get_environment_app_version
from outsystems.lifetime.lifetime_deployments import get_deployments, get_deployment_status, get_deployment_info, \
  send_deployment, delete_deployment, start_deployment, continue_deployment

############################################################## VARS ##############################################################

# Set script local variables 
# Environment details
source_env = os.environ['SourceEnvironment']
dest_env = os.environ['TargetEnvironment']
# LT url 
lt_url = os.environ['LifeTimeEnvironmentURL']
# LT Token for authentication
lt_token = os.environ['AuthorizationToken']
# List of apps to deploy
apps = os.environ['ApplicationsToDeploy'].split(',')
# Jenkins Job Name
job_name = os.environ['JOB_NAME']
# Jenkins Build Name
build_name = os.environ['BUILD_DISPLAY_NAME']

# Set script local variables
app_data_list = [] # will contain the applications to deploy details from LT
app_keys = [] # will contain the application keys to deploy from LT
to_deploy_app_keys = [] # will contain the app keys for the apps tagged

############################################################## SCRIPT ##############################################################
# Creates a list with the details for the apps you want to deploy
for app_name in apps:
  # Get the application with version details (for one version = the latest)
  app_with_versions = get_application_versions(lt_url, lt_token, 1, app_name=app_name)
  # Grab the App key
  app_key = app_with_versions[0]["ApplicationKey"]
  # Grab the Version ID from the latest version of the app
  app_version = app_with_versions[0]["Version"]
  # Grab the Version Key from the latest version of the app
  app_version_key = app_with_versions[0]["Key"]
  if LIFETIME_API_VERSION == 1: # LT for OS version < 11
    app_keys.append(app_version_key)
  else: # LT for OS v11
    app_keys.append({"ApplicationVersionKey": app_version_key, "DeploymentZoneKey": ""})
  # Add it to the app data listapp_version
  app_data_list.append({'Name': app_name, 'Key': app_key, 'Version': app_version, 'VersionKey': app_version_key})

# Check if target environment already has the application versions to be deployed
for app in app_data_list:
  app_status = get_environment_app_version(lt_url, lt_token, True, env_name=dest_env, app_key=app["Key"]) # get the status of the app in the target env, to check if they were deployed
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
print("Creating deployment plan from {} to {} including applications: {} ({}).".format(source_env,dest_env,apps,app_data_list))

wait_counter = 0
while True:
  # Get list of deployments ordered by creation date (from newest to oldest).
  date = datetime.date.today()
  deployments = get_deployments(lt_url, lt_token, date)
  if deployments != {}:
    for deployment in deployments:
      # Check status for each retrieved deployment record
      dep_status = get_deployment_status(lt_url, lt_token, deployment["Key"])
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
dep_note = "Automatic deployment plan created by Jenkins Pipeline: {} ({})".format(job_name,build_name)
dep_plan_key = send_deployment(lt_url, lt_token, app_keys, dep_note, source_env, dest_env)
print("Deployment plan {} created successfully.".format(dep_plan_key))

# Check if created deployment plan has conflicts
dep_details = get_deployment_info(lt_url, lt_token, dep_plan_key)
if len(dep_details["ApplicationConflicts"]) > 0:
  store_data(CONFLICTS_FILE, dep_details["ApplicationConflicts"])
  print("Deployment plan {} has conflicts and will be aborted. Check {} artifact for more details.".format(dep_plan_key, CONFLICTS_FILE))
  # Abort previously created deployment plan to target environment
  delete_deployment(lt_url, lt_token, dep_plan_key)
  print("Deployment plan {} was deleted successfully.".format(dep_plan_key))
  sys.exit(1)

# Check if outdated consumer applications (outside of deployment plan) should be redeployed and start the deployment plan execution
if LIFETIME_API_VERSION == 2:
  start_deployment(lt_url, lt_token, dep_plan_key, redeploy_outdated=REDEPLOY_OUTDATED_APPS)
else:
  start_deployment(lt_url, lt_token, dep_plan_key)
print("Deployment plan {} started being executed.".format(dep_plan_key))

# Sleep thread until deployment has finished
wait_counter = 0
while wait_counter < DEPLOYMENT_TIMEOUT_IN_SECS:
  # Check Deployment Plan status. 
  dep_status = get_deployment_status(lt_url, lt_token, dep_plan_key)
  if dep_status["DeploymentStatus"] != DEPLOYMENT_RUNNING_STATUS:
    # Check deployment status is pending approval. Force it to continue (if 2-Step deployment is enabled)
    if dep_status["DeploymentStatus"] == DEPLOYMENT_WAITING_STATUS:
      continue_deployment(lt_url, lt_token, dep_plan_key)
      print("Deployment plan {} resumed execution.".format(dep_plan_key))
    elif dep_status["DeploymentStatus"] in DEPLOYMENT_ERROR_STATUS_LIST:
      print("Deployment plan finished with status {}.".format(dep_status["DeploymentStatus"]))
      store_data(DEPLOY_ERROR_FILE, dep_status)
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