# earthaccess-auth

A minimal-dependency distribution containing only the NASA Earthdata Login
(EDL) authentication core of [earthaccess](https://github.com/earthaccess-dev/earthaccess):
login strategies, token lifecycle, per-DAAC S3 credential exchange, and the
redirect-safe requests session. Integrations with [fsspec](https://filesystem-spec.readthedocs.io/)
and [obstore](https://developmentseed.org/obstore/) are optional extras, so
auth-only consumers don't install the rest of earthaccess's search/download
stack.

If you only need a bearer token or temporary S3 credentials, not CMR search,
this package is probably all you need.

## Install

```
pip install earthaccess-auth            # requests + tinynetrc + typing_extensions only
pip install earthaccess-auth[fsspec]    # + fsspec/aiohttp HTTPS session
pip install earthaccess-auth[obstore]   # + obstore credential provider bridge
```

## Quickstart

```python
import earthaccess_auth

auth = earthaccess_auth.login()  # tries env vars, then ~/.netrc, then prompts
token = auth.token["access_token"]
```

`login()` returns an `Auth` instance rather than a module-level singleton, so
you can hold onto (or pass around) multiple authenticated sessions if you
need to.

## Where to go next

- [Read a dataset with xarray](howto/read-a-dataset.md): obstore, s3fs, obspec-utils, and fsspec, side by side
- [List the contents of an S3 bucket](howto/list-bucket-contents.md)
- [Identify a file from its magic bytes](howto/magic-bytes.md)
- [Get S3 credentials and bearer tokens](howto/s3-credentials-and-bearer-token.md)
- [Choosing a backend](explanation/choosing-a-backend.md): obstore vs. obspec-utils vs. fsspec vs. s3fs
- [API reference](reference/api.md)
