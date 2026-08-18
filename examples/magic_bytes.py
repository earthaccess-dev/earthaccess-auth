# /// script
# requires-python = ">=3.11"
# dependencies = ["earthaccess-auth[obstore]"]
#
# [tool.uv.sources]
# # TODO: switch to a released earthaccess-auth once this branch merges
# earthaccess-auth = { git = "https://github.com/maxrjones/earthaccess", subdirectory = "earthaccess-auth", branch = "poc/earthaccess-auth" }
# ///
"""Identify a granule's format from its magic bytes, without downloading it.

A byte-range request pulls just the first few bytes, cheap even for a
multi-gigabyte file.
"""

from obstore.store import S3Store

import earthaccess_auth
from earthaccess_auth.adapters.obstore import s3_credential_provider

auth = earthaccess_auth.login()

credential_provider = s3_credential_provider(
    auth,
    credentials_endpoint="https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
)
store = S3Store(
    "lp-prod-protected",
    region="us-west-2",
    credential_provider=credential_provider,
)

path = (
    "GWELDMO.031/L07.Globe.month11.2001.hh10vv08.h4v5.doy309to334.NBAR.v3.1/"
    "L07.Globe.month11.2001.hh10vv08.h4v5.doy309to334.NBAR.v3.1.hdf"
)
header = bytes(store.get_range(path, start=0, end=8))

if header == b"\x89HDF\r\n\x1a\n":
    print("HDF5 (or NetCDF-4)")
elif header[:4] == b"\x0e\x03\x13\x01":
    print("HDF4 (or HDF-EOS2)")
elif header[:3] == b"CDF":
    print(f"NetCDF classic, version {header[3]}")
else:
    print(f"unrecognized: {header!r}")
