# Get S3 credentials and bearer tokens

`earthaccess-auth` gives you three things once you're logged in: a bearer
token, temporary AWS S3 credentials, and (via the `obstore` extra) a
credential *provider* that fetches and refreshes those credentials for you.
Which one you want depends on what you're handing it to. Each of these is
also a standalone, runnable script in
[`examples/`](https://github.com/earthaccess-dev/earthaccess-auth/tree/main/examples)
declaring its own dependencies ([PEP 723](https://peps.python.org/pep-0723/)).

## The raw bearer token

The minimal case: no fsspec, no obstore, just the token string. Inject it
into a header yourself. This is the pattern a Lambda-deployed consumer with
a tight dependency budget would use.

```python
--8 < --"examples/bearer_token.py"
```

## Header dict for HTTP-based stores

For anything that accepts a plain `headers` dict (obstore HTTP stores,
obspec-utils's `AiohttpStore` — see [Read a dataset with xarray](read-a-dataset.md)
— or icechunk's `http_store(headers=...)` for virtual chunk containers) use
`http_client_options`:

```python
--8 < --"examples/http_headers.py"
```

## Temporary AWS S3 credentials

For anything that wants `key`/`secret`/`token` (or `aws_access_key_id`
/`aws_secret_access_key`/`aws_session_token`) directly, such as `boto3`,
`s3fs`, or the AWS CLI:

```python
--8 < --"examples/s3_credentials.py"
```

You can look credentials up by DAAC short name (`daac="NSIDC"`), by cloud
provider code (`provider="NSIDC_CPRD"`, from
[`find_provider`](../reference/api.md#earthaccess_auth.daac.find_provider)), or by a raw `s3credentials`
endpoint URL (`endpoint=...`) if you already have one. These credentials
are scoped to that DAAC's cloud bucket(s) and expire in about an hour, so
don't cache them longer than that.

## An obstore credential *provider*

If you're handing credentials to an [`obstore.store.S3Store`][] (see
[Read a dataset with xarray](read-a-dataset.md)), pass a *provider* instead
of a one-shot credentials dict. The provider re-calls `get_s3_credentials()`
on its own once the current credentials near expiry, so a long-running job
doesn't need its own refresh loop:

```python
--8 < --"examples/s3_credential_provider.py"
```

`credentials_endpoint` is a DAAC's `s3credentials` URL: the
`"s3-credentials"` field on each entry in
[`DAACS`](../reference/api.md#earthaccess_auth.daac.DAACS).
