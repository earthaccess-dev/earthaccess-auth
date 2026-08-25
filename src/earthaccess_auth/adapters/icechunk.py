"""icechunk integration (extra: earthaccess-auth[icechunk]).

Builds refreshable icechunk credentials backed by the shared
[credential manager][earthaccess_auth.credentials.S3CredentialManager].
icechunk re-invokes the callable once the credentials it holds pass
`expires_after`, and the callable is a module-level function bound with
`functools.partial`, so it — and any repository/session objects holding
it — survives pickling.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import icechunk

from earthaccess_auth.credentials import default_manager
from earthaccess_auth.daac import resolve_bucket
from earthaccess_auth.exceptions import S3CredentialsEndpointUnresolved

if TYPE_CHECKING:
    from collections.abc import Callable


def _resolve_endpoint(bucket_or_endpoint: str) -> str:
    if bucket_or_endpoint.startswith("https://"):
        return bucket_or_endpoint
    info = resolve_bucket(bucket_or_endpoint)
    if info is None:
        msg = (
            f"{bucket_or_endpoint!r} is neither an https:// s3credentials "
            "endpoint nor a bucket in the CMR-derived registry"
        )
        raise S3CredentialsEndpointUnresolved(msg)
    return info.endpoint


def _fetch_static_credentials(endpoint: str) -> icechunk.S3StaticCredentials:
    creds = default_manager().get_credentials(endpoint)
    return icechunk.S3StaticCredentials(
        access_key_id=creds.access_key_id,
        secret_access_key=creds.secret_access_key,
        session_token=creds.session_token,
        expires_after=creds.expires_at,
    )


def get_credentials_callable(
    bucket_or_endpoint: str,
) -> Callable[[], icechunk.S3StaticCredentials]:
    """Build a picklable zero-argument callable for icechunk's credential hooks.

    Suitable for `icechunk.s3_storage(get_credentials=...)` and
    `icechunk.s3_refreshable_credentials`. icechunk re-invokes it when
    the returned credentials' `expires_after` passes.

    Parameters:
        bucket_or_endpoint: A registered bucket name, an `s3://` URL of
            one, or an `https://` `s3credentials` endpoint directly.

    Raises:
        S3CredentialsEndpointUnresolved: If a bucket name/URL isn't in the
            CMR-derived
            [`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY].
    """
    return partial(_fetch_static_credentials, _resolve_endpoint(bucket_or_endpoint))


def earthdata_s3_credentials(
    bucket_or_endpoint: str,
) -> icechunk.S3Credentials.Refreshable:
    """Build a refreshable icechunk credential, e.g. for virtual chunk containers.

    Hand the result to `icechunk.Repository.open(
    authorize_virtual_chunk_access={prefix: <this>})` or anywhere an
    `icechunk.AnyS3Credential` is accepted.

    Parameters:
        bucket_or_endpoint: A registered bucket name, an `s3://` URL of
            one, or an `https://` `s3credentials` endpoint directly.

    Raises:
        S3CredentialsEndpointUnresolved: If a bucket name/URL isn't in the
            CMR-derived
            [`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY].
    """
    return icechunk.s3_refreshable_credentials(
        get_credentials_callable(bucket_or_endpoint)
    )
