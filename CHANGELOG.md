# Change Log

[//]: # (Change log default structure)
[//]: # (Changes on #date)
[//]: # (Description [optional])
[//]: # (Bug Fixes)
[//]: # (Features)
[//]: # (BREAKING CHANGES)

## May 6th, 2019

### Package naming changes

In order to prepare for the 1.0 release, there was some name changes that will break the scripts. The cd_pipelines directory was changed to examples and the custom_pipeline package was changed to outysystems_integration.

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

### Paramater refactoring

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