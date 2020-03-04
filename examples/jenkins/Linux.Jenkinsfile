pipeline {
  agent any
  parameters {
    // App List Parameters
    string(name: 'ApplicationScope', defaultValue: '', description: 'Comma-separated list of LifeTime applications to deploy.')
    string(name: 'ApplicationScopeWithTests', defaultValue: '', description: 'Comma-separated list of LifeTime applications to deploy (including test applications)')
    string(name: 'TriggeredBy', defaultValue: 'N/A', description: 'Name of LifeTime user that triggered the pipeline remotely.')
  }
  options { skipStagesAfterUnstable() }
  environment {
    // Artifacts Folder
    ArtifactsFolder = "Artifacts"
    // LifeTime Specific Variables
    LifeTimeAPIVersion = 2
    LifeTimeEnvironmentURL = 'lifetime.acmecorp.com'
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
  }
  stages {
    stage('Install Python Dependencies') {
      steps {
        echo "Create Artifacts Folder"
        sh "mkdir ${env.ArtifactsFolder}"
        // Only the virtual environment needs to be installed at the system level
        echo "Install Python Virtual environments"
        sh 'pip3 install -q -I virtualenv'
        // Install the rest of the dependencies
        withPythonEnv('python3') {
          echo "Install Python requirements"
          sh 'pip3 install -U outsystems-pipeline'
        }
      }
    }
    stage('Get Latest Tags') {
      steps {
        withPythonEnv('python3') {
          echo "Pipeline run triggered remotely by '${params.TriggeredBy}' for the following applications (including tests): '${params.ApplicationScopeWithTests}'"
          echo 'Retrieving latest application tags from Development environment...'
          sh "python3 -m outsystems.pipeline.fetch_lifetime_data --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion}"
          echo 'Deploying latest application tags to Regression...'
          lock('deployment-plan-REG') {          
            sh "python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.DevelopmentEnvironment}\" --destination_env \"${env.RegressionEnvironment}\" --app_list \"${params.ApplicationScopeWithTests}\""
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
    stage('Run Regression') {
      when { 
        expression { return params.ApplicationScope != params.ApplicationScopeWithTests } 
      }
      steps {
        withPythonEnv('python3') {
          echo 'Generating URLs for BDD testing...'
          sh "python3 -m outsystems.pipeline.generate_unit_testing_assembly --artifacts \"${env.ArtifactsFolder}\" --app_list \"${params.ApplicationScopeWithTests}\" --cicd_probe_env ${env.ProbeEnvironmentURL} --bdd_framework_env ${env.BddEnvironmentURL}"
          echo "Testing the URLs and generating the JUnit results XML..."
          sh(script: "python3 -m outsystems.pipeline.evaluate_test_results --artifacts \"${env.ArtifactsFolder}\"", returnStatus: true)
        }
      }
      post {
        always {
          withPythonEnv('python3') {
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
        withPythonEnv('python3') {
          echo 'Deploying latest application tags to Acceptance...'
          lock('deployment-plan-ACC') {          
            sh "python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.RegressionEnvironment}\" --destination_env \"${env.AcceptanceEnvironment}\" --app_list \"${params.ApplicationScope}\" --manifest \"${env.ArtifactsFolder}/deployment_data/deployment_manifest.cache\""
          }
          // Wrap the confirm in a timeout to avoid hanging Jenkins forever
          timeout(time:1, unit:'DAYS') {
          input 'Accept changes and deploy to Production?'
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
    stage('Deploy Dry-Run') {
      steps {
        withPythonEnv('python3') {
          echo 'Deploying latest application tags to Pre-Production...'
          lock('deployment-plan-PRE') {          
            sh "python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.AcceptanceEnvironment}\" --destination_env \"${env.PreProductionEnvironment}\" --app_list \"${params.ApplicationScope}\" --manifest \"${env.ArtifactsFolder}/deployment_data/deployment_manifest.cache\""
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
        withPythonEnv('python3') {
          echo 'Deploying latest application tags to Production...'
          lock('deployment-plan-PRD') {          
            sh "python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.PreProductionEnvironment}\" --destination_env \"${env.ProductionEnvironment}\" --app_list \"${params.ApplicationScope}\" --manifest \"${env.ArtifactsFolder}/deployment_data/deployment_manifest.cache\""
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
