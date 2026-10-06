# Identify a file from its magic bytes

The filename of a NASA Earthdata granule doesn't always show its format.
To find the format, you don't have to download a file that can be many
gigabytes. Use a byte-range request to get only the first bytes. Then
compare them with these known file signatures:

| Format | Magic bytes (hex) | Magic bytes (ASCII) |
| --- | --- | --- |
| HDF5 (and NetCDF-4, which is HDF5-based) | `89 48 44 46 0d 0a 1a 0a` | `\x89HDF\r\n\x1a\n` |
| HDF4 (HDF-EOS2, e.g. older MODIS/VIIRS products) | `0e 03 13 01` | `\x0e\x03\x13\x01` |
| NetCDF classic (CDF-1/2) | `43 44 46 01` / `43 44 46 02` | `CDF\x01` / `CDF\x02` |
| NetCDF classic (CDF-5, 64-bit) | `43 44 46 05` | `CDF\x05` |
| GeoTIFF (little-endian) | `49 49 2a 00` | `II*\x00` |
| GeoTIFF (big-endian) | `4d 4d 00 2a` | `MM\x00*` |

Zarr has no magic bytes. A Zarr store is not one binary file. It is a
directory or prefix that contains many small objects: `zarr.json` or
`.zarray`, `.zmetadata`, and chunk files. To find out if a prefix is a Zarr
store, check if a `zarr.json` or `.zarray` key exists at that prefix.

```python
--8<-- "examples/magic_bytes.py"
```

This script is [`examples/magic_bytes.py`](https://github.com/earthaccess-dev/earthaccess-auth/blob/main/examples/magic_bytes.py).
It declares its own dependencies ([PEP 723](https://peps.python.org/pep-0723/)),
so you can run it directly with `uv run examples/magic_bytes.py`.
