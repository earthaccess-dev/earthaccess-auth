"""Authenticated fsspec HTTPS filesystem (extra: earthaccess-auth[fsspec])."""

import fsspec

from earthaccess_auth.auth import Auth


def get_fsspec_https_session(auth: Auth) -> fsspec.AbstractFileSystem:
    """Build an fsspec HTTPFileSystem that sends the EDL bearer token on every request.

    `trust_env` is disabled: if aiohttp also picked up ambient credentials
    from the environment while a bearer token is set, EDL would reject the
    request.

    Parameters:
        auth: An authenticated `Auth` instance.

    Returns:
        An `fsspec.AbstractFileSystem` (`HTTPFileSystem`) ready to pass to
        `xarray.open_dataset` or open files directly.

    Raises:
        ValueError: If `auth` has not been authenticated (`auth.token is None`).
    """
    if auth.token is None:
        msg = "auth must be authenticated before use"
        raise ValueError(msg)
    token = auth.token["access_token"]
    client_kwargs = {
        "headers": {"Authorization": f"Bearer {token}"},
        "trust_env": False,
    }
    return fsspec.filesystem("https", client_kwargs=client_kwargs)
