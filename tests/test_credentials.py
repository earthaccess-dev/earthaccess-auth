import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import requests
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
        secret_access_key="SECRET",
        session_token="TOKEN",
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
    first = manager.get_credentials(ENDPOINT)
    second = manager.get_credentials(ENDPOINT)
    assert first is second
    assert len(responses.calls) == 1


@responses.activate
def test_manager_refreshes_within_margin() -> None:
    soon = (datetime.now(UTC) + timedelta(minutes=1)).isoformat()
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    responses.add(responses.GET, ENDPOINT, json=creds_json(soon))
    responses.add(responses.GET, ENDPOINT, json=creds_json(future))
    manager = S3CredentialManager(make_auth())
    manager.get_credentials(ENDPOINT)
    manager.get_credentials(ENDPOINT)
    assert len(responses.calls) == 2


@responses.activate
def test_manager_is_thread_safe() -> None:
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    responses.add(responses.GET, ENDPOINT, json=creds_json(future))
    manager = S3CredentialManager(make_auth())
    threads = [
        threading.Thread(target=manager.get_credentials, args=(ENDPOINT,))
        for _ in range(8)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(responses.calls) == 1


@responses.activate
def test_manager_fetch_does_not_block_other_endpoints() -> None:
    """A slow (or hung) fetch for one endpoint must not stall consumers of
    other endpoints whose cached credentials are still valid — the lock is
    per endpoint, held only around the fetch, not manager-wide.
    """
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    slow_endpoint = "https://data.slow.earthdatacloud.nasa.gov/s3credentials"
    fetch_entered = threading.Event()
    release_fetch = threading.Event()

    def hanging(request: requests.PreparedRequest) -> tuple[int, dict[str, str], str]:
        fetch_entered.set()
        assert release_fetch.wait(timeout=10)
        body = (
            '{"accessKeyId": "A", "secretAccessKey": "S", '
            f'"sessionToken": "T", "expiration": "{future}"}}'
        )
        return (200, {}, body)

    responses.add(responses.GET, ENDPOINT, json=creds_json(future))
    responses.add_callback(responses.GET, slow_endpoint, callback=hanging)

    manager = S3CredentialManager(make_auth())
    manager.get_credentials(ENDPOINT)  # warm the fast endpoint's cache

    slow = threading.Thread(target=manager.get_credentials, args=(slow_endpoint,))
    slow.start()
    try:
        assert fetch_entered.wait(timeout=10)
        # while the slow fetch holds its endpoint lock, the cached endpoint
        # must still be served
        creds = manager.get_credentials(ENDPOINT)
        assert creds.access_key_id == "AKID"
    finally:
        release_fetch.set()
        slow.join(timeout=10)
    assert not slow.is_alive()


@responses.activate
def test_get_bucket_credentials_resolves_registry() -> None:
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    responses.add(responses.GET, ENDPOINT, json=creds_json(future))
    manager = S3CredentialManager(make_auth())
    creds = manager.get_bucket_credentials("s3://podaac-ops-cumulus-protected/x.nc")
    assert creds.access_key_id == "AKID"


def test_get_bucket_credentials_unknown_raises() -> None:
    manager = S3CredentialManager(make_auth())
    with pytest.raises(S3CredentialsEndpointUnresolved, match="not-a-real-bucket"):
        manager.get_bucket_credentials("not-a-real-bucket")


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
