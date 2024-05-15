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
from outsystems.vars.file_vars import ARTIFACT_FOLDER, SOLUTIONS_FOLDER, SOLUTIONS_DEPLOY_FILE
# Functions
from outsystems.osp_tool.osp_base import call_osptool
from outsystems.vars.vars_base import load_configuration_file
from outsystems.file_helpers.file import store_data
# Exceptions
from outsystems.exceptions.osptool_error import OSPToolDeploymentError


# ############################################################# SCRIPT ##############################################################
def main(artifact_dir: str, dest_env: str, package_path: str, catalogmappings_path: str, osp_tool_path: str, credentials: str):

    # Get solution file name from path
    solution_file = os.path.split(package_path)[1]

    print("Starting deployment of '{}' into '{}' environment...".format(solution_file, dest_env), flush=True)

    # Call OSP Tool
    return_code, execution_log = call_osptool(osp_tool_path, package_path, dest_env, credentials, catalogmappings_path)

    # Split the output into lines
    execution_log = execution_log.splitlines()

    # Stores the execution log
    filename = "{}{}".format(solution_file, SOLUTIONS_DEPLOY_FILE)
    filename = os.path.join(SOLUTIONS_FOLDER, filename)
    store_data(artifact_dir, filename, execution_log)

    error_validation_list = ['Incompatible Dependency', 'Execution Plan Abort', 'Outdated Consumer', 'Missing Configuration']

    # Validate the presence of each error validation
    deploy_error_flag = False
    for error_validation in error_validation_list:
        existing_error_list = [s for s in execution_log if error_validation in s]
        if existing_error_list:
            deploy_error_flag = True
            print(f'\nFound "{error_validation}" validation:')
            for error in existing_error_list:
                print(f' - {error}')

    if deploy_error_flag:
        # Exit script with error
        raise OSPToolDeploymentError(
            "OSP Tool Deployment finished with errors. Please check the logs for further details.")


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-d", "--destination_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the destination environment where you want to deploy the apps. (if in Airgap mode should be the hostname of the destination environment where you want to deploy the apps)")
    parser.add_argument("-p", "--package_path", type=str, required=True,
                        help="Package file path")
    parser.add_argument("-c", "--catalogmappings_path", type=str,
                        help="(Optional) Catalog mappings file path")
    parser.add_argument("-o", "--osp_tool_path", type=str, required=True,
                        help="OSP Tool file path")
    parser.add_argument("-user", "--osptool_user", type=str, required=True,
                        help="Username with privileges to deploy applications on target environment")
    parser.add_argument("-pwd", "--osptool_pwd", type=str, required=True,
                        help="Password of the Username with priveleges to deploy applications on target environment")
    parser.add_argument("-cf", "--config_file", type=str,
                        help="Config file path. Contains configuration values to override the default ones.")

    args = parser.parse_args()

    # Load config file if exists
    if args.config_file:
        load_configuration_file(args.config_file)
    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse the package path
    package_path = args.package_path
    # Parse the Catalog Mapping path
    catalogmappings_path = args.catalogmappings_path
    # Parse Destination Environment
    dest_env = args.destination_env
    # Parse OSP Tool path
    osp_tool_path = args.osp_tool_path
    # Parse Credentials for OSP Tool
    credentials = args.osptool_user + " " + args.osptool_pwd

    # Calls the main script
    main(artifact_dir, dest_env, package_path, catalogmappings_path, osp_tool_path, credentials)
