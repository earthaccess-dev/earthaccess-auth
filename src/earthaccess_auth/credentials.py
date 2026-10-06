"""Shared EDL-to-S3 credential fetching and caching.

The DAAC `s3credentials` endpoints issue STS credentials that last about
an hour. obstore and icechunk call their credential function again when
those expire, so this module has no refresh loop. It has a fetch function
and a thread-safe cache per endpoint. Many buckets share an endpoint, so
one job that opens several stores fetches credentials once per endpoint.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from earthaccess_auth.auth import Auth
from earthaccess_auth.daac import resolve_bucket
from earthaccess_auth.exceptions import (
    LoginStrategyUnavailable,
    S3CredentialsEndpointUnresolved,
)


@dataclass(frozen=True)
class S3Credentials:
    """Temporary AWS credentials issued by a DAAC's `s3credentials` endpoint."""

    access_key_id: str
    secret_access_key: str
    session_token: str
    expires_at: datetime
    """Expiry as a timezone-aware datetime (endpoints report UTC)."""


def fetch_s3_credentials(auth: Auth, endpoint: str) -> S3Credentials:
    """Fetch and parse temporary S3 credentials from an `s3credentials` endpoint.

    Use [`S3CredentialManager`][earthaccess_auth.credentials.S3CredentialManager]
    for repeated access.

    Parameters:
        auth: An authenticated [`Auth`][earthaccess_auth.Auth] instance.
        endpoint: A DAAC's `s3credentials` URL.

    Returns:
        The parsed credentials, with
        [`expires_at`][earthaccess_auth.S3Credentials.expires_at] timezone-aware (a naive
        timestamp from the endpoint is interpreted as UTC).

    Raises:
        S3CredentialsRequestFailure: If the endpoint rejects the request,
            e.g. because the DAAC's EULA hasn't been accepted.
    """
    raw = auth.get_s3_credentials(endpoint=endpoint)
    expires_at = datetime.fromisoformat(raw["expiration"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return S3Credentials(
        access_key_id=raw["accessKeyId"],
        secret_access_key=raw["secretAccessKey"],
        session_token=raw["sessionToken"],
        expires_at=expires_at,
    )


class S3CredentialManager:
    """Thread-safe per-endpoint cache of temporary S3 credentials."""

    def __init__(
        self,
        auth: Auth,
        refresh_margin: timedelta = timedelta(minutes=5),
    ) -> None:
        """Initialize the manager.

        Parameters:
            auth: An authenticated [`Auth`][earthaccess_auth.Auth] instance.
            refresh_margin: Re-fetch credentials once they are within this
                margin of expiry, so consumers never receive credentials
                about to lapse mid-request.
        """
        self._auth = auth
        self._refresh_margin = refresh_margin
        self._cache: dict[str, S3Credentials] = {}
        self._lock = threading.Lock()
        self._endpoint_locks: dict[str, threading.Lock] = {}

    def _fresh(self, endpoint: str) -> S3Credentials | None:
        """Return the cached credentials if still outside the refresh margin."""
        cached = self._cache.get(endpoint)
        now = datetime.now(UTC)
        if cached is not None and cached.expires_at - self._refresh_margin > now:
            return cached
        return None

    def get_credentials(self, endpoint: str) -> S3Credentials:
        """Return cached credentials for `endpoint`, fetching if stale/absent.

        Each endpoint has its own lock for the fetch. Concurrent callers of
        the same endpoint cause only one fetch. A slow fetch for one
        endpoint doesn't block callers of a different endpoint that has
        valid cached credentials.
        """
        with self._lock:
            fresh = self._fresh(endpoint)
            if fresh is not None:
                return fresh
            endpoint_lock = self._endpoint_locks.setdefault(endpoint, threading.Lock())
        with endpoint_lock:
            with self._lock:
                # another caller may have refreshed while we waited
                fresh = self._fresh(endpoint)
                if fresh is not None:
                    return fresh
            creds = fetch_s3_credentials(self._auth, endpoint)
            with self._lock:
                self._cache[endpoint] = creds
            return creds

    def get_bucket_credentials(self, bucket_or_url: str) -> S3Credentials:
        """Return credentials for a registered bucket name or `s3://` URL.

        Raises:
            S3CredentialsEndpointUnresolved: If the bucket isn't in the
                CMR-derived
                [`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY].
        """
        info = resolve_bucket(bucket_or_url)
        if info is None:
            msg = (
                f"bucket {bucket_or_url!r} is not in the CMR-derived bucket "
                "registry; pass its s3credentials endpoint to "
                "get_credentials() directly"
            )
            raise S3CredentialsEndpointUnresolved(msg)
        return self.get_credentials(info.endpoint)


_default_manager: S3CredentialManager | None = None
_default_manager_lock = threading.Lock()


def set_default_auth(auth: Auth) -> None:
    """Make `auth` the identity behind [`default_manager`][earthaccess_auth.credentials.default_manager].

    Builds a fresh [`S3CredentialManager`][earthaccess_auth.S3CredentialManager]
    for `auth`. If you already have a manager with credentials in its cache,
    pass it to
    [`set_default_manager`][earthaccess_auth.credentials.set_default_manager]
    instead so the cache survives.
    """
    set_default_manager(S3CredentialManager(auth))


def set_default_manager(manager: S3CredentialManager) -> None:
    """Make `manager` the process-wide [`default_manager`][earthaccess_auth.credentials.default_manager].

    Most callers want
    [`set_default_auth`][earthaccess_auth.credentials.set_default_auth]. Use
    this one when you already have a manager, usually because you fetched
    credentials through it to check its identity. Consumers then reuse
    those cached credentials instead of fetching them again.
    """
    global _default_manager  # noqa: PLW0603
    with _default_manager_lock:
        _default_manager = manager


def default_manager() -> S3CredentialManager:
    """Return the process-wide credential manager, creating it on first use.

    First use logs in with the non-interactive strategies, in order:
    `environment` (`EARTHDATA_TOKEN`, or `EARTHDATA_USERNAME` +
    `EARTHDATA_PASSWORD`), then `netrc`. It never tries `interactive`,
    because this runs inside services, where an [`input()`][input] prompt would
    block.

    Adapter functions reference this module-level manager, so they can be
    pickled along with the datasets that hold them.

    Raises:
        LoginStrategyUnavailable: If neither non-interactive strategy is
            available. Call
            [`set_default_auth`][earthaccess_auth.credentials.set_default_auth]
            to supply a custom [`Auth`][earthaccess_auth.Auth] instead.
    """
    global _default_manager  # noqa: PLW0603
    with _default_manager_lock:
        if _default_manager is None:
            auth = Auth()
            for strategy in ("environment", "netrc"):
                try:
                    auth.login(strategy=strategy)
                except LoginStrategyUnavailable:
                    continue
                if auth.authenticated:
                    break
            if not auth.authenticated:
                msg = (
                    "no non-interactive EDL login strategy available: set "
                    "EARTHDATA_TOKEN (or EARTHDATA_USERNAME and "
                    "EARTHDATA_PASSWORD), provide a .netrc, or call "
                    "set_default_auth() with a pre-authenticated Auth"
                )
                raise LoginStrategyUnavailable(msg)
            _default_manager = S3CredentialManager(auth)
        return _default_manager
