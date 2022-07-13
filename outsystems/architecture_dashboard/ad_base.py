# Python Modules
import requests

# Custom Modules
# Exceptions
from outsystems.exceptions.invalid_json_response import InvalidJsonResponseError


# Method that builds the endpoint for Architecture Dashboard API and returns it
def build_ad_endpoint(ad_http_proto: str, ad_api_host: str, ad_api_endpoint: str, ad_api_version: int):
    return "{}://{}/{}/v{}".format(ad_http_proto, ad_api_host, ad_api_endpoint, ad_api_version)


# Sends a GET request to Architecture Dashboard
def send_get_request(request_string: str, activation_code: str, api_key: str, url_params: dict = None):
    # API key + Customer Activation Code
    headers = {'x-api-key': api_key,
               'x-activation-code': activation_code}

    response = requests.get(request_string, params=url_params, headers=headers)
    response_obj = {"http_status": response.status_code, "response": {}}
    if len(response.text) > 0:
        try:
            response_obj["response"] = response.json()
        except:
            raise InvalidJsonResponseError(
                "GET {}: The JSON response could not be parsed. Response: {}".format(request_string, response.text))
    return response_obj
