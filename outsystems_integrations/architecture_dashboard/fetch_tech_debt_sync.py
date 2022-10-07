# Python Modules
import sys
import os
import argparse
import dateutil.parser
from time import sleep

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
# Variables
from outsystems.vars.file_vars import ARTIFACT_FOLDER, AD_FOLDER, AD_FILE_PREFIX, AD_APP_FILE
from outsystems_integrations.architecture_dashboard.vars import SLEEP_PERIOD_IN_SECS, MAX_RETRIES

# Functions
from outsystems.file_helpers.file import load_data, clear_cache
from outsystems.architecture_dashboard.ad_tech_debt import get_app_techdebt


def convert_to_date(date_string: str):
    return dateutil.parser.parse(date_string)


# ############################################################# SCRIPT ##############################################################
def main(artifact_dir: str, activation_code: str, api_key: str, dep_manifest: list):

    last_tag_time = None
    last_analysis_time = None

    retry_counter = 0
    while retry_counter < MAX_RETRIES:

        # Compare applications tag creation datetime with Architecture Dashboard's last analysis datetime
        # to assure the analysis includes the last code changes
        for app in dep_manifest:
            app_analysis_time = convert_to_date(get_app_techdebt(artifact_dir, api_key, activation_code, app)["LastAnalysisOn"])
            app_tag_time = convert_to_date(app["CreatedOn"])

            # Save most recent application datetime
            if last_tag_time is None or last_tag_time < app_tag_time:
                last_tag_time = app_tag_time

            # Save most recent code analysis datetime
            if last_analysis_time is None or last_analysis_time < app_analysis_time:
                last_analysis_time = app_analysis_time

        if last_tag_time < last_analysis_time:
            print("Success: Code Analysis includes latest code changes.", flush=True)
            sys.exit(0)
        else:
            retry_counter += 1
            print("Code Analysis does not include the latest code changes. Trying again in {} minutes... (tentative {} out of {})".format(int(SLEEP_PERIOD_IN_SECS / 60), retry_counter, MAX_RETRIES), flush=True)
            sleep(SLEEP_PERIOD_IN_SECS)

            print("Deleting old code analysis cached files...", flush=True)
            # Clear Code Analysis cached data
            for app in dep_manifest:
                filename = "{}.{}{}".format(AD_FILE_PREFIX, app["ApplicationName"], AD_APP_FILE)
                filename = os.path.join(AD_FOLDER, filename)
                clear_cache(artifact_dir, filename)

    print("Error: Max tries reached out.", flush=True)
    sys.exit(1)

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
    parser.add_argument("-f", "--manifest_file", type=str, required=True,
                        help="Manifest file path.")

    args = parser.parse_args()

    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse the Architecture Dashboard API Key
    api_key = args.api_key
    # Parse the Infrastcucture Activation Code
    activation_code = args.activation_code
    # Parse Manifest file
    manifest_file = load_data("", args.manifest_file)

    # Calls the main script
    main(artifact_dir, activation_code, api_key, manifest_file)
