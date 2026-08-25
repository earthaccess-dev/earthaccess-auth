# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "earthaccess-auth[obstore]",
#     "obspec-utils",
#     "xarray",
#     "h5netcdf",
#     "h5py",
# ]
# ///
"""Read an S3-hosted granule into xarray via obstore + obspec-utils.

Fastest path for data in NASA's Earthdata Cloud, when running inside AWS
us-west-2 (same-region S3 reads avoid cross-region egress).
"""

import xarray as xr
from obspec_utils.readers import EagerStoreReader
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

path = "daymet/Daymet_Daily_V4R1/data/daymet_v4_daily_pr_dayl_1950.nc"
reader = EagerStoreReader(store, path)
ds = xr.open_dataset(reader, engine="h5netcdf")
print(ds)
