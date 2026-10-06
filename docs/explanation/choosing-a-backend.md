# Choosing a backend

If your code runs in AWS `us-west-2` and the data is cloud-hosted, read
directly from S3 with `obstore`. This gives the fastest reads, and obstore
refreshes the credentials automatically.

If your code runs in a different region, or the collection is only
on-prem, use
[`obspec_utils.stores.AiohttpStore`][obspec_utils.stores.AiohttpStore]
with the headers dict from
[`http_client_options`][earthaccess_auth.adapters.obstore.http_client_options]. S3 reads from a different region are slower, and
the requester pays for them.

If you already use `fsspec` and don't want obstore or obspec-utils, use
[`get_fsspec_https_session()`][earthaccess_auth.adapters.fsspec.get_fsspec_https_session].
It builds an [`fsspec.AbstractFileSystem`][fsspec.spec.AbstractFileSystem]
([`HTTPFileSystem`][fsspec.implementations.http.HTTPFileSystem]) that sends
the bearer token. It has the same use case as `AiohttpStore`, but it needs the `[fsspec]` extra instead of
`[obstore]`. See the `fsspec (HTTPS)` tab of
[Read a dataset with xarray](../howto/read-a-dataset.md).

If you already use `s3fs`, call
[`get_s3_credentials()`][earthaccess_auth.Auth.get_s3_credentials]. It
returns a dict of temporary AWS credentials.
[`s3fs.S3FileSystem`][s3fs.core.S3FileSystem] and other `boto3`-style
clients accept this dict directly, so you don't need an adapter. These
credentials don't refresh automatically. Call `get_s3_credentials()` again
before they expire. See the `s3fs` tab of
[List the contents of an S3 bucket](../howto/list-bucket-contents.md).

If you only need a token or headers and no file access, you don't need any
of these backends. See
[Get S3 credentials and bearer tokens](../howto/s3-credentials-and-bearer-token.md).
