#!/bin/bash

if [[ $# -lt 14 ]] ; then
  echo -e '\nNot enough parameters! You need to set the necessary parameters:\n'
  echo -e '-e <python environment name> \t\t Python environment name, in order to use your pip dependencies.'
  echo -e '-a <dir name> \t\t\t\t Artifacts directory used for cache files between pipeline scripts.'
  echo -e '-s <url> \t\t\t\t URL with the Slack API Hook, for API calls.'
  echo -e '-c <channel list> \t\t\t\t Comma separated list for slack channels.'
  echo -e '-p <type> \t\t\t\t Pipeline type. Current Types: azure, jenkins.'
  echo -e '-j <job name> \t\t\t\t Job name you want to show on the notification. Example: Main app name.'
  echo -e '-d <url> \t\t\t\t URL for the dashboard.'
  echo -e '\n\nusage: ./build_test_endpoints.sh -e <python environment name> -a <artifacts dir> -s <slack hook> -c <slack channel list> -p <pipeline type> -j <job name> -d <dashboard url>'
  exit 1
fi

while getopts "e:a:s:c:p:j:d:" option 
do
  case "${option}"
  in
  e) env_name=${OPTARG};;
  a) artifacts=${OPTARG};;
  s) slack_hook=${OPTARG};;
  c) slack_channels=${OPTARG};;
  p) pipeline_type=${OPTARG};;
  j) job_name=${OPTARG};;
  d) dashboard_url=${OPTARG};;
  esac
done

echo "Slack Hook: $slack_hook"

echo "Switch to Virtual Environment"
source $env_name/bin/activate

echo "Sending test results to Slack"
python3 custom_pipeline/slack/send_test_results_to_slack.py --artifacts "$artifacts" --slack_hook $slack_hook --slack_channel "$slack_channels" --pipeline "$pipeline_type" --job_name "$job_name" --job_dashboard_url "$dashboard_url"

echo "Leave the Virtual Environment for now"
deactivate
