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
    [int]$LifeTimeApi
)

Write-Host "Switch to Virtual Environment"
. .\$PythonEnv\Scripts\Activate.ps1

Write-Host "Fetch LifeTime data"
python -m outsystems.pipeline.fetch_lifetime_data --artifacts "$ArtifactDir" --lt_url $LifeTimeUrl --lt_token $LifeTimeToken --lt_api_version $LifeTimeApi

# Store the exit status from the command above, to make it the exit status of this script
$status_code = $LASTEXITCODE

Write-Host "Leave the Virtual Environment for now"
deactivate

#### For Azure DevOps, uncomment the next lines ####
#Write-Host "Stashing the *.cache generated in the pipeline logs"
#$cache_files = Get-ChildItem -Path "$PWD\$(ArtifactsFolder)\*.cache"
#foreach ($cfile in $cache_files) {
#  Write-Host "Stashing $cfile"
#  Write-Output "##vso[task.uploadfile]$cfile"
#}

exit $status_code