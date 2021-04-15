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

# Functions
from outsystems.file_helpers.file import load_data
from outsystems.architecture_dashboard.ad_tech_debt import get_infra_techdebt, get_app_techdebt


# ############################################################# SCRIPT ##############################################################
def main(artifact_dir: str, activation_code: str, api_key: str, dep_manifest: list):

    # If the manifest file is being used, the tech debt analysis will be made for each app
    # Or else you'll be doing the tech debt analysis for all infrastructure
    if dep_manifest:
        for app in dep_manifest:
            get_app_techdebt(artifact_dir, api_key, activation_code, app)
    else:
        get_infra_techdebt(artifact_dir, api_key, activation_code)

    sys.exit(0)

# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-c", "--activation_code", type=str, required=True,
                        help="Infrastructure Activation Code.")
    parser.add_argument("-t", "--api_key", type=str, required=True,
                        help="Token for Architecture Dashboard API calls.")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="(optional) Manifest file path.")

    args = parser.parse_args()

    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse the Architecture Dashboard API Key
    api_key = args.api_key
    # Parse the Infrastcucture Activation Code
    activation_code = args.activation_code
    # Parse Manifest file if it exists
    if args.manifest_file:
        manifest_file = load_data("", args.manifest_file)
    else:
        manifest_file = None

    # Calls the main script
    main(artifact_dir, activation_code, api_key, manifest_file)
