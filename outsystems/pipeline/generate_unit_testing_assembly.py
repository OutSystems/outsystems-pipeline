# Python Modules
import sys
import os

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
  sys.path.append(os.environ['WORKSPACE'])

# Custom Modules
from outsystems.file_helpers.file import store_data
from outsystems.vars.file_vars import BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_ENDPOINTS_FILE
from outsystems.lifetime.lifetime_environments import get_environment_url
from outsystems.cicd_probe.cicd_scan import scan_bdd_test_endpoint
from outsystems.bdd_framework.bdd_runner import build_bdd_test_endpoint

############################################################## VARS ##############################################################

# Set script local variables from environment
# LT url 
lt_url = os.environ['LifeTimeEnvironmentURL']
# LT Token for authentication
lt_token = os.environ['AuthorizationToken']
# Name of the Environement to target
environment = os.environ['EnvironmentName']
# Name of the app that has the tests to run
apps = os.environ['ApplicationsToDeploy'].split(',')

# Set script local variables
bdd_test = [] # will contain the BDD Framework tests for each app
bdd_modules = 0 # will count the number of bdd tests
test_names = [] # will contain the names of the tests to run
test_list = [] # will contain the webflows output from BDD for the application
test_urls = [] # will contain the urls for the BDD framework

############################################################## SCRIPT ##############################################################
# Get the environment url
environment_url = get_environment_url(lt_url, lt_token, environment)

# Query the CICD probe
for app in apps:
  response = scan_bdd_test_endpoint(environment_url, app)
  if(len(response) == 0):
    continue # It has no test suites, continue the loop
  for test_endpoint in response:
    # Get the BDD test endpoints information
    bdd_test += [{"EspaceName": test_endpoint["BDDTestEndpointsInfo"]["EspaceName"], "WebFlows": test_endpoint["BDDTestEndpointsInfo"]["WebFlows"]}]
    bdd_modules += len(test_endpoint["BDDTestEndpointsInfo"]["WebFlows"])
print("{} BDD module(s) found.".format(bdd_modules))

# Get the tests to run (just for presentation)
for bdd in bdd_test: # For each BDD test
  for webflow in bdd["WebFlows"]: # For each webflow
    test_list+=webflow["WebScreens"]
print("{} BDD endpoint(s) scanned successfully.".format(len(test_list)))

# Get the names of the tests to run (just for presentation)
for test in test_list:
    test_names.append(test["Name"])
print("Tests to run:{}".format(test_names))

# For each test, generate the URL to query the BDD framework, to be used in the test class
for bdd in bdd_test: # For each BDD test
  for webflow in bdd["WebFlows"]: # For each webflow
    for webscreen in webflow["WebScreens"]: # for each webscreen
      test_endpoint = build_bdd_test_endpoint(environment_url, bdd["EspaceName"], webscreen["Name"])
      test_urls.append({"TestSuite": bdd["EspaceName"],"Name": webscreen["Name"],"URL": test_endpoint})

# Save the test results in a file for later processing
filename = "{}\\{}".format(BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_ENDPOINTS_FILE)
store_data(filename, test_urls)
