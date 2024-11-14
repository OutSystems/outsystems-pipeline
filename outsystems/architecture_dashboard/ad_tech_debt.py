# Python Modules
import os

# Custom Modules
# Exceptions
from outsystems.exceptions.not_enough_permissions import NotEnoughPermissionsError
# Functions
from outsystems.architecture_dashboard.ad_base import send_get_request, build_ad_endpoint
from outsystems.file_helpers.file import store_data

# Variables
from outsystems.vars.ad_vars import AD_API_ENDPOINT, AD_API_SUCCESS_CODE, AD_HTTP_PROTO, AD_API_VERSION, \
    AD_API_UNAUTHORIZED_CODE, AD_APP_ENDPOINT, AD_APP_LIMIT_DEFAULT, AD_APP_SUCCESS_CODE, \
    AD_LEVELS_ENDPOINT, AD_LEVELS_SUCCESS_CODE, AD_CATEGORIES_ENDPOINT, AD_CATEGORIES_SUCCESS_CODE, \
    AD_API_NOT_FOUND_CODE
from outsystems.vars.file_vars import AD_FOLDER, AD_FILE_PREFIX, AD_INFRA_FILE, AD_APP_FILE, \
    AD_LEVELS_FILE, AD_CATEGORIES_FILE


# Returns the infrastructure technical debt summary
def get_infra_techdebt(artifact_dir: str, ad_api_host: str, activation_code: str, api_key: str):

    # Format the request URL to include the api endpoint
    base_url = build_ad_endpoint(AD_HTTP_PROTO, ad_api_host, AD_API_ENDPOINT, AD_API_VERSION)
    request_string = "{}/{}".format(base_url, AD_APP_ENDPOINT)
    params = {"Limit": AD_APP_LIMIT_DEFAULT}

    # Sends the request
    response = send_get_request(request_string, activation_code, api_key, params)
    status_code = int(response["http_status"])

    # Process the response based on the status code returned from the server
    if status_code == AD_API_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(AD_FILE_PREFIX, AD_INFRA_FILE)
        filename = os.path.join(AD_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == AD_API_UNAUTHORIZED_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to get Tecnical Debt information. Details {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns the application technical debt summary
def get_app_techdebt(artifact_dir: str, ad_api_host: str, activation_code: str, api_key: str, app: dict):

    # Format the request URL to include the api endpoint
    base_url = build_ad_endpoint(AD_HTTP_PROTO, ad_api_host, AD_API_ENDPOINT, AD_API_VERSION)
    request_string = "{}/{}".format(base_url, AD_APP_ENDPOINT)
    params = {"ApplicationGUID": app["ApplicationKey"]}

    # Sends the request
    response = send_get_request(request_string, activation_code, api_key, params)
    status_code = int(response["http_status"])

    # Process the response based on the status code returned from the server
    if status_code == AD_APP_SUCCESS_CODE:
        # Stores the result
        filename = "{}.{}{}".format(AD_FILE_PREFIX, app["ApplicationName"], AD_APP_FILE)
        filename = os.path.join(AD_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    # No application found with a key matching the Application input parameter
    # Probably all modules of the app are ignored"
    elif status_code == AD_API_NOT_FOUND_CODE:
        return None
    elif status_code == AD_API_UNAUTHORIZED_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to get Tecnical Debt information. Details {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns the technical debt levels detail
def get_techdebt_levels(artifact_dir: str, ad_api_host: str, activation_code: str, api_key: str):

    # Format the request URL to include the api endpoint
    base_url = build_ad_endpoint(AD_HTTP_PROTO, ad_api_host, AD_API_ENDPOINT, AD_API_VERSION)
    request_string = "{}/{}".format(base_url, AD_LEVELS_ENDPOINT)

    # Sends the request
    response = send_get_request(request_string, activation_code, api_key)
    status_code = int(response["http_status"])

    # Process the response based on the status code returned from the server
    if status_code == AD_LEVELS_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(AD_FILE_PREFIX, AD_LEVELS_FILE)
        filename = os.path.join(AD_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == AD_API_UNAUTHORIZED_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to get Tecnical Debt information. Details {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns the technical debt categories detail
def get_techdebt_categories(artifact_dir: str, ad_api_host: str, activation_code: str, api_key: str):

    # Format the request URL to include the api endpoint
    base_url = build_ad_endpoint(AD_HTTP_PROTO, ad_api_host, AD_API_ENDPOINT, AD_API_VERSION)
    request_string = "{}/{}".format(base_url, AD_CATEGORIES_ENDPOINT)

    # Sends the request
    response = send_get_request(request_string, activation_code, api_key)
    status_code = int(response["http_status"])

    # Process the response based on the status code returned from the server
    if status_code == AD_CATEGORIES_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(AD_FILE_PREFIX, AD_CATEGORIES_FILE)
        filename = os.path.join(AD_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == AD_API_UNAUTHORIZED_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to get Tecnical Debt information. Details {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))
