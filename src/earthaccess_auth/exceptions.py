"""Exceptions raised while authenticating with Earthdata Login (EDL)."""


class LoginStrategyUnavailable(Exception):  # noqa: N818
    """Raised when a login strategy couldn't be attempted at all.

    For example, the `"environment"` strategy raises this if none of
    `EARTHDATA_USERNAME`/`EARTHDATA_PASSWORD`/`EARTHDATA_TOKEN` are set.
    Contrast with `LoginAttemptFailure`, which is raised when a strategy
    was attempted but Earthdata Login rejected the credentials.
    """


class LoginAttemptFailure(Exception):  # noqa: N818
    """Raised when Earthdata Login rejects an authentication attempt.

    For example, because the supplied username/password or token were
    invalid. Contrast with `LoginStrategyUnavailable`, which is raised when
    a strategy couldn't even be attempted (e.g. missing credentials).
    """


class S3CredentialsEndpointUnresolved(Exception):  # noqa: N818
    """Raised when no `s3credentials` endpoint could be found for a request.

    This happens when the given `daac`/`provider` isn't in the DAAC
    registry, or the DAAC has no cloud collections and therefore no
    `s3credentials` URL.
    """
