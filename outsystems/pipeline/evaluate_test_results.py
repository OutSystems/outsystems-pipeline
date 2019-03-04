# Python Modules
import unittest, json, os, xmlrunner, sys, argparse

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
  sys.path.append(os.environ['WORKSPACE'])
else: # Else just add the project dir
  sys.path.append(os.getcwd())

# Custom Modules
# Functions
from outsystems.file_helpers.file import load_data
from outsystems.bdd_framework.bdd_runner import run_bdd_test
# Variables
from outsystems.vars.file_vars import ARTIFACT_FOLDER, BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_ENDPOINTS_FILE, JUNIT_TEST_RESULTS_FILE
from outsystems.vars.bdd_vars import BDD_HTTP_PROTO, BDD_API_VERSION, BDD_API_ENDPOINT

########################################################### TEST CLASS ###########################################################
# Generator class that will create a unit test for each entry of the test results and print out a XML in tests/python-tests/*.xml
class TestsContainer(unittest.TestCase):
  longMessage = True

def format_error_report(error_obj):
  if error_obj["SuiteSuccess"]:
    return ""
  description = "\n\nBDD Test Suite failed {} scenarios (in {})\n".format(error_obj["FailedScenarios"],error_obj["SuccessfulScenarios"])
  for failure in error_obj["FailureReports"]:
    description += failure
  return description

def run_bdd_tests(description, url):
  def test(self):
    json_obj = run_bdd_test(url)
    self.assertTrue(json_obj["SuiteSuccess"], format_error_report(json_obj))
  return test

############################################################## SCRIPT ##############################################################
if __name__ == '__main__':
  # Argument menu / parsing
  parser = argparse.ArgumentParser()
  parser.add_argument("-a", "--artifacts", type=str, help="Name of the artifacts folder. Default: \"Artifacts\"")
  args = parser.parse_args()
  # Parse the artifact directory
  # Assumes the default dir = Artifacts
  artifact_dir = ARTIFACT_FOLDER
  if args.artifacts: 
    artifact_dir = args.artifacts
    sys.argv = sys.argv[:-2] # Workaround to clear the args to avoid messing with the unittest.main()

  # Load the test endpoints
  filename = os.path.join(BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_ENDPOINTS_FILE)
  test_urls = load_data(artifact_dir, filename)

  for test in test_urls:
    # Changes the qualified name to <var>
    TestsContainer.__qualname__= test["TestSuite"]
    # Changes the class name to <var>-timestamp
    TestsContainer.__name__= test["TestSuite"]
    setattr(TestsContainer, 'test_{0}'.format(test["Name"]), run_bdd_tests(test["Name"], test["URL"]))
  filename = os.path.join(ARTIFACT_FOLDER, JUNIT_TEST_RESULTS_FILE)
  with open(filename, 'wb') as output:
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output),failfast=False, buffer=False, catchbreak=False)