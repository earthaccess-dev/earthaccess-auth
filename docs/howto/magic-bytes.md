# Identify a file from its magic bytes

NASA Earthdata granule filenames don't always advertise their format
reliably, and you don't want to download a multi-gigabyte file just to find
out it's HDF5 instead of NetCDF classic. A byte-range request fetches just
the first few bytes, so you can check them against known file signatures
without downloading the whole object:

| Format | Magic bytes (hex) | Magic bytes (ASCII) |
| --- | --- | --- |
| HDF5 (and NetCDF-4, which is HDF5-based) | `89 48 44 46 0d 0a 1a 0a` | `\x89HDF\r\n\x1a\n` |
| HDF4 (HDF-EOS2, e.g. older MODIS/VIIRS products) | `0e 03 13 01` | `\x0e\x03\x13\x01` |
| NetCDF classic (CDF-1/2) | `43 44 46 01` / `43 44 46 02` | `CDF\x01` / `CDF\x02` |
| NetCDF classic (CDF-5, 64-bit) | `43 44 46 05` | `CDF\x05` |
| GeoTIFF (little-endian) | `49 49 2a 00` | `II*\x00` |
| GeoTIFF (big-endian) | `4d 4d 00 2a` | `MM\x00*` |

Zarr has no comparable magic bytes. A Zarr store is a directory (or
prefix) of many small objects (`zarr.json`/`.zarray`, `.zmetadata`, chunk
files), not a single self-describing binary blob. "Is this Zarr?" means
checking whether a `zarr.json` or `.zarray` key exists at that prefix, not
sniffing bytes.

```python
--8 < --"examples/magic_bytes.py"
```

This script is [`examples/magic_bytes.py`](https://github.com/earthaccess-dev/earthaccess-auth/blob/main/examples/magic_bytes.py),
and declares its own dependencies ([PEP 723](https://peps.python.org/pep-0723/)),
so `uv run examples/magic_bytes.py` works standalone.
