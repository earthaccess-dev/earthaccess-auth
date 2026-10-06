# List the contents of an S3 bucket

List a bucket to see what a DAAC's cloud bucket contains before you write a
granule URL by hand. You can also use a listing to check that your S3
credentials work.

=== "obstore"

    ```python
    --8<-- "examples/list_bucket_contents_obstore.py"
    ```

    [`obstore.list()`][obstore.list] returns a stream of pages. Each
    iteration gives one page: a list of `ObjectMeta` dicts (`path`, `size`,
    `last_modified`, `e_tag`), with 50 items by default. A nested loop reads
    the items in each page. obstore fetches each page only when the loop
    needs it, so it doesn't load the full prefix into memory.

=== "s3fs"

    If you already use `s3fs` or `fsspec`, you need only the core of
    `earthaccess-auth`, with no extras.
    [`Auth.get_s3_credentials`][earthaccess_auth.Auth.get_s3_credentials]
    returns a dict of temporary AWS credentials. `s3fs.S3FileSystem` and
    other `boto3`-style clients accept this dict directly, so you don't need
    an adapter. See
    [Get S3 credentials and bearer tokens](s3-credentials-and-bearer-token.md).

    ```python
    --8<-- "examples/list_bucket_contents_s3fs.py"
    ```

    `S3FileSystem.ls()` returns one flat list, not a stream of pages. This
    is easier for a small listing. But it loads the full prefix into memory.

Both scripts are in
[`examples/`](https://github.com/earthaccess-dev/earthaccess-auth/tree/main/examples).
Each script declares its own dependencies
([PEP 723](https://peps.python.org/pep-0723/)), so you can run it directly
with `uv run examples/list_bucket_contents_obstore.py` or
`uv run examples/list_bucket_contents_s3fs.py`.
