# Python Modules
import json
import requests
import sys
import os

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
from outsystems_integrations.slack.vars import notification_type


# Sends a slack message for a given channel list
def send_slack_message(slack_hook: str, slack_channels: list, pipeline_type: str, slack_title: str, job_status: bool, slack_message: str):
    if pipeline_type not in notification_type:
        username = "Regression Testing"
        icon = ":outsystems:"
    else:
        username = "{} Regression Testing".format(notification_type[pipeline_type][0])
        icon = notification_type[pipeline_type][1]
    for channel in slack_channels:
        # Build slack post
        postData = {
            "channel": channel,
            "username": username,
            "text": "{}".format(slack_title),
            "icon_emoji": icon,
            "attachments": [{
                "color": "#49C39E" if job_status else "#D40E0D",
                "text": slack_message,
                "mrkdwn_in": ["text"]
            }]
        }
        response = requests.post(slack_hook, json.dumps(postData), None)
        if response.status_code == 200:
            print("Message sent to slack channel {} successfully...".format(channel))
        else:
            print("Error sending notification to slack channel {}: {}".format(
                channel, response.text))
