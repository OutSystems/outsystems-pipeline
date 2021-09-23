# Python Modules

# Custom Modules
# Functions
from outsystems.properties.properties_base import send_properties_put_request
# Variables


def set_site_property_value(lt_url: str, token: str, module_key: str, environment_key: str, site_property_key: str, site_property_value: str):
    # Builds the API endpoint
    api_endpoint = "Modules/{}/Environments/{}/SiteProperties/{}/Value/".format(module_key, environment_key, site_property_key)
    # Sends the request
    response = send_properties_put_request(
        lt_url, token, api_endpoint, site_property_value)
    status_code = response["http_status"]    
    if status_code == SET_SITE_PROPERTY_VALUE_SUCCESS_CODE:
        return response["response"]
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))

