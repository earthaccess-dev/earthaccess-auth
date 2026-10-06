"""Optional integrations, each guarded by an install extra.

Each module `earthaccess_auth.adapters.<name>` requires the matching
`earthaccess-auth[<name>]` extra, for `fsspec`, `obstore`, and `icechunk`.
Importing `earthaccess_auth` doesn't import any of them.
"""
