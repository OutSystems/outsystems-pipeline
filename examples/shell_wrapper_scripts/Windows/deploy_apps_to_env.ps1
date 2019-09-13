param(
  [Parameter(Mandatory=$true)]
  [string]$PythonEnv,
  [Parameter(Mandatory=$true)]
  [string]$ArtifactDir,
  [Parameter(Mandatory=$true)]
  [string]$LifeTimeUrl,
  [Parameter(Mandatory=$true)]
  [string]$LifeTimeToken,
  [Parameter(Mandatory=$true)]
  [int]$LifeTimeApi,
  [Parameter(Mandatory=$true)]
  [string]$SourceEnv,
  [Parameter(Mandatory=$true)]
  [string]$DestEnv,
  [Parameter(Mandatory=$true)]
  [string[]]$AppList,
  [Parameter(Mandatory=$true)]
  [string]$DeployMsg
)

Write-Host "Switch to Virtual Environment"
. .\$PythonEnv\Scripts\Activate.ps1

Write-Host "Deploy apps to $DestEnv"
python -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts "$ArtifactDir" --lt_url $LifeTimeUrl --lt_token $LifeTimeToken --lt_api_version $LifeTimeApi --source_env "$SourceEnv" --destination_env "$DestEnv" --app_list "$AppList" --deploy_msg "$DeployMsg"

Write-Host "Leave the Virtual Environment for now"
deactivate
