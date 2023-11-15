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
from outsystems.vars.bdd_vars import BDD_HTTP_PROTO, BDD_API_ENDPOINT, BDD_CLIENT_API_ENDPOINT, BDD_API_VERSION, \
    BDD_FRAMEWORK_TYPE_CLIENT
from outsystems.vars.cicd_vars import PROBE_HTTP_PROTO, PROBE_API_ENDPOINT, PROBE_API_VERSION
from outsystems.vars.file_vars import ARTIFACT_FOLDER, BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_ENDPOINTS_FILE
from outsystems.bdd_framework.bdd_base import build_bdd_endpoint, build_bdd_test_endpoint
from outsystems.cicd_probe.cicd_scan import scan_bdd_test_endpoint
from outsystems.cicd_probe.cicd_base import build_probe_endpoint
from outsystems.file_helpers.file import store_data, load_data
from outsystems.vars.vars_base import load_configuration_file
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS, MANIFEST_APPLICATION_NAME, MANIFEST_FLAG_IS_TEST_APPLICATION
# Exceptions
from outsystems.exceptions.invalid_parameters import InvalidParametersError
# Functions
# Variables

# ---------------------- VARS ----------------------
# Set script local variables
bdd_test = []  # will contain the BDD Framework tests for each app
bdd_modules = 0  # will count the number of bdd test modules
test_names = []  # will contain the names of the tests to run
test_list = []  # will contain the webflows output from BDD for the application
test_urls = []  # will contain the urls for the BDD framework


# ---------------------- SCRIPT ----------------------
def main(artifact_dir: str, apps: list, trigger_manifest: dict, bdd_http_proto: str, bdd_url: str, bdd_api_endpoint: str,
         bdd_client_api_endpoint: str, bdd_version: int, cicd_http_proto: str, cicd_url: str, cicd_api_endpoint: str,
         cicd_version: int, cicd_key: str, exclude_pattern: str):
    # use the script variables
    global bdd_test, bdd_modules, test_names, test_list, test_urls

    probe_endpoint = build_probe_endpoint(
        cicd_http_proto, cicd_url, cicd_api_endpoint, cicd_version)
    bdd_endpoint = build_bdd_endpoint(
        bdd_http_proto, bdd_url, bdd_api_endpoint, bdd_version)
    bdd_endpoint_client = build_bdd_endpoint(
        bdd_http_proto, bdd_url, bdd_client_api_endpoint, bdd_version)

    # Extract application list from manifest (if needed)
    if trigger_manifest:
        app_versions = trigger_manifest[MANIFEST_APPLICATION_VERSIONS]
        apps = [app_version[MANIFEST_APPLICATION_NAME] for app_version in app_versions if app_version[MANIFEST_FLAG_IS_TEST_APPLICATION]]

    # Query the CICD probe
    for app in apps:
        # Removes whitespaces in the beginning and end of the string
        app = app.strip()
        response = scan_bdd_test_endpoint(artifact_dir, probe_endpoint, app, cicd_key, exclude_pattern, cicd_version)
        if len(response) == 0:
            continue  # It has no test suites, continue the loop
        for test_endpoint in response:
            # Get the BDD test endpoints information, per module
            if cicd_version == 1 and "WebFlows" in test_endpoint["BDDTestEndpointsInfo"]:
                bdd_test += [{"EspaceName": test_endpoint["BDDTestEndpointsInfo"]["EspaceName"],
                              "WebFlows": test_endpoint["BDDTestEndpointsInfo"]["WebFlows"]}]
            elif cicd_version == 2 and "TestFlows" in test_endpoint:
                bdd_test += [{"EspaceName": test_endpoint["EspaceName"],
                              "BDDFrameworkType": test_endpoint["BDDFrameworkType"],
                              "TestFlows": test_endpoint["TestFlows"]}]
            else:
                raise NotImplementedError("Unsupported CICD Probe API version ({}).".format(cicd_version))
        # Increment bdd modules counter
        bdd_modules += len(response)

    print("{} BDD module(s) found.".format(bdd_modules), flush=True)

    # Get the tests to run (just for presentation)
    for bdd in bdd_test:  # For each BDD test
        if cicd_version == 1:
            for webflow in bdd["WebFlows"]:  # For each webflow
                if "WebScreens" in webflow:  # Sanity check to see if there are actual webscreens in the flow
                    test_list += webflow["WebScreens"]
        elif cicd_version == 2:
            for testflow in bdd["TestFlows"]:  # For each uiflow
                if "TestScreens" in testflow:  # Sanity check to see if there are actual testscreens in the flow
                    test_list += testflow["TestScreens"]

    print("{} BDD endpoint(s) scanned successfully.".format(len(test_list)), flush=True)

    # Get the names of the tests to run (just for presentation)
    for test in test_list:
        test_names.append(test["Name"])
    print("Tests to run: {}".format(test_names), flush=True)

    # For each test, generate the URL to query the BDD framework, to be used in the test class
    test_urls = []
    for bdd in bdd_test:  # For each BDD test module
        if cicd_version == 1:
            for webflow in bdd["WebFlows"]:  # For each webflow
                if "WebScreens" in webflow:  # Sanity check to see if there are actual webscreens in the flow
                    for webscreen in webflow["WebScreens"]:  # for each webscreen
                        test_endpoint = build_bdd_test_endpoint(bdd_endpoint, bdd["EspaceName"], webscreen["Name"])
                        test_urls.append(
                            {"TestSuite": bdd["EspaceName"], "Name": webscreen["Name"], "URL": test_endpoint})
        elif cicd_version == 2:
            for testflow in bdd["TestFlows"]:  # For each uiflow
                if "TestScreens" in testflow:  # Sanity check to see if there are actual testscreens in the flow
                    for testscreen in testflow["TestScreens"]:  # for each testscreen
                        if bdd["BDDFrameworkType"] == BDD_FRAMEWORK_TYPE_CLIENT:
                            target_bdd_endpoint = bdd_endpoint_client
                        else:
                            target_bdd_endpoint = bdd_endpoint
                        test_endpoint = build_bdd_test_endpoint(
                            target_bdd_endpoint, bdd["EspaceName"], testscreen["Name"])
                        test_urls.append(
                            {"TestSuite": bdd["EspaceName"], "Name": testscreen["Name"], "URL": test_endpoint})

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
                        help="Comma separated list of apps you want to deploy. Example: \"App1,App2 With Spaces,App3_With_Underscores\"")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="Manifest file (with JSON format). Contains required data used throughout the pipeline execution.")
    parser.add_argument("--cicd_probe_env", type=str,
                        help="URL for CICD Probe, without the API endpoint. Example: \"https://<host>\"", required=True)
    parser.add_argument("--cicd_probe_api", type=str,
                        help="(optional) Used to set the API endpoint for CICD Probe, without the version. Default: \"CI_CDProbe/rest\"", default=PROBE_API_ENDPOINT)
    parser.add_argument("--cicd_probe_version", type=int,
                        help="(optional) CICD Probe API version number. Default: 1", default=PROBE_API_VERSION)
    parser.add_argument("--cicd_probe_key", type=str,
                        help="(optional) Key for CICD Probe API calls (when enabled).")
    parser.add_argument("--exclude_pattern", type=str,
                        help="(optional) Regex for excluding specific ScreenFlows whose screens are not valid test endpoints")
    parser.add_argument("--bdd_framework_env", type=str,
                        help="URL for BDD Framework, without the API endpoint. Example: \"https://<host>\"", required=True)
    parser.add_argument("--bdd_framework_api", type=str,
                        help="(optional) Used to set the API endpoint for BDD Framework, without the version. Default: \"BDDFramework/rest\"", default=BDD_API_ENDPOINT)
    parser.add_argument("--bdd_framework_client_api", type=str,
                        help="(optional) Used to set the API endpoint for BDD Framework Client-side, without the version. Default: \"TestRunner_API/rest\"", default=BDD_CLIENT_API_ENDPOINT)
    parser.add_argument("--bdd_framework_version", type=int,
                        help="(optional) BDD Framework API version number. Default: 1", default=BDD_API_VERSION)
    parser.add_argument("-cf", "--config_file", type=str,
                        help="Config file path. Contains configuration values to override the default ones.")

    args = parser.parse_args()

    # Load config file if exists
    if args.config_file:
        load_configuration_file(args.config_file)
    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse App list (if it exists)
    apps = None
    if args.app_list:
        apps = args.app_list.split(',')
    # Parse Manifest file (if it exists)
    manifest_file = None
    if args.manifest_file:
        manifest_path = os.path.split(args.manifest_file)
        manifest_file = load_data(manifest_path[0], manifest_path[1])
    # Check if either an app list or a manifest file is being provided
    if not args.app_list and not args.manifest_file:
        raise InvalidParametersError("either --app_list or --manifest_file must be provided as arguments")

    # Parse the BDD API endpoint
    bdd_api_endpoint = args.bdd_framework_api
    # Parse the BDD Client-side API endpoint
    bdd_client_api_endpoint = args.bdd_framework_client_api
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
    # Parse CICD Probe API Key
    cicd_key = args.cicd_probe_key
    # Parse Exclude Pattern regex
    exclude_pattern = args.exclude_pattern

    # Calls the main script
    main(artifact_dir, apps, manifest_file, bdd_http_proto, bdd_url, bdd_api_endpoint, bdd_client_api_endpoint, bdd_version,
         cicd_http_proto, cicd_url, cicd_api_endpoint, cicd_version, cicd_key, exclude_pattern)
