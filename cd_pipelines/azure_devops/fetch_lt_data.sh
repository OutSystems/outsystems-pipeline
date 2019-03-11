#!/bin/bash

echo "Switch to Virtual Environment"
source $ENVNAME/bin/activate

echo "Fetch LifeTime data"
python3 outsystems/pipeline/fetch_lifetime_data.py --artifacts "$ARTIFACTSFOLDER" --lt_url $LTURL --lt_token $LTTOKEN --lt_api_version $LTAPIVERSION

echo "Leave the Virtual Environment for now"
deactivate