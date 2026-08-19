# earthaccess-auth

[![Tests](https://github.com/earthaccess-dev/earthaccess-auth/actions/workflows/test.yml/badge.svg)](https://github.com/earthaccess-dev/earthaccess-auth/actions/workflows/test.yml)
[![Documentation](https://readthedocs.org/projects/earthaccess-auth/badge/?version=latest)](https://earthaccess-auth.readthedocs.io/)
[![PyPI](https://img.shields.io/pypi/v/earthaccess-auth)](https://pypi.org/project/earthaccess-auth/)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/earthaccess-dev/earthaccess-auth/badge)](https://scorecard.dev/viewer/?uri=github.com/earthaccess-dev/earthaccess-auth)

A minimal-dependency distribution containing only the NASA Earthdata Login (EDL) authentication core of earthaccess: login strategies, token lifecycle, per-DAAC S3 credential exchange, and the redirect-safe requests session. Integrations with fsspec and obstore are optional extras, so auth-only consumers install none of the search/download stack.

## Motivation

Downstream services and libraries commonly need EDL auth and nothing else from earthaccess. One concrete example from the titiler ecosystem is `titiler-multidim`, which needs a bearer token string to inject into icechunk virtual chunk container headers. It deploys as an AWS Lambda zip, where earthaccess's transitive dependencies (s3fs, fsspec, python-cmr, pqdm, tenacity, ...) count against the 250 MB unpacked limit for the sake of ~500 lines of auth logic.

## Install matrix

```
pip install earthaccess-auth            # requests + tinynetrc + typing_extensions only
pip install earthaccess-auth[fsspec]    # + fsspec/aiohttp HTTPS session
pip install earthaccess-auth[obstore]   # + obstore credential provider bridge
pip install earthaccess                 # full stack (does not yet depend on this package)
```

## Example: the titiler-multidim case

```python
import earthaccess_auth

auth = earthaccess_auth.login(strategy="environment")
token = auth.token["access_token"]  # inject into icechunk http_store headers
```
