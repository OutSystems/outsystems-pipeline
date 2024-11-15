# Change Log

[//]: # (Change log default structure)
[//]: # (Changes on #date)
[//]: # (Description [optional])
[//]: # (Bug Fixes)
[//]: # (Features)
[//]: # (BREAKING CHANGES)

## Nov 14th, 2024

### Parallel Deployments

The following scripts have been updated to enable creating and running parallel deployment plans:

* `deploy_latest_tags_to_target_env.py`
* `deploy_package_to_target_env.py`
* `deploy_tags_to_target_env_with_manifest.py`

To enable this feature, use the following parameter:

* `--allow_parallel_deployments`: Skips LifeTime validation for active deployment plans.

### Enhanced Pipeline Operations

New pipeline scripts have been added to streamline operations related to manifest files:

* `generate_manifest_file.py`: Generates a trigger manifest file.
* `validate_manifest_apps_exist_in_target_env.py`: Verifies that manifest applications exist in the target environment.

### Updated Package Dependencies

* Updated `requests` dependency to version 2.32.2
* Added `packaging` dependency, version 24.1

## May 16th, 2024

### Download Application Source Code

A new script was added to download platform-generated source code:

* `fetch_apps_source_code.py`

Use the following parameters to generate more human-readable outputs and facilitate the compilation of the source code:

* --friendly_package_names: source code packages with user-friendly names.
* --include_all_refs: adds to .csproj file all assemblies in the bin folder as references.
* --remove_resources_files: removes references to embedded resources files from the.csproj file.

### Solution Download and Deploy

Added new functions to leverage the recently released/improved APIs to download and deploy outsystems packages:

* `fetch_lifetime_solution_from_manifest.py` - downloads a solution file based on manifest data.
* `deploy_package_to_target_env.py` - deploys an outsystems package (solution or application) to a target environment.
* `deploy_package_to_target_env_with_osptool.py` - deploys an outsystems package (solution or application) using OSP Tool.

### Improved OSPTool Operations

OSP Tool command line calls now have live output callback and catalog mapping support.

### Updated Package Dependencies

* Updated python-dateutil dependency to version 2.9.0.post0
* Updated python-dotenv dependency to version 1.0.1

## November 15th, 2023

### Config File Support

Load configuration values from a custom file to override default values. To use this feature, use the new `--config_file` parameter to specify the configuration file path.

This enhancement is available in the following scripts:

* `apply_configuration_values_to_target_env.py`
* `continue_deployment_to_target_env.py`
* `deploy_apps_to_target_env_with_airgap.py`
* `deploy_latest_tags_to_target_env.py`
* `deploy_tags_to_target_env_with_manifest.py`
* `evaluate_test_results.py`
* `fetch_apps_packages.py`
* `fetch_lifetime_data.py`
* `scan_test_endpoints.py`
* `start_deployment_to_target_env.py`
* `tag_apps_based_on_manifest_data.py`
* `tag_modified_apps.py`

### SSL Certificate Verification

The Python `requests` module verifies SSL certificates for HTTPS requests.
Now there's a flag to enable (default value) or disable SSL certificate verification.

### Enhancements

#### Fetch Technical Debt

Enhanced the `fetch_tech_debt` script to prevent failures when all modules of an app are marked as 'ignored' in AI Mentor Studio and when an app has no security findings.

#### Tag Modified Applications

Updated `tag_modified_apps` script to tag applications based on a app_list parameter or from the trigger_manifest artifact

## October 20th, 2023

### CI/CD Probe Integration

A new script has been added to discover Client Side and Server Side BDD test flows through the CI/CD Probe:

* `scan_test_endpoints`

For enhanced BDD test execution, flexibility and security, two new parameters were added:

* --exclude_pattern: to specify the exclude pattern (using a regular expression) for the BDD test flows.
* --cicd_probe_key: to enhance the security of the CI/CD Probe API calls.

The following scripts have been updated to benefit from the new security parameter:

* `fetch_apps_packages`
* `deploy_apps_to_target_env_with_airgap`

#### Bug fixes

Fixed the issue related with loading the manifest file when the path directories included spaces on several scripts:

* `apply_configuration_values_to_target_env`
* `deploy_apps_to_target_env_with_airgap`
* `deploy_latest_tags_to_target_env`
* `deploy_tags_to_target_env_with_manifest`
* `evaluate_test_results`
* `fetch_apps_packages`
* `fetch_tech_debt`

## April 26th, 2023

### Fixed Package Dependencies

* Updated xunitparser dependency to version 1.3.4
* Removed pytest dependency

### Air Gap Deployment Operations

Air Gap operations have been improved by the incorporation of the trigger manifest artifact option:

* `deploy_apps_to_target_env_with_airgap` - enhancements to this script:
  * Added trigger manifest artifact functionality
  * Script fails if the OSP Tool deployment is not successfull
  * Added flag parameter to export with friendly package names

* `tag_apps_based_on_manifest_data` - enhancements to this script:
  * Added trigger manifest artifact functionality
  * Only tags if the trigger manifest version is greater than the version currently in use
  * Ability to tag or exclude from tagging the test applications

* `tag_modified_apps` - renamed script (from `tag_modified_applications`) in accordance with other scripts naming convention.

A new script has been added to download application packages (oap) based on the trigger manifest data:

* `fetch_apps_packages`

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
