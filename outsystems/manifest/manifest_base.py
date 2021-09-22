# Python Modules

# Custom Modules
# Exceptions
from outsystems.exceptions.environment_not_found import EnvironmentNotFoundError
# Variables
from outsystems.vars.manifest_vars import * 
from outsystems.vars.lifetime_vars import DEPLOYMENT_MESSAGE

# Returns the environment details: tuple(Name, Key)
def get_environment_details(manifest: dict, environment_label: str):
    environment_definition = next(filter(lambda x: x[ENVIRONMENT_LABEL] == environment_label, manifest[MANIFEST_ENVIRONMENT_DEFINITIONS]), None)
    if environment_definition
        return (environment_definition[ENVIRONMENT_NAME], environment_definition[ENVIRONMENT_KEY])
    else:
        raise EnvironmentNotFoundError(
            "Failed to retrieve the environment key from label. Please make sure the label is correct. Environment label: {}".format(environment_label))


# Returns the deployment notes
def get_deployment_notes(manifest: dict):
    if DEPLOYMENT_NOTES in manifest:
        return manifest[DEPLOYMENT_NOTES]
    else:
        return DEPLOYMENT_MESSAGE

