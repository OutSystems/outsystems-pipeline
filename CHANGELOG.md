# Change Log

[//]: # (Change log default structure)
[//]: # (Changes on #date)
[//]: # (Description [optional])
[//]: # (Bug Fixes)
[//]: # (Features)
[//]: # (BREAKING CHANGES)

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