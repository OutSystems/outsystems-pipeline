


#OSPTool.com /Publish {<osp_file>|<oap_file>} <hostname> <username> <password>
def deploy_app_oap (osp_tool_file: str, osp_file: str, env_hostname: str, **kwargs):
    print("ESTOU NO DEPLOY_APPS_OSP")

    print("osp_tool_file: {}".format(osp_tool_file))
    print("osp_file: {}".format(osp_file))
    print("env_hostname: {}".format(env_hostname))
    
    credentials = _get_credentials_info(**kwargs)

    print("username: {}".format(credentials["username"]))
    print("password: {}".format(credentials["password"]))
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