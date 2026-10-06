# Get S3 credentials and bearer tokens

After you log in, `earthaccess-auth` can give you three things:

- a bearer token
- temporary AWS S3 credentials
- a credential *provider*, with the `obstore` extra, that fetches and
  refreshes S3 credentials for you

The correct one depends on the tool that uses it. Each example on this page
is also a script in
[`examples/`](https://github.com/earthaccess-dev/earthaccess-auth/tree/main/examples)
that you can run. Each script declares its own dependencies
([PEP 723](https://peps.python.org/pep-0723/)).

## The raw bearer token

This is the smallest case. It needs no fsspec and no obstore, only the
token string. You put the token into a header yourself. Use this when you
must keep dependencies to a minimum, for example in an AWS Lambda
function.

```python
--8<-- "examples/bearer_token.py"
```

## Header dict for HTTP-based stores

Use
[`http_client_options`][earthaccess_auth.adapters.obstore.http_client_options]
for any tool that accepts a plain `headers` dict. Examples:

- obstore HTTP stores
- obspec-utils's [`AiohttpStore`][obspec_utils.stores.AiohttpStore] (see
  [Read a dataset with xarray](read-a-dataset.md))
- icechunk's [`http_store(headers=...)`][icechunk.http_store] for virtual
  chunk containers

```python
--8<-- "examples/http_headers.py"
```

## Temporary AWS S3 credentials

Use these for tools that need `key`, `secret`, and `token`, or
`aws_access_key_id`, `aws_secret_access_key`, and `aws_session_token`.
Examples are `boto3`, `s3fs`, and the AWS CLI.

```python
--8<-- "examples/s3_credentials.py"
```

You can find credentials in three ways:

- by DAAC short name (`daac="NSIDC"`)
- by cloud provider code (`provider="NSIDC_CPRD"`), which
  [`find_provider`][earthaccess_auth.daac.find_provider]
  returns
- by `s3credentials` endpoint URL (`endpoint=...`), if you already have
  one

The credentials are valid only for the cloud buckets of that DAAC. They
expire after about one hour. Don't keep them in a cache for longer than
that.

## An obstore credential *provider*

To give credentials to an [`obstore.store.S3Store`][] (see
[Read a dataset with xarray](read-a-dataset.md)), use a *provider*, not a
credentials dict. The provider gets new credentials before the current
ones expire. It gets them through the process-wide credential cache, which
all stores that use the same endpoint share. So a long job doesn't need its
own refresh loop.

```python
--8<-- "examples/s3_credential_provider.py"
```

The endpoint argument is the `s3credentials` URL of a DAAC. Each entry in
[`DAACS`][earthaccess_auth.daac.DAACS] has this URL in
its `"s3-credentials"` field. If the bucket is in the CMR-derived registry,
use
[`EarthdataS3CredentialProvider.for_bucket`][earthaccess_auth.adapters.obstore.EarthdataS3CredentialProvider.for_bucket]
instead. It finds the
endpoint and region from a bucket name or an `s3://` URL.
