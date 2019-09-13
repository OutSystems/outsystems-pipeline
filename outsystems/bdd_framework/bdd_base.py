# Python Modules
import requests

# Custom Modules
# Exceptions
from outsystems.exceptions.invalid_json_response import InvalidJsonResponseError
# Variables
from outsystems.vars.bdd_vars import BDD_TEST_RUNNER_ENDPOINT


# Method that builds the BDD Framework endpoint based on the environment host
def build_bdd_endpoint(bdd_http_proto: str, bdd_url: str, bdd_api_endpoint: str, bdd_api_version: int):
    # Builds the endpoint for BDD Framework and returns it
    return "{}://{}/{}/v{}".format(bdd_http_proto, bdd_url, bdd_api_endpoint, bdd_api_version)


# Method that builds the BDD Framework test endpoint based on the environment host, application and test name
def build_bdd_test_endpoint(bdd_endpoint: str, espace_name: str, webscreen_name: str):
    # Builds the endpoint for BDD Framework and returns it
    return "{}/{}/{}/{}".format(bdd_endpoint, BDD_TEST_RUNNER_ENDPOINT, espace_name, webscreen_name)


# Runs the test on the BDD Framework app
def send_bdd_get_request(bdd_api: str, bdd_endpoint: str, url_params: str):
    # Format the request URL to include the api endpoint
    request_string = "{}/{}".format(bdd_api, bdd_endpoint)
    return send_bdd_get_run_request(request_string, url_params)


# Runs the test on the BDD Framework app
def send_bdd_get_run_request(test_endpoint: str, url_params: str):
    # Send the request
    response = requests.get(test_endpoint, params=url_params)
    response_obj = {"http_status": response.status_code, "response": {}}
    if len(response.text) > 0:
        try:
            response_obj["response"] = response.json()
        except:
            raise InvalidJsonResponseError(
                "GET {}: The JSON response could not be parsed. Response: {}".format(test_endpoint, response.text))
    return response_obj
