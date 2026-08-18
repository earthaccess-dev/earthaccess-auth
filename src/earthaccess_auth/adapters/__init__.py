"""Optional integrations, each guarded by an install extra.

`earthaccess_auth.adapters.fsspec` requires earthaccess-auth[fsspec];
`earthaccess_auth.adapters.obstore` requires earthaccess-auth[obstore].
Nothing here imports at package-import time, so the core stays
requests-only.
"""
