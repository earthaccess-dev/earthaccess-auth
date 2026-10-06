# earthaccess-auth

A minimal-dependency distribution containing only the NASA Earthdata Login
(EDL) authentication core of [earthaccess](https://github.com/earthaccess-dev/earthaccess),
such as login strategies, token lifecycle, per-DAAC S3 credential exchange, and the
redirect-safe requests session.

`earthacess-auth` provides integrations with [fsspec](https://filesystem-spec.readthedocs.io/),
[obstore](https://developmentseed.org/obstore/), and [icechunk](https://icechunk.io/) using
 optional extras.

This library is meant for people and applications using data in NASA cloud buckets
but not CMR search.

## Install

```
pip install earthaccess-auth            # requests + tinynetrc only
pip install earthaccess-auth[fsspec]    # + fsspec/aiohttp HTTPS session
pip install earthaccess-auth[obstore]   # + obstore credential provider bridge
```

## Quickstart

```python
import earthaccess_auth

auth = earthaccess_auth.login()  # tries env vars, then ~/.netrc, then prompts
if not auth.authenticated:
    raise SystemExit("no Earthdata Login credentials found")
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
