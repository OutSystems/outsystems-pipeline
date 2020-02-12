# Python Modules
import os
import sys
import argparse

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
from outsystems.vars.file_vars import ARTIFACT_FOLDER
from outsystems.file_helpers.file import load_data
from outsystems_integrations.slack.send_slack_message import send_slack_message


# ---------------------- SCRIPT ----------------------
def main(artifact_dir: str, error_file_name: str, slack_hook: str, slack_channels: list, pipeline_type: str, pipeline_status: bool, msg_title: str, message: str):
    slack_message = message
    if error_file_name:
        try:
            file_contents = load_data(artifact_dir, error_file_name)
            slack_message += "\n\n*Details:*\n\n`{}`".format(file_contents)
        except FileNotFoundError:
            slack_message += "\nCould not found the file {} in the {} directory".format(error_file_name, artifact_dir)
        except:
            slack_message += "\nCould not load the file {} in the {} directory".format(error_file_name, artifact_dir)

    send_slack_message(slack_hook, slack_channels, pipeline_type, msg_title, pipeline_status, slack_message)


# End of main()

if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str,
                        help="Name of the artifacts folder. Default: \"Artifacts\"", default=ARTIFACT_FOLDER)
    parser.add_argument("--error_in_file", type=str,
                        help="Filename where the error output is stored", default="")
    parser.add_argument("--slack_hook", type=str,
                        help="Slack hook URL for API calls. Example: \"https://hooks.slack.com/services/<id>/<id>/<id>\"", required=True)
    parser.add_argument("--slack_channel", type=str,
                        help="Comma separeted list with slack channel names. Example: \"Channel1,Channel-2\"", required=True)
    parser.add_argument("--pipeline", type=str,
                        help="Sets the pipeline type. Currently supported values: \"azure\" or \"jenkins\". Default: \"jenkins\"", default="")
    parser.add_argument("--title", type=str,
                        help="Title of the message that will show up on the notification.", required=True)
    parser.add_argument("--status", type=str,
                        help="Status of the pipeline. True if OK, False if Not OK.", required=True)
    parser.add_argument("--message", type=str,
                        help="Message that will show up on the notification.", required=True)
    args = parser.parse_args()

    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse the artifact file with errors
    error_file_name = args.error_in_file
    # Parse Slack Hook
    slack_hook = args.slack_hook
    # Parse Slack Channel list
    slack_channels = args.slack_channel.split(',')
    # Parse Pipeline Type
    pipeline_type = args.pipeline
    # Parse Message Title
    msg_title = args.title
    # Parse status
    status = (args.status.lower() == "true")
    # Parse Message
    message = args.message

    # Calls the main script
    main(artifact_dir, error_file_name, slack_hook, slack_channels, pipeline_type, status, msg_title, message)
