import pytest
import responses

from earthaccess_auth import Auth

obstore = pytest.importorskip("obstore")


def _authed() -> Auth:
    auth = Auth()
    auth.token = {"access_token": "test-token-abc"}
    auth.authenticated = True
    return auth


@responses.activate
def test_s3_credential_provider_wires_token_and_endpoint() -> None:
    from obstore.auth.earthdata import (  # noqa: PLC0415
        NasaEarthdataCredentialProvider,
    )

    from earthaccess_auth.adapters.obstore import (  # noqa: PLC0415
        s3_credential_provider,
    )

    endpoint = "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials"
    responses.add(
        responses.GET,
        endpoint,
        json={
            "accessKeyId": "AKIDEXAMPLE",
            "secretAccessKey": "secret",
            "sessionToken": "session-token",
            "expiration": "2030-01-01T00:00:00+00:00",
        },
        status=200,
    )

    provider = s3_credential_provider(_authed(), endpoint)
    assert isinstance(provider, NasaEarthdataCredentialProvider)

    # Drives the public __call__ surface, not private attrs, so this survives
    # an obstore attribute rename.
    credentials = provider()

    assert len(responses.calls) == 1
    request = responses.calls[0].request
    assert request.url is not None
    assert request.url.startswith(endpoint)
    assert request.headers["Authorization"] == "Bearer test-token-abc"
    assert credentials["access_key_id"] == "AKIDEXAMPLE"
    assert credentials["secret_access_key"] == "secret"  # noqa: S105
    assert credentials["token"] == "session-token"  # noqa: S105


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


def test_s3_credential_provider_rejects_unauthenticated_auth() -> None:
    from earthaccess_auth.adapters.obstore import (  # noqa: PLC0415
        s3_credential_provider,
    )

    with pytest.raises(ValueError, match="authenticated"):
        s3_credential_provider(Auth(), "https://example.com/s3credentials")


def test_http_client_options_rejects_unauthenticated_auth() -> None:
    from earthaccess_auth.adapters.obstore import (  # noqa: PLC0415
        http_client_options,
    )

    with pytest.raises(ValueError, match="authenticated"):
        http_client_options(Auth())
