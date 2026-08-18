# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "earthaccess-auth[obstore]",
#     "obspec-utils",
#     "aiohttp",
#     "xarray",
#     "h5netcdf",
# ]
#
# [tool.uv.sources]
# # TODO: switch to a released earthaccess-auth once this branch merges
# earthaccess-auth = { git = "https://github.com/maxrjones/earthaccess", subdirectory = "earthaccess-auth", branch = "poc/earthaccess-auth" }
# ///
"""Read a granule into xarray over HTTPS via obspec-utils.

Use this for on-prem-only granules (no S3 bucket), or for cloud-hosted
granules when you're running outside us-west-2 and cross-region S3 egress
isn't worth paying for. Uses the same EagerStoreReader as the S3 example,
reading the identical granule: xarray doesn't need to know which backend
is underneath.
"""

import xarray as xr
from obspec_utils.readers import EagerStoreReader
from obspec_utils.stores import AiohttpStore

import earthaccess_auth
from earthaccess_auth.adapters.obstore import http_client_options

auth = earthaccess_auth.login()
headers = http_client_options(auth)["default_headers"]

url = "https://data.ornldaac.earthdata.nasa.gov/protected/daymet/Daymet_Daily_V4R1/data/daymet_v4_daily_pr_dayl_1950.nc"
base_url, path = url.rsplit("/", 1)

store = AiohttpStore(base_url, headers=headers)
reader = EagerStoreReader(store, path)
ds = xr.open_dataset(reader, engine="h5netcdf")
print(ds)
