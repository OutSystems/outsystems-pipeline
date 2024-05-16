# Python Modules
import requests
import json

# Custom Modules
# Exceptions
from outsystems.exceptions.invalid_json_response import InvalidJsonResponseError
# Variables
from outsystems.vars.lifetime_vars import LIFETIME_SSL_CERT_VERIFY
# Functions
from outsystems.vars.vars_base import get_configuration_value
from outsystems.file_helpers.file import check_file


# Method that builds the LifeTime endpoint based on the LT host
def build_lt_endpoint(lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int):
    # Builds the endpoint for LT and returns it
    return "{}://{}/{}/v{}".format(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)


# Sends a GET request to LT, with url_params
def send_get_request(lt_api: str, token: str, api_endpoint: str, url_params: dict):
    # Auth token + content type json
    headers = {'content-type': 'application/json',
               'authorization': 'Bearer ' + token}
    # Format the request URL to include the api endpoint
    request_string = "{}/{}".format(lt_api, api_endpoint)
    response = requests.get(request_string, params=url_params, headers=headers, verify=get_configuration_value("LIFETIME_SSL_CERT_VERIFY", LIFETIME_SSL_CERT_VERIFY))
    response_obj = {"http_status": response.status_code, "response": {}}
    if len(response.text) > 0:
        try:
            response_obj["response"] = response.json()
        except:
            raise InvalidJsonResponseError(
                "GET {}: The JSON response could not be parsed. Response: {}".format(request_string, response.text))
    return response_obj


# Sends a POST request to LT, with a payload. The json part is ignored
def send_post_request(lt_api: str, token: str, api_endpoint: str, payload: str):
    # Auth token + content type json
    headers = {'content-type': 'application/json',
               'authorization': 'Bearer ' + token}
    # Format the request URL to include the api endpoint
    request_string = "{}/{}".format(lt_api, api_endpoint)
    response = requests.post(
        request_string, data=payload, json=None, headers=headers, verify=get_configuration_value("LIFETIME_SSL_CERT_VERIFY", LIFETIME_SSL_CERT_VERIFY))
    response_obj = {"http_status": response.status_code, "response": {}}
    # Since LT API POST requests do not reply with native JSON, we have to make it ourselves
    if len(response.text) > 0:
        try:
            response_obj["response"] = response.json()
        except:
            # Workaround for POST /deployments/ since the response is not JSON, just text
            response_obj["response"] = json.loads('"{}"'.format(response.text))
    return response_obj


# Sends a POST request to LT, with binary content.
def send_binary_post_request(lt_api: str, token: str, api_endpoint: str, dest_env: str, lt_endpont: str, binary_file_path: str):
    # Auth token + content type octet-stream
    headers = {'content-type': 'application/octet-stream',
               'authorization': 'Bearer ' + token}
    # Format the request URL to include the api endpoint
    request_string = "{}/{}/{}/{}".format(lt_api, api_endpoint, dest_env, lt_endpont)

    if check_file("", binary_file_path):
        with open(binary_file_path, 'rb') as f:
            data = f.read()
    response = requests.post(request_string, data=data, headers=headers, verify=get_configuration_value("LIFETIME_SSL_CERT_VERIFY", LIFETIME_SSL_CERT_VERIFY))
    response_obj = {"http_status": response.status_code, "response": {}}
    # Since LT API POST requests do not reply with native JSON, we have to make it ourselves
    if len(response.text) > 0:
        try:
            response_obj["response"] = response.json()
        except:
            # Workaround for POST /deployments/ since the response is not JSON, just text
            response_obj["response"] = json.loads('"{}"'.format(response.text))
    return response_obj


# Sends a DELETE request to LT
def send_delete_request(lt_api: str, token: str, api_endpoint: str):
    # Auth token + content type json
    headers = {'content-type': 'application/json',
               'authorization': 'Bearer ' + token}
    # Format the request URL to include the api endpoint
    request_string = "{}/{}".format(lt_api, api_endpoint)
    response = requests.delete(request_string, headers=headers, verify=get_configuration_value("LIFETIME_SSL_CERT_VERIFY", LIFETIME_SSL_CERT_VERIFY))
    response_obj = {"http_status": response.status_code, "response": {}}
    if len(response.text) > 0:
        try:
            response_obj["response"] = response.json()
        except:
            raise InvalidJsonResponseError(
                "DELETE {}: The JSON response could not be parsed. Response: {}".format(request_string, response.text))
    return response_obj


# Sends a GET request to LT, with url_params
def send_download_request(pkg_url: str, token: str):
    # Auth token + content type json
    headers = {'content-type': 'application/json',
               'authorization': token}
    # Format the request URL to include the api endpoint
    response = requests.get(pkg_url, headers=headers, verify=get_configuration_value("LIFETIME_SSL_CERT_VERIFY", LIFETIME_SSL_CERT_VERIFY))
    response_obj = {"http_status": response.status_code, "response": response.content}
    return response_obj
