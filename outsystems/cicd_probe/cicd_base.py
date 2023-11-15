# Python Modules
import requests

# Custom Modules
from outsystems.exceptions.invalid_json_response import InvalidJsonResponseError
# Variables
from outsystems.vars.cicd_vars import PROBE_API_SSL_CERT_VERIFY
# Functions
from outsystems.vars.vars_base import get_configuration_value


# Method that builds the CICD Probe endpoint based on the environment host
def build_probe_endpoint(probe_http_proto: str, probe_url: str, probe_api_endpoint: str, probe_api_version: int):
    return "{}://{}/{}/v{}".format(probe_http_proto, probe_url, probe_api_endpoint, probe_api_version)


# Sends a GET request to LT, with url_params
def send_probe_get_request(probe_api: str, probe_endpoint: str, api_key: str, url_params: str):
    # Format the request URL to include the api endpoint
    request_string = "{}/{}".format(probe_api, probe_endpoint)
    # Set API key header, when provided
    headers = {"X-CICDProbe-Key": api_key} if api_key else None
    # Send the request
    response = requests.get(request_string, params=url_params, headers=headers, verify=get_configuration_value("PROBE_API_SSL_CERT_VERIFY", PROBE_API_SSL_CERT_VERIFY))
    response_obj = {"http_status": response.status_code, "response": {}}
    if len(response.text) > 0:
        try:
            response_obj["response"] = response.json()
        except:
            raise InvalidJsonResponseError(
                "GET {}: The JSON response could not be parsed. Response: {}".format(request_string, response.text))

    return response_obj
