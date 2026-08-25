# Read a dataset with xarray

Every NASA Earthdata granule is served from one of two places: a plain
HTTPS URL (on-prem DAAC archives), or an S3 bucket in `us-west-2` (NASA
Earthdata Cloud, for clients running in that same region). Once you're
authenticated, `earthaccess-auth` gets you a credential provider or a
headers dict for either, and whichever file-like wrapper you pick —
[obspec-utils](https://github.com/developmentseed/obspec-utils)'s
`EagerStoreReader`, or plain `fsspec`/`s3fs` — the `xarray.open_dataset`
call underneath doesn't change.

=== "obstore (S3)"

    Requires the `obstore` extra plus `obspec-utils`:
    `pip install earthaccess-auth[obstore] obspec-utils`.

    ```python
    --8<-- "examples/read_a_dataset_obstore.py"
    ```

=== "s3fs (S3)"

    Already on `s3fs`/`fsspec` elsewhere? `earthaccess-auth`'s core (no
    extras) is enough: `get_s3_credentials()` returns a plain temporary AWS
    credential dict that `s3fs.S3FileSystem` accepts directly, no separate
    adapter needed.

    ```python
    --8<-- "examples/read_a_dataset_s3fs.py"
    ```

=== "obspec-utils (HTTPS)"

    Requires the `obstore` extra (for `http_client_options`) plus
    `obspec-utils` and `aiohttp`:
    `pip install earthaccess-auth[obstore] obspec-utils aiohttp`.

    Use this for granules that are on-prem only (no S3 bucket), or for
    cloud-hosted granules when you're running outside `us-west-2` and don't
    want to pay cross-region S3 egress — the example below reads a
    cloud-hosted granule this way, over HTTPS instead of S3, so the same
    file stays comparable across all four tabs.

    ```python
    --8<-- "examples/read_a_dataset_obspec_utils.py"
    ```

=== "fsspec (HTTPS)"

    Requires only the `fsspec` extra: `pip install earthaccess-auth[fsspec]`
    — no obstore, no obspec-utils. Same use case as the obspec-utils tab
    (on-prem granules, or cross-region reads), for when you're already on
    fsspec elsewhere.

    ```python
    --8<-- "examples/read_a_dataset_fsspec.py"
    ```

All four scripts live in
[`examples/`](https://github.com/earthaccess-dev/earthaccess-auth/tree/main/examples)
and declare their own dependencies ([PEP 723](https://peps.python.org/pep-0723/)),
so e.g. `uv run examples/read_a_dataset_obstore.py` works standalone, no separate
install step required.

!!! note "S3 credentials are DAAC-scoped and short-lived"

    `get_s3_credentials()` / `EarthdataS3CredentialProvider` yield
    credentials valid for one DAAC's cloud bucket(s), for about an hour. If
    you're reading granules from more than one DAAC, fetch credentials per
    DAAC; if a read fails with an auth error partway through a long-running
    job, get fresh credentials rather than retrying with the ones you have.
    The obstore provider refreshes on its own, but `s3fs` doesn't — re-call
    `get_s3_credentials()` yourself once credentials near expiry. (The
    `fsspec (HTTPS)` tab uses a bearer token instead of S3 credentials,
    with its own separate expiry.)

See [Choosing a backend](../explanation/choosing-a-backend.md) for how to
decide between these four.
