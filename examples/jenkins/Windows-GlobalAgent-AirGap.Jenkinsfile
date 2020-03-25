pipeline {
  agent any // Replace by specific label for narrowing down to OutSystems pipeline-specific agents. A dedicated agent will be allocated for the entire pipeline run.
  parameters {
    // App List Parameters -> automatically filled by LT Trigger plugin
    string(name: 'ApplicationScope', defaultValue: '', description: 'Comma-separated list of LifeTime applications to deploy.')
    string(name: 'ApplicationScopeWithTests', defaultValue: '', description: 'Comma-separated list of LifeTime applications to deploy (including test applications)')
    string(name: 'TriggeredBy', defaultValue: 'N/A', description: 'Name of LifeTime user that triggered the pipeline remotely.')
  }
  options { skipStagesAfterUnstable() }
  environment {
    // Artifacts Folder
    ArtifactsFolder = "Artifacts"
    // LifeTime Specific Variables
    LifeTimeHostname = 'lifetime.acmecorp.com'
    LifeTime2Hostname = 'lifetime2.acmecorp.com'
    LifeTimeAPIVersion = 2
    // Authentication Specific Variables
    AuthorizationToken = credentials('LifeTimeServiceAccountToken')
    // Environments Specification Variables
    /*
    * Pipeline for 5 Environments:
    * DevelopmentEnvironment -> Where you develop your applications. This should be the default environment you connect with service studio.
    * RegressionEnvironment -> Where your automated tests will test your applications.
    * AcceptanceEnvironment -> Where you run your acceptance tests of your applications.
    * PreProductionEnvironment -> Where you prepare your apps to go live.
    * ProductionEnvironment -> Where your apps are live.
    */
    DevelopmentEnvironment = 'Development'
    RegressionEnvironment = 'Regression'
    AcceptanceEnvironment = 'Acceptance'
    PreProductionEnvironment = 'Pre-Production'
    ProductionEnvironment = 'Production'
    // Regression URL Specification
    ProbeEnvironmentURL = 'https://regression-env.acmecorp.com/'
    BddEnvironmentURL = 'https://regression-env.acmecorp.com/'
    // OutSystems PyPI package version
    OSPackageVersion = '0.3.1'
    // AirGap Specific Variables
    OSPToolPath = 'C:\\Program Files\\Common Files\\OutSystems\\11.0\\OSPTool.com'
    AirGapUser = 'air_gap_user'
    AirGapPass = credentials('AirGapPass')
    PreProductionEnvironmentHostName = 'preprod.acmecorp.com'
  }
  stages {
    stage('Install Python Dependencies') {
      steps {
        echo "Create ${env.ArtifactsFolder} Folder"
        // Create folder for storing artifacts
        powershell "mkdir ${env.ArtifactsFolder}"
        // Only the virtual environment needs to be installed at the system level
        echo "Install Python Virtual environments"
        powershell 'pip install -q -I virtualenv --user'
        // Install the rest of the dependencies at the environment level and not the system level
        withPythonEnv('python') {
          echo "Install Python requirements"
          powershell "pip install -U outsystems-pipeline==\"${env.OSPackageVersion}\""
        }
      }
    }
    stage('Get and Deploy Latest Tags') {
      steps {
        withPythonEnv('python') {
          echo "Pipeline run triggered remotely by '${params.TriggeredBy}' for the following applications (including tests): '${params.ApplicationScopeWithTests}'"
          echo 'Retrieving latest application tags from Development environment...'
          // Retrive the Applications and Environment details from the Source environment
          powershell "python -m outsystems.pipeline.fetch_lifetime_data --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion}"
          echo 'Deploying latest application tags to Regression...'
          // Deploy the application list, with tests, to the Regression environment
          lock('deployment-plan-REG') {
            powershell "python -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.DevelopmentEnvironment}\" --destination_env \"${env.RegressionEnvironment}\" --app_list \"${params.ApplicationScopeWithTests}\""
          }
        }
      }
      post {
        // It will always store the cache files generated, for observability purposes
        always {
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "*.cache", onlyIfSuccessful: true
            archiveArtifacts artifacts: "*_data/*.cache", onlyIfSuccessful: true
          }
        }
        // If there's a failure, tries to store the Deployment conflicts (if exists), for observability and troubleshooting purposes
        failure {
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "DeploymentConflicts"
          }
        }
      }
    }
    stage('Run Regression') {
      when {
        expression { return params.ApplicationScope != params.ApplicationScopeWithTests }
      }
      steps {
        withPythonEnv('python') {
          echo 'Generating URLs for BDD testing...'
          // Generate the URL endpoints of the BDD tests
          powershell "python -m outsystems.pipeline.generate_unit_testing_assembly --artifacts \"${env.ArtifactsFolder}\" --app_list \"${params.ApplicationScopeWithTests}\" --cicd_probe_env ${env.ProbeEnvironmentURL} --bdd_framework_env ${env.BddEnvironmentURL}"
          echo "Testing the URLs and generating the JUnit results XML..."
          // Run those tests and generate a JUNIT test report
          powershell(script: "python -m outsystems.pipeline.evaluate_test_results --artifacts \"${env.ArtifactsFolder}\"", returnStatus: true)
        }
      }
      post {
        always {
          withPythonEnv('python') {
            echo "Publishing JUnit test results..."
            junit(testResults: "${env.ArtifactsFolder}\\junit-result.xml", allowEmptyResults: true)
          }
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "*_data/*.cache", onlyIfSuccessful: true
          }
        }
      }
    }
    stage('Accept Changes') {
      steps {
        withPythonEnv('python') {
          echo 'Deploying latest application tags to Acceptance...'
          // Deploy the application list, without tests, to the Acceptance environment
          lock('deployment-plan-ACC') {
            powershell "python -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.RegressionEnvironment}\" --destination_env \"${env.AcceptanceEnvironment}\" --app_list \"${params.ApplicationScope}\" --manifest \"${env.ArtifactsFolder}\\deployment_data\\deployment_manifest.cache\""
          }
        }
        // Define milestone before approval gate to manage concurrent builds
        milestone(ordinal: 40, label: 'before-approval')
        // Wrap the confirm option in a timeout to avoid hanging Jenkins forever
        timeout(time:1, unit:'DAYS') {
          input 'Accept changes and deploy to Production?'
        }
        // Discard previous builds that have not been accepted yet
        milestone(ordinal: 50, label: 'after-approval')
      }
      post {
        always {
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "*_data/*.cache", onlyIfSuccessful: true
          }
        }
        failure {
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "DeploymentConflicts"
          }
        }
      }
    }
    stage('Deploy Dry-Run (Air Gap)') {
      steps {
        withPythonEnv('python') {
          echo 'Deploying latest application tags to Pre-Production...'
          // Deploy the application list, without tests, to the Pre-Production environment
          lock('deployment-plan-PRE') {
            powershell "python -m outsystems.pipeline.deploy_apps_to_target_env_with_airgap --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.AcceptanceEnvironment}\" --destination_env \"${env.PreProductionEnvironmentHostName}\" --app_list \"${params.ApplicationScope}\" --manifest \"${env.ArtifactsFolder}\\deployment_data\\deployment_manifest.cache\" --osp_tool_path \"${env.OSPToolPath}\" --airgap_user \"${env.AirGapUser}\" --airgap_pass \"${env.AirGapPass}\" --cicd_probe_url \"${env.ProbeEnvironmentURL}\""
          }
        }
      }
      post {
        always {
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "*_data/*.cache", onlyIfSuccessful: true
          }
        }
        failure {
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "DeploymentConflicts"
          }
        }
      }
    }
    stage('Deploy Production') {
      steps {
        withPythonEnv('python') {
          echo 'Deploying latest application tags to Production...'
          // Deploy the application list, without tests, to the Production environment
          lock('deployment-plan-PRD') {
            powershell "python -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTime2Hostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.PreProductionEnvironment}\" --destination_env \"${env.ProductionEnvironment}\" --app_list \"${params.ApplicationScope}\" --manifest \"${env.ArtifactsFolder}\\deployment_data\\deployment_manifest.cache\""
          }
        }
      }
      post {
        always {
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "*_data/*.cache", onlyIfSuccessful: true
          }
        }
        failure {
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "DeploymentConflicts"
          }
        }
      }
    }
  }
  post {
    always {
      echo 'Deleting artifacts folder content...'
      dir ("${env.ArtifactsFolder}") {
        deleteDir()
      }
    }
  }
}
