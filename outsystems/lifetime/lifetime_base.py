# Python Modules
import requests
import json

# Custom Modules
# Exceptions
from outsystems.exceptions.invalid_json_response import InvalidJsonResponseError

# Method that builds the LifeTime endpoint based on the LT host
def build_lt_endpoint(lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int):
    # Builds the endpoint for LT and returns it
    return "{}://{}/{}/v{}".format(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

# Sends a GET request to LT, with url_params
def send_get_request(lt_api: str, token: str, api_endpoint: str, url_params: str):
    response_obj = {}
    # Auth token + content type json
    headers = {'content-type': 'application/json',
               'authorization': 'Bearer ' + token}
    # Format the request URL to include the api endpoint
    request_string = "{}/{}".format(lt_api, api_endpoint)
    response = requests.get(request_string, params=url_params, headers=headers)
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
    response_obj = {}
    # Auth token + content type json
    headers = {'content-type': 'application/json',
               'authorization': 'Bearer ' + token}
    # Format the request URL to include the api endpoint
    request_string = "{}/{}".format(lt_api, api_endpoint)
    response = requests.post(
        request_string, data=payload, json=None, headers=headers)
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
    response_obj = {}
    # Auth token + content type json
    headers = {'content-type': 'application/json',
               'authorization': 'Bearer ' + token}
    # Format the request URL to include the api endpoint
    request_string = "{}/{}".format(lt_api, api_endpoint)
    response = requests.delete(request_string, headers=headers)
    response_obj = {"http_status": response.status_code, "response": {}}
    if len(response.text) > 0:
        try:
            response_obj["response"] = response.json()
        except:
            raise InvalidJsonResponseError(
                "DELETE {}: The JSON response could not be parsed. Response: {}".format(request_string, response.text))
    return response_obj