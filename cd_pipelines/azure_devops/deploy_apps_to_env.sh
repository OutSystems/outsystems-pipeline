#!/bin/bash

echo "Switch to Virtual Environment"
source $ENVNAME/bin/activate

echo "Deploy apps to $DESTENV"
python3 outsystems/pipeline/deploy_latest_tags_to_target_env.py --artifacts "$ARTIFACTSFOLDER" --lt_url $LTURL --lt_token $LTTOKEN --lt_api_version $LTAPIVERSION --source_env "$SOURCEENV" --destination_env "$DESTENV" --app_list "$APPLIST" --deploy_msg "$DEPLOYMSG"

echo "Leave the Virtual Environment for now"
deactivate