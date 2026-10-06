# earthaccess-auth

`earthaccess-auth` contains only the NASA Earthdata Login (EDL)
authentication core of
[earthaccess](https://github.com/earthaccess-dev/earthaccess). It has few
dependencies. It includes the login strategies, token handling, the S3
credential exchange for each DAAC, and a requests session that keeps
authentication across redirects.

Optional extras add integrations with
[fsspec](https://filesystem-spec.readthedocs.io/),
[obstore](https://developmentseed.org/obstore/), and
[icechunk](https://icechunk.io/).

Use this library to read data from NASA cloud buckets when you don't need
CMR search.

## Install

```
pip install earthaccess-auth            # requests + tinynetrc only
pip install earthaccess-auth[fsspec]    # + fsspec/aiohttp HTTPS session
pip install earthaccess-auth[obstore]   # + obstore credential provider
pip install earthaccess-auth[icechunk]  # + icechunk credentials
```

## Quickstart

```python
import earthaccess_auth

auth = earthaccess_auth.login()  # tries env vars, then ~/.netrc, then prompts
if not auth.authenticated:
    raise SystemExit("no Earthdata Login credentials found")
token = auth.token["access_token"]
```

`login()` returns a new `Auth` instance each time. You can keep more than
one authenticated instance and pass each one where you need it.

## Where to go next

- [Read a dataset with xarray](howto/read-a-dataset.md): obstore, s3fs, obspec-utils, and fsspec, side by side
- [List the contents of an S3 bucket](howto/list-bucket-contents.md)
- [Identify a file from its magic bytes](howto/magic-bytes.md)
- [Get S3 credentials and bearer tokens](howto/s3-credentials-and-bearer-token.md)
- [Choosing a backend](explanation/choosing-a-backend.md): obstore vs. obspec-utils vs. fsspec vs. s3fs
- [API reference](reference/api.md)
