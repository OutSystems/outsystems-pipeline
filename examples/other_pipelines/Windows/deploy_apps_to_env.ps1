param(
    [Parameter(Mandatory = $true)]
    [string]$PythonEnv,
    [Parameter(Mandatory = $true)]
    [string]$ArtifactDir,
    [Parameter(Mandatory = $true)]
    [string]$LifeTimeUrl,
    [Parameter(Mandatory = $true)]
    [string]$LifeTimeToken,
    [Parameter(Mandatory = $true)]
    [int]$LifeTimeApi,
    [Parameter(Mandatory = $true)]
    [string]$SourceEnv,
    [Parameter(Mandatory = $true)]
    [string]$DestEnv,
    [Parameter(Mandatory = $true)]
    [string[]]$AppList,
    [Parameter(Mandatory = $true)]
    [string]$DeployMsg
)

Write-Host "Switch to Virtual Environment"
. .\$PythonEnv\Scripts\Activate.ps1

Write-Host "Deploy apps to $DestEnv"
python -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts "$ArtifactDir" --lt_url $LifeTimeUrl --lt_token $LifeTimeToken --lt_api_version $LifeTimeApi --source_env "$SourceEnv" --destination_env "$DestEnv" --app_list "$AppList" --deploy_msg "$DeployMsg"

# Store the exit status from the command above, to make it the exit status of this script
$status_code = $LASTEXITCODE

Write-Host "Leave the Virtual Environment for now"
deactivate

Write-Host "Stashing the *.cache generated in the pipeline logs"

#### For Azure DevOps, uncomment the next lines ####
## The recurse flag is used to go into each directory (application_data, etc)
#$cache_files = Get-ChildItem -Path "$PWD\$(ArtifactsFolder)\*.cache" -Recurse
#foreach ($cfile in $cache_files) {
#  Write-Host "Stashing $cfile"
#  Write-Output "##vso[task.uploadfile]$cfile"
#}

#$conflicts_file = Get-ChildItem -Path $PWD\$(ArtifactsFolder)\DeploymentConflicts
#if(Test-Path $conflicts_file) {
#  Write-Host "Stashing $conflicts_file"
#  Write-Output "##vso[task.uploadfile]$conflicts_file"
#}

exit $status_code