# Python Modules
import os
from configparser import ConfigParser

# Custom Modules
# Variables
from outsystems.vars.pipeline_vars import SSL_CERT_VERIFY, DEPLOYMENT_TIMEOUT_IN_SECS


# Returns the configuration value which may be defined in a properties file.
def get_conf_value(conf: str):

    _create_global_conf()
    global global_config

    # If config value already has been defined in global dict then return its value
    if conf in global_config:
        return global_config[conf]

    # Check if config file path is defined in the env var
    # Retrieve the config value from the config file
    elif "OS_PIPELINE_CONFIG_FILE" in os.environ:
        config_file = ConfigParser()
        config_file.read(os.environ["OS_PIPELINE_CONFIG_FILE"])
        if config_file.has_section('PIPELINE_CONFIG'):
            details_dict = dict(config_file.items('PIPELINE_CONFIG'))
            if conf.lower() in details_dict:
                global_config[conf] = details_dict[conf.lower()]
                print("[PIPELINE_CONFIG] Configuration overridden: '{}' has now the value '{}'".format(conf, global_config[conf]), flush=True)

    # If configuration is not yet defined at this moment then set it to its default value
    if conf not in global_config:
        global_config[conf] = eval(conf)

    return global_config[conf]


# ---------------------- PRIVATE METHODS ----------------------
# Private method to create a globel dict if it does not already exists.
def _create_global_conf():
    global global_config
    if "global_config" not in globals():
        global_config = {}
