pipeline {
  agent any
  options { skipStagesAfterUnstable() }
  environment {
    // Artifacts Specific Variables
    ArtifactsFolder = "Artifacts"
    // LifeTime Specific Variables
    LifeTimeEnvironmentURL = "${params.LTUrl}"
    LifeTimeAPIVersion = "${params.LTApiVersion}"
    // Authentication Specific Variables
    AuthorizationToken = credentials("${params.LTToken}")
    // App list with the test apps
    ApplicationsWithTests = "${params.AppScope},${params.AppWithTests}"

    /*
    * Pipeline for 3 Environments:
    * DEV -> Where you develop you applications
    * REG -> Where you test your applications
    * PRD -> Where your apps will go live
    */

    DevEnv = "${params.DevEnv}"
    RegEnv = "${params.RegEnv}"
    PrdEnv = "${params.PrdEnv}"
  }
  stages {
    stage('Install Python Dependencies and create Artifact directory') {
      steps {
        echo "Create Artifacts Folder"
        sh "mkdir ${env.ArtifactsFolder}"
        // Only the virtual environment needs to be installed at the system level
        echo "Install Python Virtual environments"
        sh 'pip3 install -q -I virtualenv --user'
        // Install the rest of the dependencies at the environment level and not the system level
        withPythonEnv('python') {
          echo "Install Python requirements"
          sh 'pip3 install -U outsystems-pipeline'
        }
      }
    }
    stage('Get Latest Applications and Environments from LifeTime') {
      steps {
        withPythonEnv('python') {
          echo 'Retrieving latest application tags from Development environment...'
          sh "python3 -m outsystems.pipeline.fetch_lifetime_data --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion}"
        }
      }
      post {
        always {
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "*.cache", onlyIfSuccessful: true
          }
        }
      }
    }
    stage('Deploy tags to Regression Environment') {
      steps {
        withPythonEnv('python') {
          echo 'Deploying latest application tags to Regression...'
          sh "python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.DevEnv}\" --destination_env \"${env.RegEnv}\" --app_list \"${env.ApplicationsWithTests}\""
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
    stage('Run Regression tests on the Regression Environment') {
      steps {
        withPythonEnv('python') {
          echo 'Generating URLs for BDD testing...'
          sh "python3 outsystems.pipeline.generate_unit_testing_assembly --artifacts \"${env.ArtifactsFolder}\" --app_list \"${env.ApplicationsWithTests}\" --cicd_probe_env ${params.ProbeUrl} --bdd_framework_env ${params.BddUrl}"
          echo "Testing the URLs and generating the JUnit results XML..."
          sh(script: "python3 -m outsystems.pipeline.evaluate_test_results --artifacts \"${env.ArtifactsFolder}\"", returnStatus: true)
        }
      }
      post {
        always {
          withPythonEnv('python') {
            echo "Publishing JUnit test results..."
            junit(testResults: "${env.ArtifactsFolder}/junit-result.xml", allowEmptyResults: true)
          }
          dir ("${env.ArtifactsFolder}") {
            archiveArtifacts artifacts: "*_data/*.cache", onlyIfSuccessful: true
          }
        }
      }
    }
    stage('Confirm push to Production') {
      steps {
        // Wrap the confirm in a timeout to avoid hanging Jenkins forever
        timeout(time:1, unit:'DAYS') {
          input 'Accept changes and deploy to Production?'
        }
      }
    }
    stage('Deploy to Production Environment') {
      steps {
        withPythonEnv('python') {
          echo 'Deploying latest application tags to Production...'
          sh "python3 -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.RegEnv}\" --destination_env \"${env.PrdEnv}\" --app_list \"${params.AppScope}\""
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
