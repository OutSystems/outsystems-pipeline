# Python Modules
import os
from configparser import ConfigParser

# Custom Modules
# Variables
from outsystems.vars.pipeline_vars import SSL_CERT_VERIFY, DEPLOYMENT_TIMEOUT_IN_SECS
# Exceptions
from outsystems.exceptions.configuration_not_found import ConfigurationNotFoundError


def create_global_conf():
    global global_config
    if "global_config" not in globals():
        global_config = {}


# Returns the configuration value which may be defined in a properties file.
def get_conf_value(conf: str):

    # verify valid configurations
    if conf not in ("SSL_CERT_VERIFY", "DEPLOYMENT_TIMEOUT_IN_SECS"):
        raise ConfigurationNotFoundError

    create_global_conf()
    global global_config

    # if config value already has been define in global dict then return it
    if conf in global_config:
        return global_config[conf]

    # if not, try to retrieve it from the config file
    elif "OS_PIPELINE_CONFIG_FILE" in os.environ:
        config_file = ConfigParser()
        config_file.read(os.environ["OS_PIPELINE_CONFIG_FILE"])
        if config_file.has_section('PIPELINE_CONFIG'):
            details_dict = dict(config_file.items('PIPELINE_CONFIG'))
            if conf.lower() in details_dict:
                global_config[conf] = details_dict[conf.lower()]

    # If configuration is not yet defined at this moment then set it to its default value
    if conf not in global_config:
        if conf == "SSL_CERT_VERIFY":
            global_config[conf] = SSL_CERT_VERIFY
        elif conf == "DEPLOYMENT_TIMEOUT_IN_SECS":
            global_config[conf] = DEPLOYMENT_TIMEOUT_IN_SECS

    return global_config[conf]
