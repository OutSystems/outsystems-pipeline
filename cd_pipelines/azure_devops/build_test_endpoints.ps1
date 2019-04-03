param(
  [Parameter(Mandatory=$true)]
  [string]$PythonEnv,
  [Parameter(Mandatory=$true)]
  [string]$ArtifactDir,
  [Parameter(Mandatory=$true)]
  [string[]]$AppList,
  [Parameter(Mandatory=$true)]
  [string]$BddUrl,
  [Parameter(Mandatory=$true)]
  [string]$CicdUrl
)

Write-Host "Switch to Virtual Environment"
. .\$PythonEnv\Scripts\Activate.ps1

Write-Host "Building the test endpoints"
python outsystems/pipeline/generate_unit_testing_assembly.py --artifacts "$ArtifactDir" --app_list "$AppList" --cicd_probe_env $CicdUrl --bdd_framework_env $BddUrl

Write-Host "Leave the Virtual Environment for now"
deactivate