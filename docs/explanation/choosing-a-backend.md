# Choosing a backend

If you're running in AWS `us-west-2` and the data is cloud-hosted, go
straight to S3 with `obstore`: fastest reads, automatic credential refresh.

If you're running anywhere else, or the collection is on-prem only, use
`obspec_utils.stores.AiohttpStore` with the headers dict from
`http_client_options`. Cross-region S3 reads are billed to the requester
and slower than same-region reads.

Already on `fsspec` and don't want obstore or obspec-utils in the mix?
`get_fsspec_https_session()` builds an `fsspec.AbstractFileSystem`
(`HTTPFileSystem`) straight from the bearer token — same use case as
`AiohttpStore`, just the `[fsspec]` extra instead of `[obstore]`. See the
`fsspec (HTTPS)` tab of
[Read a dataset with xarray](../howto/read-a-dataset.md).

Already on `s3fs`? `get_s3_credentials()` returns a plain temporary AWS
credential dict that `s3fs.S3FileSystem` (like anything else `boto3`-shaped)
accepts directly — no separate adapter needed, just no automatic refresh:
re-call `get_s3_credentials()` yourself once credentials near expiry. See
the `s3fs` tab of
[List the contents of an S3 bucket](../howto/list-bucket-contents.md).

If you just need a token or headers and no file access at all, skip both.
See [Get S3 credentials and bearer tokens](../howto/s3-credentials-and-bearer-token.md).
