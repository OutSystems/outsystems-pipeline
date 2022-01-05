# Python Modules
import json
import os
import datetime

# Custom Modules
# Exceptions
from outsystems.exceptions.no_deployments import NoDeploymentsError
from outsystems.exceptions.invalid_parameters import InvalidParametersError
from outsystems.exceptions.not_enough_permissions import NotEnoughPermissionsError
from outsystems.exceptions.server_error import ServerError
from outsystems.exceptions.environment_not_found import EnvironmentNotFoundError
from outsystems.exceptions.impossible_action_deployment import ImpossibleApplyActionDeploymentError
# Functions
from outsystems.lifetime.lifetime_base import send_get_request, send_post_request, send_delete_request
from outsystems.lifetime.lifetime_environments import get_environment_key
from outsystems.file_helpers.file import store_data
# Variables
from outsystems.vars.lifetime_vars import DEPLOYMENTS_ENDPOINT, DEPLOYMENT_STATUS_ENDPOINT, \
    DEPLOYMENT_START_ENDPOINT, DEPLOYMENT_CONTINUE_ENDPOINT, DEPLOYMENTS_SUCCESS_CODE, DEPLOYMENTS_EMPTY_CODE, \
    DEPLOYMENTS_INVALID_CODE, DEPLOYMENTS_NO_PERMISSION_CODE, DEPLOYMENTS_FAILED_CODE, DEPLOYMENT_GET_SUCCESS_CODE, \
    DEPLOYMENT_GET_NO_PERMISSION_CODE, DEPLOYMENT_GET_NO_DEPLOYMENT_CODE, DEPLOYMENT_GET_FAILED_CODE, \
    DEPLOYMENT_STATUS_SUCCESS_CODE, DEPLOYMENT_STATUS_NO_PERMISSION_CODE, DEPLOYMENT_STATUS_NO_DEPLOYMENT_CODE, DEPLOYMENT_STATUS_FAILED_CODE, \
    DEPLOYMENT_SUCCESS_CODE, DEPLOYMENT_INVALID_CODE, DEPLOYMENT_NO_PERMISSION_CODE, DEPLOYMENT_NO_ENVIRONMENT_CODE, DEPLOYMENT_FAILED_CODE, \
    DEPLOYMENT_DELETE_SUCCESS_CODE, DEPLOYMENT_DELETE_IMPOSSIBLE_CODE, DEPLOYMENT_DELETE_NO_PERMISSION_CODE, DEPLOYMENT_DELETE_NO_DEPLOYMENT_CODE, \
    DEPLOYMENT_DELETE_FAILED_CODE, DEPLOYMENT_ACTION_SUCCESS_CODE, DEPLOYMENT_ACTION_IMPOSSIBLE_CODE, DEPLOYMENT_ACTION_NO_PERMISSION_CODE, \
    DEPLOYMENT_ACTION_NO_DEPLOYMENT_CODE, DEPLOYMENT_ACTION_FAILED_CODE, DEPLOYMENT_PLAN_V1_API_OPS, DEPLOYMENT_PLAN_V2_API_OPS
from outsystems.vars.file_vars import DEPLOYMENTS_FILE, DEPLOYMENT_FILE, DEPLOYMENT_FOLDER, DEPLOYMENT_STATUS_FILE
from outsystems.vars.pipeline_vars import DEPLOYMENT_STATUS_LIST, DEPLOYMENT_SAVED_STATUS


# Returns a list of deployments ordered by creation date, from newest to oldest.
def get_deployments(artifact_dir: str, endpoint: str, auth_token: str, date: str):
    # Builds the parameters for the api call
    params = {"MinDate": date}
    # Sends the request
    response = send_get_request(
        endpoint, auth_token, DEPLOYMENTS_ENDPOINT, params)
    status_code = int(response["http_status"])
    if status_code == DEPLOYMENTS_SUCCESS_CODE:
        # Stores the result
        store_data(artifact_dir, DEPLOYMENTS_FILE, response["response"])
        return response["response"]
    elif status_code == DEPLOYMENTS_EMPTY_CODE:
        raise NoDeploymentsError("There are no deployments starting on {} until now. Details: {}".format(
            date, response["response"]))
    elif status_code == DEPLOYMENTS_INVALID_CODE:
        raise InvalidParametersError("Invalid request starting on {} until now. Parameters: {}. Details: {}".format(
            date, params, response["response"]))
    elif status_code == DEPLOYMENTS_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the deployment list. Details: {}".format(response["response"]))
    elif status_code == DEPLOYMENTS_FAILED_CODE:
        raise ServerError(
            "Failed to list the deployments. Details {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns the details of a given deployment, validating if there are any conflicts.
# The returned information contains the applications included in the deployment plan and
# the possible conflicts that can arise from the deployment of the selected applications.
def get_deployment_info(artifact_dir: str, endpoint: str, auth_token: str, deployment_key: str):
    # Builds the API call
    query = "{}/{}".format(DEPLOYMENTS_ENDPOINT, deployment_key)
    # Sends the request
    response = send_get_request(endpoint, auth_token, query, None)
    status_code = int(response["http_status"])
    if status_code == DEPLOYMENT_GET_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(deployment_key, DEPLOYMENT_FILE)
        filename = os.path.join(DEPLOYMENT_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == DEPLOYMENT_GET_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the details of that deployment. Details: {}".format(response["response"]))
    elif status_code == DEPLOYMENT_GET_NO_DEPLOYMENT_CODE:
        raise NoDeploymentsError("There are no deployments with the key {}. Details: {}".format(
            deployment_key, response["response"]))
    elif status_code == DEPLOYMENT_GET_FAILED_CODE:
        raise ServerError("Failed to access the details of deployment with key {}. Details: {}".format(
            deployment_key, response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns the details of a given deployment execution, including the deployment status and messages.
def get_deployment_status(artifact_dir: str, endpoint: str, auth_token: str, deployment_key: str):
    # Builds the API call
    query = "{}/{}/{}".format(DEPLOYMENTS_ENDPOINT,
                              deployment_key, DEPLOYMENT_STATUS_ENDPOINT)
    # Sends the request
    response = send_get_request(endpoint, auth_token, query, None)
    status_code = int(response["http_status"])
    if status_code == DEPLOYMENT_STATUS_SUCCESS_CODE:
        # Stores the result
        filename = "{}{}".format(deployment_key, DEPLOYMENT_STATUS_FILE)
        filename = os.path.join(DEPLOYMENT_FOLDER, filename)
        store_data(artifact_dir, filename, response["response"])
        return response["response"]
    elif status_code == DEPLOYMENT_STATUS_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to see the details of that deployment. Details: {}".format(response["response"]))
    elif status_code == DEPLOYMENT_STATUS_NO_DEPLOYMENT_CODE:
        raise NoDeploymentsError("There are no deployments with the key {}. Details: {}".format(
            deployment_key, response["response"]))
    elif status_code == DEPLOYMENT_STATUS_FAILED_CODE:
        raise ServerError("Failed to get the status of deployment with key {}. Details: {}".format(
            deployment_key, response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Returns the details of the running deployment plan to a specific target environment or empty if nothing is running
def get_running_deployment(artifact_dir: str, endpoint: str, auth_token: str, dest_env_key: str):
    # List of running deployments
    running_deployments = []
    # Date 24h prior to now
    date = datetime.datetime.now() - datetime.timedelta(days=1)
    date = date.date()
    try:
        latest_deployments = get_deployments(artifact_dir, endpoint, auth_token, date)
        for deplyoment in latest_deployments:
            if deplyoment["TargetEnvironmentKey"] == dest_env_key:
                deployment_status = get_deployment_status(artifact_dir, endpoint, auth_token, deplyoment["Key"])
                if deployment_status["DeploymentStatus"] in DEPLOYMENT_STATUS_LIST:
                    running_deployments.append(deplyoment)

        return running_deployments

    except NoDeploymentsError:
        # If there are no deployments, return empty
        return running_deployments
    except:
        # Legit exception that needs to be handle -> bubble up
        raise


# Returns the details of the saved deployment plan to a specific target environment or None if nothing is found
def get_saved_deployment(artifact_dir: str, endpoint: str, auth_token: str, dest_env_key: str):
    # Date 24h prior to now
    date = datetime.datetime.now() - datetime.timedelta(days=1)
    date = date.date()
    try:
        latest_deployments = get_deployments(artifact_dir, endpoint, auth_token, date)
        for deployment in latest_deployments:
            if deployment["TargetEnvironmentKey"] == dest_env_key:
                deployment_status = get_deployment_status(artifact_dir, endpoint, auth_token, deployment["Key"])
                if deployment_status["DeploymentStatus"] in DEPLOYMENT_SAVED_STATUS:
                    return deployment

        return None

    except NoDeploymentsError:
        # If there are no deployments, return empty
        return None
    except:
        # Legit exception that needs to be handle -> bubble up
        raise


# Creates a deployment to a target environment.
# An optional list of applications to include in the deployment can be specified.
# The input is a subset of deployment object.
def send_deployment(artifact_dir: str, endpoint: str, auth_token: str, lt_api_version: int, app_keys: list, dep_note: str, source_env: str, dest_env: str):
    # builds the deployment plan
    deployment_request = _create_deployment_plan(
        artifact_dir, endpoint, lt_api_version, auth_token, app_keys, dep_note, source_env, dest_env)
    # Sends the request
    response = send_post_request(
        endpoint, auth_token, DEPLOYMENTS_ENDPOINT, deployment_request)
    status_code = int(response["http_status"])
    if status_code == DEPLOYMENT_SUCCESS_CODE:
        return response["response"]
    elif status_code == DEPLOYMENT_INVALID_CODE:
        raise InvalidParametersError("The request is invalid. Check the body of the request for errors. Body: {}. Details: {}.".format(
            deployment_request, response["response"]))
    elif status_code == DEPLOYMENT_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to create the deployment. Details: {}".format(response["response"]))
    elif status_code == DEPLOYMENT_NO_ENVIRONMENT_CODE:
        raise EnvironmentNotFoundError(
            "Can't find the source or target environment. Details: {}.".format(response["response"]))
    elif status_code == DEPLOYMENT_FAILED_CODE:
        raise ServerError(
            "Failed to create the deployment. Details: {}".format(response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Discards a deployment, if possible. Only deployments whose state is “saved” can be deleted.
def delete_deployment(endpoint: str, auth_token: str, deployment_key: str):
    # Builds the API call
    query = "{}/{}".format(DEPLOYMENTS_ENDPOINT, deployment_key)
    # Sends the request
    response = send_delete_request(endpoint, auth_token, query)
    status_code = int(response["http_status"])
    if status_code == DEPLOYMENT_DELETE_SUCCESS_CODE:
        return response["response"]
    elif status_code == DEPLOYMENT_DELETE_IMPOSSIBLE_CODE:
        raise ImpossibleApplyActionDeploymentError(
            "You can't delete the deployment with key {}. Try aborting the deployment first. Details: {}".format(deployment_key, response["response"]))
    elif status_code == DEPLOYMENT_DELETE_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to delete the deployment. Details: {}".format(response["response"]))
    elif status_code == DEPLOYMENT_DELETE_NO_DEPLOYMENT_CODE:
        raise NoDeploymentsError("There are no deployments with the key {}. Details: {}".format(
            deployment_key, response["response"]))
    elif status_code == DEPLOYMENT_DELETE_FAILED_CODE:
        raise ServerError("Failed to delete the deployment with key {}. Details: {}".format(
            deployment_key, response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Executes the start command in a specified deployment.
# The initiation of a deployment plan will check if it's valid.
# The applications to redeploy, if applicable, will also be included in the deployment plan.
def start_deployment(endpoint: str, auth_token: str, deployment_key: str, **kwargs):
    redeploy = False
    if "redeploy_outdated" not in kwargs:
        redeploy = True
    # Builds the API call
    query = "{}/{}/{}".format(DEPLOYMENTS_ENDPOINT,
                              deployment_key, DEPLOYMENT_START_ENDPOINT)
    # If the parameter to redeploy outdated has a value, that must be included in the call
    if not redeploy:
        query = "{}?RedeployOutdated={}".format(
            query, kwargs["redeploy_outdated"])
    # Sends the request
    response = send_post_request(endpoint, auth_token, query, None)
    status_code = int(response["http_status"])
    if status_code == DEPLOYMENT_ACTION_SUCCESS_CODE:
        return response["response"]
    elif status_code == DEPLOYMENT_ACTION_IMPOSSIBLE_CODE:
        raise ImpossibleApplyActionDeploymentError(
            "You can't start the deployment with key {}. Details: {}".format(deployment_key, response["response"]))
    elif status_code == DEPLOYMENT_ACTION_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to start the deployment. Details: {}".format(response["response"]))
    elif status_code == DEPLOYMENT_ACTION_NO_DEPLOYMENT_CODE:
        raise NoDeploymentsError("There are no deployments with the key {}. Details: {}".format(
            deployment_key, response["response"]))
    elif status_code == DEPLOYMENT_ACTION_FAILED_CODE:
        raise ServerError("Failed to start the deployment with key {}. Details: {}".format(
            deployment_key, response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Executes the continue command in a specified deployment.
def continue_deployment(endpoint: str, auth_token: str, deployment_key: str):
    # Builds the API call
    query = "{}/{}/{}".format(DEPLOYMENTS_ENDPOINT,
                              deployment_key, DEPLOYMENT_CONTINUE_ENDPOINT)
    # Sends the request
    response = send_post_request(endpoint, auth_token, query, None)
    status_code = int(response["http_status"])
    if status_code == DEPLOYMENT_ACTION_SUCCESS_CODE:
        return response["response"]
    elif status_code == DEPLOYMENT_ACTION_IMPOSSIBLE_CODE:
        raise ImpossibleApplyActionDeploymentError(
            "You can't continue the deployment with key {}. Details: {}".format(deployment_key, response["response"]))
    elif status_code == DEPLOYMENT_ACTION_NO_PERMISSION_CODE:
        raise NotEnoughPermissionsError(
            "You don't have enough permissions to continue the deployment. Details: {}".format(response["response"]))
    elif status_code == DEPLOYMENT_ACTION_NO_DEPLOYMENT_CODE:
        raise NoDeploymentsError("There are no deployments with the key {}. Details: {}".format(
            deployment_key, response["response"]))
    elif status_code == DEPLOYMENT_ACTION_FAILED_CODE:
        raise ServerError("Failed to continue the deployment with key {}. Details: {}".format(
            deployment_key, response["response"]))
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# ---------------------- PRIVATE METHODS ----------------------
def _create_deployment_plan(artifact_dir: str, endpoint: str, lt_api_version: int, auth_token: str, app_keys: str, dep_note: str, source_env: str, dest_env: str):
    if lt_api_version == 1:
        api_var_name = DEPLOYMENT_PLAN_V1_API_OPS
    elif lt_api_version == 2:
        api_var_name = DEPLOYMENT_PLAN_V2_API_OPS
    else:
        raise NotImplementedError(
            "Unsupported API version for LifeTime: used {}".format(lt_api_version))
    source_env_key = get_environment_key(
        artifact_dir, endpoint, auth_token, source_env)
    dest_env_key = get_environment_key(
        artifact_dir, endpoint, auth_token, dest_env)
    deployment_request = {api_var_name: app_keys, "Notes": dep_note,
                          "SourceEnvironmentKey": source_env_key, "TargetEnvironmentKey": dest_env_key}
    return json.dumps(deployment_request)
