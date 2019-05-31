#!/bin/bash

if [[ $# -lt 10 ]] ; then
    echo -e '\nNot enough parameters! You need to set the necessary parameters:\n'
    echo -e '-e <python environment name> \t\t Python environment name, in order to use your pip dependencies.'
    echo -e '-a <dir name> \t\t\t\t Artifacts directory used for cache files between pipeline scripts.'
    echo -e '-u <url> \t\t\t\t URL for the environment containing the LifeTime. You dont need to set the API endpoint.'
    echo -e '-t <token> \t\t\t\t API Token for the LifeTime service account.'
    echo -e '-v <int> \t\t\t\t LifeTime API version number.'
    echo -e '\n\nusage: ./fetch_lt_data.sh -e <python environment name> -a <artifacts dir> -u <LT url> -t <LT token> -v <LT version>'
    exit 1
fi

while getopts "e:a:u:t:v:" option 
do
    case "${option}"
    in
        e) env_name=${OPTARG};;
        a) artifacts=${OPTARG};;
        u) lt_url=${OPTARG};;
        t) lt_token=${OPTARG};;
        v) lt_api=${OPTARG};;
    esac
done

echo "Switch to Virtual Environment"
source $env_name/bin/activate

echo "Fetch LifeTime data"
python3 outsystems/pipeline/fetch_lifetime_data.py --artifacts "$artifacts" --lt_url $lt_url --lt_token $lt_token --lt_api_version $lt_api

echo "Leave the Virtual Environment for now"
deactivate

echo "Stashing the *.cache generated in the pipeline logs"
cache_files = $artifacts/*.cache
for cfile in $cache_files
do
    echo "Caching $cfile"
    echo "##vso[task.uploadfile]$cfile"
done