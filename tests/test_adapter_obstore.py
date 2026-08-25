from datetime import UTC, datetime

import pytest

from earthaccess_auth import Auth
from earthaccess_auth.credentials import S3Credentials
from earthaccess_auth.exceptions import S3CredentialsEndpointUnresolved

obstore = pytest.importorskip("obstore")


def _authed() -> Auth:
    auth = Auth()
    auth.token = {"access_token": "test-token-abc"}
    auth.authenticated = True
    return auth


def test_http_client_options_accepted_by_obstore() -> None:
    from earthaccess_auth.adapters.obstore import (  # noqa: PLC0415
        http_client_options,
    )

    options = http_client_options(_authed())
    assert options == {"default_headers": {"authorization": "Bearer test-token-abc"}}
    # Constructing a store with these options proves the key is real; no
    # network I/O happens at construction time.
    store = obstore.store.HTTPStore.from_url(
        "https://example.com", client_options=options
    )
    assert store is not None


def test_http_client_options_rejects_unauthenticated_auth() -> None:
    from earthaccess_auth.adapters.obstore import (  # noqa: PLC0415
        http_client_options,
    )

    with pytest.raises(ValueError, match="authenticated"):
        http_client_options(Auth())


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


def test_provider_returns_obstore_credential_shape() -> None:
    from earthaccess_auth.adapters.obstore import (  # noqa: PLC0415
        EarthdataS3CredentialProvider,
    )

    manager = StubManager()
    provider = EarthdataS3CredentialProvider(
        "https://archive.podaac.earthdata.nasa.gov/s3credentials",
        manager=manager,
    )
    assert provider() == {
        "access_key_id": "AKID",
        "secret_access_key": "SECRET",
        "token": "TOKEN",
        "expires_at": EXPIRES,
    }
    assert provider.config == {"region": "us-west-2"}
    assert manager.requested == [
        "https://archive.podaac.earthdata.nasa.gov/s3credentials"
    ]


def test_provider_for_bucket_resolves_registry() -> None:
    from earthaccess_auth.adapters.obstore import (  # noqa: PLC0415
        EarthdataS3CredentialProvider,
    )

    provider = EarthdataS3CredentialProvider.for_bucket(
        "s3://lp-prod-protected/HLS/x.tif", manager=StubManager()
    )
    provider()
    assert provider.config == {"region": "us-west-2"}


def test_provider_for_bucket_unknown_raises() -> None:
    from earthaccess_auth.adapters.obstore import (  # noqa: PLC0415
        EarthdataS3CredentialProvider,
    )

    with pytest.raises(S3CredentialsEndpointUnresolved, match="not-a-real-bucket"):
        EarthdataS3CredentialProvider.for_bucket("not-a-real-bucket")
