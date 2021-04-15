# Python Modules
import os

# Custom Modules
# Exceptions
from outsystems.exceptions.not_enough_permissions import NotEnoughPermissionsError
# Functions
from outsystems.architecture_dashboard.ad_base import send_get_request, build_ad_endpoint
from outsystems.file_helpers.file import store_data

# Variables
from outsystems.vars.ad_vars import AD_API_ENDPOINT, AD_API_SUCCESS_CODE, AD_HTTP_PROTO, AD_API_HOST, AD_API_VERSION, AD_API_UNAUTHORIZED_CODE, AD_APP_ENDPOINT, AD_APP_SUCCESS_CODE
from outsystems.vars.file_vars import AD_FOLDER, AD_INFRA_FILE, AD_APP_FILE


# Returns the infrastructure technical debt summary
def get_infra_techdebt(artifact_dir: str, api_key: str, activation_code: str):

    request_string = build_ad_endpoint(AD_HTTP_PROTO, AD_API_HOST, AD_API_ENDPOINT, AD_API_VERSION)

    # Sends the request
    response = send_get_request(request_string, activation_code, api_key)
    status_code = int(response["http_status"])

    # Process the response based on the status code returned from the server
    if status_code == AD_API_SUCCESS_CODE:
        # Stores the result
        filename = os.path.join(AD_FOLDER, AD_INFRA_FILE)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == AD_API_UNAUTHORIZED_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to get Tecnical Debt information. Details {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns the application technical debt summary
def get_app_techdebt(artifact_dir: str, api_key: str, activation_code: str, app: dict):

    # Format the request URL to include the api endpoint
    request_string = "{}/{}/{}".format(build_ad_endpoint(AD_HTTP_PROTO, AD_API_HOST, AD_API_ENDPOINT, AD_API_VERSION), AD_APP_ENDPOINT, app["ApplicationKey"])
    # Sends the request
    response = send_get_request(request_string, activation_code, api_key)
    status_code = int(response["http_status"])

    # Process the response based on the status code returned from the server
    if status_code == AD_APP_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(app["ApplicationName"], AD_APP_FILE)
        filename = os.path.join(AD_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == AD_API_UNAUTHORIZED_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to get Tecnical Debt information. Details {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))
