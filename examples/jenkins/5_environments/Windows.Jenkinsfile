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
    * Pipeline for 5 Environments:
    * DEV -> Where you develop you applications
    * REG -> Where you test your applications
    * QA -> Where you run your acceptance of your applications
    * PP -> Where you prepare your apps to go live
    * PRD -> Where your apps will go live
    */

    DevEnv = "${params.DevEnv}"
    RegEnv = "${params.RegEnv}"
    QaEnv = "${params.QAEnv}"
    PpEnv = "${params.PpEnv}"
    PrdEnv = "${params.PrdEnv}"


  }
  stages {
    stage('Install Python Dependencies and create Artifact directory') {
      steps {
        echo "Create Artifacts Folder"
        powershell "mkdir ${env.ArtifactsFolder}"
        // Only the virtual environment needs to be installed at the system level
        echo "Install Python Virtual environments"
        powershell 'pip install -q -I virtualenv --user'
        // Install the rest of the dependencies at the environment level and not the system level
        withPythonEnv('python') {
          echo "Install Python requirements"
          powershell 'pip install -U outsystems-pipeline'
        }
      }
    }
    stage('Get Latest Applications and Environments from LifeTime') {
      steps {
        withPythonEnv('python') {
          echo 'Retrieving latest application tags from Development environment...'
          powershell "python -m outsystems.pipeline.fetch_lifetime_data --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion}"
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
          powershell "python -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.DevEnv}\" --destination_env \"${env.RegEnv}\" --app_list \"${env.ApplicationsWithTests}\""
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
          powershell "python -m outsystems.pipeline.generate_unit_testing_assembly --artifacts \"${env.ArtifactsFolder}\" --app_list \"${env.ApplicationsWithTests}\" --cicd_probe_env ${params.ProbeUrl} --bdd_framework_env ${params.BddUrl}"
          echo "Testing the URLs and generating the JUnit results XML..."
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
    stage('Deploy to Quality Assurance Environment') {
      steps {
        // Wrap the confirm in a timeout to avoid hanging Jenkins forever
        timeout(time:1, unit:'DAYS') {
          input 'Deploy changes to Acceptance?'
        }
        withPythonEnv('python') {
          echo 'Deploying latest application tags to Acceptance...'
          powershell "python -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.RegEnv}\" --destination_env \"${env.QaEnv}\" --app_list \"${params.AppScope}\""
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
    stage('Confirm push to Pre-Production and Production') {
      steps {
        // Wrap the confirm in a timeout to avoid hanging Jenkins forever
        timeout(time:1, unit:'DAYS') {
          input 'Accept changes and deploy to Pre- and Production?'
        }
      }
    }
    stage('Deploy to Pre-Production Environment') {
      steps {
        withPythonEnv('python') {
          echo 'Deploying latest application tags to Pre-Production...'
          powershell "python -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.QaEnv}\" --destination_env \"${env.PpEnv}\" --app_list \"${params.AppScope}\""
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
    stage('Deploy to Production Environment') {
      steps {
        withPythonEnv('python') {
          echo 'Deploying latest application tags to Production...'
          powershell "python -m outsystems.pipeline.deploy_latest_tags_to_target_env --artifacts \"${env.ArtifactsFolder}\" --lt_url ${env.LifeTimeEnvironmentURL} --lt_token ${env.AuthorizationToken} --lt_api_version ${env.LifeTimeAPIVersion} --source_env \"${env.PpEnv}\" --destination_env \"${env.PrdEnv}\" --app_list \"${params.AppScope}\""
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
