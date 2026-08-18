"""obstore integration (extra: earthaccess-auth[obstore]).

Bridges an authenticated `Auth` to obstore's own EDL-to-S3 credential
exchange, and adds an HTTP-headers helper for the cases obstore's
credential provider doesn't cover.
"""

from typing import Any

# Re-exported so consumers have one import root for EDL auth. Long term the
# implementation could migrate here and obstore could depend on this package
# instead (open question in the README).
from obstore.auth.earthdata import (  # noqa: F401
    NasaEarthdataAsyncCredentialProvider,
    NasaEarthdataCredentialProvider,
)

from earthaccess_auth.auth import Auth


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
