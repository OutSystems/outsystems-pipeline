# Python Modules
import os

# Custom Modules
# Exceptions
from outsystems.exceptions.app_does_not_exist import AppDoesNotExistError
from outsystems.exceptions.invalid_parameters import InvalidParametersError
from outsystems.exceptions.no_apps_available import NoAppsAvailableError
from outsystems.exceptions.server_error import ServerError
from outsystems.exceptions.not_enough_permissions import NotEnoughPermissionsError
from outsystems.exceptions.environment_not_found import EnvironmentNotFoundError
from outsystems.exceptions.app_version_error import AppVersionsError
# Functions
from outsystems.file_helpers.file import store_data, load_data, clear_cache
from outsystems.lifetime.lifetime_base import send_get_request
# Variables
from outsystems.vars.file_vars import APPLICATION_FOLDER, APPLICATIONS_FILE, APPLICATION_FILE, APPLICATION_VERSIONS_FILE, APPLICATION_VERSION_FILE
from outsystems.vars.lifetime_vars import APPLICATIONS_ENDPOINT, APPLICATION_VERSIONS_ENDPOINT, APPLICATIONS_SUCCESS_CODE, \
    APPLICATIONS_EMPTY_CODE, APPLICATIONS_FLAG_FAILED_CODE, APPLICATIONS_FAILED_CODE, APPLICATION_SUCCESS_CODE, \
    APPLICATION_FLAG_FAILED_CODE, APPLICATION_NO_PERMISSION_CODE, APPLICATION_FAILED_CODE, APPLICATION_VERSION_SUCCESS_CODE, \
    APPLICATION_VERSION_INVALID_CODE, APPLICATION_VERSION_NO_PERMISSION_CODE, APPLICATION_VERSION_FAILED_CODE, APPLICATION_VERSION_FAILED_LIST_CODE

# Returns a list of applications that exist in the infrastructure.
def get_applications(artifact_dir: str, endpoint: str, auth_token: str, extra_data: bool):
    params = {"IncludeModules": extra_data, "IncludeEnvStatus": extra_data}
    # Sends the request
    response = send_get_request(
        endpoint, auth_token, APPLICATIONS_ENDPOINT, params)
    status_code = int(response["http_status"])
    # Process the response based on the status code returned from the server
    if status_code == APPLICATIONS_SUCCESS_CODE:
        # Stores the result
        store_data(artifact_dir, APPLICATIONS_FILE, response["response"])
        return response["response"]
    elif status_code == APPLICATIONS_EMPTY_CODE:
        raise NoAppsAvailableError(
            "No applications available in the infrastructure. Details {}".format(response["response"]))
    elif status_code == APPLICATIONS_FLAG_FAILED_CODE:
        raise InvalidParametersError(
            "There was an error with the 'extra_data' flag or the request was invalid when listing all applications. The params used were: {}. Details: {}".format(params, response["response"]))
    elif status_code == APPLICATIONS_FAILED_CODE:
        raise ServerError(
            "Failed to list the applications. Details {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))

# Returns the details of a given application.
def get_application_data(artifact_dir: str, endpoint: str, auth_token: str, extra_data: bool, **kwargs):
    # Tuple with (AppName, AppKey): app_info[0] = AppName; app_info[1] = AppKey
    app_info = _get_application_info(
        artifact_dir, endpoint, auth_token, **kwargs)
    query = "{}/{}".format(APPLICATIONS_ENDPOINT, app_info[1])
    params = {"IncludeModules": extra_data, "IncludeEnvStatus": extra_data}
    # Sends the request
    response = send_get_request(endpoint, auth_token, query, params)
    status_code = int(response["http_status"])
    if status_code == APPLICATION_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(app_info[0], APPLICATION_FILE)
        filename = os.path.join(APPLICATION_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == APPLICATION_FLAG_FAILED_CODE:
        raise InvalidParametersError(
            "There was an error with the 'extra_data' flag or the request was invalid when listing the application. The params used were: {}. Details: {}".format(params, response["response"]))
    elif status_code == APPLICATION_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the details of that application. Details: {}".format(response["response"]))
    elif status_code == APPLICATION_FAILED_CODE:
        raise EnvironmentNotFoundError(
            "Failed getting running applications because one of the environments was not found. Details: {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))

# Returns a list of versions of a given application.
def get_application_versions(artifact_dir: str, endpoint: str, auth_token: str, number_of_versions: int, **kwargs):
    # Tuple with (AppName, AppKey): app_info[0] = AppName; app_info[1] = AppKey
    app_info = _get_application_info(
        artifact_dir, endpoint, auth_token, **kwargs)
    query = "{}/{}/{}".format(APPLICATIONS_ENDPOINT,
                              app_info[1], APPLICATION_VERSIONS_ENDPOINT)
    # Sends the request
    response = send_get_request(endpoint, auth_token, query, {
                                "MaximumVersionsToReturn": number_of_versions})
    status_code = int(response["http_status"])
    if status_code == APPLICATION_VERSION_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(app_info[0], APPLICATION_VERSIONS_FILE)
        filename = os.path.join(APPLICATION_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == APPLICATION_VERSION_INVALID_CODE:
        raise InvalidParametersError(
            "Invalid request due to invalid max versions to return (less than 0). Details: {}".format(response["response"]))
    elif status_code == APPLICATION_VERSION_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the versions of that application. Details: {}".format(response["response"]))
    elif status_code == APPLICATION_VERSION_FAILED_CODE:
        raise AppDoesNotExistError(
            "Failed to retrieve the application. Details: {}".format(response["response"]))
    elif status_code == APPLICATION_VERSION_FAILED_LIST_CODE:
        raise AppVersionsError(
            "Failed to list the application versions. Details: {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))

def get_application_version(artifact_dir: str, endpoint: str, auth_token: str, extra_data: bool, version_id: str, **kwargs):
    # Tuple with (AppName, AppKey): app_info[0] = AppName; app_info[1] = AppKey
    app_info = _get_application_info(artifact_dir, endpoint, auth_token, **kwargs)
    query = "{}/{}/{}/{}".format(APPLICATIONS_ENDPOINT,
                              app_info[1], APPLICATION_VERSIONS_ENDPOINT, version_id)
    # Sends the request
    params = {"IncludeModules": extra_data, "IncludeEnvStatus": extra_data}
    response = send_get_request(endpoint, auth_token, query, params)
    status_code = int(response["http_status"])
    if status_code == APPLICATION_VERSION_SUCCESS_CODE:
        # Stores the result
        filename = "{}.{}{}".format(app_info[0], version_id, APPLICATION_VERSION_FILE)
        filename = os.path.join(APPLICATION_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == APPLICATION_VERSION_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the versions of that application. Details: {}".format(response["response"]))
    elif status_code == APPLICATION_VERSION_FAILED_CODE:
        raise AppDoesNotExistError(
            "Failed to retrieve the application. Details: {}".format(response["response"]))
    elif status_code == APPLICATION_VERSION_FAILED_LIST_CODE:
        raise AppVersionsError(
            "Failed to retrieve the application version. Details: {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))

def get_running_app_version(artifact_dir: str, endpoint: str, auth_token: str, env_key :str, **kwargs):
    # Tuple with (AppName, AppKey): app_tuple[0] = AppName; app_tuple[1] = AppKey
    app_tuple = _get_application_info(artifact_dir, endpoint, auth_token, **kwargs)
    app_data = {}

    deployed_app = get_application_data(artifact_dir, endpoint, auth_token, True, app_name=app_tuple[0])
    for status_in_env in deployed_app["AppStatusInEnvs"]:
        if status_in_env["EnvironmentKey"] == env_key:
            app_version_data = get_application_version(artifact_dir, endpoint, auth_token, True, status_in_env["BaseApplicationVersionKey"], app_name=app_tuple[0])
            app_data = {"ApplicationName": app_tuple[0], "ApplicationKey": app_tuple[1], "Version": app_version_data["Version"],
                    "VersionKey": status_in_env["BaseApplicationVersionKey"]}
            # Since these 2 fields were only introduced in a minor of OS11, we check here if they exist
            # We can't just use the version
            if "CreatedOn" in app_version_data:
                app_data.update({"CreatedOn": app_version_data["CreatedOn"]})
            if "ChangeLog" in app_version_data:
                app_data.update({"ChangeLog": app_version_data["ChangeLog"]})
            break

    return app_data

########################################## PRIVATE METHODS ##########################################
# Private method to get the App name or key into a tuple (name,key).
def _get_application_info(artifact_dir: str, api_url: str, auth_token: str, **kwargs):
    if "app_name" in kwargs:
        app_key = _find_application_key(
            artifact_dir, api_url, auth_token, kwargs["app_name"])
        app_name = kwargs["app_name"]
    elif "app_key" in kwargs:
        app_key = kwargs["app_key"]
        app_name = _find_application_name(
            artifact_dir, api_url, auth_token, kwargs["app_key"])
    else:
        raise InvalidParametersError(
            "You need to use either app_name=<name> or app_key=<key> as parameters to call this method.")
    return (app_name, app_key)

# Private method to find an application key from name
def _find_application_key(artifact_dir: str, api_url: str, auth_token: str, application_name: str):
    app_key = ""
    cached_results = False
    try:
        # Try searching the key on the cache
        applications = load_data(artifact_dir, APPLICATIONS_FILE)
        cached_results = True
    except FileNotFoundError:
        # Query the LT API, since there's no cache
        applications = get_applications(
            artifact_dir, api_url, auth_token, False)
    for app in applications:
        if app["Name"] == application_name:
            app_key = app["Key"]
            break
    # If the app key was not found, determine if it needs to invalidate the cache or the application does not exist
    # since we explitly clear the cache, and the code is not multithreaded, it should not lead to recursion issues
    # If the cache was not used in the first place, it means the app does not exist
    if app_key == "" and not cached_results:
        raise AppDoesNotExistError(
            "Failed to retrieve the application. Please make sure the app exists in the environment. App Name: {}".format(application_name))
    # If the cache was used, it needs to be cleared and re-fetched from the LT server
    elif app_key == "" and cached_results:
        clear_cache(artifact_dir, APPLICATIONS_FILE)
        return _find_application_key(artifact_dir, api_url, auth_token, application_name)
    return app_key

# Private method to find an application name from key
def _find_application_name(artifact_dir: str, api_url: str, auth_token: str, application_key: str):
    app_name = ""
    cached_results = False
    try:
        # Try searching the key on the cache
        applications = load_data(artifact_dir, APPLICATIONS_FILE)
        cached_results = True
    except FileNotFoundError:
        # Query the LT API, since there's no cache
        applications = get_applications(
            artifact_dir, api_url, auth_token, False)
    for app in applications:
        if app["Key"] == application_key:
            app_name = app["Name"]
            break
    # If the app name  was not found, determine if it needs to invalidate the cache or the application does not exist
    # since we explitly clear the cache, and the code is not multithreaded, it should not lead to recursion issues
    # If the cache was not used in the first place, it means the app does not exist
    if app_name == "" and not cached_results:
        raise AppDoesNotExistError(
            "Failed to retrieve the application. Please make sure the app exists in the environment. App Key: {}".format(application_key))
    # If the cache was used, it needs to be cleared and re-fetched from the LT server
    elif app_name == "" and cached_results:
        clear_cache(artifact_dir, APPLICATIONS_FILE)
        return _find_application_name(artifact_dir, api_url, auth_token, application_key)
    return app_name
