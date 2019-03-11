#!/bin/bash

echo "Switch to Virtual Environment"
source $ENVNAME/bin/activate

echo "Building the test endpoints"
python3 outsystems/pipeline/generate_unit_testing_assembly.py --artifacts "$ARTIFACTSFOLDER" --app_list "$APPLIST" --cicd_probe_env $CICDPROBEURL --bdd_framework_env $BDDFRAMEWORKURL

echo "Leave the Virtual Environment for now"
deactivate
