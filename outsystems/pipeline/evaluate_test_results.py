# Python Modules
import unittest, json, os, xmlrunner, sys, argparse

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
from outsystems.vars.bdd_vars import BDD_HTTP_PROTO, BDD_API_VERSION, BDD_API_ENDPOINT
from outsystems.vars.file_vars import ARTIFACT_FOLDER, BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_ENDPOINTS_FILE, JUNIT_TEST_RESULTS_FILE
from outsystems.bdd_framework.bdd_runner import run_bdd_test
from outsystems.file_helpers.file import load_data
# Functions
# Variables

########################################################### TEST CLASS ###########################################################
# Generator class that will create a unit test for each entry of the test results and print out a XML in tests/python-tests/*.xml
class BDDTestRunner(unittest.TestCase):
    longMessage = False

    TEST_URL = ""
    TEST_MODULE = ""
    TEST_NAME = ""

    def set_test_info(self, url :str, name :str, module :str):
        self.TEST_URL = url
        self.TEST_NAME = name
        self.TEST_MODULE = module
    
    def format_error_report(self, error_obj):
        description = "Test Name:{};Test Module:{}".format(self.TEST_NAME, self.TEST_MODULE)

        if not error_obj["ErrorMessage"]:
            description += "\nBDD Test Suite failed {} scenarios (in {})\n".format(error_obj["FailedScenarios"], error_obj["SuccessfulScenarios"])
            for failure in error_obj["FailureReports"]:
                description += failure
        else:
            description += "\nAn error was found in the unit test.\nError: {}".format(error_obj["ErrorMessage"])
        return description

    def test_bdd_output(self):
        json_obj = run_bdd_test(self.TEST_URL)
        self.assertTrue(json_obj["SuiteSuccess"], self.format_error_report(json_obj))

############################################################## SCRIPT ##############################################################
if __name__ == '__main__':
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, help="Name of the artifacts folder. Default: \"Artifacts\"", default=ARTIFACT_FOLDER)
    args = parser.parse_args()
    # Parse the artifact directory
    # Assumes the default dir = Artifacts
    artifact_dir = args.artifacts
    if len(sys.argv) == 3:  # Workaround to clear the args to avoid messing with the unittest.main()
        sys.argv = sys.argv[:-2]

    # Load the test endpoints
    filename = os.path.join(BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_ENDPOINTS_FILE)
    test_urls = load_data(artifact_dir, filename)
    # Creates a test suite with all the tests. 
    # It also provides each test with information (name, module) to be used in the notifications
    suite = unittest.TestSuite()
    for test in test_urls:
        test_case = BDDTestRunner(methodName='test_bdd_output')
        test_case.set_test_info(test["URL"], test["Name"], test["TestSuite"])
        suite.addTest(test_case)

    # Runs the test suite and stores the value in a XMN file to be used by JUNIT
    filename = os.path.join(ARTIFACT_FOLDER, JUNIT_TEST_RESULTS_FILE)
    with open(filename, 'wb') as output:
        xmlrunner.XMLTestRunner(output=output, failfast=False, buffer=False).run(suite)