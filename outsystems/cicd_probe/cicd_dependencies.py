# Python Modules
from toposort import toposort_flatten, CircularDependencyError

# Custom Modules
# Functions
from outsystems.cicd_probe.cicd_base import send_probe_get_request
# Variables
from outsystems.vars.cicd_vars import GET_APPLICATION_DEPENDENCIES_ENDPOINT, PROBE_DEPENDENCIES_SUCCESS_CODE


# Get a set of applications which are producers for a specified application version.
def get_app_dependencies(artifact_dir: str, probe_endpoint: str, application_version_key: str, application_name: str, application_version: str):
    # Builds the API params
    params = {"ApplicationName": application_name, "ApplicationVersion": application_version}

    # Sends the request
    response = send_probe_get_request(
        probe_endpoint, GET_APPLICATION_DEPENDENCIES_ENDPOINT, params)
    status_code = response["http_status"]

    if status_code == PROBE_DEPENDENCIES_SUCCESS_CODE:
        response = response["response"]
        dependencies_list = []
        for dependency in response:
            dependencies_list.append(dependency["ApplicationKey"])
        return set(dependencies_list)
    else:
        raise NotImplementedError(
            "There was an error. Response from server: {}".format(response))


# Topological ordering (linear ordering) of a dependency list
def sort_app_dependencies(dep_list: list):
    try:
        return toposort_flatten(dep_list)
    except:
        raise CircularDependencyError(
            "There are circular dependencies among the list of applications.")
