# Python Modules
import unittest
import json
import os
import xmlrunner
import sys

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
  sys.path.append(os.environ['WORKSPACE'])

# Custom Modules
from outsystems.file_helpers.file import load_data
from outsystems.vars.file_vars import ARTIFACT_FOLDER, BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_ENDPOINTS_FILE, JUNIT_TEST_RESULTS_FILE
from outsystems.bdd_framework.bdd_runner import run_bdd_test

############################################################## VARS ##############################################################

# Set script local variables
test_urls = [] # will contain the test urls for the BDD framework (loaded from a mapping file)

############################################################## SCRIPT ##############################################################

# Load the test endpoints
filename = "{}\\{}".format(BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_ENDPOINTS_FILE)
test_urls = load_data(filename)

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

if __name__ == '__main__':
  for test in test_urls:
    # Changes the qualified name to <var>
    TestsContainer.__qualname__= test["TestSuite"]
    # Changes the class name to <var>-timestamp
    TestsContainer.__name__= test["TestSuite"]
    setattr(TestsContainer, 'test_{0}'.format(test["Name"]), run_bdd_tests(test["Name"], test["URL"]))
  filename = "{}/{}".format(ARTIFACT_FOLDER, JUNIT_TEST_RESULTS_FILE)
  with open(filename, 'wb') as output:
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output),failfast=False, buffer=False, catchbreak=False)



