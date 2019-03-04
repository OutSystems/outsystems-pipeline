# Python Modules
import os, sys, argparse

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
  sys.path.append(os.environ['WORKSPACE'])
else: # Else just add the project dir
  sys.path.append(os.getcwd())

# Custom Modules
from outsystems.vars.file_vars import ARTIFACT_FOLDER
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION

from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.lifetime.lifetime_environments import get_environments
from outsystems.lifetime.lifetime_applications import get_applications

############################################################## SCRIPT ##############################################################
def main( artifact_dir : str, lt_http_proto :str, lt_url :str, lt_api_endpoint :str, lt_api_version :int, lt_token :str ):
  # Builds the LifeTime endpoint
  lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)
  
  # Get Environments
  get_environments(artifact_dir, lt_endpoint, lt_token )
  print("OS Environments data retrieved successfully.")
  # Get Applications without extra data
  get_applications(artifact_dir, lt_endpoint, lt_token, False)
  print("OS Applications data retrieved successfully.")

if __name__ == "__main__":
  # Argument menu / parsing
  parser = argparse.ArgumentParser()
  parser.add_argument("-a", "--artifacts", type=str, help="Name of the artifacts folder. Default: \"Artifacts\"")
  parser.add_argument("-u", "--lt_url", type=str, help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
  parser.add_argument("-t", "--lt_token", type=str, help="Token for LifeTime API calls.")
  parser.add_argument("-v", "--lt_api_version", type=int, help="LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
  parser.add_argument("-e", "--lt_endpoint", type=str, help="(optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")

  args = parser.parse_args()
  # Parse the artifact directory
  # Assumes the default dir = Artifacts
  artifact_dir = ARTIFACT_FOLDER
  if args.artifacts: artifact_dir = args.artifacts
  # Parse the API endpoint
  # Assumes the default endpoint = lifetimeapi/rest
  lt_api_endpoint = LIFETIME_API_ENDPOINT
  if args.lt_endpoint: lt_api_endpoint = args.lt_endpoint
  # Parse the LT Url and split the LT hostname from the HTTP protocol
  # Assumes the default HTTP protocol = https
  lt_http_proto = LIFETIME_HTTP_PROTO
  lt_url = args.lt_url
  if lt_url:
    if lt_url.startswith("http://"): 
      lt_http_proto = "http"
      lt_url = lt_url.replace("http://","")
    else:
      lt_url = lt_url.replace("https://","")
    if lt_url.endswith("/"): lt_url = lt_url[:-1]
  else:
    print("You need to set the LifeTime URL.")
    exit(1)
  # Parte LT API Version
  # Assumes the default version = 2
  lt_version = LIFETIME_API_VERSION
  if args.lt_api_version: lt_version = args.lt_api_version
  # Parse the LT Token
  lt_token = args.lt_token
  if not lt_token: 
    print("You need to set the LifeTime Token or else you won't be able to authenticate.")
    exit(1)
    
  # Calls the main script
  main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token)