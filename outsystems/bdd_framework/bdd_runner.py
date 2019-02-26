# Custom Modules
from outsystems.bdd_framework.bdd_base import build_bdd_endpoint, send_bdd_get_request, send_bdd_get_run_request
from outsystems.vars.bdd_vars import BDD_HTTP_PROTO, BDD_API_ENDPOINT, BDD_API_VERSION, BDD_TEST_RUNNER_ENDPOINT, BDD_RUNNER_SUCCESS_CODE
from outsystems.vars.file_vars import BDD_FRAMEWORK_FOLDER, BDD_FRAMEWORK_TEST_RUN_FILE
from outsystems.file_helpers.file import store_data

# Method that builds the BDD Framework test endpoint based on the environment host, application and test name
def build_bdd_test_endpoint(env_url :str, espace_name :str, webscreen_name :str):
  # Builds the endpoint for BDD Framework and returns it
  return "{}://{}/{}{}/{}/{}/{}".format(BDD_HTTP_PROTO, env_url, BDD_API_ENDPOINT, BDD_API_VERSION, BDD_TEST_RUNNER_ENDPOINT, espace_name, webscreen_name) 

# Run existing BDD test in the target environment.
def run_bdd_test_full(env_url :str, espace_name :str, webscreen_name :str):
  # Builds the endpoint for BDD Framework and params
  endpoint = build_bdd_endpoint(env_url)
  query = "{}/{}/{}".format(BDD_TEST_RUNNER_ENDPOINT, espace_name, webscreen_name)
  # Sends the request
  data = send_bdd_get_request(endpoint, query, None)
  # Stores the result
  filename = "{}\\{}.{}{}".format(BDD_FRAMEWORK_FOLDER, espace_name, webscreen_name, BDD_FRAMEWORK_TEST_RUN_FILE)
  store_data(filename, data)
  return data

# Run existing BDD test in the target environment.
def run_bdd_test(test_url :str):
  # Sends the request
  response = send_bdd_get_run_request(test_url, None)
  status_code = response["http_status"]
  if status_code == BDD_RUNNER_SUCCESS_CODE:
    return response["response"]
  else:
    raise NotImplementedError("There was an error. Response from server: {}".format(response))