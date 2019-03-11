#!/bin/bash

echo "Switch to Virtual Environment"
source $ENVNAME/bin/activate

echo "Sending test results to Slack"
python3 custom_pipeline/slack/send_test_results_to_slack.py --artifacts "$ARTIFACTSFOLDER" --slack_hook $SLACKHOOK --slack_channel "$SLACKCHANNELS" --pipeline "$PIPELINETYPE" --job_name "$JOBNAME" --job_dashboard_url "$JOBDASHBOARD"

echo "Leave the Virtual Environment for now"
deactivate
