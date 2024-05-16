import subprocess
import threading

# Custom Modules
# Variables
from outsystems.vars.pipeline_vars import SOLUTION_TIMEOUT_IN_SECS
# Functions
from outsystems.vars.vars_base import get_configuration_value
# Exceptions
from outsystems.exceptions.osptool_error import OSPToolDeploymentError


def run_command(command, live_output_callback=None, timeout=None):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def read_output(pipe, callback, output_list):
        with pipe:
            for line in iter(pipe.readline, ''):
                callback(line.strip())
                output_list.append(line)

    # List to capture the live output
    live_output = []

    # Create a thread for reading and displaying live output
    live_output_thread = threading.Thread(target=read_output, args=(process.stdout, live_output_callback, live_output))
    live_output_thread.start()

    # Wait for the process to finish and get the return code
    try:
        return_code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        # Process has exceeded the timeout
        process.terminate()
        raise OSPToolDeploymentError("OSPTool Deployment timed out.")

    # Wait for the live output thread to finish
    live_output_thread.join()

    # Combine the live output into a single string (execution log)
    execution_log = ''.join(live_output)

    return return_code, execution_log


def call_osptool(osp_tool_path: str, package_file_path: str, env_hostname: str, credentials: str, catalogmappings_path: str):

    if catalogmappings_path:
        # Construct the command using a formatted string
        command = '"{}" "{}" "{}" {} /catalogmappings "{}"'.format(osp_tool_path, package_file_path, env_hostname, credentials, catalogmappings_path)
    else:
        # Construct the command using a formatted string
        command = '"{}" "{}" "{}" {}'.format(osp_tool_path, package_file_path, env_hostname, credentials)

    # Define a callback function for live output
    def live_output_callback(output_line):
        print(output_line)

    # Run the command and get the return code and execution log
    return_code, execution_log = run_command(command, live_output_callback, timeout=get_configuration_value("SOLUTION_TIMEOUT_IN_SECS", SOLUTION_TIMEOUT_IN_SECS))

    return return_code, execution_log
