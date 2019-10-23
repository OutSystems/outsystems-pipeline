import subprocess



#OSPTool.com /Publish {<osp_file>|<oap_file>} <hostname> <username> <password>
#deploy_app_oap(osp_tool_path, osp_path, dest_env, credentials)
def deploy_app_oap (osp_tool_path: str, osp_file_path: str, env_hostname: str, credentials: str):
    print("ESTOU NO DEPLOY_APPS_OSP")

    print("osp_tool_path: {}".format(osp_tool_path))
    print("osp_path: {}".format(osp_file_path))
    print("env_hostname: {}".format(env_hostname))
    print("credentials: {}".format(credentials))

    print("execute: {} {} {} {}".format(osp_tool_path, osp_file_path, env_hostname, credentials))

    subprocess.call("{} {} {} {}".format(osp_tool_path, osp_file_path, env_hostname, credentials))


    print("A SAIR DO DEPLOY_APPS_OSP")
    pass


# ---------------------- PRIVATE METHODS ----------------------

# Private method to get the Username and Password  into a tuple (user,pass).
def _get_credentials_info(**kwargs):
    if "username" in kwargs and "password" in kwargs:
        username = kwargs["app_name"]
        password = kwargs["password"]
    else:
        raise InvalidParametersError(
            "You need to use either username=<username> or passowrd=<passowrd> as parameters to call this method.")
    return (username, password)