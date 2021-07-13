import sys
import os
sys.path.append("C:\\Users\\dmc\\Documents\\github")
sys.path.append("C:\\Users\\dmc\\Documents\\github\\outsystems-pipeline")
sys.path.append("C:\\Users\\dmc\\Documents\\github\\outsystems-pipeline\\outsystems")
sys.path.append(os.getcwd())


if __name__ == "__main__":

    args = {
        'fileshare_pass': "Potato12#",
        'artifacts_folder': "C:\\Users\\dmc\\Documents\\github\\outsystems-pipeline\\test\\Artifacts",
        'lt_url': "csdevops11-lt.outsystems.net",
        'lt_token': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsaWZldGltZSIsInN1YiI6IlpERmxZelEyTldFdFkyUmpaaTAwWldFNUxUazBOemd0WVRJeE1EVTNNRFk0Tm1ReSIsImF1ZCI6ImxpZmV0aW1lIiwiaWF0IjoiMTYyNTI0ODU3NCIsImppdCI6ImhaTlRXVFJOWkkifQ==.Zw+TQ1NVMO2YWUjfBV+/VNWpebD3hfkkitS52iNNHeY=",
        'lt_version': "2",
        'target_env': "Regression",
        'app_list': "Cases",
        'manifest_file': None,
        'fileshare_user': "duarte.castano@outsystems.com",
        'inc_pattern': None,
        'exc_pattern': None
    }

    call = r"C:\\Users\\dmc\\Documents\\github\\outsystems-pipeline\\outsystems\\pipeline\\fetch_apps_source_code.py --artifacts {} --lt_url {} --lt_token {} --lt_api_version {} --fileshare_user {} --fileshare_pass {} --target_env {} --app_list {} --inc_pattern {} --exc_pattern {}".format(args["artifacts_folder"], args["lt_url"], args["lt_token"], args["lt_version"], args["fileshare_user"], args["fileshare_pass"], args["target_env"], args["app_list"], args["inc_pattern"], args["exc_pattern"])

    os.system(call)
