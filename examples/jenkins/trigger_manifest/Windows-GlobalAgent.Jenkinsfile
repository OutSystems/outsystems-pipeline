import groovy.json.*
// Function to check if there are Test Apps within the Trigger Manifest artifact
boolean hasTestApplications(){
  result = false
  json = readJSON file: "${env.ArtifactsFolder}\\${env.ManifestFolder}\\${env.ManifestFile}"
  json['ApplicationVersions'].each { key, value ->
    if (key.IsTestApplication) { result = true }
  }

  return result
}
// Function to get the Application List from the Trigger Manifest artifact
def getApplicationList(){
  app_list = ""
  json = readJSON file: "${env.ArtifactsFolder}\\${env.ManifestFolder}\\${env.ManifestFile}"
  json['ApplicationVersions'].each { key, value -> app_list += key.ApplicationName + "," }
  // remove last comma from the application comma-separated list
  return app_list[0..-2]
}

pipeline {
  agent any // Replace by specific label for narrowing down to OutSystems pipeline-specific agents. A dedicated agent will be allocated for the entire pipeline run.
  parameters {
    // Pipeline parameters are automatically filled by LT Trigger plugin
    string(name: 'TriggerManifest', defaultValue: '', description: 'Trigger manifest artifact (in JSON format) for the current pipeline run.')
    string(name: 'TriggeredBy', defaultValue: 'N/A', description: 'Name of LifeTime user that triggered the pipeline remotely.')
  }
  options { skipStagesAfterUnstable() }
  environment {
    // Artifacts Folder
    ArtifactsFolder = "Artifacts"
    // Trigger Manifest Specific Variables
    ManifestFolder = "trigger_manifest"
    ManifestFile = "trigger_manifest.json"
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
    DevelopmentEnvironmentLabel = 'DEV'
    RegressionEnvironmentLabel = 'REG'
    AcceptanceEnvironmentLabel = 'ACC'
    PreProductionEnvironmentLabel = 'PRE'
    ProductionEnvironmentLabel = 'PRD'
    // Regression URL Specification
    CICDProbeEnvironmentURL = 'https://regression-env.acmecorp.com/'
    BDDFrameworkEnvironmentURL = 'https://regression-env.acmecorp.com/'
    // OutSystems PyPI package version
    OSPackageVersion = '0.6.0'
  }
  stages {
    stage('Install Python Dependencies') {
      steps {
        cleanWs()
        // Create folder for storing artifacts
        powershell script: "mkdir ${env.ArtifactsFolder}", label: 'Create artifacts folder'
        dir ("${env.ArtifactsFolder}") {
          // Create manifest folder
          powershell script: "mkdir ${env.ManifestFolder}", label: 'Create trigger manifest folder'
          // Create Trigger Manifest artifact
          powershell script: "('${params.TriggerManifest}') | Out-File -FilePath \"${env.ManifestFolder}\\${env.ManifestFile}\" -Encoding default", label: 'Create trigger manifest file'
        }
        // Only the virtual environment needs to be installed at the system level
        powershell script: 'pip install -q -I virtualenv --user', label: 'Install Python virtual environments'
        // Install the rest of the dependencies at the environment level and not the system level
        withPythonEnv('python') {
          powershell script: "pip install -U outsystems-pipeline==\"${env.OSPackageVersion}\"", label: 'Install required packages'
        }
      }
    }
    stage('Get and Deploy Latest Tags') {
      steps {
        withPythonEnv('python') {
          echo "Pipeline run triggered remotely by '${params.TriggeredBy}'"
         // Deploy the application list, with tests, to the Regression environment
          lock('deployment-plan-REG') {
            powershell script: "python -m outsystems.pipeline.deploy_tags_to_target_env_with_manifest --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken}  --lt_api_version ${env.LifeTimeAPIVersion} --source_env_label ${env.DevelopmentEnvironmentLabel} --destination_env_label ${env.RegressionEnvironmentLabel} --include_test_apps --manifest_file \"${env.ArtifactsFolder}\\${env.ManifestFolder}\\${env.ManifestFile}\"", label: "Deploy latest application tags (including tests) to ${env.RegressionEnvironmentLabel}"
          }
        }
      }
    }
    stage('Run Regression') {
      when {
        // Checks if there are any test applications in scope before running the regression stage
        expression { return hasTestApplications() }
      }
      steps {
        withPythonEnv('python') {
          // Generate the URL endpoints of the BDD tests
          powershell script: "python -m outsystems.pipeline.generate_unit_testing_assembly --artifacts \"${env.ArtifactsFolder}\" --app_list \"${getApplicationList()}\" --cicd_probe_env ${env.CICDProbeEnvironmentURL} --bdd_framework_env ${env.BDDFrameworkEnvironmentURL}", label: 'Generate URL endpoints for BDD test suites'
          // Run those tests and generate a JUnit test report
          powershell script: "python -m outsystems.pipeline.evaluate_test_results --artifacts \"${env.ArtifactsFolder}\"", returnStatus: true, label: 'Run BDD test suites and generate JUnit test report'          
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
        withPythonEnv('python') {
          // Deploy the application list to the Acceptance environment
          lock('deployment-plan-ACC') {
            powershell script: "python -m outsystems.pipeline.deploy_tags_to_target_env_with_manifest --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env_label ${env.RegressionEnvironmentLabel} --destination_env_label ${env.AcceptanceEnvironmentLabel} --manifest_file \"${env.ArtifactsFolder}\\${env.ManifestFolder}\\${env.ManifestFile}\"", label: "Deploy latest application tags to ${env.AcceptanceEnvironmentLabel}"
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
        withPythonEnv('python') {
          // Deploy the application list to the Pre-Production environment
          lock('deployment-plan-PRE') {
            powershell script: "python -m outsystems.pipeline.deploy_tags_to_target_env_with_manifest --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env_label ${env.AcceptanceEnvironmentLabel} --destination_env_label ${env.PreProductionEnvironmentLabel} --manifest_file \"${env.ArtifactsFolder}\\${env.ManifestFolder}\\${env.ManifestFile}\"", label: "Deploy latest application tags to ${env.PreProductionEnvironmentLabel}"
          }
        }
      }
    }
    stage('Deploy Production') {
      steps {
        withPythonEnv('python') {
          // Deploy the application list to the Production environment
          lock('deployment-plan-PRD') {
            powershell script: "python -m outsystems.pipeline.deploy_tags_to_target_env_with_manifest --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeHostname} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env_label ${env.PreProductionEnvironmentLabel} --destination_env_label ${env.ProductionEnvironmentLabel} --manifest_file \"${env.ArtifactsFolder}\\${env.ManifestFolder}\\${env.ManifestFile}\"", label: "Deploy latest application tags to ${env.ProductionEnvironmentLabel}"
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
        archiveArtifacts artifacts: "${env.ManifestFolder}\\${env.ManifestFile}"
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
