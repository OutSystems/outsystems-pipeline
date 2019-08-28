#!/bin/bash

if [[ $# -lt 6 ]] ; then
  echo -e '\nNot enough parameters! You need to set the necessary parameters:\n'
  echo -e '-e <python environment name> \t\t Python environment name, in order to use your pip dependencies.'
  echo -e '-a <dir name> \t\t\t\t Artifacts directory used for cache files between pipeline scripts.'
  echo -e '-f <dir name> \t\t\t\t Requirements filepath for pip.'
  echo -e '\n\nusage: ./install_dependencies.sh -e <python environment name> -a <artifacts dir> -f <dependencies file>'
  exit 1
fi

while getopts "e:a:f:" option 
do
  case "${option}"
  in
  e) env_name=${OPTARG};;
  a) artifacts=${OPTARG};;
  f) dep_file=${OPTARG};;
  esac
done

echo "Create Artifacts Folder"
mkdir $artifacts

echo "Create Python Virtual environment"
python3 -m venv $env_name --clear

echo "Switch to Virtual Environment"
source $env_name/bin/activate

echo "Install Python requirements"
pip3 install -q -I -r $dep_file

echo "Leave the Virtual Environment for now"
deactivate