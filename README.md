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
* **LTUrl**: URL for LifeTime, without the API endpoint and the trailing slash and the HTTPS protocol (`https://`). Select the type **String**
* **LTToken**: Token that you'll use to interact with LifeTime's API. It should be created, on LifeTime, as a Service Account and given enough priviledges to deploy the code until production. Select type **Secret Text**
* **DevEnv**: Name of the development environment, as shown in LifeTime. Select the type **String**
* **RegEnv**: Name of the regression environment, as shown in LifeTime. Select the type **String**
* **QAEnv**: Name of the quality assurance environment, as shown in LifeTime. Select the type **String**
* **PpEnv**: Name of the pre-production environment, as shown in LifeTime. Select the type **String**
* **PrdEnv**: Name of the production environment, as shown in LifeTime. Select the type **String**
* **SlackChannel**: (Optional if you use the slack plugin) Name of the Slack Channel(s) you wish to send notifications. For multiple channels, use a comma-separated list. *Example:* Channel1,Channel-2. Select the type **String**
* **ProbeUrl**: URL of the environment, without the API part, of the CICD Probe (e.g. `https://<regression_hostname>`). Select the type **String**
* **BddUrl**: URL of the environment, without the API part, of the BDD Framework (e.g. `https://<regression_hostname>`). Select the type **String**

Then select **Trigger builds remotely (e.g., from scripts)**. This will allow you to queue a job remotely, through the Trigger plugin on LifeTime. A box will appear for you to insert the token. Remember that token since you will have to use it on the LifeTime Trigger plugin.

Finally, you'll have to set which pipeline file to load (the Jenkinsfile). Since the Jenkinsfile is part of the source code, you just need to point to the same GitHub repo. Select **Pipeline script from SCM**, then **Git** as your SCM. In the Repository URL, set the **project url**. The URL must have the git protocol forced (using git@), followed by the link to the .git without the protocol (https or ssh). Example: git@github.com:OutSystems/outsystems-pipeline.git

The credentials must be inserted on Jenkins beforehand (or you have to click on the Add button). You must generate a Keypair for the GIT repo in question. For GitHub, go to `https://github.com/\<ORG\>/\<ProjectName\>/settings/keys`.

If you're using this repo as a source for the pipeline code, the sample Jenkinsfile should be under cd_pipelines > jenkins > Jenkinsfile. If you're using the Python Package, you can point it to your own Jenkinsfile. Use the Jenkinsfile on this repository as a point of reference.

When you're ready, save the pipeline.

## Azure DevOps Pipeline Setup

**Beta - Subject to change**
To create a pipeline on Azure DevOps, you can use the scripts defined under **cd_pipelines > azure_devops**. You can use either Linux or Windows as your agents. If you use Linux, use the *.sh scripts, if you use Windows use the *.ps1 scripts.

In order to run it on Azure DevOps you'll create either **Bash** tasks (for Linux) or **PowerShell** tasks (for Windows).

If your LifeTime environment is not exposed to the Internet, you'll need to install an Azure DevOps agent on your internal network. Alternatively, you can expose your LifeTime to Azure DevOps Hosted Agents IPs. The process to install your own local agent is described [here](https://docs.microsoft.com/en-us/azure/devops/pipelines/agents/agents?view=azure-devops#install).

Since Azure DevOps doesn't support Release Pipelines as Code yet, we can't give you a working example, so the way you set up your pipeline is left as an exercise. But there are still parameters you need to setup. Under the variable tab, you can choose either to use Pipeline variables or Variable groups and link those to specific environments. Again, is left to your choice at this moment. We will describe the process with *Pipeline variables*.

The following variables are to be set for the Release Scope:

* **AppScope**: Name of the App(s) without the tests, to deploy. If you add more than one, use a comma to separate them. *Example:* App1,App2 With Spaces,App3_With_Underscores.
* **AppWithTests**: Name of the App(s) without the tests, to deploy. If you add more than one, use a comma to separate them. *Example:* App1,App2 With Spaces,App3_With_Underscores.
* **ArtifactsFolder**: Name of the Artifacts folder, where the pipeline will store the cache files between Jobs.
* **BDDFrameworkURL**: URL of the environment, without the API part, of the BDD Framework (e.g. `https://<regression_hostname>`).
* **CICDProbeURL**: URL of the environment, without the API part, of the CICD Probe (e.g. `https://<regression_hostname>`).
* **DashBoardUrl**: (Optional if you use the slack plugin) URL for the dashboard link you'll receive in the slack notification.
* **DeployMsg**: Message that will be written on the deployment plan in LifeTime.
* **DevEnv**: Name of the development environment, as shown in LifeTime.
* **RegEnv**: Name of the regression environment, as shown in LifeTime.
* **QAEnv**: Name of the quality assurance environment, as shown in LifeTime.
* **PPEnv**: Name of the pre-production environment, as shown in LifeTime.
* **PRDEnv**: Name of the production environment, as shown in LifeTime.
* **JobName**: (Optional if you use the slack plugin) Name of the Pipeline you're deploying.
* **LTAPIVersion**: LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2.
* **LTToken**: Token that you'll use to interact with LifeTime's API. It should be created, on LifeTime, as a Service Account and given enough priviledges to deploy the code until production. **Important**: Set this as a secret type, to avoid having it shown on the logs.
* **LTURL**: URL for LifeTime, without the API endpoint and the trailing slash and the HTTPS protocol (`https://`).
* **PipelineType**: (Optional if you use the slack plugin) Since this Azure DevOps, set it as *azure*.
* **PythonEnvName**: Name of the Python Environment where the pipeline dependencies will be installed. Example: OSPipeline
* **SlackChannels**: (Optional if you use the slack plugin) Name of the Slack Channel(s) you wish to send notifications. For multiple channels, use a comma-separated list. *Example:* Channel1,Channel-2.
* **SlackHook**: (Optional if you use the slack plugin) Slack hook to make API calls. **Important**: Set this as a secret type, to avoid having it shown on the logs.

The division between Environments is up to you (at this moment) but we suggest a division similar to the Jenkins one:

* Install Python Dependencies and create Artifact directory
* Get Latest Applications and Environments from LifeTime
* Deploy tags to Regression Environment
* Run Regression tests on the Regression Environment
* Deploy tags to Quality Assurance Environment
* Deploy tags to PP Environment
* Deploy tags to PRD Environment

Since Azure DevOps' Python tasks don't support Python Environments, we need to wrap our Python calls in scripts. The following Jobs will need to be setup on the pipeline:

* Install Python Dependencies and create Artifact directory
  * One Job with either one Linux agent pool or Windows Agent pool
  * One task (either **Bash** for Linux agents or **PowerShell** for Windows agents)
  * Linux:
    * Script path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/install_dependencies.sh`
    * Arguments: `-e "$(PythonEnvName)" -a "$(ArtifactsFolder)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * Windows:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/install_dependencies.ps1`
    * Arguments: `-PythonEnv "$(PythonEnvName)" -ArtifactDir "$(ArtifactsFolder)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
* Get Latest Applications and Environments from LifeTime
  * One Job with either one Linux agent pool or Windows Agent pool
  * One task (either **Bash** for Linux agents or **PowerShell** for Windows agents)
  * Linux:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/fetch_lt_data.sh`
    * Arguments: `-e "$(PythonEnvName)" -a "$(ArtifactsFolder)" -u $(LTURL) -t $(LTToken) -v $(LTAPIVersion)`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * Windows:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/fetch_lt_data.ps1`
    * Arguments: `-PythonEnv "$(PythonEnvName)" -ArtifactDir "$(ArtifactsFolder)" -LifeTimeUrl $(LTURL) -LifeTimeToken $(LTToken) -LifeTimeApi $(LTAPIVersion)`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
* Deploy tags to Regression Environment
  * One Job with either one Linux agent pool or Windows Agent pool
  * One task (either **Bash** for Linux agents or **PowerShell** for Windows agents)
  * Linux:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/deploy_apps_to_env.sh`
    * Arguments: `-e "$(PythonEnvName)" -a "$(ArtifactsFolder)" -u $(LTURL) -t $(LTToken) -v $(LTAPIVersion) -s "$(DevEnv)" -d "$(RegEnv)" -l "$(AppScope),$(AppWithTests)" -m "$(DeployMsg)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * Windows:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/deploy_apps_to_env.ps1`
    * Arguments: `-PythonEnv "$(PythonEnvName)" -ArtifactDir "$(ArtifactsFolder)" -LifeTimeUrl $(LTURL) -LifeTimeToken $(LTToken) -LifeTimeApi $(LTAPIVersion) -SourceEnv "$(DevEnv)" -DestEnv "$(RegEnv)" -AppList "$(AppScope),$(AppWithTests)" -DeployMsg "$(DeployMsg)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
* Run Regression tests on the Regression Environment
  * One Job with either one Linux agent pool or Windows Agent pool
  * One task (either **Bash** for Linux agents or **PowerShell** for Windows agents)
  * Linux:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/build_test_endpoints.sh`
    * Arguments: `-e "$(PythonEnvName)" -a "$(ArtifactsFolder)" -l "$(AppWithTests)" -c $(CICDProbeURL) -b $(BDDFrameworkURL)`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * Windows:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/build_test_endpoints.ps1`
    * Arguments: `-PythonEnv "$(PythonEnvName)" -ArtifactDir "$(ArtifactsFolder)" -AppList "$(AppWithTests)" -BddUrl $(BDDFrameworkURL) -CicdUrl $(CICDProbeURL)`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * One task (either **Bash** for Linux agents or **PowerShell** for Windows agents)
  * Linux:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/running_test_endpoints.sh`
    * Arguments: `-e "$(PythonEnvName)" -a "$(ArtifactsFolder)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * Windows:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/running_test_endpoints.ps1`
    * Arguments: `-PythonEnv "$(PythonEnvName)" -ArtifactDir "$(ArtifactsFolder)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * One task: **Publish Test Results**
    * Test result format: `JUnit`
    * Test results files: `**/junit-result.xml`
    * Search Folder: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/$(ArtifactsFolder)`
    * Fail if there are test failures: `true`
  * (Optional if you use the slack plugin) One task (either **Bash** for Linux agents or **PowerShell** for Windows agents)
  * Linux:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/send_notifications_slack.sh`
    * Arguments: `-e "$(PythonEnvName)" -a "$(ArtifactsFolder)" -s $(SlackHook) -c "$(SlackChannels)" -p "$(PipelineType)" -j "$(JobName)" -d $(DashBoardUrl)`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * Windows:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/send_notifications_slack.ps1`
    * Arguments: `-PythonEnv "$(PythonEnvName)" -ArtifactDir "$(ArtifactsFolder)" -SlackHook $(SlackHook) -SlackChannels "$(SlackChannels)" -PipelineType "$(PipelineType)" -JobName "$(JobName)" -DashboardUrl $(DashBoardUrl)`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
* Deploy tags to Quality Assurance Environment
  * One Agentless Job
  * One task: **Manual Intervention**
    * Instructions: `Do you approve deployment to QA?`
    * Notify Users: `<user list>`
  * One Job with either one Linux agent pool or Windows Agent pool
  * One task (either **Bash** for Linux agents or **PowerShell** for Windows agents)
  * Linux:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/deploy_apps_to_env.sh`
    * Arguments: `-e "$(PythonEnvName)" -a "$(ArtifactsFolder)" -u $(LTURL) -t $(LTToken) -v $(LTAPIVersion) -s "$(RegEnv)" -d "$(QAEnv)" -l "$(AppScope),$(AppWithTests)" -m "$(DeployMsg)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * Windows:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/deploy_apps_to_env.ps1`
    * Arguments: `-PythonEnv "$(PythonEnvName)" -ArtifactDir "$(ArtifactsFolder)" -LifeTimeUrl $(LTURL) -LifeTimeToken $(LTToken) -LifeTimeApi $(LTAPIVersion) -SourceEnv "$(RegEnv)" -DestEnv "$(QAEnv)" -AppList "$(AppScope),$(AppWithTests)" -DeployMsg "$(DeployMsg)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
* Deploy tags to PP Environment
  * One Agentless Job
  * One task: **Manual Intervention**
    * Instructions: `Do you approve deployment to PP and Production?`
    * Notify Users: `<user list>`
  * One Job with either one Linux agent pool or Windows Agent pool
  * One task (either **Bash** for Linux agents or **PowerShell** for Windows agents)
  * Linux:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/deploy_apps_to_env.sh`
    * Arguments: `-e "$(PythonEnvName)" -a "$(ArtifactsFolder)" -u $(LTURL) -t $(LTToken) -v $(LTAPIVersion) -s "$(QAEnv)" -d "$(PPEnv)" -l "$(AppScope),$(AppWithTests)" -m "$(DeployMsg)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * Windows:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/deploy_apps_to_env.ps1`
    * Arguments: `-PythonEnv "$(PythonEnvName)" -ArtifactDir "$(ArtifactsFolder)" -LifeTimeUrl $(LTURL) -LifeTimeToken $(LTToken) -LifeTimeApi $(LTAPIVersion) -SourceEnv "$(QAEnv)" -DestEnv "$(PPEnv)" -AppList "$(AppScope),$(AppWithTests)" -DeployMsg "$(DeployMsg)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
* Deploy tags to PRD Environment
  * One Job with either one Linux agent pool or Windows Agent pool
  * One task (either **Bash** for Linux agents or **PowerShell** for Windows agents)
  * Linux:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/deploy_apps_to_env.sh`
    * Arguments: `-e "$(PythonEnvName)" -a "$(ArtifactsFolder)" -u $(LTURL) -t $(LTToken) -v $(LTAPIVersion) -s "$(PPEnv)" -d "$(PRDEnv)" -l "$(AppScope),$(AppWithTests)" -m "$(DeployMsg)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`
  * Windows:
    * Script Path: `$(System.DefaultWorkingDirectory)/$(Release.PrimaryArtifactSourceAlias)/cd_pipelines/azure_devops/deploy_apps_to_env.ps1`
    * Arguments: `-PythonEnv "$(PythonEnvName)" -ArtifactDir "$(ArtifactsFolder)" -LifeTimeUrl $(LTURL) -LifeTimeToken $(LTToken) -LifeTimeApi $(LTAPIVersion) -SourceEnv "$(PPEnv)" -DestEnv "$(PRDEnv)" -AppList "$(AppScope),$(AppWithTests)" -DeployMsg "$(DeployMsg)"`
    * Working Directory: `$(Release.PrimaryArtifactSourceAlias)`

**Important**

You should clone the folder *cd_pipelines* > *azure_devops* to your local repository. You can clone it to GitHub or Azure DevOps repository. If you're using GitHub, you'll need to create a connection to GitHub on Azure DevOps.
The Release pipeline artifact will be the direct connection to the repository. Since you don't need to compile code, you don't need a Build Pipeline. 
If you use more than one artifact make sure that the artifact with the pipeline scripts is the **primary** artifact!

## OutSystems Platform Setup

You'll need to install the following applications on your OutSystems environment:

* Under outsystems_components > lifetime you will find the trigger application, that will run the jobs from LifeTime with one click. Install it on your LifeTime environment;
* Under outsystems_components > regression_environment you will find the CICD probe that will find the tests to run for a given app. Install it on your regression environment;

## Change Log

See the change log [here](../master/CHANGELOG.md)