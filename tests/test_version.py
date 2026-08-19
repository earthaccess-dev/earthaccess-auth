"""The package exposes its installed version as ``__version__``."""

from importlib.metadata import version

import earthaccess_auth


def test_dunder_version_matches_installed_metadata() -> None:
    assert earthaccess_auth.__version__ == version("earthaccess-auth")
