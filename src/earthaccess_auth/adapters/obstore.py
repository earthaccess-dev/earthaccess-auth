"""obstore integration (extra: earthaccess-auth[obstore]).

This module provides both a new native obstore-protocol credential provider
([`EarthdataS3CredentialProvider`]) and re-exports of obstore's own
EDL-to-S3 credential exchange for compatibility. The native provider is the
recommended way to integrate with obstore, as it needs no obstore import
and shares the process-wide credential cache.

Also adds an HTTP-headers helper for the cases the credential provider
doesn't cover.
"""

from typing import Any, Protocol

# Re-exported so consumers have one import root for EDL auth. Long term the
# implementation could migrate here and obstore could depend on this package
# instead (open question in the README).
from obstore.auth.earthdata import (  # noqa: F401
    NasaEarthdataAsyncCredentialProvider,
    NasaEarthdataCredentialProvider,
)
from typing_extensions import deprecated

from earthaccess_auth.auth import Auth
from earthaccess_auth.credentials import S3Credentials, default_manager
from earthaccess_auth.daac import resolve_bucket
from earthaccess_auth.exceptions import S3CredentialsEndpointUnresolved


class _CredentialSource(Protocol):
    """Anything that can serve cached credentials for an endpoint.

    Structural on purpose: `S3CredentialManager` satisfies it, and so do
    test stubs — mirroring how obstore itself duck-types providers.
    """

    def credentials_for(self, endpoint: str) -> S3Credentials: ...


class EarthdataS3CredentialProvider:
    """obstore-compatible S3 credential provider backed by earthaccess-auth.

    Implements obstore's *structural* `S3CredentialProvider` protocol — a
    callable returning the credential dict, plus a `config` attribute
    carrying the region — so it needs no obstore import and works with any
    obstore version that accepts custom providers. obstore re-invokes the
    provider itself once `expires_at` passes; the shared credential
    manager behind it deduplicates those fetches across stores.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        region: str = "us-west-2",
        manager: _CredentialSource | None = None,
    ) -> None:
        """Initialize the provider.

        Parameters:
            endpoint: A DAAC's `s3credentials` URL.
            region: The bucket's AWS region, forwarded to obstore via the
                protocol's `config` attribute.
            manager: Credential source to fetch through. Defaults to the
                process-wide
                [`default_manager`][earthaccess_auth.credentials.default_manager]
                (resolved lazily at first call, not at construction).
        """
        self._endpoint = endpoint
        self._manager = manager
        self.config: dict[str, str] = {"region": region}

    @classmethod
    def for_bucket(
        cls,
        bucket_or_url: str,
        *,
        manager: _CredentialSource | None = None,
    ) -> "EarthdataS3CredentialProvider":
        """Build a provider from a registered bucket name or `s3://` URL.

        Raises:
            S3CredentialsEndpointUnresolved: If the bucket isn't in the
                CMR-derived
                [`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY].
        """
        info = resolve_bucket(bucket_or_url)
        if info is None:
            msg = (
                f"bucket {bucket_or_url!r} is not in the CMR-derived bucket "
                "registry; pass its s3credentials endpoint to the "
                "constructor directly"
            )
            raise S3CredentialsEndpointUnresolved(msg)
        return cls(info.endpoint, region=info.region, manager=manager)

    def __call__(self) -> dict[str, Any]:
        """Fetch credentials in obstore's `S3Credential` dict shape."""
        manager = self._manager if self._manager is not None else default_manager()
        creds = manager.credentials_for(self._endpoint)
        return {
            "access_key_id": creds.access_key_id,
            "secret_access_key": creds.secret_access_key,
            "token": creds.session_token,
            "expires_at": creds.expires_at,
        }


@deprecated(
    "Use EarthdataS3CredentialProvider instead; it needs no obstore import "
    "and shares the process-wide credential cache."
)
def s3_credential_provider(
    auth: Auth,
    credentials_endpoint: str,
) -> NasaEarthdataCredentialProvider:
    """Build an obstore credential provider that refreshes EDL-issued S3 credentials.

    Hand this to [`obstore.store.S3Store`][]`(credential_provider=...)` instead of
    a one-shot credentials dict, so a long-running job doesn't need its own
    refresh loop — the provider re-authenticates with EDL once the current
    credentials near expiry.

    Parameters:
        auth: An authenticated `Auth` instance.
        credentials_endpoint: A DAAC's `s3credentials` URL, e.g. the
            `"s3-credentials"` field on an entry in
            [`DAACS`][earthaccess_auth.daac.DAACS].

    Returns:
        A credential provider usable as [`obstore.store.S3Store`][]'s
        `credential_provider` argument.

    Raises:
        ValueError: If `auth` has not been authenticated (`auth.token is None`).
    """
    if auth.token is None:
        msg = "auth must be authenticated before use"
        raise ValueError(msg)
    # obstore 0.9.2's NasaEarthdataCredentialProvider takes the credentials
    # URL positionally plus a keyword-only `auth` (bearer token string,
    # (username, password) tuple, or None) — there is no `token=` keyword.
    return NasaEarthdataCredentialProvider(
        credentials_endpoint,
        auth=auth.token["access_token"],
    )


def http_client_options(auth: Auth) -> dict[str, Any]:
    """Build default-header client options for HTTPS stores fronting EDL-protected data.

    Usable for obstore HTTP stores and any store config that accepts plain
    headers, such as icechunk's `http_store(headers=...)` for virtual chunk
    containers.

    Parameters:
        auth: An authenticated `Auth` instance.

    Returns:
        A dict with a `default_headers` key carrying the bearer token,
        matching [`obstore.store.ClientConfig`][]'s shape.

    Raises:
        ValueError: If `auth` has not been authenticated (`auth.token is None`).
    """
    if auth.token is None:
        msg = "auth must be authenticated before use"
        raise ValueError(msg)
    # obstore 0.9.2's ClientConfig.default_headers accepts dict[str, str] |
    # dict[str, bytes], matching the shape returned here.
    return {
        "default_headers": {"authorization": f"Bearer {auth.token['access_token']}"}
    }
