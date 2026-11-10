import datetime

import pytest

from outsystems.exceptions.invalid_parameters import InvalidParametersError
from outsystems.exceptions.no_deployments import NoDeploymentsError
from outsystems.lifetime import lifetime_deployments
from outsystems.lifetime.lifetime_deployments import get_deployments_min_date, get_running_deployment, \
    get_saved_deployment

TARGET_ENV_KEY = "target-env-key"
OTHER_ENV_KEY = "other-env-key"


def expected_min_dates(days: int):
    # Accept both sides of a midnight boundary that may be crossed while the test runs
    now = datetime.datetime.now()
    return {(now - datetime.timedelta(days=days)).date(), (now - datetime.timedelta(days=days, seconds=-5)).date()}


@pytest.fixture
def override_config(monkeypatch):
    def _override(value: str):
        monkeypatch.setenv("OVERRIDE_CONFIG_IN_USE", "True")
        monkeypatch.setenv("DEPLOYMENT_LOOKBACK_DAYS", value)
    return _override


@pytest.fixture(autouse=True)
def clear_config(monkeypatch):
    monkeypatch.delenv("OVERRIDE_CONFIG_IN_USE", raising=False)
    monkeypatch.delenv("DEPLOYMENT_LOOKBACK_DAYS", raising=False)


@pytest.fixture
def lifetime_api(monkeypatch):
    # Fakes the LifeTime API calls and records the MinDate used to search deployments
    state = {"min_date": None, "deployments": [], "statuses": {}}

    def fake_get_deployments(artifact_dir, endpoint, auth_token, date):
        state["min_date"] = date
        if not state["deployments"]:
            raise NoDeploymentsError("No deployments")
        return state["deployments"]

    def fake_get_deployment_status(artifact_dir, endpoint, auth_token, deployment_key):
        return {"DeploymentStatus": state["statuses"][deployment_key]}

    monkeypatch.setattr(lifetime_deployments, "get_deployments", fake_get_deployments)
    monkeypatch.setattr(lifetime_deployments, "get_deployment_status", fake_get_deployment_status)
    return state


def test_min_date_defaults_to_one_day():
    assert get_deployments_min_date() in expected_min_dates(1)


def test_min_date_uses_configured_lookback_days(override_config):
    override_config("4")
    assert get_deployments_min_date() in expected_min_dates(4)


@pytest.mark.parametrize("value", ["0", "-2", "2.5", "true", "abc"])
def test_min_date_rejects_invalid_lookback_days(override_config, value):
    override_config(value)
    with pytest.raises(InvalidParametersError):
        get_deployments_min_date()


def test_lookback_override_ignored_without_config_file(monkeypatch):
    # Environment variables only take effect when a configuration file has been loaded
    monkeypatch.setenv("DEPLOYMENT_LOOKBACK_DAYS", "7")
    assert get_deployments_min_date() in expected_min_dates(1)


def test_get_saved_deployment_uses_configured_lookback(override_config, lifetime_api):
    override_config("3")
    lifetime_api["deployments"] = [
        {"Key": "dep-other-env", "TargetEnvironmentKey": OTHER_ENV_KEY},
        {"Key": "dep-running", "TargetEnvironmentKey": TARGET_ENV_KEY},
        {"Key": "dep-saved", "TargetEnvironmentKey": TARGET_ENV_KEY},
    ]
    lifetime_api["statuses"] = {"dep-other-env": "saved", "dep-running": "running", "dep-saved": "saved"}

    deployment = get_saved_deployment("artifacts", "endpoint", "token", TARGET_ENV_KEY)

    assert deployment["Key"] == "dep-saved"
    assert lifetime_api["min_date"] in expected_min_dates(3)


def test_get_running_deployment_uses_configured_lookback(override_config, lifetime_api):
    override_config("5")
    lifetime_api["deployments"] = [
        {"Key": "dep-waiting", "TargetEnvironmentKey": TARGET_ENV_KEY},
        {"Key": "dep-finished", "TargetEnvironmentKey": TARGET_ENV_KEY},
        {"Key": "dep-other-env", "TargetEnvironmentKey": OTHER_ENV_KEY},
    ]
    lifetime_api["statuses"] = {"dep-waiting": "needs_user_intervention", "dep-finished": "finished_successful",
                                "dep-other-env": "running"}

    deployments = get_running_deployment("artifacts", "endpoint", "token", TARGET_ENV_KEY)

    assert [deployment["Key"] for deployment in deployments] == ["dep-waiting"]
    assert lifetime_api["min_date"] in expected_min_dates(5)


def test_no_deployments_found(lifetime_api):
    assert get_running_deployment("artifacts", "endpoint", "token", TARGET_ENV_KEY) == []
    assert get_saved_deployment("artifacts", "endpoint", "token", TARGET_ENV_KEY) is None
    assert lifetime_api["min_date"] in expected_min_dates(1)
