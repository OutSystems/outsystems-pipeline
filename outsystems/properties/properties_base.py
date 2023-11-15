# Python Modules
import requests

# Custom Modules
from outsystems.exceptions.invalid_json_response import InvalidJsonResponseError
from outsystems.vars.properties_vars import PROPERTIES_API_HTTP_PROTO, PROPERTIES_API_ENDPOINT, PROPERTIES_API_VERSION, PROPERTIES_API_SSL_CERT_VERIFY
# Functions
from outsystems.vars.vars_base import get_configuration_value


# Method that builds the Properties API endpoint based on the environment host
def build_properties_api_url(properties_http_proto: str, lt_url: str, properties_api_endpoint: str, properties_api_version: int):
    return "{}://{}/{}/v{}".format(properties_http_proto, lt_url, properties_api_endpoint, properties_api_version)


# Sends a PUT request to Properties API, with a payload. The json part is ignored
def send_properties_put_request(lt_url: str, token: str, api_endpoint: str, payload: str):
    # Auth token + content type json
    headers = {'content-type': 'application/json',
               'authorization': 'Bearer ' + token}
    # Format the request URL to include the api endpoint
    properties_api_url = build_properties_api_url(PROPERTIES_API_HTTP_PROTO, lt_url, PROPERTIES_API_ENDPOINT, PROPERTIES_API_VERSION)
    request_string = "{}/{}".format(properties_api_url, api_endpoint)
    response = requests.put(
        request_string, data=payload, json=None, headers=headers, verify=get_configuration_value("PROPERTIES_API_SSL_CERT_VERIFY", PROPERTIES_API_SSL_CERT_VERIFY))
    response_obj = {"http_status": response.status_code, "response": {}}
    if len(response.text) > 0:
        try:
            response_obj["response"] = response.json()
        except:
            raise InvalidJsonResponseError(
                "PUT {}: The JSON response could not be parsed. Response: {}".format(request_string, response.text))

    return response_obj
