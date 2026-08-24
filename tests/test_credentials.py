import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import responses

import earthaccess_auth.credentials as credentials_module
from earthaccess_auth import Auth
from earthaccess_auth.credentials import (
    S3CredentialManager,
    S3Credentials,
    default_manager,
    fetch_s3_credentials,
    set_default_auth,
)
from earthaccess_auth.exceptions import (
    LoginStrategyUnavailable,
    S3CredentialsEndpointUnresolved,
)

ENDPOINT = "https://archive.podaac.earthdata.nasa.gov/s3credentials"


@pytest.fixture(autouse=True)
def _reset_default_manager() -> None:
    credentials_module._default_manager = None


def make_auth() -> Auth:
    auth = Auth()
    auth.token = {"access_token": "EDL-token"}
    auth.authenticated = True
    return auth


def creds_json(expiration: str) -> dict[str, str]:
    return {
        "accessKeyId": "AKID",
        "secretAccessKey": "SECRET",
        "sessionToken": "TOKEN",
        "expiration": expiration,
    }


@responses.activate
def test_fetch_parses_credentials_and_space_separated_expiration() -> None:
    responses.add(responses.GET, ENDPOINT, json=creds_json("2026-08-24 12:00:00+00:00"))
    creds = fetch_s3_credentials(make_auth(), ENDPOINT)
    assert creds == S3Credentials(
        access_key_id="AKID",
        secret_access_key="SECRET",  # noqa: S106
        session_token="TOKEN",  # noqa: S106
        expires_at=datetime(2026, 8, 24, 12, tzinfo=UTC),
    )


@responses.activate
def test_fetch_assumes_utc_for_naive_expiration() -> None:
    responses.add(responses.GET, ENDPOINT, json=creds_json("2026-08-24T12:00:00"))
    creds = fetch_s3_credentials(make_auth(), ENDPOINT)
    assert creds.expires_at.tzinfo == UTC


@responses.activate
def test_manager_caches_per_endpoint() -> None:
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    responses.add(responses.GET, ENDPOINT, json=creds_json(future))
    manager = S3CredentialManager(make_auth())
    first = manager.credentials_for(ENDPOINT)
    second = manager.credentials_for(ENDPOINT)
    assert first is second
    assert len(responses.calls) == 1


@responses.activate
def test_manager_refreshes_within_margin() -> None:
    soon = (datetime.now(UTC) + timedelta(minutes=1)).isoformat()
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    responses.add(responses.GET, ENDPOINT, json=creds_json(soon))
    responses.add(responses.GET, ENDPOINT, json=creds_json(future))
    manager = S3CredentialManager(make_auth())
    manager.credentials_for(ENDPOINT)
    manager.credentials_for(ENDPOINT)
    assert len(responses.calls) == 2


@responses.activate
def test_manager_is_thread_safe() -> None:
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    responses.add(responses.GET, ENDPOINT, json=creds_json(future))
    manager = S3CredentialManager(make_auth())
    threads = [
        threading.Thread(target=manager.credentials_for, args=(ENDPOINT,))
        for _ in range(8)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(responses.calls) == 1


@responses.activate
def test_credentials_for_bucket_resolves_registry() -> None:
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    responses.add(responses.GET, ENDPOINT, json=creds_json(future))
    manager = S3CredentialManager(make_auth())
    creds = manager.credentials_for_bucket("s3://podaac-ops-cumulus-protected/x.nc")
    assert creds.access_key_id == "AKID"


def test_credentials_for_bucket_unknown_raises() -> None:
    manager = S3CredentialManager(make_auth())
    with pytest.raises(S3CredentialsEndpointUnresolved, match="not-a-real-bucket"):
        manager.credentials_for_bucket("not-a-real-bucket")


def test_set_default_auth_installs_manager() -> None:
    set_default_auth(make_auth())
    assert default_manager()._auth.authenticated


def test_default_manager_without_credentials_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    for var in ("EARTHDATA_TOKEN", "EARTHDATA_USERNAME", "EARTHDATA_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("NETRC", str(tmp_path / "missing-netrc"))
    with pytest.raises(LoginStrategyUnavailable):
        default_manager()
