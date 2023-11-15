# Python Modules
import sys
import os
import argparse
import json

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
# Variables
from outsystems.vars.manifest_vars import MANIFEST_CONFIG_ITEM_TYPE, MANIFEST_MODULE_KEY, MANIFEST_CONFIG_ITEM_KEY, \
    MANIFEST_CONFIG_ITEM_TARGET_VALUE, MANIFEST_CONFIG_ITEM_NAME
from outsystems.vars.properties_vars import PROPERTY_TYPE_SITE_PROPERTY, PROPERTY_TYPE_REST_ENDPOINT, PROPERTY_TYPE_SOAP_ENDPOINT, \
    PROPERTY_TYPE_TIMER_SCHEDULE
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO
from outsystems.vars.file_vars import ARTIFACT_FOLDER
# Functions
from outsystems.file_helpers.file import load_data
from outsystems.manifest.manifest_base import get_configuration_items_for_environment
from outsystems.manifest.manifest_base import get_environment_details
from outsystems.properties.properties_set_value import set_site_property_value, set_rest_endpoint_url, set_soap_endpoint_url, \
    set_timer_schedule
from outsystems.vars.vars_base import load_configuration_file
# Exceptions
from outsystems.exceptions.manifest_does_not_exist import ManifestDoesNotExistError


# Function to apply configuration values to a target environment
def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_token: str, target_env_label: str, trigger_manifest: dict):

    # Tuple with (EnvName, EnvKey): target_env_tuple[0] = EnvName; target_env_tuple[1] = EnvKey
    target_env_tuple = get_environment_details(trigger_manifest, target_env_label)

    # Get configuration items defined in the manifest for target environment
    config_items = get_configuration_items_for_environment(trigger_manifest, target_env_tuple[1])

    # Check if there are any configuration item values to apply for target environment
    if len(config_items) == 0:
        print("No configuration item values were found in the manifest for {} (Label: {}).".format(target_env_tuple[0], target_env_label), flush=True)
    else:
        print("Applying new values to configuration items in {} (Label: {})...".format(target_env_tuple[0], target_env_label), flush=True)

    # Apply target value for each configuration item according to its type
    for cfg_item in config_items:
        result = {}
        if cfg_item[MANIFEST_CONFIG_ITEM_TYPE] == PROPERTY_TYPE_SITE_PROPERTY:
            result = set_site_property_value(
                lt_url, lt_token, cfg_item[MANIFEST_MODULE_KEY], target_env_tuple[1], cfg_item[MANIFEST_CONFIG_ITEM_KEY], cfg_item[MANIFEST_CONFIG_ITEM_TARGET_VALUE])
        elif cfg_item[MANIFEST_CONFIG_ITEM_TYPE] == PROPERTY_TYPE_REST_ENDPOINT:
            result = set_rest_endpoint_url(
                lt_url, lt_token, cfg_item[MANIFEST_MODULE_KEY], target_env_tuple[1], cfg_item[MANIFEST_CONFIG_ITEM_KEY], cfg_item[MANIFEST_CONFIG_ITEM_TARGET_VALUE])
        elif cfg_item[MANIFEST_CONFIG_ITEM_TYPE] == PROPERTY_TYPE_SOAP_ENDPOINT:
            result = set_soap_endpoint_url(
                lt_url, lt_token, cfg_item[MANIFEST_MODULE_KEY], target_env_tuple[1], cfg_item[MANIFEST_CONFIG_ITEM_KEY], cfg_item[MANIFEST_CONFIG_ITEM_TARGET_VALUE])
        elif cfg_item[MANIFEST_CONFIG_ITEM_TYPE] == PROPERTY_TYPE_TIMER_SCHEDULE:
            result = set_timer_schedule(
                lt_url, lt_token, cfg_item[MANIFEST_MODULE_KEY], target_env_tuple[1], cfg_item[MANIFEST_CONFIG_ITEM_KEY], cfg_item[MANIFEST_CONFIG_ITEM_TARGET_VALUE])
        else:
            raise NotImplementedError("Configuration item type '{}' not supported.".format(cfg_item[MANIFEST_CONFIG_ITEM_TYPE]))

        # Check returned result after setting configuration item value
        if "Success" in result and result["Success"]:
            print("New value successfully applied to configuration item '{}' ({}).".format(cfg_item[MANIFEST_CONFIG_ITEM_NAME], cfg_item[MANIFEST_CONFIG_ITEM_TYPE]), flush=True)
        else:
            print("Unable to apply new value to configuration item '{}' ({}).\nReason: {}".format(cfg_item[MANIFEST_CONFIG_ITEM_NAME], cfg_item[MANIFEST_CONFIG_ITEM_TYPE], result["Message"]), flush=True)

    # Exit the script to continue with the pipeline
    sys.exit(0)


# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="(Optional) Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-u", "--lt_url", type=str, required=True,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
    parser.add_argument("-t", "--lt_token", type=str, required=True,
                        help="Service account token for Properties API calls.")
    parser.add_argument("-e", "--target_env_label", type=str, required=True,
                        help="Label, as configured in the manifest, of the target environment where the configuration values will be applied.")
    parser.add_argument("-m", "--trigger_manifest", type=str,
                        help="Manifest artifact (in JSON format) received when the pipeline is triggered. Contains required data used throughout the pipeline execution.")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="Manifest file (with JSON format). Contains required data used throughout the pipeline execution.")
    parser.add_argument("-cf", "--config_file", type=str,
                        help="Config file path. Contains configuration values to override the default ones.")

    args = parser.parse_args()

    # Load config file if exists
    if args.config_file:
        load_configuration_file(args.config_file)
    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse the LT Url and split the LT hostname from the HTTP protocol
    # Assumes the default HTTP protocol = https
    lt_http_proto = LIFETIME_HTTP_PROTO
    lt_url = args.lt_url
    if lt_url.startswith("http://"):
        lt_http_proto = "http"
        lt_url = lt_url.replace("http://", "")
    else:
        lt_url = lt_url.replace("https://", "")
    if lt_url.endswith("/"):
        lt_url = lt_url[:-1]
    # Parse the LT Token
    lt_token = args.lt_token
    # Parse Destination Environment
    target_env_label = args.target_env_label

    # Validate Manifest is being passed either as JSON or as file
    if not args.trigger_manifest and not args.manifest_file:
        raise ManifestDoesNotExistError("The manifest was not provided as JSON or as a file. Aborting!")

    # Parse Trigger Manifest artifact
    if args.manifest_file:
        trigger_manifest_path = os.path.split(args.manifest_file)
        trigger_manifest = load_data(trigger_manifest_path[0], trigger_manifest_path[1])
    else:
        trigger_manifest = json.loads(args.trigger_manifest)

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_token, target_env_label, trigger_manifest)
