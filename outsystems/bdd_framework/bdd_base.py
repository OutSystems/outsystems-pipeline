# Python Modules
import requests
import json

# Custom Modules
from outsystems.exceptions.invalid_json_response import InvalidJsonResponseError
from outsystems.vars.bdd_vars import BDD_HTTP_PROTO, BDD_API_ENDPOINT, BDD_API_VERSION

# Method that builds the BDD Framework endpoint based on the environment host
def build_bdd_endpoint(env_url :str):
  # Builds the endpoint for BDD Framework and returns it
  return "{}://{}/{}{}".format(BDD_HTTP_PROTO, env_url, BDD_API_ENDPOINT, BDD_API_VERSION) 

# Runs the test on the BDD Framework app
def send_bdd_get_request(bdd_api :str, bdd_endpoint :str, url_params :str):
  # Format the request URL to include the api endpoint
  request_string = "{}/{}".format(bdd_api, bdd_endpoint)
  return send_bdd_get_run_request(request_string, url_params)

# Runs the test on the BDD Framework app
def send_bdd_get_run_request(test_endpoint :str, url_params :str):
  response_obj = {}
  # Send the request
  response = requests.get(test_endpoint, params=url_params)
  response_obj = { "http_status": response.status_code, "response": {} }
  if len(response.text) > 0:
    try:
      response_obj["response"] = response.json()
    except:
      raise InvalidJsonResponseError("GET {}: The JSON response could not be parsed. Response: {}".format(test_endpoint, response.text))
  return response_obj