# Change Log

[//]: # (Change log default structure)
[//]: # (Changes on #date)
[//]: # (Description [optional])
[//]: # (Bug Fixes)
[//]: # (Features)
[//]: # (BREAKING CHANGES)


## November 7th, 2022

### Fetch Application Source Code for SAST Analysis

Added new function (fetch_apps_source_code) to retrieve the source code of a set of LifeTime applications from an environment platform server. The function can also include in the project files all the assembly references found in the 'bin' directory of a given module.

**NOTE:** This function requires network connectivity to the target environment platform server.

=======

## July 4th, 2022

### LifeTime Deployment Operations

Added new functionality to provide more flexibility to handle LifeTime deployments:    

* `deploy_tags_to_target_env_with_manifest` - Add new optional input parameters:
    * `--force_two_step_deployment` - Force the execution of the second stage, in an environment where 2-stage deployments are enabled. By default, the script exits after the first stage is completed.
    * `--include_deployment_zones` - Apply deployment zone selection on the target environment based on the deployment zone defined in the trigger manifest.

* `continue_deployment_to_target_env` - Continues an existing deployment plan that is waiting for user intervention on a given environment.

## April 7th, 2022

### Trigger Manifest with configuration items

Added new functions to leverage the trigger manifest artifact provided since version 2.4.0 of Trigger Pipeline LifeTime plugin:

* `deploy_tags_to_target_env_with_manifest` - Creates and executes a deployment plan based on the application versions defined in the trigger manifest submitted as input parameter by the Trigger Pipeline plugin.
* `apply_configuration_values_to_target_env` - Sets configuration items values in a target environment based on the values found on the trigger manifest artifact.


## December 29th, 2021

### Start an existing deployment plan

Added new function (`start_deployment_to_target_env`) to start a deployment plan previously created in LifeTime UI for a target environment. The function also generates a Deployment Manifest artifact which can be reused in subsequent pipeline stages.

**NOTE:** The existing deployment plan must not have "Tag & Deploy" operations, otherwise the LifeTime API will return a 400 error when running the plan.

## April 22nd, 2021

### Code analysis with Architecture Dashboard

Added new functions to fetch code analysis results from Architecture Dashboard: 
* `fetch_tech_debt` - Fetches last code analysis information from the Architecture Dashboard API (either for the entire infrastructure or for the applications in the Manifest file).
* `fetch_tech_debt_sync` - Compares the Manifest file applications tag creation datetime with the Architecture Dashboards' last analysis datetime to assure the analysis includes the last tagged code changes.

## December 6th, 2019

### Deployment Manifest artifact

Included the generation of a Deployment Manifest artifact that can be used to promote the same application versions throughout the pipeline execution.

### Air Gap Support

Added new functions to support Air Gap deployment scenarios: 
* `deploy_apps_to_target_env_with_airgap` - Deploy OutSystems Applications to a target environment without using the Deployment API
* `tag_apps_based_on_manifest_data` - Synchronize LifeTime application versions from a Manifest file to target LifeTime

### New Jenkins Templates

New jenkins templates that include:
* Lockable resources - Each stage has a semaphore to guarantee that the target environment does not have any ongoing deployment
* Milestones - Ongoing builds of the same pipeline will be discarded whenever a newer build reaches a given pipeline milestone
* Multi-agent configuration - Ability to define different agents for different stages

#### Bug fixes

* Fixed a bug to flush print messages instead of being displayed only at the end of an execution.

## June 26th, 2019

#### Bug fixes

* Fixed a bug when the pipeline was used without tests. The evaluate test results module would give an error. Now it creates an empty junit-result.xml. The pipeline assumes that, if no tests are run, the pipeline is OK.
* Fixed bug where the pipeline would fail if there was a saved plan on LifeTime. Now, saved plans are treated as "LifeTime is busy" and can timeout the pipeline execution.

## June 5th, 2019

#### Bug fixes

* Fixed a bug with the wait cycle for LifeTime to be free that would, in some cases, lead to the pipeline attempting to deploy multiple plans in parallel, leading to errors.

## May 10th, 2019

### Application versioning mismatch

There's a scenario where the LifeTime API can have unexpected behaviors: if you tag an application with an inferior tag that was deployed somewhere in time, the search for highest tag to deploy would return the old one and not the running version on the source environment.

### Bug fixes

* Fixed the version mismatch when the tags are not done in an incremental way.
* Added notification to provide more information on what's being deployed.

## May 6th, 2019

### Package naming changes

In order to prepare for the 1.0 release, there was some name changes that will break the scripts. The cd_pipelines directory was changed to examples and the custom_pipeline package was changed to outsystems_integration.

#### Breaking changes

With the change of packages, it might have broken some integrations. If you were using code directly from the repo, please be aware that the slack integration and the pip install inside the virtual environment might fail.

## April 30th, 2019

### Slack integration

Modularized the slack integration, to allow multiple message types. Before it was only using it for Test Results.

#### Bug Fixes

* Fixed a bug where BDD tests would not have test cases and would fail when generating the test unit cases
* Fixed a bug where the Slack Notification for test errors would only display the last espace that run and not the actual espace the test belonged.

## April 3rd, 2019

### Azure DevOps support (beta)

In order to be as flexible and agnostic as possible, we decided to start building some quick start scripts for other CD engines besides Jenkins. The first one to be integrated is Azure DevOps. In this release we added some supporting scripts that you can add to your Azure DevOps pipeline. At this point in time, Azure DevOps still doesn't support pipeline as code but, when it does, we will also provide a sample.

### No more Environment Variables

All the scripts were refactored to be able to be used through parameters. This will help when we move to the Python module, allowing you to call the module functions directly by passing the necessary parameters. It should allow for easier use since you no longer have to "figure out" the environment variables. You can also integrate in your existing scripts quite easily.

#### Bug fixes

* Fixed bug where the test message would not have information when the test failed due to a bug in the unit test itself. It should now display those errors.
* Fix for WinError 5 when trying to install pip packages on Windows.

## March 11th, 2019

### Parameter refactoring

In order to increase the portability of the pipeline, it was decided to move away from the environment variables, that were being used in the base Jenkins pipeline, into script parameters. This will allow users to use the Python module by passing the parameters directly with the module call, instead of having to set all the environment variables necessary.

#### Bug Fixes

* File handling module is now OS agnostic. Previously was only built with Windows filesystem in mind;
* Bug with the deployment plan creation, where the parameters were switched, leading to errors;
* Added catch for the "NoDeploymentError" when checking for deployments. This was being triggered in environments where no deployments happened in the day the pipeline was being called;
* Added extra quotes on the python calls in Jenkinsfile, for params where a space might be included. This will allow users to create artifact dirs or have environments with spaces in the name;
* Added a better fix for the initialization of the module path, to include the outsystems module. Previously was only being done on Jenkins, local users needed to set the PYTHONPATH variable.

#### Features

CLI parameters:

* You can now use the Python module with parameters, bypassing the Environment variables;
* Those parameters can be used with short flags (-a, -e, -u, etc.) or long flags (--artifact, --lt-url, etc.);
* Every module has a built-in usage, you can use the *-h* flag to print it;
* The ammount of environment variables was substantially reduced in the Jenkinsfile.

#### Breaking changes

Since Environment variables are not being passed to the script, previous Jenkinsfiles won't work. The module methods under /pipeline can only be used now with CLI parameters. Use the *-h* for usage information.

Pipeline will work the same, so general usage should remain the same.