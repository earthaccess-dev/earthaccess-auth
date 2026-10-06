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
    """Build a refreshable icechunk credential for one Earthdata bucket.

    The result is an `icechunk.AnyS3Credential`. To read virtual chunks
    from a single bucket, wrap it with `icechunk.containers_credentials`.
    To authorize every container a repository declares, use
    [`earthdata_containers_credentials`][earthaccess_auth.adapters.icechunk.earthdata_containers_credentials]
    instead.

    Parameters:
        bucket_or_endpoint: A bucket name from the CMR-derived
            [`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY], an
            `s3://` URL of one, or an `https://` `s3credentials` endpoint.

    Raises:
        S3CredentialsEndpointUnresolved: If a bucket name/URL isn't in the
            CMR-derived
            [`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY].

    Examples:
        Authorize one virtual chunk container by hand:

        ```python
        prefix = "s3://podaac-ops-cumulus-protected/"
        repo = icechunk.Repository.open(
            storage,
            authorize_virtual_chunk_access=icechunk.containers_credentials(
                {prefix: earthdata_s3_credentials(prefix)}
            ),
        )
        ```
    """
    return icechunk.s3_refreshable_credentials(
        get_credentials_callable(bucket_or_endpoint)
    )


def earthdata_containers_credentials(
    repo: icechunk.Repository,
) -> dict[str, icechunk.AnyCredential | None]:
    """Authorize a repository's virtual chunk containers in CMR-referenced buckets.

    Returns credentials for each virtual chunk container in `repo`'s config
    whose bucket is in the CMR-derived
    [`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY], which holds
    the buckets that CMR references for Earthdata granules. Each gets
    [`earthdata_s3_credentials`][earthaccess_auth.adapters.icechunk.earthdata_s3_credentials].
    Pass the result to `repo.reopen`, which reuses the already loaded
    config instead of reading it from storage again.

    Containers in any other bucket are left out, even one that holds
    Earthdata granules but that CMR doesn't reference. A repository without
    containers yields an empty dict.

    Parameters:
        repo: An open `icechunk.Repository`. It needs no virtual chunk
            credentials yet.

    Examples:
        Open a repository without knowing which buckets hold its chunks:

        ```python
        repo = icechunk.Repository.open(storage)
        repo = repo.reopen(
            authorize_virtual_chunk_access=earthdata_containers_credentials(repo)
        )
        ```

        Add credentials for a container outside the registry:

        ```python
        repo = icechunk.Repository.open(storage)
        authorized = earthdata_containers_credentials(repo)
        authorized |= icechunk.containers_credentials(
            {"s3://my-bucket/": icechunk.s3_credentials(from_env=True)}
        )
        repo = repo.reopen(authorize_virtual_chunk_access=authorized)
        ```
    """
    containers = repo.config.virtual_chunk_containers or {}
    return icechunk.containers_credentials(
        {
            container.url_prefix: earthdata_s3_credentials(container.url_prefix)
            for container in containers.values()
            if resolve_bucket(container.url_prefix) is not None
        }
    )
