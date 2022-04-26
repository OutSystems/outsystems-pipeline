pipeline {
  agent any // Replace by specific label for narrowing down to OutSystems pipeline-specific agents. A dedicated agent will be allocated for the entire pipeline run.
  parameters {
    // Pipeline parameters are automatically filled by LT Trigger plugin
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
    LifeTimeAPIVersion = 2
    // Authentication Specific Variables
    AuthorizationToken = credentials('LifeTimeServiceAccountToken')
    // Environments Specification Variables
    /*
    * Pipeline for 5 Environments:
    *   DevelopmentEnvironment    -> Where you develop your applications. This should be the default environment you connect with service studio.
    *   RegressionEnvironment     -> Where your automated tests will test your applications.
    *   AcceptanceEnvironment     -> Where you run your acceptance tests of your applications.
    *   PreProductionEnvironment  -> Where you prepare your apps to go live.
    *   ProductionEnvironment     -> Where your apps are live.
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
    OSPackageVersion = '0.4.0'
  }
  stages {
    stage('Install Python Dependencies') {
      steps {
        // Create folder for storing artifacts
        sh script: "mkdir ${env.ArtifactsFolder}", label: 'Create artifacts folder'
        // Only the virtual environment needs to be installed at the system level
        sh script: 'pip3 install -q -I virtualenv --user', label: 'Install Python virtual environments'
        // Install the rest of the dependencies at the environment level and not the system level
        withPythonEnv('python3') {
          sh script: "pip3 install -U outsystems-pipeline==\"${env.OSPackageVersion}\"", label: 'Install required packages'
        }
      }
    }
    stage('Get and Deploy Latest Tags') {
      steps {
        withPythonEnv('python3') {
          echo "Pipeline run triggered remotely by '${params.TriggeredBy}' for the following applications (including tests): '${params.ApplicationScopeWithTests}'"
          // Retrieve the Applications and Environment details from LifeTime
          sh script: "python3 -m outsystems.pipeline.fetch_lifetime_data --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion}", label: 'Retrieve list of Environments and Applications'
         // Deploy the application list, with tests, to the Regression environment
          lock('deployment-plan-REG') {
            sh script: "python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.DevelopmentEnvironment}\" --destination_env \"${env.RegressionEnvironment}\" --app_list \"${params.ApplicationScopeWithTests}\"", label: "Deploy latest application tags (including tests) to ${env.RegressionEnvironment}"
          }
        }
      }
    }
    stage('Run Regression') {
      when {
        // Checks if there are any test applications in scope before running the regression stage
        expression { return params.ApplicationScope != params.ApplicationScopeWithTests }
      }
      steps {
        withPythonEnv('python3') {
          // Generate the URL endpoints of the BDD tests
          sh script: "python3 -m outsystems.pipeline.generate_unit_testing_assembly --artifacts \"${env.ArtifactsFolder}\" --app_list \"${params.ApplicationScopeWithTests}\" --cicd_probe_env ${env.ProbeEnvironmentURL} --bdd_framework_env ${env.BddEnvironmentURL}", label: 'Generate URL endpoints for BDD test suites'
          // Run those tests and generate a JUnit test report
          sh script: "python3 -m outsystems.pipeline.evaluate_test_results --artifacts \"${env.ArtifactsFolder}\"", returnStatus: true, label: 'Run BDD test suites and generate JUnit test report'          
        }
      }
      post {
        always {
          // Publish results in JUnit test report
          junit testResults: "${env.ArtifactsFolder}/junit-result.xml", allowEmptyResults: true, skipPublishingChecks: true
        }
      }
    }
    stage('Deploy Acceptance') {
      steps {     
        withPythonEnv('python3') {
          // Deploy the application list to the Acceptance environment
          lock('deployment-plan-ACC') {
            sh script: "python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.RegressionEnvironment}\" --destination_env \"${env.AcceptanceEnvironment}\" --app_list \"${params.ApplicationScope}\" --manifest \"${env.ArtifactsFolder}/deployment_data/deployment_manifest.cache\"", label: "Deploy latest application tags to ${env.AcceptanceEnvironment}"
          }
        }        
      }
    }
    stage('Accept Changes') {
      steps {
        // Define milestone before approval gate to manage concurrent builds
        milestone(ordinal: 40, label: 'before-approval')
        // Wrap the confirm option in a timeout to avoid hanging Jenkins forever
        timeout(time:1, unit:'DAYS') {
          input 'Accept changes and deploy to Production?'
        }
        // Discard previous builds that have not been accepted yet
        milestone(ordinal: 50, label: 'after-approval')
      }
    }
    stage('Deploy Dry-Run') {
      steps {
        withPythonEnv('python3') {
          // Deploy the application list to the Pre-Production environment
          lock('deployment-plan-PRE') {
            sh script: "python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.AcceptanceEnvironment}\" --destination_env \"${env.PreProductionEnvironment}\" --app_list \"${params.ApplicationScope}\" --manifest \"${env.ArtifactsFolder}/deployment_data/deployment_manifest.cache\"", label: "Deploy latest application tags to ${env.PreProductionEnvironment}"
          }
        }
      }
    }
    stage('Deploy Production') {
      steps {
        withPythonEnv('python3') {
          // Deploy the application list to the Production environment
          lock('deployment-plan-PRD') {
            sh script: "python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.PreProductionEnvironment}\" --destination_env \"${env.ProductionEnvironment}\" --app_list \"${params.ApplicationScope}\" --manifest \"${env.ArtifactsFolder}/deployment_data/deployment_manifest.cache\"", label: "Deploy latest application tags to ${env.ProductionEnvironment}"
          }
        }
      }
    }
  }
  post {
    // It will always store the cache files generated, for observability purposes, and notifies the result
    always {
      dir ("${env.ArtifactsFolder}") {
        archiveArtifacts artifacts: "**/*.cache"
      }
    }
    // If there's a failure, tries to store the Deployment conflicts (if exists), for troubleshooting purposes
    failure {
      dir ("${env.ArtifactsFolder}") {
        archiveArtifacts artifacts: 'DeploymentConflicts', allowEmptyArchive: true
      }
    }
    // Delete artifacts folder content
    cleanup {      
      dir ("${env.ArtifactsFolder}") {
        deleteDir()
      }
    }
  }
}
