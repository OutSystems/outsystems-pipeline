# Custom Modules
from outsystems.vars.file_vars import APPLICATION_FOLDER, APPLICATIONS_FILE, APPLICATION_FILE, APPLICATION_VERSIONS_FILE
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION, APPLICATIONS_ENDPOINT, \
  APPLICATION_VERSIONS_ENDPOINT, APPLICATIONS_SUCCESS_CODE, APPLICATIONS_EMPTY_CODE, APPLICATIONS_FLAG_FAILED_CODE, \
  APPLICATIONS_FAILED_CODE, APPLICATION_SUCCESS_CODE, APPLICATION_FLAG_FAILED_CODE, APPLICATION_NO_PERMISSION_CODE, \
  APPLICATION_FAILED_CODE, APPLICATION_VERSION_SUCCESS_CODE, APPLICATION_VERSION_INVALID_CODE, APPLICATION_VERSION_NO_PERMISSION_CODE, \
  APPLICATION_VERSION_FAILED_CODE, APPLICATION_VERSION_FAILED_LIST_CODE
from outsystems.file_helpers.file import store_data, check_file, load_data, clear_cache
from outsystems.lifetime.lifetime_base import build_lt_endpoint, send_get_request
from outsystems.exceptions.app_does_not_exist import AppDoesNotExistError
from outsystems.exceptions.invalid_parameters import InvalidParametersError
from outsystems.exceptions.no_apps_available import NoAppsAvailableError
from outsystems.exceptions.server_error import ServerError
from outsystems.exceptions.not_enough_permissions import NotEnoughPermissionsError
from outsystems.exceptions.environment_not_found import EnvironmentNotFoundError
from outsystems.exceptions.app_varsion_error import AppVersionsError

# Returns a list of applications that exist in the infrastructure.
def get_applications(lt_url :str, auth_token :str, extra_data :bool):
  # Builds the endpoint and params for LT
  endpoint = build_lt_endpoint(lt_url)
  params = {"IncludeModules": extra_data, "IncludeEnvStatus": extra_data}
  # Sends the request
  response = send_get_request(endpoint, auth_token, APPLICATIONS_ENDPOINT, params)
  status_code = int(response["http_status"])
  # Process the response based on the status code returned from the server
  if status_code == APPLICATIONS_SUCCESS_CODE:
    # Stores the result
    store_data(APPLICATIONS_FILE, response["response"])
    return response["response"]
  elif status_code == APPLICATIONS_EMPTY_CODE:
    raise NoAppsAvailableError("No applications available in the infrastructure. Details {}".format(response["response"]))
  elif status_code == APPLICATIONS_FLAG_FAILED_CODE:
    raise InvalidParametersError("There was an error with the 'extra_data' flag or the request was invalid when listing all applications. The params used were: {}. Details: {}".format(params, response["response"]))
  elif status_code == APPLICATIONS_FAILED_CODE:
    raise ServerError("Failed to list the applications. Details {}".format(response["response"]))
  else:
    raise NotImplementedError("There was an error. Response from server: {}".format(response))

# Returns the details of a given application.
def get_application_data(lt_url :str, auth_token :str, extra_data :bool, **kwargs):
  # Tuple with (AppName, AppKey): app_info[0] = AppName; app_info[1] = AppKey
  app_info = _get_application_info(lt_url, auth_token, **kwargs)
  # Builds the endpoint and query for LT
  endpoint = build_lt_endpoint(lt_url)
  query = "{}/{}".format(APPLICATIONS_ENDPOINT, app_info[1])
  params = {"IncludeModules": extra_data, "IncludeEnvStatus": extra_data}
  # Sends the request
  response = send_get_request(endpoint, auth_token, query, params)
  status_code = int(response["http_status"])
  if status_code == APPLICATION_SUCCESS_CODE:
    # Stores the result
    filename = "{}\\{}{}".format(APPLICATION_FOLDER, app_info[0], APPLICATION_FILE)
    store_data(filename, response["response"])
    return response["response"]
  elif status_code == APPLICATION_FLAG_FAILED_CODE:
    raise InvalidParametersError("There was an error with the 'extra_data' flag or the request was invalid when listing the application. The params used were: {}. Details: {}".format(params, response["response"]))
  elif status_code == APPLICATION_NO_PERMISSION_CODE:
    raise NotEnoughPermissionsError("You don't have enough permissions to see the details of that application. Details: {}".format(response["response"]))
  elif status_code == APPLICATION_FAILED_CODE:
    raise EnvironmentNotFoundError("Failed getting running applications because one of the environments was not found. Details: {}".format(response["response"]))
  else:
    raise NotImplementedError("There was an error. Response from server: {}".format(response))

# Returns a list of versions of a given application.
def get_application_versions(lt_url :str, auth_token :str, number_of_versions :int, **kwargs):
  # Tuple with (AppName, AppKey): app_info[0] = AppName; app_info[1] = AppKey
  app_info = _get_application_info(lt_url, auth_token, **kwargs)
  # Builds the endpoint and query for LT
  endpoint = build_lt_endpoint(lt_url)
  query = "{}/{}/{}".format(APPLICATIONS_ENDPOINT, app_info[1], APPLICATION_VERSIONS_ENDPOINT)
  # Sends the request
  response = send_get_request(endpoint, auth_token,query,{"MaximumVersionsToReturn": number_of_versions})
  status_code = int(response["http_status"])
  if status_code == APPLICATION_VERSION_SUCCESS_CODE:
    # Stores the result
    filename = "{}\\{}{}".format(APPLICATION_FOLDER, app_info[0], APPLICATION_VERSIONS_FILE)
    store_data(filename, response["response"])
    return response["response"]
  elif status_code == APPLICATION_VERSION_INVALID_CODE:
    raise InvalidParametersError("Invalid request due to invalid max versions to return (less than 0). Details: {}".format(response["response"]))
  elif status_code == APPLICATION_VERSION_NO_PERMISSION_CODE:
    raise NotEnoughPermissionsError("You don't have enough permissions to see the versions of that application. Details: {}".format(response["response"]))
  elif status_code == APPLICATION_VERSION_FAILED_CODE:
    raise AppDoesNotExistError("Failed to retrieve the application. Details: {}".format(response["response"]))
  elif status_code == APPLICATION_VERSION_FAILED_LIST_CODE:
    raise AppVersionsError("Failed to list the application versions. Details: {}".format(response["response"]))
  else:
    raise NotImplementedError("There was an error. Response from server: {}".format(response))

########################################## PRIVATE METHODS ##########################################
# Private method to get the App name or key into a tuple (name,key). 
def _get_application_info(api_url :str, auth_token :str, **kwargs):
  if "app_name" in kwargs:
    app_key = _find_application_key(api_url, auth_token, kwargs["app_name"])
    app_name = kwargs["app_name"]
  elif "app_key" in kwargs:  
    app_key = kwargs["app_key"]
    app_name = _find_application_name(api_url, auth_token, kwargs["app_key"])
  else:
    raise InvalidParametersError("You need to use either app_name=<name> or app_key=<key> as parameters to call this method.")
  return (app_name, app_key)
    
# Private method to find an application key from name
def _find_application_key(api_url :str, auth_token :str, application_name: str):
  app_key = ""
  cached_results = False
  try:
    # Try searching the key on the cache
    applications = load_data(APPLICATIONS_FILE)
    cached_results = True
  except FileNotFoundError:
    # Query the LT API, since there's no cache
    applications = get_applications(api_url, auth_token, False)
  for app in applications:
    if app["Name"] == application_name:
      app_key = app["Key"]
      break
  # If the app key was not found, determine if it needs to invalidate the cache or the application does not exist
  # since we explitly clear the cache, and the code is not multithreaded, it should not lead to recursion issues
  if app_key == "" and not cached_results: # If the cache was not used in the first place, it means the app does not exist
    raise AppDoesNotExistError("Failed to retrieve the application. Please make sure the app exists in the environment. App Name: {}".format(application_name))
  elif app_key == "" and cached_results: # If the cache was used, it needs to be cleared and re-fetched from the LT server
    clear_cache(APPLICATIONS_FILE)
    return _find_application_key(api_url, auth_token, application_name)
  return app_key

# Private method to find an application name from key
def _find_application_name(api_url :str, auth_token :str, application_key :str):
  app_name = ""
  cached_results = False
  try:
    # Try searching the key on the cache
    applications = load_data(APPLICATIONS_FILE)
    cached_results = True
  except FileNotFoundError:
    # Query the LT API, since there's no cache
    applications = get_applications(api_url, auth_token, False)
  for app in applications:
    if app["Key"] == application_key:
      app_name = app["Name"]
      break
  # If the app name  was not found, determine if it needs to invalidate the cache or the application does not exist
  # since we explitly clear the cache, and the code is not multithreaded, it should not lead to recursion issues
  if app_name == "" and not cached_results: # If the cache was not used in the first place, it means the app does not exist
    raise AppDoesNotExistError("Failed to retrieve the application. Please make sure the app exists in the environment. App Key: {}".format(application_key))
  elif app_name == "" and cached_results: # If the cache was used, it needs to be cleared and re-fetched from the LT server
    clear_cache(APPLICATIONS_FILE)
    return _find_application_name(api_url, auth_token, application_key)
  return app_name