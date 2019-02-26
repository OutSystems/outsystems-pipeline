# Python Modules
import os

# Base CICD Probe Variables
BDD_HTTP_PROTO = os.environ['BDDAPIProto']
BDD_API_ENDPOINT = os.environ['BDDAPIEndpoint']
BDD_API_VERSION = int(os.environ['BDDAPIVersion'])

# Test Runner Endpoint Variables
BDD_TEST_RUNNER_ENDPOINT = "BDDTestRunner"
BDD_RUNNER_SUCCESS_CODE = 200