"""Shared EDL-to-S3 credential fetching and caching.

The DAAC `s3credentials` endpoints issue roughly one-hour STS
credentials. Consumers like obstore and icechunk each re-invoke their
credential callable when the credentials they hold expire, so what
belongs here is not a refresh loop but a fetch primitive plus a
thread-safe cache: the 36 registered buckets funnel into ~15 endpoints,
and one job commonly opens stores on several of them, so sharing a
manager turns many EDL round-trips into one per endpoint.
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

    A one-shot, uncached fetch — the primitive external credential
    providers (e.g. obstore's) can delegate to. For repeated access, use
    [`S3CredentialManager`][earthaccess_auth.credentials.S3CredentialManager].

    Parameters:
        auth: An authenticated `Auth` instance.
        endpoint: A DAAC's `s3credentials` URL.

    Returns:
        The parsed credentials, with `expires_at` timezone-aware (a naive
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
            auth: An authenticated `Auth` instance.
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

        The fetch is guarded by a per-endpoint lock, so concurrent callers
        of the same endpoint still trigger a single fetch, while a slow
        fetch for one endpoint never blocks callers of another endpoint
        whose cached credentials are still valid.
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
    """Install `auth` as the identity behind [`default_manager`][earthaccess_auth.credentials.default_manager]."""
    global _default_manager  # noqa: PLW0603
    with _default_manager_lock:
        _default_manager = S3CredentialManager(auth)


def default_manager() -> S3CredentialManager:
    """Return the process-wide credential manager, creating it on first use.

    First use logs in with the non-interactive strategies, in order:
    `environment` (`EARTHDATA_TOKEN`, or `EARTHDATA_USERNAME` +
    `EARTHDATA_PASSWORD`), then `netrc`. `interactive` is deliberately
    not attempted: this path runs inside services, where a blocked
    `input()` prompt is worse than a clear error.

    Living at module level keeps adapter callables that reference it
    picklable, which matters for consumers that pickle opened datasets.

    Raises:
        LoginStrategyUnavailable: If neither non-interactive strategy is
            available. Call
            [`set_default_auth`][earthaccess_auth.credentials.set_default_auth]
            to supply a custom `Auth` instead.
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
