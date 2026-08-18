"""NASA Earthdata Login (EDL) authentication core, extracted from earthaccess.

Runtime dependencies are requests, tinynetrc, and typing-extensions only.
fsspec and obstore integrations live under `earthaccess_auth.adapters`
behind optional extras.
"""

import logging

from earthaccess_auth.auth import (
    Auth,
    SessionWithHeaderRedirection,
    netrc_path,
)
from earthaccess_auth.daac import DAACS
from earthaccess_auth.exceptions import (
    LoginAttemptFailure,
    LoginStrategyUnavailable,
    S3CredentialsEndpointUnresolved,
)
from earthaccess_auth.system import PROD, UAT, System

__all__ = [
    "DAACS",
    "PROD",
    "UAT",
    "Auth",
    "LoginAttemptFailure",
    "LoginStrategyUnavailable",
    "S3CredentialsEndpointUnresolved",
    "SessionWithHeaderRedirection",
    "System",
    "login",
    "netrc_path",
]

logger = logging.getLogger(__name__)


def login(
    strategy: str = "all",
    persist: bool = False,  # noqa: FBT001, FBT002
    system: System = PROD,
) -> Auth:
    """Authenticate with Earthdata Login (EDL) and return an Auth instance.

    Parameters:
        strategy:
            The authentication method.

            * **"all"**: (default) Try, in order: environment variables,
                `~/.netrc`, then an interactive prompt — stopping at the
                first one that works.
            * **"interactive"**: Enter a username and password.
            * **"netrc"**: Retrieve a username and password from `~/.netrc`.
            * **"environment"**:
                Retrieve either a username and password pair from the
                `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` environment
                variables, or an Earthdata login token from the
                `EARTHDATA_TOKEN` environment variable.
        persist: Persist username and password credentials in a `.netrc` file.
        system: The EDL endpoint to authenticate against. Defaults to `PROD`.

    Returns:
        An authenticated `Auth` instance. Hold onto it yourself — there's no
        module-level singleton, so pass it to whatever needs it.
    """
    auth = Auth()

    if strategy == "all":
        for strategy_name in ["environment", "netrc", "interactive"]:
            try:
                auth.login(strategy=strategy_name, persist=persist, system=system)
            except LoginStrategyUnavailable as err:
                logger.debug(err)
                continue

            if auth.authenticated:
                break
    else:
        auth.login(strategy=strategy, persist=persist, system=system)

    return auth
