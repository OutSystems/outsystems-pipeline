#!/bin/bash

if [[ $# -lt 18 ]] ; then
    echo -e '\nNot enough parameters! You need to set the necessary parameters:\n'
    echo -e '-e <python environment name> \t\t Python environment name, in order to use your pip dependencies.'
    echo -e '-a <dir name> \t\t\t\t Artifacts directory used for cache files between pipeline scripts.'
    echo -e '-u <url> \t\t\t\t URL for the environment containing the LifeTime. You dont need to set the API endpoint.'
    echo -e '-t <token> \t\t\t\t API Token for the LifeTime service account.'
    echo -e '-v <int> \t\t\t\t LifeTime API version number.'
    echo -e '-s <int> \t\t\t\t Source environment name, where the apps you want to deploy are tagged.'
    echo -e '-d <int> \t\t\t\t Destination environment name, where the apps you deploy will be.'
    echo -e '-l <int> \t\t\t\t Comma separated list of applications you want to deploy.'
    echo -e '-m <int> \t\t\t\t Message you want to set on the deployment plan in LifeTime.'
    echo -e '\n\nusage: ./deploy_apps_to_env.sh -e <python environment name> -a <artifacts dir> -u <LT url> -t <LT token> -v <LT version> -s <source env name> -d <source env name> -l <app list> -m <deployment message>'
    exit 1
fi

while getopts "e:a:u:t:v:s:d:l:m:" option 
do
    case "${option}"
    in
        e) env_name=${OPTARG};;
        a) artifacts=${OPTARG};;
        u) lt_url=${OPTARG};;
        t) lt_token=${OPTARG};;
        v) lt_api=${OPTARG};;
        s) source_env=${OPTARG};;
        d) dest_env=${OPTARG};;
        l) app_list=${OPTARG};;
        m) dep_msg=${OPTARG};;
    esac
done

echo "Switch to Virtual Environment"
source $env_name/bin/activate

echo "Deploy apps to $dest_env"
python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts "$artifacts" --lt_url $lt_url --lt_token $lt_token --lt_api_version $lt_api --source_env "$source_env" --destination_env "$dest_env" --app_list "$app_list" --deploy_msg "$dep_msg"

echo "Leave the Virtual Environment for now"
deactivate

echo "Stashing the *.cache generated in the pipeline logs"
cache_files=$PWD/$artifacts/**/*.cache
for cfile in $cache_files
do
    echo "Stashing $cfile"
    echo "##vso[task.uploadfile]$cfile"
done

cache_files=$PWD/$artifacts/*.cache
for cfile in $cache_files
do
    echo "Stashing $cfile"
    echo "##vso[task.uploadfile]$cfile"
done

conflicts_file=$PWD/$artifacts/DeploymentConflicts
if test -f "$conflicts_file"; then
    echo "Stashing $conflicts_file"
    echo "##vso[task.uploadfile]$conflicts_file"
fi
