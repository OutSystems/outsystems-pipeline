# Python Modules

# Custom Modules
# Exceptions
from outsystems.exceptions.environment_not_found import EnvironmentNotFoundError
# Variables
from outsystems.vars.manifest_vars import MANIFEST_ENVIRONMENT_KEY, MANIFEST_ENVIRONMENT_NAME, MANIFEST_ENVIRONMENT_LABEL, \
    MANIFEST_ENVIRONMENT_DEFINITIONS, MANIFEST_CONFIGURATION_ITEMS, MANIFEST_CONFIG_ITEM_VALUES, MANIFEST_MODULE_KEY, MANIFEST_MODULE_NAME, \
    MANIFEST_CONFIG_ITEM_KEY, MANIFEST_CONFIG_ITEM_NAME, MANIFEST_CONFIG_ITEM_TYPE, MANIFEST_CONFIG_ITEM_TARGET_VALUE, MANIFEST_DEPLOYMENT_NOTES
from outsystems.vars.lifetime_vars import DEPLOYMENT_MESSAGE


# Returns the environment details: tuple(Name, Key)
def get_environment_details(manifest: dict, environment_label: str):
    environment_definition = next(filter(lambda x: x[MANIFEST_ENVIRONMENT_LABEL] == environment_label, manifest[MANIFEST_ENVIRONMENT_DEFINITIONS]), None)
    if environment_definition:
        return (environment_definition[MANIFEST_ENVIRONMENT_NAME], environment_definition[MANIFEST_ENVIRONMENT_KEY])
    else:
        raise EnvironmentNotFoundError(
            "Failed to retrieve the environment key from label. Please make sure the label is correct. Environment label: {}".format(environment_label))


# Returns the configuration items for the target environment key
def get_configuration_items_for_environment(manifest: dict, target_env_key: str):
    config_items = []
    if MANIFEST_CONFIGURATION_ITEMS in manifest:
        for cfg_item in manifest[MANIFEST_CONFIGURATION_ITEMS]:
            target_value = next(filter(lambda x: x[MANIFEST_ENVIRONMENT_KEY] == target_env_key, cfg_item[MANIFEST_CONFIG_ITEM_VALUES]), None)
            if target_value:
                # Add it to the config items list
                config_items.append({
                    MANIFEST_MODULE_KEY: cfg_item[MANIFEST_MODULE_KEY],
                    MANIFEST_MODULE_NAME: cfg_item[MANIFEST_MODULE_NAME],
                    MANIFEST_CONFIG_ITEM_KEY: cfg_item[MANIFEST_CONFIG_ITEM_KEY],
                    MANIFEST_CONFIG_ITEM_NAME: cfg_item[MANIFEST_CONFIG_ITEM_NAME],
                    MANIFEST_CONFIG_ITEM_TYPE: cfg_item[MANIFEST_CONFIG_ITEM_TYPE],
                    MANIFEST_CONFIG_ITEM_TARGET_VALUE: target_value[MANIFEST_CONFIG_ITEM_TARGET_VALUE],
                    MANIFEST_ENVIRONMENT_NAME: target_value[MANIFEST_ENVIRONMENT_NAME]
                })

    return config_items


# Returns the deployment notes
def get_deployment_notes(manifest: dict):
    if MANIFEST_DEPLOYMENT_NOTES in manifest:
        return manifest[MANIFEST_DEPLOYMENT_NOTES]
    else:
        return DEPLOYMENT_MESSAGE
