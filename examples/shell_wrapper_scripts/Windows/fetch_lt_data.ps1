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
  [int]$LifeTimeApi
)

Write-Host "Switch to Virtual Environment"
. .\$PythonEnv\Scripts\Activate.ps1

Write-Host "Fetch LifeTime data"
python -m outsystems.pipeline.fetch_lifetime_data --artifacts "$ArtifactDir" --lt_url $LifeTimeUrl --lt_token $LifeTimeToken --lt_api_version $LifeTimeApi

Write-Host "Leave the Virtual Environment for now"
deactivate