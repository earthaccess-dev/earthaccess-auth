from __future__ import annotations

import getpass
import importlib.metadata
import logging
import os
import platform
import shutil
from collections.abc import Mapping
from netrc import NetrcParseError
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, cast
from urllib.parse import urlparse

if TYPE_CHECKING:
    from collections.abc import Mapping
    from http.cookiejar import CookieJar

import requests
import requests.cookies
from tinynetrc import Netrc

from earthaccess_auth.daac import DAACS
from earthaccess_auth.exceptions import (
    LoginAttemptFailure,
    LoginStrategyUnavailable,
    S3CredentialsEndpointUnresolved,
    S3CredentialsRequestFailure,
)
from earthaccess_auth.system import PROD, System


def _default_user_agent() -> str:
    try:
        return f"earthaccess-auth v{importlib.metadata.version('earthaccess-auth')}"
    except importlib.metadata.PackageNotFoundError:
        return "earthaccess-auth"


logger = logging.getLogger(__name__)


def netrc_path() -> Path:
    """Return the path of the `.netrc` file.

    The path may or may not exist.

    See [the `.netrc` file](https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html).

    Returns:
        `Path` of the `NETRC` environment variable, if the value is non-empty;
        otherwise, the path of the platform-specific default location:
        `~/_netrc` on Windows systems, `~/.netrc` on non-Windows systems.
    """
    sys_netrc_name = "_netrc" if platform.system() == "Windows" else ".netrc"
    env_netrc = os.environ.get("NETRC")

    return Path(env_netrc) if env_netrc else Path.home() / sys_netrc_name


class BasicAuthResponseHook:
    def __init__(self, hostname: str, auth: tuple[str, str]) -> None:
        self.hostname = hostname
        self.auth = auth

    def __call__(self, r: requests.Response, **kwargs: Any) -> requests.Response:
        # If the response's URL is not for the EDL system we're authenticating
        # against, then simply return the response unchanged.  Otherwise, we'll
        # prepare a new request below with the user's EDL credentials.
        if urlparse(r.url).hostname != self.hostname:
            return r

        # Consume content and release the original connection to allow our new
        # request to reuse the same one.
        r.raw.drain_conn()
        r.close()

        prepared_request = r.request.copy()
        cookies: CookieJar = prepared_request._cookies  # type: ignore[attr-defined] # noqa: SLF001
        # untyped in types-requests
        requests.cookies.extract_cookies_to_jar(  # type: ignore[no-untyped-call]
            cookies, r.request, r.raw
        )
        prepared_request.prepare_cookies(cookies)
        prepared_request.prepare_auth(self.auth)

        new_r = r.connection.send(prepared_request, **kwargs)
        new_r.history.append(r)
        new_r.request = prepared_request

        return new_r


class SessionWithHeaderRedirection(requests.Session):
    """Requests removes auth headers if the redirect happens outside the
    original req domain.
    """

    def __init__(
        self,
        edl_hostname: str,
        auth: tuple[str, str] | None = None,
        user_agent: str | None = None,
    ) -> None:
        super().__init__()
        self.headers.update({"User-Agent": user_agent or _default_user_agent()})

        if auth:
            hook = BasicAuthResponseHook(edl_hostname, auth)
            self.hooks["response"].append(hook)


class Auth:
    """Authentication class for operations that require Earthdata login (EDL)."""

    def __init__(self, user_agent: str | None = None) -> None:
        # Maybe all these predefined URLs should be in a constants.py file
        self.user_agent = user_agent or _default_user_agent()
        self.authenticated = False
        self.token: Mapping[str, str] | None = None
        self.username: str | None = None
        self.password: str | None = None
        self._set_earthdata_system(PROD)

    def login(
        self,
        strategy: str = "netrc",
        persist: bool = False,  # noqa: FBT001, FBT002
        system: System | None = None,
    ) -> Self:
        """Authenticate with Earthdata Login (EDL).

        Parameters:
            strategy:
                The authentication method.

                * **"interactive"**: Enter a username and password.
                * **"netrc"**: (default) Retrieve a username and password from `~/.netrc`.
                * **"environment"**:
                    Retrieve either a username and password pair from the
                    `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` environment variables,
                    or an Earthdata login token from the `EARTHDATA_TOKEN` environment
                    variable.
            persist: Persist username and password credentials in a `.netrc` file.
            system: The EDL endpoint to authenticate against. Defaults to `PROD`.

        Returns:
            This `Auth` instance, now authenticated.

        Raises:
            LoginAttemptFailure: If the NASA Earthdata Login service rejects
                credentials.
            ValueError: If `strategy` is not a known strategy name.
        """
        if system is not None:
            self._set_earthdata_system(system)

        if self.authenticated and (system is None or system == self.system):
            logger.debug("We are already authenticated with NASA EDL")
            return self

        if strategy == "interactive":
            self._interactive(persist)
        elif strategy == "netrc":
            self._netrc()
        elif strategy == "environment":
            self._environment()
        else:
            msg = (
                f"Unknown login strategy: {strategy!r}; expected one of "
                "'interactive', 'netrc', or 'environment'"
            )
            raise ValueError(msg)

        return self

    def _set_earthdata_system(self, system: System) -> None:
        self.system = system

        # Maybe all these predefined URLs should be in a constants.py file
        self._edl_token_url = (
            f"https://{self.system.edl_hostname}/api/users/find_or_create_token"
        )

        self._eula_url = (
            f"https://{self.system.edl_hostname}/users/earthaccess/unaccepted_eulas"
        )
        self._apps_url = f"https://{self.system.edl_hostname}/application_search"

    def get_s3_credentials(
        self,
        daac: str | None = None,
        provider: str | None = None,
        endpoint: str | None = None,
    ) -> dict[str, str]:
        """Get temporary AWS S3 credentials for a NASA DAAC's cloud bucket(s).

        Usually you only need `daac`. `provider` and `endpoint` are for when
        you already know the DAAC's cloud provider code or its
        `s3credentials` URL and want to skip the DAAC registry lookup.

        Parameters:
            daac: A DAAC's short name, e.g. `"NSIDC"` or `"PODAAC"`.
            provider: A DAAC's cloud provider code, e.g. `"NSIDC_CPRD"`.
            endpoint: A DAAC's `s3credentials` URL directly.

        Returns:
            A dict with the temporary AWS S3 credentials (`accessKeyId`,
            `secretAccessKey`, `sessionToken`, `expiration`).

        Raises:
            ValueError: If this instance has not been authenticated yet.
            S3CredentialsEndpointUnresolved: If no `s3credentials` endpoint
                could be resolved from `endpoint`, `daac`, or `provider`.
            S3CredentialsRequestFailure: If the `s3credentials` endpoint
                rejects the request, e.g. because the DAAC's EULA hasn't
                been accepted.
        """
        if not self.authenticated:
            msg = "auth must be authenticated before use"
            raise ValueError(msg)

        auth_url = endpoint or self._get_cloud_auth_url(
            daac_shortname=daac,
            provider=provider,
        )

        if not auth_url.startswith("https://"):
            # This happens if daac/provider aren't in the DAAC registry, or
            # the DAAC has no cloud collections and therefore no
            # `s3credentials` URL.
            msg = (
                f"Could not resolve an s3credentials endpoint for "
                f"daac={daac!r}, provider={provider!r}, endpoint={endpoint!r}. "
                "Pass a known DAAC short name/provider code, or the "
                "s3credentials URL directly via `endpoint`."
            )
            raise S3CredentialsEndpointUnresolved(msg)

        with self.get_session() as session, session.get(auth_url, timeout=15) as r:
            if r:
                return cast("dict[str, str]", r.json())

            msg = (
                f"The s3credentials endpoint {auth_url} rejected the request "
                f"with status {r.status_code}:\n{r.text[:1000]}\n"
                f"Consider accepting the EULAs available at {self._eula_url} "
                f"and applications at {self._apps_url}."
            )
            raise S3CredentialsRequestFailure(msg)

    def get_session(self) -> requests.Session:
        """Build a new `requests.Session` with EDL authentication configured.

        Returns:
            A `requests.Session` carrying the bearer token (if authenticated)
            and re-attaching EDL credentials after redirects.
        """
        username, password = self.username, self.password
        auth = (username, password) if username and password else None
        session = SessionWithHeaderRedirection(
            self.system.edl_hostname, auth, user_agent=self.user_agent
        )

        if self.token:
            session.headers["Authorization"] = f"Bearer {self.token['access_token']}"

        return session

    def _interactive(
        self,
        persist_credentials: bool = False,  # noqa: FBT001, FBT002
    ) -> bool:
        username = input("Enter your Earthdata Login username: ")
        password = getpass.getpass(prompt="Enter your Earthdata password: ")
        authenticated = self._get_credentials(username, password, None)
        if authenticated:
            logger.debug("Using user provided credentials for EDL")
            if persist_credentials:
                self._persist_user_credentials(username, password)
        return authenticated

    def _netrc(self) -> bool:
        netrc_loc = netrc_path()

        try:
            my_netrc = Netrc(str(netrc_loc))
        except FileNotFoundError as err:
            msg = f"No .netrc found at {netrc_loc}"
            raise LoginStrategyUnavailable(msg) from err
        except NetrcParseError as err:
            msg = f"Unable to parse .netrc file {netrc_loc}"
            raise LoginStrategyUnavailable(msg) from err

        creds = my_netrc[self.system.edl_hostname]
        if creds is None:
            msg = f"Earthdata Login hostname {self.system.edl_hostname} not found in .netrc file {netrc_loc}"
            raise LoginStrategyUnavailable(msg)

        username = creds["login"]
        password = creds["password"]

        if username is None:
            msg = f"Username not found in .netrc file {netrc_loc}"
            raise LoginStrategyUnavailable(msg)
        if password is None:
            msg = f"Password not found in .netrc file {netrc_loc}"
            raise LoginStrategyUnavailable(msg)

        authenticated = self._get_credentials(username, password, None)

        if authenticated:
            logger.debug("Using .netrc file for EDL")

        return authenticated

    def _environment(self) -> bool:
        username = os.getenv("EARTHDATA_USERNAME")
        password = os.getenv("EARTHDATA_PASSWORD")
        token = os.getenv("EARTHDATA_TOKEN")

        if (not username or not password) and not token:
            msg = (
                "Either the environment variables EARTHDATA_USERNAME and "
                "EARTHDATA_PASSWORD must both be set, or EARTHDATA_TOKEN must be set for "
                "the 'environment' login strategy."
            )
            raise LoginStrategyUnavailable(msg)

        logger.debug("Using environment variables for EDL")
        return self._get_credentials(username, password, token)

    def _get_credentials(
        self,
        username: str | None,
        password: str | None,
        user_token: str | None,
    ) -> bool:
        if user_token is not None:
            self.token = {"access_token": user_token}
            self.authenticated = True
        elif username is not None and password is not None:
            self.username = username
            self.password = password
            token_resp = self._find_or_create_token()

            if not (token_resp.ok):
                msg = f"Authentication with Earthdata Login failed with:\n{token_resp.text}"
                logger.error(msg)
                raise LoginAttemptFailure(msg)

            logger.info("You're now authenticated with NASA Earthdata Login")

            token = token_resp.json()
            logger.info("Using token with expiration date %s", token["expiration_date"])
            self.token = token
            self.authenticated = True

        return self.authenticated

    def _find_or_create_token(self) -> requests.Response:
        with self.get_session() as session:
            return session.post(
                self._edl_token_url,
                headers={"Accept": "application/json"},
                timeout=10,
            )

    def _persist_user_credentials(self, username: str, password: str) -> bool:
        # See: https://github.com/sloria/tinynetrc/issues/34

        netrc_loc = netrc_path()
        logger.info("Persisting credentials to %s", netrc_loc)

        try:
            netrc_loc.touch(exist_ok=True)
            netrc_loc.chmod(0o600)
        except OSError:
            logger.exception("Failed to persist credentials to %s", netrc_loc)
            return False

        my_netrc = Netrc(str(netrc_loc))
        my_netrc[self.system.edl_hostname] = {
            "login": username,
            "password": password,
        }
        my_netrc.save()

        urs_cookies_path = Path.home() / ".urs_cookies"

        if not urs_cookies_path.exists():
            urs_cookies_path.write_text("")

        # Create and write to .dodsrc file
        dodsrc_path = Path.home() / ".dodsrc"

        if not dodsrc_path.exists():
            dodsrc_contents = (
                f"HTTP.COOKIEJAR={urs_cookies_path}\nHTTP.NETRC={netrc_loc}"
            )
            dodsrc_path.write_text(dodsrc_contents)

        if platform.system() == "Windows":
            local_dodsrc_path = Path.cwd() / dodsrc_path.name

            if not local_dodsrc_path.exists():
                shutil.copy2(dodsrc_path, local_dodsrc_path)

        return True

    def _get_cloud_auth_url(
        self,
        daac_shortname: str | None = "",
        provider: str | None = "",
    ) -> str:
        for daac in DAACS:
            if daac_shortname == daac["short-name"] or (
                provider in daac["cloud-providers"] and len(daac["s3-credentials"]) > 0
            ):
                return str(daac["s3-credentials"])
        return ""
