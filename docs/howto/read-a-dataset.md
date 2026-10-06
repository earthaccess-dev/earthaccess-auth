# Read a dataset with xarray

NASA Earthdata serves each granule from one of two places:

- a plain HTTPS URL, from an on-prem DAAC archive
- an S3 bucket in `us-west-2`, from NASA Earthdata Cloud, for clients that
  run in that region

After you log in, `earthaccess-auth` gives you a credential provider or a
headers dict for each of these. You can open the file with
[obspec-utils](https://github.com/developmentseed/obspec-utils)'s
`EagerStoreReader`, or with `fsspec` or `s3fs`. The call to
`xarray.open_dataset` is the same for all of them.

=== "obstore (S3)"

    Requires the `obstore` extra and `obspec-utils`:
    `pip install earthaccess-auth[obstore] obspec-utils`.

    ```python
    --8<-- "examples/read_a_dataset_obstore.py"
    ```

=== "s3fs (S3)"

    If you already use `s3fs` or `fsspec`, you need only the core of
    `earthaccess-auth`, with no extras. `get_s3_credentials()` returns a
    dict of temporary AWS credentials. `s3fs.S3FileSystem` accepts this dict
    directly, so you don't need an adapter.

    ```python
    --8<-- "examples/read_a_dataset_s3fs.py"
    ```

=== "obspec-utils (HTTPS)"

    Requires the `obstore` extra (for `http_client_options`), `obspec-utils`,
    and `aiohttp`:
    `pip install earthaccess-auth[obstore] obspec-utils aiohttp`.

    Use this for granules that are only on-prem, with no S3 bucket. Also
    use it for cloud-hosted granules when your code runs outside
    `us-west-2`, so that you don't pay for S3 egress to a different region.
    The example reads a cloud-hosted granule over HTTPS instead of S3. This
    way, all four tabs read the same file.

    ```python
    --8<-- "examples/read_a_dataset_obspec_utils.py"
    ```

=== "fsspec (HTTPS)"

    Requires only the `fsspec` extra: `pip install earthaccess-auth[fsspec]`.
    It doesn't need obstore or obspec-utils. Use it for the same cases as
    the obspec-utils tab, on-prem granules or reads from a different region,
    when you already use fsspec.

    ```python
    --8<-- "examples/read_a_dataset_fsspec.py"
    ```

All four scripts are in
[`examples/`](https://github.com/earthaccess-dev/earthaccess-auth/tree/main/examples).
Each script declares its own dependencies
([PEP 723](https://peps.python.org/pep-0723/)), so you can run it directly,
for example with `uv run examples/read_a_dataset_obstore.py`. You don't
need a separate install step.

!!! note "S3 credentials are for one DAAC and expire after about an hour"

    `get_s3_credentials()` and `EarthdataS3CredentialProvider` give
    credentials for the cloud buckets of one DAAC. The credentials are valid
    for about one hour.

    - If you read granules from more than one DAAC, get credentials for
      each DAAC.
    - If a read fails with an authentication error during a long job, get
      new credentials. Don't try again with the old ones.
    - The obstore provider refreshes credentials automatically. `s3fs`
      doesn't. With `s3fs`, call `get_s3_credentials()` again before the
      credentials expire.

    The `fsspec (HTTPS)` tab uses a bearer token, not S3 credentials. The
    token has a different expiry time.

See [Choosing a backend](../explanation/choosing-a-backend.md) to decide
which of the four to use.
