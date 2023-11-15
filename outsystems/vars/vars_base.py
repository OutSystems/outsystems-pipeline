import os
from dotenv import load_dotenv


# Evaluates whether there are environment variables that match a global variable
# If a matching environment variable is found, it returns the environment variable with the correct data type
# Otherwise, it returns the default value
def get_configuration_value(variable_name: str, default_value: any):
    if "OVERRIDE_CONFIG_IN_USE" in os.environ:
        # Verify if there's the variable exists within all env variables
        if (os.environ.get("OVERRIDE_CONFIG_IN_USE") == 'True') and variable_name in os.environ:
            env_value = os.environ[variable_name]
            # Convert env variable type from a string to a int
            if env_value.isnumeric():
                return int(env_value)
            # Convert env variable type from a string to a boolean
            elif env_value.lower() in ('true', 'false'):
                return env_value.lower() == 'true'
            else:
                return env_value
    return default_value


# loads configuration values from a specified file into the environment variables
def load_configuration_file(config_file_path: str):
    if os.path.isfile(config_file_path):
        load_dotenv(config_file_path)
        os.environ["OVERRIDE_CONFIG_IN_USE"] = 'True'
        print("Configuration file loaded successfully.", flush=True)
