# Python Modules
import os

# Custom Modules
# Functions
from outsystems.cicd_probe.cicd_base import send_probe_get_request
from outsystems.file_helpers.file import store_data
# Variables
from outsystems.vars.cicd_vars import SCAN_BDD_TESTS_ENDPOINT, PROBE_SCAN_SUCCESS_CODE
from outsystems.vars.file_vars import PROBE_APPLICATION_SCAN_FILE, PROBE_FOLDER


# Scan existing BDD test endpoints (i.e. WebScreens) in the target environment.
def scan_bdd_test_endpoint(artifact_dir: str, endpoint: str, application_name: str):
    # Builds the API params
    params = {"ApplicationName": application_name}
    # Sends the request
    response = send_probe_get_request(
        endpoint, SCAN_BDD_TESTS_ENDPOINT, params)
    status_code = response["http_status"]
    if status_code == PROBE_SCAN_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(application_name, PROBE_APPLICATION_SCAN_FILE)
        filename = os.path.join(PROBE_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))
