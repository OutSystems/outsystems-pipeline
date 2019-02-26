# Python Modules
import os

# Base CICD Probe Variables
PROBE_HTTP_PROTO = os.environ['CICDProbeProto']
PROBE_API_ENDPOINT = os.environ['CICDProbeAPIEndpoint']
PROBE_API_VERSION = int(os.environ['CICDProbeAPIVersion'])

# Scan Endpoints
SCAN_BDD_TESTS_ENDPOINT = "ScanBDDTestEndpoints"
PROBE_SCAN_SUCCESS_CODE = 200