# List the contents of an S3 bucket

Useful for exploring what a DAAC's cloud bucket actually contains before you
build a granule URL by hand, or for a quick sanity check that your S3
credentials work at all.

=== "obstore"

    ```python
    --8<-- "examples/list_bucket_contents_obstore.py"
    ```

    [`obstore.list()`][obstore.list] returns a lazily-paginated stream: each
    iteration yields a chunk (a list, 50 items by default) of `ObjectMeta`
    dicts (`path`, `size`, `last_modified`, `e_tag`), not a single object, so
    a nested loop unpacks each chunk. Iterating fetches pages as needed
    instead of loading the whole prefix into memory up front.

=== "s3fs"

    Already on `s3fs`/`fsspec` elsewhere? `earthaccess-auth`'s core (no
    extras) is enough:
    [`Auth.get_s3_credentials`][earthaccess_auth.Auth.get_s3_credentials]
    returns a plain temporary AWS credential dict that `s3fs.S3FileSystem`
    (like anything else `boto3`-shaped) accepts directly, no separate
    adapter needed. See
    [Get S3 credentials and bearer tokens](s3-credentials-and-bearer-token.md).

    ```python
    --8<-- "examples/list_bucket_contents_s3fs.py"
    ```

    Unlike `obstore.list()`, `S3FileSystem.ls()` returns a single flat list
    rather than a paginated stream — simpler for a quick listing, but it
    collects the whole prefix into memory instead of paging through it.

Both scripts live in
[`examples/`](https://github.com/earthaccess-dev/earthaccess-auth/tree/main/examples)
and declare their own dependencies ([PEP 723](https://peps.python.org/pep-0723/)),
so `uv run examples/list_bucket_contents_obstore.py` (or
`uv run examples/list_bucket_contents_s3fs.py`) works standalone.
