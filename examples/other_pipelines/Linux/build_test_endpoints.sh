#!/bin/bash

if [[ $# -lt 10 ]] ; then
    echo -e '\nNot enough parameters! You need to set the necessary parameters:\n'
    echo -e '-e <python environment name> \t\t Python environment name, in order to use your pip dependencies.'
    echo -e '-a <dir name> \t\t\t\t Artifacts directory used for cache files between pipeline scripts.'
    echo -e '-l <app list> \t\t\t\t Comma separeted list of apps you want to test (including the ones with tests).'
    echo -e '-c <url> \t\t\t\t URL for the environment containing the CICD probe. You dont need to set the API endpoint.'
    echo -e '-b <url> \t\t\t\t URL for the environment containing the BDD Framework. You dont need to set the API endpoint.'
    echo -e '\n\nusage: ./build_test_endpoints.sh -e <python environment name> -a <artifacts dir> -l <app list> -c <cicd probe host url> -b <bdd framework host url>'
    exit 1
fi

while getopts "e:a:l:c:b:" option 
do
    case "${option}"
    in
        e) env_name=${OPTARG};;
        a) artifacts=${OPTARG};;
        l) app_list=${OPTARG};;
        c) cicd_url=${OPTARG};;
        b) bdd_url=${OPTARG};;
    esac
done

echo "Switch to Virtual Environment"
source $env_name/bin/activate

echo "Building the test endpoints"
python3 -m outsystems.pipeline.generate_unit_testing_assembly --artifacts "$artifacts" --app_list "$app_list" --cicd_probe_env $cicd_url --bdd_framework_env $bdd_url

# Store the exit status from the command above, to make it the exit status of this script
status_code=$?

echo "Leave the Virtual Environment for now"
deactivate

#### For Azure DevOps, uncomment the next lines ####
#echo "Stashing the *.cache generated in the pipeline logs"
#cache_files=$PWD/$artifacts/**/*.cache
#for cfile in $cache_files
#do
#    echo "Stashing $cfile"
#    echo "##vso[task.uploadfile]$cfile"
#done

exit $status_code