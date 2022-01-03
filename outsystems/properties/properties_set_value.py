# Python Modules

# Custom Modules
# Functions
from outsystems.properties.properties_base import send_properties_put_request
# Variables
from outsystems.vars.properties_vars import SET_SITE_PROPERTY_VALUE_SUCCESS_CODE, SET_TIMER_SCHEDULE_SUCCESS_CODE, \
    SET_REST_ENDPOINT_URL_SUCCESS_CODE, SET_SOAP_ENDPOINT_URL_SUCCESS_CODE


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


def set_rest_endpoint_url(lt_url: str, token: str, module_key: str, environment_key: str, rest_endpoint_key: str, rest_endpoint_url: str):
    # Builds the API endpoint
    api_endpoint = "Modules/{}/Environments/{}/RESTReferences/{}/EffectiveURL/".format(module_key, environment_key, rest_endpoint_key)
    # Sends the request
    response = send_properties_put_request(
        lt_url, token, api_endpoint, rest_endpoint_url)
    status_code = response["http_status"]
    if status_code == SET_REST_ENDPOINT_URL_SUCCESS_CODE:
        return response["response"]
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


def set_soap_endpoint_url(lt_url: str, token: str, module_key: str, environment_key: str, soap_endpoint_key: str, soap_endpoint_url: str):
    # Builds the API endpoint
    api_endpoint = "Modules/{}/Environments/{}/SOAPReferences/{}/EffectiveURL/".format(module_key, environment_key, soap_endpoint_key)
    # Sends the request
    response = send_properties_put_request(
        lt_url, token, api_endpoint, soap_endpoint_url)
    status_code = response["http_status"]
    if status_code == SET_SOAP_ENDPOINT_URL_SUCCESS_CODE:
        return response["response"]
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


def set_timer_schedule(lt_url: str, token: str, module_key: str, environment_key: str, timer_key: str, timer_schedule: str):
    # Builds the API endpoint
    api_endpoint = "Modules/{}/Environments/{}/Timers/{}/Schedule/".format(module_key, environment_key, timer_key)
    # Sends the request
    response = send_properties_put_request(
        lt_url, token, api_endpoint, timer_schedule)
    status_code = response["http_status"]
    if status_code == SET_TIMER_SCHEDULE_SUCCESS_CODE:
        return response["response"]
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))
