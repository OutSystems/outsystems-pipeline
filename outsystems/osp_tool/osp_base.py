import subprocess


# Deploys an OutSystems Application Package (.oap) on a target environment
def deploy_app_oap(osp_tool_path: str, osp_file_path: str, env_hostname: str, credentials: str):
    subprocess.call("{} {} {} {}".format(osp_tool_path, osp_file_path, env_hostname, credentials))
