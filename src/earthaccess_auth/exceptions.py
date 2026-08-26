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
    `s3credentials` URL. It is also raised when a bucket name or `s3://`
    URL isn't in the CMR-derived `BUCKET_REGISTRY`, by
    `credentials.S3CredentialManager.get_bucket_credentials`,
    `adapters.obstore.EarthdataS3CredentialProvider.for_bucket`, and
    `adapters.icechunk`.
    """


class S3CredentialsRequestFailure(Exception):  # noqa: N818
    """Raised when a DAAC's `s3credentials` endpoint rejects a request.

    Commonly this means the EDL profile hasn't accepted the DAAC's EULA or
    application terms yet; the error message includes the URLs to review
    them. `status_code` carries the endpoint's HTTP status (`None` when the
    failure wasn't an HTTP rejection), so consumers can distinguish invalid
    credentials (401 — a service-side problem) from an unaccepted EULA
    (403 — a user-side problem).
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
