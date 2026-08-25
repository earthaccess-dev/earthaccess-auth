import pickle
from datetime import UTC, datetime

import pytest

import earthaccess_auth.credentials as credentials_module
from earthaccess_auth.credentials import S3Credentials
from earthaccess_auth.exceptions import S3CredentialsEndpointUnresolved

icechunk = pytest.importorskip("icechunk")

ENDPOINT = "https://archive.podaac.earthdata.nasa.gov/s3credentials"
EXPIRES = datetime(2026, 8, 24, 12, tzinfo=UTC)


class StubManager:
    def __init__(self) -> None:
        self.requested: list[str] = []

    def get_credentials(self, endpoint: str) -> S3Credentials:
        self.requested.append(endpoint)
        return S3Credentials(
            access_key_id="AKID",
            secret_access_key="SECRET",
            session_token="TOKEN",
            expires_at=EXPIRES,
        )


@pytest.fixture
def stub_manager(monkeypatch: pytest.MonkeyPatch) -> StubManager:
    stub = StubManager()
    monkeypatch.setattr(credentials_module, "_default_manager", stub)
    return stub


def test_callable_returns_icechunk_static_credentials(
    stub_manager: StubManager,
) -> None:
    from earthaccess_auth.adapters.icechunk import (  # noqa: PLC0415
        get_credentials_callable,
    )

    creds = get_credentials_callable(ENDPOINT)()
    assert isinstance(creds, icechunk.S3StaticCredentials)
    assert creds.access_key_id == "AKID"
    assert creds.session_token == "TOKEN"
    assert creds.expires_after == EXPIRES
    assert stub_manager.requested == [ENDPOINT]


def test_callable_accepts_registered_bucket_name(stub_manager: StubManager) -> None:
    from earthaccess_auth.adapters.icechunk import (  # noqa: PLC0415
        get_credentials_callable,
    )

    get_credentials_callable("podaac-ops-cumulus-protected")()
    assert stub_manager.requested == [ENDPOINT]


def test_callable_is_picklable(stub_manager: StubManager) -> None:
    from earthaccess_auth.adapters.icechunk import (  # noqa: PLC0415
        get_credentials_callable,
    )

    unpickled = pickle.loads(pickle.dumps(get_credentials_callable(ENDPOINT)))
    assert unpickled().secret_access_key == "SECRET"


def test_unknown_bucket_raises() -> None:
    from earthaccess_auth.adapters.icechunk import (  # noqa: PLC0415
        get_credentials_callable,
    )

    with pytest.raises(S3CredentialsEndpointUnresolved, match="not-a-real-bucket"):
        get_credentials_callable("not-a-real-bucket")


def test_refreshable_credentials_wrapper(stub_manager: StubManager) -> None:
    from earthaccess_auth.adapters.icechunk import (  # noqa: PLC0415
        earthdata_s3_credentials,
    )

    refreshable = earthdata_s3_credentials(ENDPOINT)
    assert isinstance(refreshable, icechunk.S3Credentials.Refreshable)
