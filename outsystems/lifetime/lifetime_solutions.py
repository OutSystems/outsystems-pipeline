# Python Modules
import json
import os

# Custom Modules
# Exceptions
from outsystems.exceptions.no_deployments import NoDeploymentsError
from outsystems.exceptions.not_enough_permissions import NotEnoughPermissionsError
from outsystems.exceptions.server_error import ServerError
# Functions
from outsystems.lifetime.lifetime_base import send_post_request, send_get_request
from outsystems.file_helpers.file import store_data
# Variables
from outsystems.vars.lifetime_vars import ENVIRONMENTS_ENDPOINT, ENVIRONMENT_SOLUTION_ENDPOINT, ENVIRONMENT_SOLUTION_SUCCESS_CODE, \
    ENVIRONMENT_SOLUTION_STATUS_ENDPOINT, ENVIRONMENT_SOLUTION_STATUS_SUCCESS_CODE, ENVIRONMENT_SOLUTION_STATUS_NOT_STATUS_CODE, ENVIRONMENT_SOLUTION_STATUS_NO_PERMISSION_CODE, \
    ENVIRONMENT_SOLUTION_STATUS_FAILED_CODE, ENVIRONMENT_SOLUTION_LINK_SUCCESS_CODE, ENVIRONMENT_SOLUTION_LINK_FAILED_CODE
from outsystems.vars.file_vars import SOLUTIONS_LINK_FILE, SOLUTIONS_FOLDER  # , SOLUTIONS_STATUS_FILE


# Sends a request to create a solution, on a target environment, for a specific set of app keys.
# Returns a solution key.
def create_solution(artifact_dir: str, endpoint: str, auth_token: str, environment_key: str, solution_name: str, app_keys: list, include_refs: bool):
    # Builds the API call
    query = "{}/{}/{}".format(ENVIRONMENTS_ENDPOINT, environment_key, ENVIRONMENT_SOLUTION_ENDPOINT)

    # Builds the body for the request
    solution_request = _create_solution_request(solution_name, app_keys, include_refs)
    # Sends the request
    response = send_post_request(
        endpoint, auth_token, query, solution_request)
    status_code = int(response["http_status"])
    if status_code == ENVIRONMENT_SOLUTION_SUCCESS_CODE:
        return response["response"]
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns the status of a given solution key
def get_solution_status(artifact_dir: str, endpoint: str, auth_token: str, environment_key: str, solution_key: str):
    # Builds the API call
    query = "{}/{}/{}/{}".format(ENVIRONMENTS_ENDPOINT, environment_key, ENVIRONMENT_SOLUTION_STATUS_ENDPOINT, solution_key)

    # Sends the request
    response = send_get_request(endpoint, auth_token, query, None)
    status_code = int(response["http_status"])
    if status_code == ENVIRONMENT_SOLUTION_STATUS_SUCCESS_CODE:
        # Stores the result
        # filename = "{}{}".format(solution_key, SOLUTIONS_STATUS_FILE)
        # filename = os.path.join(SOLUTIONS_FOLDER, filename)
        # store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == ENVIRONMENT_SOLUTION_STATUS_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the details of that solution. Details: {}".format(response["response"]))
    elif status_code == ENVIRONMENT_SOLUTION_STATUS_NOT_STATUS_CODE:
        raise NoDeploymentsError("There is no solution with the key {}. Details: {}".format(
            solution_key, response["response"]))
    elif status_code == ENVIRONMENT_SOLUTION_STATUS_FAILED_CODE:
        raise ServerError("Failed to get the status of solution with key {}. Details: {}".format(
            solution_key, response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns download link of source code package of the specified application in a given environment.
def get_solution_url(artifact_dir: str, endpoint: str, auth_token: str, environment_key: str, solution_key: str):
    # Builds the API call
    query = "{}/{}/{}/{}".format(ENVIRONMENTS_ENDPOINT, environment_key, ENVIRONMENT_SOLUTION_ENDPOINT, solution_key)

    # Sends the request
    response = send_get_request(endpoint, auth_token, query, None)
    status_code = int(response["http_status"])
    if status_code == ENVIRONMENT_SOLUTION_LINK_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(solution_key, SOLUTIONS_LINK_FILE)
        filename = os.path.join(SOLUTIONS_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]["url"]
    elif status_code == ENVIRONMENT_SOLUTION_LINK_FAILED_CODE:
        raise ServerError("Failed to access the solution package link. Details: {}".format(
            response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# ---------------------- PRIVATE METHODS ----------------------
def _create_solution_request(solution_name: str, app_keys: str, include_refs: bool):

    solution_request = {"SolutionName": solution_name,
                        "ApplicationKeys": app_keys,
                        "IncludeReferences": include_refs}

    return json.dumps(solution_request)
