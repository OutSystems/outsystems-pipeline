param(
    [Parameter(Mandatory = $true)]
    [string]$PythonEnv,
    [Parameter(Mandatory = $true)]
    [string]$ArtifactDir,
    [Parameter(Mandatory = $true)]
    [string[]]$AppList,
    [Parameter(Mandatory = $true)]
    [string]$BddUrl,
    [Parameter(Mandatory = $true)]
    [string]$CicdUrl
)

Write-Host "Switch to Virtual Environment"
. .\$PythonEnv\Scripts\Activate.ps1

Write-Host "Building the test endpoints"
python -m outsystems.pipeline.generate_unit_testing_assembly --artifacts "$ArtifactDir" --app_list "$AppList" --cicd_probe_env $CicdUrl --bdd_framework_env $BddUrl

# Store the exit status from the command above, to make it the exit status of this script
$status_code = $LASTEXITCODE

Write-Host "Leave the Virtual Environment for now"
deactivate

#### For Azure DevOps, uncomment the next lines ####
#Write-Host "Stashing the *.cache generated in the pipeline logs"
## The recurse flag is used to go into each directory (application_data, etc)
#$cache_files = Get-ChildItem -Path "$PWD\$(ArtifactsFolder)\*.cache" -Recurse
#foreach ($cfile in $cache_files) {
#    Write-Host "Stashing $cfile"
#    Write-Output "##vso[task.uploadfile]$cfile"
#}

exit $status_code