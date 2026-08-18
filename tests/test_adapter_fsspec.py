import pytest

from earthaccess_auth import Auth

fsspec = pytest.importorskip("fsspec")


def test_fsspec_session_carries_bearer_token_and_no_ambient_auth() -> None:
    from earthaccess_auth.adapters.fsspec import (  # noqa: PLC0415
        get_fsspec_https_session,
    )

    auth = Auth()
    auth.token = {"access_token": "test-token-abc"}
    fs = get_fsspec_https_session(auth)
    assert fs.client_kwargs["headers"]["Authorization"] == "Bearer test-token-abc"
    assert fs.client_kwargs["trust_env"] is False


def test_fsspec_session_rejects_unauthenticated_auth() -> None:
    from earthaccess_auth.adapters.fsspec import (  # noqa: PLC0415
        get_fsspec_https_session,
    )

    with pytest.raises(ValueError, match="authenticated"):
        get_fsspec_https_session(Auth())
