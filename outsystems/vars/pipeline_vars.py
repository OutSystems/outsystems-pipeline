# Deployment specific variables
QUEUE_TIMEOUT_IN_SECS = 1800
DEPLOYMENT_TIMEOUT_IN_SECS = 3600
SLEEP_PERIOD_IN_SECS = 20
REDEPLOY_OUTDATED_APPS = True
ALLOW_CONTINUE_WITH_ERRORS = False
DEPLOYMENT_STATUS_LIST = ["saved", "running", "needs_user_intervention", "aborting"]
DEPLOYMENT_ERROR_STATUS_LIST = ["aborted", "finished_with_errors"]
DEPLOYMENT_WAITING_STATUS = "needs_user_intervention"
DEPLOYMENT_RUNNING_STATUS = "running"
DEPLOYMENT_SAVED_STATUS = "saved"

# Pipeline files variables
CONFLICTS_FILE = "DeploymentConflicts"
DEPLOY_ERROR_FILE = "DeploymentErrors"

# Application specific variables
MAX_VERSIONS_TO_RETURN = 10
TAG_APP_MAX_RETRIES = 5
