# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "earthaccess-auth[obstore]",
#     "obspec-utils",
#     "xarray",
#     "h5netcdf",
# ]
#
# [tool.uv.sources]
# # TODO: switch to a released earthaccess-auth once this branch merges
# earthaccess-auth = { git = "https://github.com/maxrjones/earthaccess", subdirectory = "earthaccess-auth", branch = "poc/earthaccess-auth" }
# ///
"""Read an S3-hosted granule into xarray via obstore + obspec-utils.

Fastest path for data in NASA's Earthdata Cloud, when running inside AWS
us-west-2 (same-region S3 reads avoid cross-region egress).
"""

import xarray as xr
from obspec_utils.readers import EagerStoreReader
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

path = "daymet/Daymet_Daily_V4R1/data/daymet_v4_daily_pr_dayl_1950.nc"
reader = EagerStoreReader(store, path)
ds = xr.open_dataset(reader, engine="h5netcdf")
print(ds)
