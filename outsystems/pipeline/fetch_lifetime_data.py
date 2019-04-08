# Python Modules
import os, sys, argparse

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
from outsystems.lifetime.lifetime_applications import get_applications
from outsystems.lifetime.lifetime_environments import get_environments
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION
from outsystems.vars.file_vars import ARTIFACT_FOLDER

############################################################## SCRIPT ##############################################################
def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str):
    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(
        lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Get Environments
    get_environments(artifact_dir, lt_endpoint, lt_token)
    print("OS Environments data retrieved successfully.")
    # Get Applications without extra data
    get_applications(artifact_dir, lt_endpoint, lt_token, False)
    print("OS Applications data retrieved successfully.")


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str,
                        help="Name of the artifacts folder. Default: \"Artifacts\"", default=ARTIFACT_FOLDER)
    parser.add_argument("-u", "--lt_url", type=str,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"", required=True)
    parser.add_argument("-t", "--lt_token", type=str,
                        help="Token for LifeTime API calls.", required=True)
    parser.add_argument("-v", "--lt_api_version", type=int,
                        help="LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2", default=LIFETIME_API_VERSION)
    parser.add_argument("-e", "--lt_endpoint", type=str,
                        help="(optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"", default=LIFETIME_API_ENDPOINT)

    args = parser.parse_args()
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

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url,
         lt_api_endpoint, lt_version, lt_token)
