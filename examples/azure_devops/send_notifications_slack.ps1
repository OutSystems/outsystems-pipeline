param(
  [Parameter(Mandatory=$true)]
  [string]$PythonEnv,
  [Parameter(Mandatory=$true)]
  [string]$ArtifactDir,
  [Parameter(Mandatory=$true)]
  [string]$SlackHook,
  [Parameter(Mandatory=$true)]
  [string[]]$SlackChannels,
  [Parameter(Mandatory=$true)]
  [ValidateSet("jenkins","azure")]
  [string]$PipelineType,
  [Parameter(Mandatory=$true)]
  [string]$JobName,
  [Parameter(Mandatory=$true)]
  [string]$DashboardUrl
)

Write-Host "Switch to Virtual Environment"
. .\$PythonEnv\Scripts\Activate.ps1

Write-Host "Building the test endpoints"
python outsystems_integrations/slack/send_test_results_to_slack.py --artifacts "$ArtifactDir" --slack_hook $SlackHook --slack_channel "$SlackChannels" --pipeline "$PipelineType" --job_name "$JobName" --job_dashboard_url "$DashboardUrl"

Write-Host "Leave the Virtual Environment for now"
deactivate