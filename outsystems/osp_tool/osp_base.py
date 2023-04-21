from subprocess import PIPE, run
# Exceptions
from outsystems.exceptions.osptool_error import OSPToolDeploymentError


# Deploys an OutSystems Application Package (.oap) on a target environment
def call_osptool(osp_tool_path: str, package_file_path: str, env_hostname: str, credentials: str):

    command = "{} {} {} {}".format(osp_tool_path, package_file_path, env_hostname, credentials)
    result = run(command, stderr=PIPE, universal_newlines=True)

    if result.returncode != 0:
        raise OSPToolDeploymentError("OSPTool deployment failed, please check the logs for more detail.")
