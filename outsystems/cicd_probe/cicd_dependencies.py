# Python Modules
import os
from toposort import toposort_flatten

# Custom Modules
# Functions
from outsystems.cicd_probe.cicd_base import send_probe_get_request
from outsystems.file_helpers.file import store_data
# Variables
from outsystems.vars.cicd_vars import GET_APPLICATION_DEPENDENCIES_ENDPOINT, PROBE_DEPENDENCIES_SUCCESS_CODE
from outsystems.vars.file_vars import PROBE_APPLICATION_DEPENDENCIES_FILE, PROBE_FOLDER


# Get a set of applications which are producers for a specified application version in the target environment.
def get_app_dependencies(artifact_dir: str, probe_endpoint: str, application_version_key: str, application_name: str, application_version: str):

    # Builds the API params
    params = {"ApplicationName": application_name, "ApplicationVersion": application_version}

    #TEST MARTELADA
    probe_endpoint = "https://csdevops11-reg.outsystems.net/CI_CDProbe/rest/v1"

    # Sends the request
    response = send_probe_get_request(
        probe_endpoint, GET_APPLICATION_DEPENDENCIES_ENDPOINT, params)
    status_code = response["http_status"]

    if status_code == PROBE_DEPENDENCIES_SUCCESS_CODE:
       response = response["response"]
       dependencies_list = []
       for dependencie in response:
           dependencies_list.append(dependencie["ApplicationKey"])
       return set(dependencies_list)
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))

#TODO try catch circular cenas
def sort_app_dependencies(dep_list: list):
    deployment_order = []

    deployment_order = toposort_flatten(dep_list)
    return deployment_order[::-1]

