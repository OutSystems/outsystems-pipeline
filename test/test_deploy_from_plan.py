# Python Modules
import sys
import os

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

sys.path.append("C:\\Users\\jfg\\source\\repos\\OutSystems\\outsystems-pipeline")

if __name__ == "__main__":

    args = {
        'artifact_dir': "C:\\work\\DevOps\\Pipeline\\artifacts",
        'lt_url': "csdevops11-lt.outsystems.net",
        # 'lt_token': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsaWZldGltZSIsInN1YiI6Ik5qaGhORFl3T1RRdFkyRXdaaTAwTW1NMUxXSXlPVGd0WWpnMk9EVXdNRGs0T1dNdyIsImF1ZCI6ImxpZmV0aW1lIiwiaWF0IjoiMTU3MTgzMjM4MCIsImppdCI6Ik82UXVqS3NmWEMifQ==.rAoeSCIpsi/zWndsw8aDPQ72yoyBmmHWVchagJPkpPI=",
        'lt_token': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsaWZldGltZSIsInN1YiI6Ik9ERmpPREZpWVdVdE9XWXdNaTAwT0RSaUxXRTNNR1F0T1RrMlpHWTFOMkV3TkdZMSIsImF1ZCI6ImxpZmV0aW1lIiwiaWF0IjoiMTU3MDUzNTQ3OCIsImppdCI6IlRmTTlVZDcyZHUifQ==.Dj08j5YgawJ7HuXSg8QxOO6/FvrfHdFoHjsBoUS51Ws=",
        'lt_api_version': 2,
        'source_env': "Development",
        'destination_env': "Regression",
        # 'destination_env': "csdevops11-pp.outsystems.net",
        # 'manifest_file': "C:\\work\\DevOps\\Pipeline\\artifacts\\manifest\\deployment_manifest.cache",
        'manifest_file': None,
        'osp_tool_path': "C:\\work\\DevOps\\Pipeline\\artifacts\\OSPTool\\OSPTool.com",
        'airgap_user': "dmc",
        'airgap_pass': "OutSystems123",
        'cicd_probe_url': "csdevops11-reg.outsystems.net",
        'deployment_plan_key': "b69ba677-963e-4ed1-93de-bd68072330a9"
    }

    print(sys.path)
    call_deploy = "..\\outsystems\\pipeline\\deploy_from_plan_to_target_env.py --artifacts \"{}\" --lt_url {} --lt_token {} --lt_api_version {} --source_env {} --destination_env {} --deployment_plan_key \"{}\" ".format(args["artifact_dir"], args["lt_url"], args["lt_token"], args["lt_api_version"], args["source_env"], args["destination_env"], args["deployment_plan_key"])

    os.system(call_deploy)
