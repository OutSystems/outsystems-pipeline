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
from outsystems.vars.file_vars import MODULES_FOLDER, MODULES_FILE, MODULE_FILE, MODULE_VERSIONS_FILE, MODULE_VERSION_FILE
from outsystems.vars.lifetime_vars import MODULES_ENDPOINT, MODULE_VERSIONS_ENDPOINT, MODULES_SUCCESS_CODE, \
    MODULES_EMPTY_CODE, MODULES_FLAG_FAILED_CODE, MODULES_FAILED_CODE, MODULE_SUCCESS_CODE, \
    MODULE_FLAG_FAILED_CODE, MODULE_NO_PERMISSION_CODE, MODULE_FAILED_CODE, MODULE_VERSION_SUCCESS_CODE, \
    MODULE_VERSION_INVALID_CODE, MODULE_VERSION_NO_PERMISSION_CODE, MODULE_VERSION_FAILED_CODE, \
    MODULE_VERSION_FAILED_LIST_CODE


# Returns a list of modules that exist in the infrastructure.
def get_modules(artifact_dir: str, endpoint: str, auth_token: str, extra_data: bool):
    params = {"IncludeEnvStatus": extra_data}
    # Sends the request
    response = send_get_request(
        endpoint, auth_token, MODULES_ENDPOINT, params)
    status_code = int(response["http_status"])
    # Process the response based on the status code returned from the server
    if status_code == MODULES_SUCCESS_CODE:
        # Stores the result
        store_data(artifact_dir, MODULES_FILE, response["response"])
        return response["response"]
    elif status_code == MODULES_EMPTY_CODE:
        raise NoAppsAvailableError(
            "No applications available in the infrastructure. Details {}".format(response["response"]))
    elif status_code == MODULES_FLAG_FAILED_CODE:
        raise InvalidParametersError(
            "There was an error with the 'extra_data' flag or the request was invalid when listing all applications. The params used were: {}. Details: {}".format(params, response[
                "response"]))
    elif status_code == MODULES_FAILED_CODE:
        raise ServerError(
            "Failed to list the applications. Details {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns the details of a given module.
def get_module_data(artifact_dir: str, endpoint: str, auth_token: str, extra_data: bool, **kwargs):
    # Tuple with (AppName, AppKey): app_info[0] = AppName; app_info[1] = AppKey
    app_info = _get_module_info(
        artifact_dir, endpoint, auth_token, **kwargs)
    query = "{}/{}".format(MODULES_ENDPOINT, app_info[1])
    params = {"IncludeModules": extra_data, "IncludeEnvStatus": extra_data}
    # Sends the request
    response = send_get_request(endpoint, auth_token, query, params)
    status_code = int(response["http_status"])
    if status_code == MODULE_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(app_info[0], MODULE_FILE)
        filename = os.path.join(MODULES_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == MODULE_FLAG_FAILED_CODE:
        raise InvalidParametersError(
            "There was an error with the 'extra_data' flag or the request was invalid when listing the application. The params used were: {}. Details: {}".format(params, response[
                "response"]))
    elif status_code == MODULE_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the details of that application. Details: {}".format(response["response"]))
    elif status_code == MODULE_FAILED_CODE:
        raise EnvironmentNotFoundError(
            "Failed getting running applications because one of the environments was not found. Details: {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns a list of versions of a given module.
def get_module_versions(artifact_dir: str, endpoint: str, auth_token: str, number_of_versions: int, **kwargs):
    # Tuple with (AppName, AppKey): app_info[0] = AppName; app_info[1] = AppKey
    module_info = _get_module_info(
        artifact_dir, endpoint, auth_token, **kwargs)
    query = "{}/{}/{}".format(MODULES_ENDPOINT,
                              module_info[1], MODULE_VERSIONS_ENDPOINT)
    # Sends the request
    response = send_get_request(endpoint, auth_token, query, {"MaximumVersionsToReturn": number_of_versions})
    status_code = int(response["http_status"])
    if status_code == MODULE_VERSION_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(module_info[0], MODULE_VERSIONS_FILE)
        filename = os.path.join(MODULES_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == MODULE_VERSION_INVALID_CODE:
        raise InvalidParametersError(
            "Invalid request due to invalid max versions to return (less than 0). Details: {}".format(response["response"]))
    elif status_code == MODULE_VERSION_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the versions of that module. Details: {}".format(response["response"]))
    elif status_code == MODULE_VERSION_FAILED_CODE:
        raise AppDoesNotExistError(
            "Failed to retrieve the module. Details: {}".format(response["response"]))
    elif status_code == MODULE_VERSION_FAILED_LIST_CODE:
        raise AppVersionsError(
            "Failed to list the module versions. Details: {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns the details of a given module version.
def get_module_version(artifact_dir: str, endpoint: str, auth_token: str, extra_data: bool, version_id: str, **kwargs):
    # Tuple with (ModuleName, ModuleKey): module_info[0] = ModuleName; module_info[1] = ModuleKey
    module_info = _get_module_info(artifact_dir, endpoint, auth_token, **kwargs)
    query = "{}/{}/{}/{}".format(MODULES_ENDPOINT,
                                 module_info[1], MODULE_VERSIONS_ENDPOINT, version_id)
    # Sends the request
    params = {"IncludeModules": extra_data, "IncludeEnvStatus": extra_data}
    response = send_get_request(endpoint, auth_token, query, params)
    status_code = int(response["http_status"])
    if status_code == MODULE_VERSION_SUCCESS_CODE:
        # Stores the result
        filename = "{}.{}{}".format(module_info[0], version_id, MODULE_VERSION_FILE)
        filename = os.path.join(MODULES_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == MODULE_VERSION_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the versions of that module. Details: {}".format(response["response"]))
    elif status_code == MODULE_VERSION_FAILED_CODE:
        raise AppDoesNotExistError(
            "Failed to retrieve the module. Details: {}".format(response["response"]))
    elif status_code == MODULE_VERSION_FAILED_LIST_CODE:
        raise AppVersionsError(
            "Failed to retrieve the module version. Details: {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# ---------------------- PRIVATE METHODS ----------------------

# Private method to get the Module name or key into a tuple (name,key).
def _get_module_info(artifact_dir: str, api_url: str, auth_token: str, **kwargs):
    if "module_name" in kwargs:
        module_key = _find_module_key(
            artifact_dir, api_url, auth_token, kwargs["app_name"])
        module_name = kwargs["module_name"]
    elif "module_key" in kwargs:
        module_key = kwargs["module_key"]
        module_name = _find_module_name(
            artifact_dir, api_url, auth_token, kwargs["module_key"])
    else:
        raise InvalidParametersError(
            "You need to use either module_name=<name> or module_key=<key> as parameters to call this method.")
    return (module_name, module_key)


# Private method to find a Module key from name
def _find_module_key(artifact_dir: str, api_url: str, auth_token: str, module_name: str):
    module_key = ""
    cached_results = False
    try:
        # Try searching the key on the cache
        modules = load_data(artifact_dir, MODULES_FILE)
        cached_results = True
    except FileNotFoundError:
        # Query the LT API, since there's no cache
        modules = get_modules(
            artifact_dir, api_url, auth_token, False)
    for module in modules:
        if module["Name"] == module_name:
            module_key = module["Key"]
            break
    # If the Module key was not found, determine if it needs to invalidate the cache or the Module does not exist
    # since we explitly clear the cache, and the code is not multithreaded, it should not lead to recursion issues
    # If the cache was not used in the first place, it means the app does not exist
    if module_key == "" and not cached_results:
        raise AppDoesNotExistError(
            "Failed to retrieve the module. Please make sure the module exists in the environment. Module Name: {}".format(module_name))
    # If the cache was used, it needs to be cleared and re-fetched from the LT server
    elif module_key == "" and cached_results:
        clear_cache(artifact_dir, MODULES_FILE)
        return _find_module_key(artifact_dir, api_url, auth_token, module_name)
    return module_key


# Private method to find a Module name from key
def _find_module_name(artifact_dir: str, api_url: str, auth_token: str, module_key: str):
    module_name = ""
    cached_results = False
    try:
        # Try searching the key on the cache
        modules = load_data(artifact_dir, MODULES_FILE)
        cached_results = True
    except FileNotFoundError:
        # Query the LT API, since there's no cache
        modules = get_modules(
            artifact_dir, api_url, auth_token, False)
    for module in modules:
        if module["Key"] == module_key:
            module_name = module["Name"]
            break
    # If the Module name was not found, determine if it needs to invalidate the cache or the application does not exist
    # since we explitly clear the cache, and the code is not multithreaded, it should not lead to recursion issues
    # If the cache was not used in the first place, it means the app does not exist
    if module_name == "" and not cached_results:
        raise AppDoesNotExistError(
            "Failed to retrieve the module. Please make sure the module exists in the environment. Module Key: {}".format(module_key))
    # If the cache was used, it needs to be cleared and re-fetched from the LT server
    elif module_name == "" and cached_results:
        clear_cache(artifact_dir, MODULES_FILE)
        return _find_module_name(artifact_dir, api_url, auth_token, module_key)
    return module_name
