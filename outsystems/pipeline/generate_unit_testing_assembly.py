# Python Modules
import sys
import os
import argparse

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
from outsystems.vars.bdd_vars import BDD_HTTP_PROTO, BDD_API_ENDPOINT, BDD_API_VERSION
from outsystems.vars.cicd_vars import PROBE_HTTP_PROTO, PROBE_API_ENDPOINT, PROBE_API_VERSION
from outsystems.vars.file_vars import ARTIFACT_FOLDER, BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_ENDPOINTS_FILE
from outsystems.bdd_framework.bdd_base import build_bdd_endpoint, build_bdd_test_endpoint
from outsystems.cicd_probe.cicd_scan import scan_bdd_test_endpoint
from outsystems.cicd_probe.cicd_base import build_probe_endpoint
from outsystems.file_helpers.file import store_data

# Functions
# Variables

# ---------------------- VARS ----------------------
# Set script local variables
bdd_test = []  # will contain the BDD Framework tests for each app
bdd_modules = 0  # will count the number of bdd tests
test_names = []  # will contain the names of the tests to run
test_list = []  # will contain the webflows output from BDD for the application
test_urls = []  # will contain the urls for the BDD framework


# ---------------------- SCRIPT ----------------------
def main(artifact_dir: str, apps: list, bdd_http_proto: str, bdd_url: str, bdd_api_endpoint: str, bdd_version: int,
         cicd_http_proto: str, cicd_url: str, cicd_api_endpoint: str, cicd_version: int):
    # use the script variables
    global bdd_test, bdd_modules, test_names, test_list, test_urls

    probe_endpoint = build_probe_endpoint(
        cicd_http_proto, cicd_url, cicd_api_endpoint, cicd_version)
    bdd_endpoint = build_bdd_endpoint(
        bdd_http_proto, bdd_url, bdd_api_endpoint, bdd_version)

    # Query the CICD probe
    for app in apps:
        # Removes whitespaces in the beginning and end of the string
        app = app.strip()
        response = scan_bdd_test_endpoint(artifact_dir, probe_endpoint, app)
        if len(response) == 0:
            continue  # It has no test suites, continue the loop
        for test_endpoint in response:
            # Get the BDD test endpoints information
            bdd_test += [{"EspaceName": test_endpoint["BDDTestEndpointsInfo"]["EspaceName"],
                          "WebFlows": test_endpoint["BDDTestEndpointsInfo"]["WebFlows"]}]
            bdd_modules += len(test_endpoint["BDDTestEndpointsInfo"]
                               ["WebFlows"])
    print("{} BDD module(s) found.".format(bdd_modules), flush=True)

    # Get the tests to run (just for presentation)
    for bdd in bdd_test:  # For each BDD test
        if "WebFlows" in bdd:  # Sanity check to see if there are actual webflows in tests
            for webflow in bdd["WebFlows"]:  # For each webflow
                if "WebScreens" in webflow:  # Sanity check to see if there are actual webscreens in tests
                    test_list += webflow["WebScreens"]
    print("{} BDD endpoint(s) scanned successfully.".format(len(test_list)), flush=True)

    # Get the names of the tests to run (just for presentation)
    for test in test_list:
        test_names.append(test["Name"])
    print("Tests to run:{}".format(test_names), flush=True)

    # For each test, generate the URL to query the BDD framework, to be used in the test class
    for bdd in bdd_test:  # For each BDD test
        if "WebFlows" in bdd:  # Sanity check to see if there are actual webflows in tests
            for webflow in bdd["WebFlows"]:  # For each webflow
                if "WebScreens" in webflow:  # Sanity check to see if there are actual webscreens in tests
                    for webscreen in webflow["WebScreens"]:  # for each webscreen
                        test_endpoint = build_bdd_test_endpoint(
                            bdd_endpoint, bdd["EspaceName"], webscreen["Name"])
                        test_urls.append(
                            {"TestSuite": bdd["EspaceName"], "Name": webscreen["Name"], "URL": test_endpoint})

    # Save the test results in a file for later processing
    filename = os.path.join(BDD_FRAMEWORK_FOLDER,
                            BDD_FRAMEWORK_TEST_ENDPOINTS_FILE)
    store_data(artifact_dir, filename, test_urls)


# end of main()

if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str,
                        help="Name of the artifacts folder. Default: \"Artifacts\"", default=ARTIFACT_FOLDER)
    parser.add_argument("-l", "--app_list", type=str,
                        help="Comma separated list of apps you want to deploy. Example: \"App1,App2 With Spaces,App3_With_Underscores\"", required=True)

    parser.add_argument("--cicd_probe_env", type=str,
                        help="URL for CICD Probe, without the API endpoint. Example: \"https://<host>\"", required=True)
    parser.add_argument("--cicd_probe_api", type=str,
                        help="(optional) Used to set the API endpoint for CICD Probe, without the version. Default: \"CI_CDProbe/rest\"", default=PROBE_API_ENDPOINT)
    parser.add_argument("--cicd_probe_version", type=int,
                        help="(optional) CICD Probe API version number. Default: 1", default=PROBE_API_VERSION)

    parser.add_argument("--bdd_framework_env", type=str,
                        help="URL for BDD Framework, without the API endpoint. Example: \"https://<host>\"", required=True)
    parser.add_argument("--bdd_framework_api", type=str,
                        help="(optional) Used to set the API endpoint for BDD Framework, without the version. Default: \"BDDFramework/rest\"", default=BDD_API_ENDPOINT)
    parser.add_argument("--bdd_framework_version", type=int,
                        help="(optional) BDD Framework API version number. Default: 1", default=BDD_API_VERSION)

    args = parser.parse_args()

    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse App list
    _apps = args.app_list
    apps = _apps.split(',')

    # Parse the BDD API endpoint
    bdd_api_endpoint = args.bdd_framework_api
    # Parse the BDD Url and split the BDD hostname from the HTTP protocol
    # Assumes the default HTTP protocol = "https"
    bdd_http_proto = BDD_HTTP_PROTO
    bdd_url = args.bdd_framework_env
    if bdd_url.startswith("http://"):
        bdd_http_proto = "http"
        bdd_url = bdd_url.replace("http://", "")
    else:
        bdd_url = bdd_url.replace("https://", "")
    if bdd_url.endswith("/"):
        bdd_url = bdd_url[:-1]
    # Parse BDD API Version
    bdd_version = args.bdd_framework_version

    # Parse the CICD Probe API endpoint
    cicd_api_endpoint = args.cicd_probe_api
    # Parse the CICD Probe Url and split the CICD Probe hostname from the HTTP protocol
    # Assumes the default HTTP protocol = "https"
    cicd_http_proto = PROBE_HTTP_PROTO
    cicd_url = args.cicd_probe_env
    if cicd_url.startswith("http://"):
        cicd_http_proto = "http"
        cicd_url = cicd_url.replace("http://", "")
    else:
        cicd_url = cicd_url.replace("https://", "")
    if cicd_url.endswith("/"):
        cicd_url = cicd_url[:-1]
    # Parse CICD Probe API Version
    cicd_version = args.cicd_probe_version

    # Calls the main script
    main(artifact_dir, apps, bdd_http_proto, bdd_url, bdd_api_endpoint, bdd_version,
         cicd_http_proto, cicd_url, cicd_api_endpoint, cicd_version)
