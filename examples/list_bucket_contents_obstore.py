# /// script
# requires-python = ">=3.11"
# dependencies = ["earthaccess-auth[obstore]"]
#
# [tool.uv.sources]
# # TODO: switch to a released earthaccess-auth once this branch merges
# earthaccess-auth = { git = "https://github.com/maxrjones/earthaccess", subdirectory = "earthaccess-auth", branch = "poc/earthaccess-auth" }
# ///
"""List the contents of an S3 bucket prefix.

Useful for exploring what a DAAC's cloud bucket actually contains before
building a granule URL by hand, or for a quick sanity check that S3
credentials work at all.
"""

import obstore
from obstore.store import S3Store

import earthaccess_auth
from earthaccess_auth.adapters.obstore import s3_credential_provider

auth = earthaccess_auth.login()

credential_provider = s3_credential_provider(
    auth,
    credentials_endpoint="https://data.ornldaac.earthdata.nasa.gov/s3credentials",
)
store = S3Store(
    "ornl-cumulus-prod-protected",
    region="us-west-2",
    credential_provider=credential_provider,
)

for batch in obstore.list(store, prefix="daymet/Daymet_Daily_V4R1/data"):
    for obj in batch:
        print(obj["path"], obj["size"])
