# Deployment specific variables
QUEUE_TIMEOUT_IN_SECS = 1800
DEPLOYMENT_TIMEOUT_IN_SECS = 3600
SLEEP_PERIOD_IN_SECS = 20
REDEPLOY_OUTDATED_APPS = True
DEPLOYMENT_STATUS_LIST = ["saved","running", "needs_user_intervention", "aborting"]
DEPLOYMENT_ERROR_STATUS_LIST = ["aborted", "finished_with_errors"]
DEPLOYMENT_WAITING_STATUS = "needs_user_intervention"
DEPLOYMENT_RUNNING_STATUS = "running"

# Pipeline files variables
CONFLICTS_FILE = "DeploymentConflicts"
DEPLOY_ERROR_FILE = "DeploymentErrors"