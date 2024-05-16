# Python Modules
import os

# Custom Modules
# Exceptions
from outsystems.exceptions.invalid_parameters import InvalidParametersError
from outsystems.exceptions.environment_not_found import EnvironmentNotFoundError
from outsystems.exceptions.not_enough_permissions import NotEnoughPermissionsError
from outsystems.exceptions.server_error import ServerError
# Functions
from outsystems.lifetime.lifetime_base import send_download_request

# Variables
from outsystems.vars.lifetime_vars import DOWNLOAD_SUCCESS_CODE, DOWNLOAD_INVALID_KEY_CODE, \
    DOWNLOAD_NO_PERMISSION_CODE, DOWNLOAD_NOT_FOUND, DOWNLOAD_FAILED_CODE


# Downloads a binary file from a LifeTime download link
def download_package(file_path: str, auth_token: str, pkg_url: str):
    # Sends the request
    response = send_download_request(pkg_url, auth_token)
    status_code = int(response["http_status"])

    if status_code == DOWNLOAD_SUCCESS_CODE:
        # Remove the spaces in the filename
        file_path = file_path.replace(" ", "_")
        # Makes sure that, if a directory is in the filename, that directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(response["response"])
    elif status_code == DOWNLOAD_INVALID_KEY_CODE:
        raise InvalidParametersError("The required type <Type> is invalid for given keys (EnvironmentKey; ApplicationKey). Details: {}".format(
            response["response"]))
    elif status_code == DOWNLOAD_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError("User doesn't have permissions for the given keys (EnvironmentKey; ApplicationKey). Details: {}".format(
            response["response"]))
    elif status_code == DOWNLOAD_NOT_FOUND:
        raise EnvironmentNotFoundError("No environment or application found. Please check that the EnvironmentKey and ApplicationKey exist. Details: {}".format(
            response["response"]))
    elif status_code == DOWNLOAD_FAILED_CODE:
        raise ServerError("Failed to start the operation to package. Details: {}".format(
            response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))
