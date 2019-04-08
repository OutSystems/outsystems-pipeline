# Custom Modules
# Functions
from outsystems.bdd_framework.bdd_base import send_bdd_get_run_request
# Variables
from outsystems.vars.bdd_vars import BDD_RUNNER_SUCCESS_CODE

# Run existing BDD test in the target environment.
def run_bdd_test(test_url: str):
    # Sends the request
    response = send_bdd_get_run_request(test_url, None)
    status_code = response["http_status"]
    if status_code == BDD_RUNNER_SUCCESS_CODE:
        return response["response"]
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))
