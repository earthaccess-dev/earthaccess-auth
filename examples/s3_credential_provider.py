# /// script
# requires-python = ">=3.11"
# dependencies = ["earthaccess-auth[obstore]"]
#
# [tool.uv.sources]
# # TODO: switch to a released earthaccess-auth once this branch merges
# earthaccess-auth = { git = "https://github.com/maxrjones/earthaccess", subdirectory = "earthaccess-auth", branch = "poc/earthaccess-auth" }
# ///
"""Build an obstore credential provider that refreshes S3 credentials itself.

Hand this to obstore.store.S3Store (or obspec_utils' readers, see
read_a_dataset_obstore.py) instead of a one-shot credentials dict, so a
long-running job doesn't need its own refresh loop.
"""

import earthaccess_auth
from earthaccess_auth.adapters.obstore import s3_credential_provider

auth = earthaccess_auth.login()

credential_provider = s3_credential_provider(
    auth,
    credentials_endpoint="https://data.nsidc.earthdatacloud.nasa.gov/s3credentials",
)
print(credential_provider)
