# Python Modules
import os

# Custom Modules
# Variables
from outsystems.vars.pipeline_vars import SSL_CERT_VERIFY, DEPLOYMENT_TIMEOUT_IN_SECS


# Returns the value for the timeout of a deployment which may be defined as environment variable.
def get_ssl_cert_verify_value():
    if "ENV_SSL_CERT_VERIFY" in os.environ:
        return os.environ['ENV_SSL_CERT_VERIFY']
    return SSL_CERT_VERIFY


# Returns the value for the timeout of a deployment which may be defined as environment variable.
def get_deployment_timeout_in_secs_value():
    if "ENV_DEPLOYMENT_TIMEOUT_IN_SECS" in os.environ:
        return os.environ['ENV_DEPLOYMENT_TIMEOUT_IN_SECS']
    return DEPLOYMENT_TIMEOUT_IN_SECS
