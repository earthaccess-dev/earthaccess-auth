# earthaccess-auth

[![Tests](https://github.com/earthaccess-dev/earthaccess-auth/actions/workflows/test.yml/badge.svg)](https://github.com/earthaccess-dev/earthaccess-auth/actions/workflows/test.yml)
[![Documentation](https://readthedocs.org/projects/earthaccess-auth/badge/?version=latest)](https://earthaccess-auth.readthedocs.io/)
[![PyPI](https://img.shields.io/pypi/v/earthaccess-auth)](https://pypi.org/project/earthaccess-auth/)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/earthaccess-dev/earthaccess-auth/badge)](https://scorecard.dev/viewer/?uri=github.com/earthaccess-dev/earthaccess-auth)

A minimal-dependency distribution containing only the NASA Earthdata Login (EDL) authentication core of earthaccess: login strategies, token lifecycle, per-DAAC S3 credential exchange, and the redirect-safe requests session. Integrations with fsspec and obstore are optional extras, so auth-only consumers install none of the search/download stack.

## Motivation

Several downstream services need EDL auth and nothing else from earthaccess. Two concrete examples from the titiler ecosystem:

- titiler-multidim needs a bearer token string to inject into icechunk virtual chunk container headers. It deploys as an AWS Lambda zip, where earthaccess's transitive dependencies (s3fs, fsspec, python-cmr, pqdm, tenacity, ...) count against the 250 MB unpacked limit for the sake of ~500 lines of auth logic.
- titiler-cmr uses `earthaccess.login()` plus `get_fsspec_https_session()` and `get_s3_credentials()`; it uses CMR search too, so it keeps full earthaccess, but its auth usage is exactly the surface extracted here.

obstore has independently grown `obstore.auth.earthdata` (EDL to temporary S3 credential exchange, sync and async, with refresh). Without a shared auth core, EDL logic now lives in at least two places and drifts. This package is the proposed single home; the obstore extra bridges to (not duplicates) obstore's provider.

Stayed in earthaccess: everything else. `earthaccess/auth.py`, `system.py`, and `daac.py` are now re-export shims, `earthaccess/exceptions.py` re-exports the two login exceptions, and earthaccess depends on `earthaccess-auth`, so no import path broke and there is exactly one implementation. The earthaccess-side changes — shims, dependency edits, and the test split — are documented in [MIGRATION.md](MIGRATION.md).

## Install matrix

```
pip install earthaccess-auth            # requests + tinynetrc + typing_extensions only
pip install earthaccess-auth[fsspec]    # + fsspec/aiohttp HTTPS session
pip install earthaccess-auth[obstore]   # + obstore credential provider bridge
pip install earthaccess                 # unchanged UX; depends on earthaccess-auth
```

## Example: the titiler-multidim case

```python
import earthaccess_auth

auth = earthaccess_auth.login(strategy="environment")
token = auth.token["access_token"]  # inject into icechunk http_store headers
```

## Repo mechanics

`earthaccess-auth` lives in its own repository, versioned and released independently of [earthaccess](https://github.com/earthaccess-dev/earthaccess) (which depends on it). The project is managed with [uv](https://docs.astral.sh/uv/); see [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow.
