#!/bin/bash

echo "Switch to Virtual Environment"
source $ENVNAME/bin/activate

echo "Building the test endpoints"
python3 outsystems/pipeline/evaluate_test_results.py --artifacts "$ARTIFACTSFOLDER"

echo "Leave the Virtual Environment for now"
deactivate
