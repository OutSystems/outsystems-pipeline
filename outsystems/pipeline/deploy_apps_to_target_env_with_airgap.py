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
from outsystems.vars.file_vars import ARTIFACT_FOLDER, APPLICATION_OAP_FOLDER, APPLICATION_OAP_FILE
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION, DEPLOYMENT_MESSAGE
from outsystems.vars.cicd_vars import PROBE_HTTP_PROTO, PROBE_API_ENDPOINT, PROBE_API_VERSION
# Functions
from outsystems.lifetime.lifetime_environments import get_environment_key
from outsystems.lifetime.lifetime_applications import export_app_oap
from outsystems.file_helpers.file import load_data
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.cicd_probe.cicd_base import build_probe_endpoint
from outsystems.osp_tool.osp_base import call_osptool
from outsystems.cicd_probe.cicd_dependencies import get_app_dependencies, sort_app_dependencies
from outsystems.pipeline.deploy_latest_tags_to_target_env import generate_deployment_based_on_manifest as generate_deployment_based_on_deploy_manifest, \
    generate_regular_deployment
from outsystems.pipeline.deploy_tags_to_target_env_with_manifest import generate_deployment_based_on_manifest as generate_deployment_based_on_trigger_manifest
from outsystems.vars.vars_base import load_configuration_file
# Exceptions
from outsystems.exceptions.invalid_parameters import InvalidParametersError


# ############################################################# SCRIPT ##############################################################
def generate_oap_list(app_data_list: list, friendly_package_names: bool):
    app_oap_list = []
    filename = ""
    for app in app_data_list:
        if friendly_package_names:
            filename = "{}_v{}{}".format(app["Name"].replace(" ", "_"), app["Version"].replace(".", "_"), APPLICATION_OAP_FILE)
        else:
            filename = "{}{}".format(app["VersionKey"], APPLICATION_OAP_FILE)
        app_oap_list.append({"app_name": app["Name"], "app_version": app["Version"], "app_key": app["Key"], "version_key": app["VersionKey"], "filename": filename})
    return app_oap_list


def export_apps_oap(artifact_dir: str, lt_endpoint: str, lt_token: str, env_key: str, app_oap_list: list):
    print("Application Scope:", flush=True)
    for app in app_oap_list:
        file_path = os.path.join(artifact_dir, APPLICATION_OAP_FOLDER, app["filename"])
        export_app_oap(file_path, lt_endpoint, lt_token, env_key, app_key=app["app_key"], app_version_key=app["version_key"])
        print("     {} application with version {}, exported as {}".format(app["app_name"], app["app_version"], app["filename"]), flush=True)


def generate_deployment_order(artifact_dir: str, probe_endpoint: str, api_key: str, app_oap_list: list):
    dependencies_list = {}
    for app in app_oap_list:
        dependencies_list[app["app_key"]] = get_app_dependencies(artifact_dir, probe_endpoint, api_key,
                                                                 app["version_key"], app["app_name"], app["app_version"])
    dependencies_order_list = sort_app_dependencies(dependencies_list)
    final_list = []
    for app_dep in dependencies_order_list:
        for app_oap in app_oap_list:
            if app_dep == app_oap["app_key"]:
                final_list.append(app_oap)
    return final_list


def deploy_apps_oap(artifact_dir: str, dest_env: str, osp_tool_path: str, credentials: str, app_oap_list: list):
    for app in app_oap_list:
        oap_file_path = os.path.join(artifact_dir, APPLICATION_OAP_FOLDER, app["filename"])
        call_osptool(osp_tool_path, oap_file_path, dest_env, credentials)


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, source_env: str, dest_env: str, apps: list, dep_manifest: list, trigger_manifest: dict, include_test_apps: bool, dep_note: str, osp_tool_path: str, credentials: str, cicd_http_proto: str, cicd_url: str, cicd_api_endpoint: str, cicd_version: str, cicd_key: str, friendly_package_names: bool):

    app_data_list = []  # will contain the applications to deploy details from LT

    if lt_api_version == 1:  # LT for OS version < 11
        raise InvalidParametersError("Air Gap deployments are not supported for Deployment API v1")

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)
    # Builds the Probe endpoint
    probe_endpoint = build_probe_endpoint(cicd_http_proto, cicd_url, cicd_api_endpoint, cicd_version)

    # Gets the environment key for the source environment
    src_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, source_env)

    # If the manifest file is being used, the app versions MUST come from that file
    # Or else you might not be deploying the same app versions that were deployed in
    # previous pipeline steps
    if dep_manifest:
        app_data_list = generate_deployment_based_on_deploy_manifest(artifact_dir, lt_endpoint, lt_token, src_env_key, source_env, apps, dep_manifest)
    elif trigger_manifest:
        app_data_list = generate_deployment_based_on_trigger_manifest(artifact_dir, lt_endpoint, lt_token, src_env_key, source_env, trigger_manifest, include_test_apps, False)
    else:
        app_data_list = generate_regular_deployment(artifact_dir, lt_endpoint, lt_token, src_env_key, apps)

    # Export binary files
    app_oap_list = generate_oap_list(app_data_list, friendly_package_names)
    export_apps_oap(artifact_dir, lt_endpoint, lt_token, src_env_key, app_oap_list)

    # Generate deployment order
    sorted_oap_list = generate_deployment_order(artifact_dir, probe_endpoint, cicd_key, app_oap_list)

    print("\nDeployment Order:\n", flush=True)
    for oap in sorted_oap_list:
        print("      " + str(sorted_oap_list.index(oap) + 1) + ". " + oap["app_name"] + " (" + oap["version_key"] + ")\n", flush=True)

    # Deploy binary files to target environment
    deploy_apps_oap(artifact_dir, dest_env, osp_tool_path, credentials, sorted_oap_list)

# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-u", "--lt_url", type=str, required=True,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
    parser.add_argument("-t", "--lt_token", type=str, required=True,
                        help="Token for LifeTime API calls.")
    parser.add_argument("-v", "--lt_api_version", type=int, default=LIFETIME_API_VERSION,
                        help="LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
    parser.add_argument("-e", "--lt_endpoint", type=str, default=LIFETIME_API_ENDPOINT,
                        help="(Optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-s", "--source_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the source environment where the apps are.")
    parser.add_argument("-d", "--destination_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the destination environment where you want to deploy the apps. (if in Airgap mode should be the hostname of the destination environment where you want to deploy the apps)")
    parser.add_argument("-m", "--deploy_msg", type=str, default=DEPLOYMENT_MESSAGE,
                        help="Message you want to show on the deployment plans in LifeTime. Default: \"Automated deploy using OS Pipelines\".")
    parser.add_argument("-l", "--app_list", type=str,
                        help="Comma separated list of apps you want to deploy. Example: \"App1,App2 With Spaces,App3_With_Underscores\"")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="Manifest file path (either deployment or trigger), used to promote the same application versions throughout the pipeline execution.")
    parser.add_argument("-i", "--include_test_apps", action='store_true',
                        help="(Optional) Flag that indicates if applications marked as \"Test Application\" in the trigger manifest are included in the Air Gap deployment.")
    parser.add_argument("-o", "--osp_tool_path", type=str, required=True,
                        help="OSP Tool file path")
    parser.add_argument("-user", "--airgap_user", type=str, required=True,
                        help="Username with privileges to deploy applications on target environment")
    parser.add_argument("-pass", "--airgap_pass", type=str, required=True,
                        help="Password of the Username with priveleges to deploy applications on target environment")
    parser.add_argument("-pu", "--cicd_probe_url", type=str, required=True,
                        help="URL of the environment where the CI/CD Probe is installed (without the API endpoint).")
    parser.add_argument("-pv", "--cicd_probe_version", type=str, default=PROBE_API_VERSION,
                        help="(Optional) CI/CD Probe API version number.")
    parser.add_argument("-pe", "--cicd_probe_endpoint", type=str, default=PROBE_API_ENDPOINT,
                        help="(Optional) Used to set the API endpoint for CI/CD Probe, without the version.")
    parser.add_argument("-pk", "--cicd_probe_key", type=str,
                        help="(Optional) Key for CI/CD Probe API calls (when enabled).")
    parser.add_argument("-n", "--friendly_package_names", action='store_true',
                        help="Flag that indicates if downloaded application packages should have a user-friendly name. Example: \"AppName_v1_2_1\"")
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
    source_env = args.source_env
    # Parse Destination Environment
    dest_env = args.destination_env
    # Parse Manifest file if it exists
    # Based on the file content it can be a deployment manifest (list-based) or trigger manifest (dict-based)
    if args.manifest_file:
        manifest_path = os.path.split(args.manifest_file)
        manifest_file = load_data(manifest_path[0], manifest_path[1])
    else:
        manifest_file = None
    dep_manifest = manifest_file if type(manifest_file) is list else None
    trigger_manifest = manifest_file if type(manifest_file) is dict else None
    # Check if either an app list or a manifest file is being provided
    if not args.app_list and not args.manifest_file:
        raise InvalidParametersError("either --app_list or --manifest_file must be provided as arguments")

    if dep_manifest and not args.app_list:
        raise InvalidParametersError("--app_list parameter is required for Deployment Manifest operation")
    # Parse App list
    apps = None
    if args.app_list:
        _apps = args.app_list
        apps = _apps.split(',')
    # Parse Include Test Apps flag
    include_test_apps = args.include_test_apps
    # Parse Deployment Message
    dep_note = args.deploy_msg
    # Parse OSP Tool path
    osp_tool_path = args.osp_tool_path
    # Parse Credentials for OSP Tool
    credentials = args.airgap_user + " " + args.airgap_pass
    # Parse the CICD Probe API endpoint
    cicd_api_endpoint = args.cicd_probe_endpoint
    # Parse the CICD Probe Url and split the CICD Probe hostname from the HTTP protocol
    # Assumes the default HTTP protocol = "https"
    cicd_http_proto = PROBE_HTTP_PROTO
    cicd_url = args.cicd_probe_url
    if cicd_url.startswith("http://"):
        cicd_http_proto = "http"
        cicd_url = cicd_url.replace("http://", "")
    else:
        cicd_url = cicd_url.replace("https://", "")
    if cicd_url.endswith("/"):
        cicd_url = cicd_url[:-1]
    # Parse CICD Probe API Version
    cicd_version = args.cicd_probe_version
    # Parse CICD Probe API Key
    cicd_key = args.cicd_probe_key
    # Parse Friendly Package Names flag
    friendly_package_names = args.friendly_package_names

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, source_env, dest_env, apps, dep_manifest, trigger_manifest, include_test_apps, dep_note, osp_tool_path, credentials, cicd_http_proto, cicd_url, cicd_api_endpoint, cicd_version, cicd_key, friendly_package_names)
