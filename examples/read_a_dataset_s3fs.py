# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "earthaccess-auth",
#     "s3fs",
#     "xarray",
#     "h5netcdf",
# ]
#
# [tool.uv.sources]
# # TODO: switch to a released earthaccess-auth once this branch merges
# earthaccess-auth = { git = "https://github.com/maxrjones/earthaccess", subdirectory = "earthaccess-auth", branch = "poc/earthaccess-auth" }
# ///
"""Read an S3-hosted granule into xarray via s3fs.

For when you're already using s3fs/fsspec elsewhere and don't want to add
obstore as a second S3 client. earthaccess-auth's core (no extras) is
enough: get_s3_credentials() returns a plain AWS credential dict that
s3fs.S3FileSystem accepts directly.
"""

import s3fs
import xarray as xr

import earthaccess_auth

auth = earthaccess_auth.login()

creds = auth.get_s3_credentials(daac="ORNLDAAC")
fs = s3fs.S3FileSystem(
    key=creds["accessKeyId"],
    secret=creds["secretAccessKey"],
    token=creds["sessionToken"],
    client_kwargs={"region_name": "us-west-2"},
)

path = "ornl-cumulus-prod-protected/daymet/Daymet_Daily_V4R1/data/daymet_v4_daily_pr_dayl_1950.nc"
ds = xr.open_dataset(fs.open(path), engine="h5netcdf")
print(ds)
