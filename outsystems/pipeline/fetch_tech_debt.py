# Python Modules
import sys
import os
import argparse

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
# Variables
from outsystems.vars.file_vars import ARTIFACT_FOLDER
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS
from outsystems.vars.ad_vars import AD_API_HOST

# Functions
from outsystems.file_helpers.file import load_data
from outsystems.architecture_dashboard.ad_tech_debt import get_infra_techdebt, get_app_techdebt, \
    get_techdebt_levels, get_techdebt_categories


# ############################################################# SCRIPT ##############################################################
def main(artifact_dir: str, ad_api_host: str, activation_code: str, api_key: str, trigger_manifest: dict):

    # Get tech debt reference data (levels)
    get_techdebt_levels(artifact_dir, ad_api_host, activation_code, api_key)
    print("Technical debt levels retrieved successfully.", flush=True)

    # Get tech debt reference data (categories)
    get_techdebt_categories(artifact_dir, ad_api_host, activation_code, api_key)
    print("Technical debt categories retrieved successfully.", flush=True)

    # If the manifest file is being used, tech debt analysis is made for each app in the manifest
    # Otherwise it runs for the entire infrastructure
    if trigger_manifest and MANIFEST_APPLICATION_VERSIONS in trigger_manifest:
        for app in trigger_manifest[MANIFEST_APPLICATION_VERSIONS]:
            status = get_app_techdebt(artifact_dir, ad_api_host, activation_code, api_key, app)
            if status:
                print("Technical debt data retrieved successfully for application {}.".format(app["ApplicationName"]), flush=True)
            else:
                print("No technical debt data found for application {}.".format(app["ApplicationName"]), flush=True)

    else:
        get_infra_techdebt(artifact_dir, ad_api_host, activation_code, api_key)
        print("Technical debt data retrieved successfully for infrastructure {}.".format(activation_code), flush=True)

    sys.exit(0)

# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-n", "--ad_hostname", type=str, default=AD_API_HOST,
                        help="Hostname of Architecture Dashboard, without the API endpoint. Default: \"architecture.outsystems.com\"")
    parser.add_argument("-c", "--activation_code", type=str, required=True,
                        help="Activation code of target infrastructure.")
    parser.add_argument("-k", "--api_key", type=str, required=True,
                        help="Key for Architecture Dashboard API calls.")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="(Optional) Trigger manifest file path.")

    args = parser.parse_args()

    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse the Architecture Dashboard hostname
    ad_api_host = args.ad_hostname
    # Parse the Infrastcucture Activation Code
    activation_code = args.activation_code
    # Parse the Architecture Dashboard API Key
    api_key = args.api_key
    # Parse Manifest file if it exists
    if args.manifest_file:
        manifest_path = os.path.split(args.manifest_file)
        manifest_file = load_data(manifest_path[0], manifest_path[1])
    else:
        manifest_file = None

    # Calls the main script
    main(artifact_dir, ad_api_host, activation_code, api_key, manifest_file)
