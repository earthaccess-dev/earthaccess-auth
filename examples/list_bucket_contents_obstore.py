# /// script
# requires-python = ">=3.12"
# dependencies = ["earthaccess-auth[obstore]"]
# ///
"""List the contents of an S3 bucket prefix.

Useful for exploring what a DAAC's cloud bucket actually contains before
building a granule URL by hand, or for a quick sanity check that S3
credentials work at all.
"""

import obstore
from obstore.store import S3Store

import earthaccess_auth
from earthaccess_auth.adapters.obstore import EarthdataS3CredentialProvider

earthaccess_auth.set_default_auth(earthaccess_auth.login())

credential_provider = EarthdataS3CredentialProvider(
    "https://data.ornldaac.earthdata.nasa.gov/s3credentials",
)
store = S3Store(
    "ornl-cumulus-prod-protected",
    region="us-west-2",
    credential_provider=credential_provider,
)

for batch in obstore.list(store, prefix="daymet/Daymet_Daily_V4R1/data"):
    for obj in batch:
        print(obj["path"], obj["size"])
