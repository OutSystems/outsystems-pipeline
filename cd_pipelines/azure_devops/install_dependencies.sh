#!/bin/bash

echo "Create Artifacts Folder"
mkdir $ARTIFACTSFOLDER

echo "Create Python Virtual environment"
python3 -m venv $ENVNAME --clear

echo "Switch to Virtual Environment"
source $ENVNAME/bin/activate

echo "Install Python requirements"
pip3 install -q -I -r cd_pipelines/jenkins/requirements.txt

echo "Leave the Virtual Environment for now"
deactivate