# Python Modules
import sys
import os
import argparse
from time import sleep
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
from outsystems.vars.file_vars import ARTIFACT_FOLDER, SOLUTIONS_OSP_FILE, SOLUTIONS_FOLDER
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS, MANIFEST_APPLICATION_KEY, MANIFEST_FLAG_IS_TEST_APPLICATION, MANIFEST_APPLICATION_NAME
from outsystems.vars.pipeline_vars import SOLUTION_TIMEOUT_IN_SECS, SOLUTION_SLEEP_PERIOD_IN_SECS, SOLUTION_CREATED_STATUS, \
    SOLUTION_READY_STATUS, SOLUTION_GATHERING_DEPENDENCIES_STATUS, SOLUTION_GETTING_BINARIES_STATUS, SOLUTION_GENERATING_META_MODEL_STATUS, \
    SOLUTION_GENERATING_SOLUTION_STATUS, SOLUTION_COMPLETED_STATUS, SOLUTION_ABORTED_STATUS

# Functions
from outsystems.file_helpers.file import load_data, bytes_human_readable_size
from outsystems.lifetime.lifetime_solutions import create_solution, get_solution_status, get_solution_url
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.lifetime.lifetime_downloads import download_package
from outsystems.manifest.manifest_base import get_environment_details
from outsystems.vars.vars_base import get_configuration_value, load_configuration_file
# Exceptions
from outsystems.exceptions.manifest_does_not_exist import ManifestDoesNotExistError


# ############################################################# SCRIPT ##############################################################
# Get a formatted status message for the different statuses of a solution generation process.
def get_status_message(status: str):
    status_messages = {
        SOLUTION_CREATED_STATUS: "An empty solution was created in the system - it does not contain any associated application.",
        SOLUTION_READY_STATUS: "All included applications were added to the database and the solution is ready to be processed.",
        SOLUTION_GATHERING_DEPENDENCIES_STATUS: "Calculating all the dependencies for the solution.",
        SOLUTION_GETTING_BINARIES_STATUS: "Getting the binaries for each module included in the solution.",
        SOLUTION_GENERATING_META_MODEL_STATUS: "Building the solution package manifest.",
        SOLUTION_GENERATING_SOLUTION_STATUS: "Creating the solution file."
    }

    return status_messages.get(status, "Unknown status: " + status)


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, source_env_label: str, include_test_apps: bool, solution_name: str, include_refs: bool, trigger_manifest: dict):

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Tuple with (EnvName, EnvKey): src_env_tuple[0] = EnvName; src_env_tuple[1] = EnvKey
    env_tuple = get_environment_details(trigger_manifest, source_env_label)

    # Retrive the app keys from the manifest content
    application_keys = [app[MANIFEST_APPLICATION_KEY] for app in trigger_manifest.get(MANIFEST_APPLICATION_VERSIONS, []) if include_test_apps or not app.get(MANIFEST_FLAG_IS_TEST_APPLICATION)]

    # Send request to create a solution with the given app keys
    solution_key = create_solution(artifact_dir, lt_endpoint, lt_token, env_tuple[1], solution_name, application_keys, include_refs)

    # Wait for solution package creation to finish
    wait_counter = 0
    package_url_available = False
    check_status = None
    IN_PROGESS_STATUS = [SOLUTION_CREATED_STATUS, SOLUTION_READY_STATUS, SOLUTION_GATHERING_DEPENDENCIES_STATUS,
                         SOLUTION_GETTING_BINARIES_STATUS, SOLUTION_GENERATING_META_MODEL_STATUS,
                         SOLUTION_GENERATING_SOLUTION_STATUS]

    # Retrieve the app names from the manifest content
    application_names = [app[MANIFEST_APPLICATION_NAME] for app in trigger_manifest.get(MANIFEST_APPLICATION_VERSIONS, []) if include_test_apps or not app.get(MANIFEST_FLAG_IS_TEST_APPLICATION)]

    # Print information about the solution package
    print("A solution package will be created from '{}', containing the latest version of each module from the following applications:".format(env_tuple[0]), flush=True)

    for app_name in application_names:
        print(" - {} ".format(app_name), flush=True)

    # Print additional information if include_refs is True
    if include_refs:
        print("Producer modules will also be included in the solution package", flush=True)

    print("Start creation of '{}' package:".format(solution_name), flush=True)
    while wait_counter < get_configuration_value("SOLUTION_TIMEOUT_IN_SECS", SOLUTION_TIMEOUT_IN_SECS):
        # Check current package status
        solution_status = get_solution_status(artifact_dir, lt_endpoint, lt_token, env_tuple[1], solution_key)
        if solution_status["Status"] == SOLUTION_COMPLETED_STATUS:
            # Package was created successfully
            package_url_available = True
            break
        elif solution_status["Status"] == SOLUTION_ABORTED_STATUS:
            print(" - {}. Reason: {}".format(solution_status["Status"], solution_status["StatusReason"]), flush=True)
            exit(1)
        elif solution_status["Status"] in IN_PROGESS_STATUS:
            # Solution package is still being created. Go back to sleep.
            sleep_value = get_configuration_value("SOLUTION_SLEEP_PERIOD_IN_SECS", SOLUTION_SLEEP_PERIOD_IN_SECS)
            sleep(sleep_value)
            wait_counter += sleep_value
            if check_status != solution_status["Status"]:
                print(" - {} - {}".format(solution_status["Status"], get_status_message(solution_status["Status"])), flush=True)
                check_status = solution_status["Status"]
        else:
            raise NotImplementedError("Unknown solution code status: {}.".format(solution_status["Status"]))

    # When the package is created, download it using the provided key
    if package_url_available:
        print("Solution package {} created successfully.".format(solution_key), flush=True)
        solution_url = get_solution_url(artifact_dir, lt_endpoint, lt_token, env_tuple[1], solution_key)

        file_name = solution_name + SOLUTIONS_OSP_FILE
        file_path = os.path.join(artifact_dir, SOLUTIONS_FOLDER, file_name)
        download_package(file_path, lt_token, solution_url)

        print("Solution package successfully downloaded as '{}' ({}).".format(file_name, bytes_human_readable_size(os.path.getsize(file_path))), flush=True)
    else:
        print("Timeout expired while generating solution package {}.".format(solution_key), flush=True)

# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="(Optional) Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-u", "--lt_url", type=str, required=True,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
    parser.add_argument("-t", "--lt_token", type=str, required=True,
                        help="Token for LifeTime API calls.")
    parser.add_argument("-v", "--lt_api_version", type=int, default=LIFETIME_API_VERSION,
                        help="(Optional) LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
    parser.add_argument("-e", "--lt_endpoint", type=str, default=LIFETIME_API_ENDPOINT,
                        help="(Optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-s", "--source_env_label", type=str, required=True,
                        help="Label, as configured in the manifest, of the source environment where the apps are.")
    parser.add_argument("-i", "--include_test_apps", action='store_true',
                        help="Flag that indicates if applications marked as \"Test Application\" in the manifest are included in the solution.")
    parser.add_argument("-m", "--trigger_manifest", type=str,
                        help="Manifest artifact (in JSON format) received when the pipeline is triggered. Contains required data used throughout the pipeline execution.")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="Manifest file (with JSON format). Contains required data used throughout the pipeline execution.")
    parser.add_argument("-sn", "--solution_name", type=str, required=True,
                        help="Name of the solution package that will be created.")
    parser.add_argument("-r", "--include_refs", action='store_true',
                        help="Flag that indicates if whether to include producer modules in the solution.")
    parser.add_argument("-cf", "--config_file", type=str,
                        help="Config file path. Contains configuration values to override the default ones.")

    args = parser.parse_args()

    # Load config file if exists
    if args.config_file:
        load_configuration_file(args.config_file)
    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse the API endpoint
    lt_api_endpoint = args.lt_endpoint
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
    # Parte LT API Version
    lt_version = args.lt_api_version
    # Parse the LT Token
    lt_token = args.lt_token
    # Parse Source Environment
    source_env_label = args.source_env_label
    # Parse Include Test Apps flag
    include_test_apps = args.include_test_apps
    # Parse Solution Name
    solution_name = args.solution_name
    # Parse Include References flag
    include_refs = args.include_refs

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
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, source_env_label, include_test_apps, solution_name, include_refs, trigger_manifest)
