# Python Modules
import os

# Custom Modules
# Exceptions
from outsystems.exceptions.invalid_parameters import InvalidParametersError
from outsystems.exceptions.environment_not_found import EnvironmentNotFoundError
from outsystems.exceptions.not_enough_permissions import NotEnoughPermissionsError
from outsystems.exceptions.app_does_not_exist import AppDoesNotExistError
from outsystems.exceptions.server_error import ServerError
# Functions
from outsystems.lifetime.lifetime_base import send_get_request
from outsystems.lifetime.lifetime_applications import _get_application_info
from outsystems.file_helpers.file import load_data, store_data, clear_cache
# Variables
from outsystems.vars.lifetime_vars import ENVIRONMENTS_ENDPOINT, ENVIRONMENT_APPLICATIONS_ENDPOINT, ENVIRONMENTS_SUCCESS_CODE, \
    ENVIRONMENTS_NOT_FOUND_CODE, ENVIRONMENTS_FAILED_CODE, ENVIRONMENT_APP_SUCCESS_CODE, ENVIRONMENT_APP_NOT_STATUS_CODE, \
    ENVIRONMENT_APP_NO_PERMISSION_CODE, ENVIRONMENT_APP_NOT_FOUND, ENVIRONMENT_APP_FAILED_CODE
from outsystems.vars.file_vars import ENVIRONMENTS_FILE, ENVIRONMENT_FOLDER, ENVIRONMENT_APPLICATION_FILE

# Lists all the environments in the infrastructure.
def get_environments(artifact_dir: str, endpoint: str, auth_token: str):
    # Sends the request
    response = send_get_request(
        endpoint, auth_token, ENVIRONMENTS_ENDPOINT, None)
    status_code = int(response["http_status"])
    if status_code == ENVIRONMENTS_SUCCESS_CODE:
        # Stores the result
        store_data(artifact_dir, ENVIRONMENTS_FILE, response["response"])
        return response["response"]
    elif status_code == ENVIRONMENTS_NOT_FOUND_CODE:
        raise EnvironmentNotFoundError(
            "No environments found. Details {}".format(response["response"]))
    elif status_code == ENVIRONMENTS_FAILED_CODE:
        raise ServerError(
            "Failed to list the environments. Details: {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))

# Returns the environment key.
def get_environment_key(artifact_dir: str, endpoint: str, auth_token: str, environment_name: str):
    return _find_environment_key(artifact_dir, endpoint, auth_token, environment_name)

# Returns information about the running version of the specified application in a given environment.
def get_environment_app_version(artifact_dir: str, endpoint: str, auth_token: str, extra_data: bool, **kwargs):
    # Tuple with (AppName, AppKey): app_tuple[0] = AppName; app_tuple[1] = AppKey
    app_tuple = _get_application_info(
        artifact_dir, endpoint, auth_token, **kwargs)
    # Tuple with (EnvName, EnvKey): env_tuple[0] = EnvName; env_tuple[1] = EnvKey
    env_tuple = _get_environment_info(
        artifact_dir, endpoint, auth_token, **kwargs)
    # Builds the query and arguments for the call to the API
    query = "{}/{}/{}/{}".format(ENVIRONMENTS_ENDPOINT,
                                 env_tuple[1], ENVIRONMENT_APPLICATIONS_ENDPOINT, app_tuple[1])
    arguments = {"IncludeEnvStatus": extra_data, "IncludeModules": extra_data}
    # Sends the request
    response = send_get_request(endpoint, auth_token, query, arguments)
    status_code = int(response["http_status"])
    if status_code == ENVIRONMENT_APP_SUCCESS_CODE:
        # Stores the result
        filename = "{}.{}{}".format(
            env_tuple[0], app_tuple[0], ENVIRONMENT_APPLICATION_FILE)
        filename = os.path.join(ENVIRONMENT_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == ENVIRONMENT_APP_NOT_STATUS_CODE:
        raise InvalidParametersError("Error in the request parameters. Params: {}. Details {}".format(
            arguments, response["response"]))
    elif status_code == ENVIRONMENT_APP_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the application in that environment. Details: {}".format(response["response"]))
    elif status_code == ENVIRONMENT_APP_NOT_FOUND:
        raise AppDoesNotExistError(
            "The application does not exist in the environment. Details: {}".format(response["response"]))
    elif status_code == ENVIRONMENT_APP_FAILED_CODE:
        raise ServerError("Failed to access the running version of an application. Details: {}".format(
            response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))

########################################## PRIVATE METHODS ##########################################
# Private method to get the App name or key into a tuple (name,key).
def _get_environment_info(artifact_dir: str, api_url: str, auth_token: str, **kwargs):
    if "env_name" in kwargs:
        env_key = _find_environment_key(
            artifact_dir, api_url, auth_token, kwargs["env_name"])
        env_name = kwargs["env_name"]
    elif "env_key" in kwargs:
        env_key = kwargs["env_key"]
        env_name = _find_environment_name(
            artifact_dir, api_url, auth_token, kwargs["env_key"])
    else:
        raise InvalidParametersError(
            "You need to use either env_name=<name> or env_key=<key> as parameters to call this method.")
    return (env_name, env_key)

# Private method to find an environment key from name
def _find_environment_key(artifact_dir: str, api_url: str, auth_token: str, environment_name: str):
    env_key = ""
    cached_results = False
    try:
        # Try searching the key on the cache
        environments = load_data(artifact_dir, ENVIRONMENTS_FILE)
        cached_results = True
    except:
        # Query the LT API, since there's no cache
        environments = get_environments(artifact_dir, api_url, auth_token)
    for env in environments:
        if env["Name"] == environment_name:
            env_key = env["Key"]
            break
    # If the env key  was not found, determine if it needs to invalidate the cache or the application does not exist
    # since we explitly clear the cache, and the code is not multithreaded, it should not lead to recursion issues
    # If the cache was not used in the first place, it means the app does not exist
    if env_key == "" and not cached_results:
        raise EnvironmentNotFoundError(
            "Failed to retrieve the environment. Please make sure the environment exists. Environment name: {}".format(environment_name))
    # If the cache was used, it needs to be cleared and re-fetched from the LT server
    elif env_key == "" and cached_results:
        clear_cache(artifact_dir, ENVIRONMENTS_FILE)
        return _find_environment_key(artifact_dir, api_url, auth_token, environment_name)
    return env_key

# Private method to find an environment name from key
def _find_environment_name(artifact_dir: str, api_url: str, auth_token: str, environment_key: str):
    env_name = ""
    cached_results = False
    try:
        # Try searching the key on the cache
        environments = load_data(artifact_dir, ENVIRONMENTS_FILE)
        cached_results = True
    except:
        # Query the LT API, since there's no cache
        environments = get_environments(artifact_dir, api_url, auth_token)
    for env in environments:
        if env["Key"] == environment_key:
            env_name = env["Name"]
            break
    # If the env key  was not found, determine if it needs to invalidate the cache or the application does not exist
    # since we explitly clear the cache, and the code is not multithreaded, it should not lead to recursion issues
    # If the cache was not used in the first place, it means the app does not exist
    if env_name == "" and not cached_results:
        raise EnvironmentNotFoundError(
            "Failed to retrieve the environment. Please make sure the environment exists. Environment key: {}".format(environment_key))
    # If the cache was used, it needs to be cleared and re-fetched from the LT server
    elif env_name == "" and cached_results:
        clear_cache(artifact_dir, ENVIRONMENTS_FILE)
        return _find_environment_name(artifact_dir, api_url, auth_token, environment_key)
    return env_name

def _find_environment_url(artifact_dir: str, api_url: str, auth_token: str, environment_name: str):
    env_url = ""
    cached_results = False
    try:
        # Try searching the key on the cache
        environments = load_data(artifact_dir, ENVIRONMENTS_FILE)
        cached_results = True
    except:
        # Query the LT API, since there's no cache
        environments = get_environments(artifact_dir, api_url, auth_token)
    for env in environments:
        if env["Name"] == environment_name:
            env_url = env["HostName"]
    # If the env key  was not found, determine if it needs to invalidate the cache or the application does not exist
    # since we explitly clear the cache, and the code is not multithreaded, it should not lead to recursion issues
    # If the cache was not used in the first place, it means the app does not exist
    if env_url == "" and not cached_results:
        raise EnvironmentNotFoundError(
            "Failed to retrieve the environment. Please make sure the environment exists. Environment name: {}".format(environment_name))
    # If the cache was used, it needs to be cleared and re-fetched from the LT server
    elif env_url == "" and cached_results:
        clear_cache(artifact_dir, ENVIRONMENTS_FILE)
        return _find_environment_url(artifact_dir, api_url, auth_token, environment_name)
    return env_url