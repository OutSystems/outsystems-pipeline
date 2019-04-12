# OutSystems Regression Testing Pipeline [![Build Status](https://dev.azure.com/os-pipeline/OutSystems-Pipeline/_apis/build/status/OutSystems.outsystems-pipeline?branchName=master)](https://dev.azure.com/os-pipeline/OutSystems-Pipeline/_build/latest?definitionId=1&branchName=master)

Open source project to enable continuous testing using OutSystems.

## Getting started

To setup your local environment, check the install guide [here](../master/INSTALL.md).

## Jenkins Pipeline Setup

Assuming your Jenkins server is already installed and configured, let's jump straight into the pipeline.

On the main dashboard, click **New Item** on the left side menu. Choose your project name and select the **Pipeline** option. You will then be presented with the pipeline configuration.

Select **This project is parameterized**. Since the Jenkinsfile, that supports the pipeline, has some variables, you'll have to set them here. If you check the Jenkinsfile, it should state, in the initial environment configuration, what variables you'll need. Here is the list:

* **GitKey**: (Optional) Git SSH Key. Only needed if you're not using the python package and you want to use the source code directly. Select the type **SSH Username and Key**
* **AppScope**: Name of the App(s) without the tests, to deploy. If you add more than one, use a comma to separate them. *Example:* App1,App2 With Spaces,App3_With_Underscores. Select the type **String**
* **AppWithTests**: Name of the App(s) with the tests, to deploy. If you add more than one, use a comma to separate them. *Example:* App1,App2 With Spaces,App3_With_Underscores. Select the type **String**
* **LTApiVersion**: LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Select the type **String**
* **LTUrl**: URL for LifeTime, without the API endpoint and the trailing slash and the HTTPS protocol (https://). Select the type **String**
* **LTToken**: Token that you'll use to interact with LifeTime's API. It should be created, on LifeTime, as a Service Account and given enough priviledges to deploy the code until production. Select type **Secret Text**
* **DevEnv**: Name of the development environment, as shown in LifeTime. Select the type **String**
* **RegEnv**: Name of the regression environment, as shown in LifeTime. Select the type **String**
* **QAEnv**: Name of the quality assurance environment, as shown in LifeTime. Select the type **String**
* **PpEnv**: Name of the pre-production environment, as shown in LifeTime. Select the type **String**
* **PrdEnv**: Name of the production environment, as shown in LifeTime. Select the type **String**
* **SlackChannel**: (Optional if you use the slack plugin) Name of the Slack Channel(s) you wish to send notifications. For multiple channels, use a comma-separated list. *Example:* Channel1,Channel-2. Select the type **String**
* **ProbeUrl**: URL of the environment, without the API part, of the CICD Probe (e.g. https://<regression_hostname>). Select the type **String**
* **BddUrl**: URL of the environment, without the API part, of the BDD Framework (e.g. https://<regression_hostname>). Select the type **String**

Then select **Trigger builds remotely (e.g., from scripts)**. This will allow you to queue a job remotely, through the Trigger plugin on LifeTime. A box will appear for you to insert the token. Remember that token since you will have to use it on the LifeTime Trigger plugin.

Finally, you'll have to set which pipeline file to load (the Jenkinsfile). Since the Jenkinsfile is part of the source code, you just need to point to the same GitHub repo. Select **Pipeline script from SCM**, then **Git** as your SCM. In the Repository URL, set the **project url**. The URL must have the git protocol forced (using git@), followed by the link to the .git without the protocol (https or ssh). Example: git@github.com:OutSystems/outsystems-pipeline.git

The credentials must be inserted on Jenkins beforehand (or you have to click on the Add button). You must generate a Keypair for the GIT repo in question. For GitHub, go here: <https://github.com/OutSystems/outsystems-pipeline/settings/> keys (or https://github.com/\<ORG\>/\<ProjectName\>/settings/keys )

If you're using this repo as a source for the pipeline code, the sample Jenkinsfile should be under cd_pipelines > jenkins > Jenkinsfile. If you're using the Python Package, you can point it to your own Jenkinsfile. Use the Jenkinsfile on this repository as a point of reference.

When you're ready, save the pipeline.

## Azure DevOps Pipeline Setup

TODO

## OutSystems Platform Setup

You'll need to install the following applications on your OutSystems environment:

* Under outsystems_components > lifetime you will find the trigger application, that will run the jobs from LifeTime with one click. Install it on your LifeTime environment;
* Under outsystems_components > regression_environment you will find the CICD probe that will find the tests to run for a given app. Install it on your regression environment;

## Change Log

See the change log [here](../master/CHANGELOG.md)