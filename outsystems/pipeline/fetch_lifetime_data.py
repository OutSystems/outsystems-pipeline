# Python Modules
import os
import sys

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
  sys.path.append(os.environ['WORKSPACE'])

# Custom Modules
from outsystems.lifetime.lifetime_applications import get_applications
from outsystems.lifetime.lifetime_environments import get_environments

############################################################## VARS ##############################################################

# Set script local variables from environment
# LT url 
lt_url = os.environ['LifeTimeEnvironmentURL']
# LT Token for authentication
lt_token = os.environ['AuthorizationToken']

############################################################## SCRIPT ##############################################################

# Get Environments
get_environments(lt_url, lt_token)
print("OS Environments data retrieved successfully.")
# Get Applications without extra data
get_applications(lt_url, lt_token, False)
print("OS Applications data retrieved successfully.")
