# DAACS ~= NASA Earthdata data centers

from typing import TypedDict

import requests

DAACConfig = TypedDict(
    "DAACConfig",
    {
        "short-name": str,
        "name": str,
        "homepage": str,
        "cloud-providers": list[str],
        "on-prem-providers": list[str],
        "s3-credentials": str,
        "eulas": list[str],
    },
)


DAACS: list[DAACConfig] = [
    {
        "short-name": "NSIDC",
        "name": "National Snow and Ice Data Center",
        "homepage": "https://nsidc.org",
        "cloud-providers": ["NSIDC_CPRD"],
        "on-prem-providers": ["NSIDC_ECS"],
        "s3-credentials": "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "GHRCDAAC",
        "name": "Global Hydrometeorology Resource Center",
        "homepage": "https://ghrc.nsstc.nasa.gov/home/",
        "cloud-providers": ["GHRC_DAAC"],
        "on-prem-providers": ["GHRC_DAAC"],
        "s3-credentials": "https://data.ghrc.earthdata.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "PODAAC",
        "name": "Physical Oceanography Distributed Active Archive Center",
        "homepage": "https://podaac.jpl.nasa.gov",
        "cloud-providers": ["POCLOUD"],
        "on-prem-providers": ["PODAAC"],
        "s3-credentials": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "ASF",
        "name": "Alaska Satellite Facility",
        "homepage": "https://asf.alaska.edu",
        "cloud-providers": ["ASF"],
        "on-prem-providers": ["ASF"],
        "s3-credentials": "https://sentinel1.asf.alaska.edu/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "ORNLDAAC",
        "name": "Oak Ridge National Laboratory",
        "homepage": "https://daac.ornl.gov",
        "cloud-providers": ["ORNL_CLOUD"],
        "on-prem-providers": ["ORNL_DAAC"],
        "s3-credentials": "https://data.ornldaac.earthdata.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "LPDAAC",
        "name": " Land Processes Distributed Active Archive Center",
        "homepage": "https://lpdaac.usgs.gov",
        "cloud-providers": ["LPCLOUD"],
        "on-prem-providers": ["LPDAAC_ECS"],
        "s3-credentials": "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "GES_DISC",
        "name": "NASA Goddard Earth Sciences (GES) Data and Information Services Center (DISC)",
        "homepage": "https://daac.gsfc.nasa.gov",
        "cloud-providers": ["GES_DISC"],
        "on-prem-providers": ["GES_DISC"],
        "s3-credentials": "https://data.gesdisc.earthdata.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "OBDAAC",
        "name": "NASA's Ocean Biology Distributed Active Archive Center",
        "homepage": "https://oceancolor.gsfc.nasa.gov/",
        "cloud-providers": ["OB_CLOUD"],
        "on-prem-providers": ["OB_DAAC"],
        "s3-credentials": "https://obdaac-tea.earthdatacloud.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "SEDAC",
        "name": "NASA's Socioeconomic Data and Applications Center",
        "homepage": "https://earthdata.nasa.gov/eosdis/daacs/sedac",
        "cloud-providers": [],
        "on-prem-providers": ["ESDIS"],
        "s3-credentials": "",
        "eulas": [],
    },
    {
        "short-name": "LAADS",
        "name": "Level-1 and Atmosphere Archive & Distribution System Distributed Active Archive Center",
        "homepage": "https://ladsweb.modaps.eosdis.nasa.gov/",
        "cloud-providers": ["LAADS"],
        "on-prem-providers": ["LAADS"],
        "s3-credentials": "https://data.laadsdaac.earthdatacloud.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "ASDC",
        "name": "Atmospheric Science Data Center",
        "homepage": "https://asdc.larc.nasa.gov/",
        "cloud-providers": ["LARC_CLOUD"],
        "on-prem-providers": ["LARC_ASDC"],
        "s3-credentials": "https://data.asdc.earthdata.nasa.gov/s3credentials",
        "eulas": [],
    },
]
"""The registry of NASA Earthdata DAACs known to `earthaccess-auth`.

Each entry is a `DAACConfig` describing one DAAC's short name,
cloud/on-prem provider codes, and `s3credentials` endpoint. Look entries up
with [`find_provider`][earthaccess_auth.daac.find_provider] rather than
scanning this list directly.
"""


# Some testing urls behind EDL
DAAC_TEST_URLS = [
    "https://archive.podaac.earthdata.nasa.gov/podaac-ops-cumulus-protected/JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/",
    "https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/ATLAS/ATL03/005/2018/10/14/dummy.nc",
    "https://n5eil01u.ecs.nsidc.org/DP7/ATLAS/ATL06.005/2018.10.14/ATL06_20181014045341_02380102_005_01.iso.xml",
    "https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH10_M.2.0/1948/",
    "https://e4ftl01.cr.usgs.gov//DP114/MOTA/MCD43A3.006/2000.02.24/MCD43A3.A2000055.h15v07.006.2016101151720.hdf.xml",
    "https://daac.ornl.gov/daacdata/npp/grassland/NPP_BCN/data/bcn_cli.txt",
    "https://data.asdc.earthdata.nasa.gov/asdc-prod-protected/FIELDCAMPAIGN/TRACE/TRACE-A_001/TRACE-A-tra11_90.m.Z",
]


# S3 bucket name -> `s3credentials` endpoint. Sourced from CMR's
# `DirectDistributionInformation.S3BucketAndObjectPrefixNames` /
# `S3CredentialsAPIEndpoint` fields (see
# `earthaccess-auth/scripts/sync_bucket_registry.py` and
# `docs/explanation/cmr-s3-buckets.md`), which is authoritative straight
# from CMR rather than guessed from the bucket name. This is a flat mapping
# rather than a per-`DAACConfig` field because the endpoint doesn't always
# line up 1:1 with a DAAC: CSDA has no `DAACS` entry at all, and some
# missions (e.g. SWOT) have their own endpoint distinct from their hosting
# DAAC's default.
#
# Generated by sweeping all 9,846 cloud-hosted CMR collections on
# 2026-08-18; re-run `sync_bucket_registry.py --check` to detect drift.
# Two caveats worth knowing:
#
# * ASF publishes its two OPERA buckets under both
#   `cumulus.asf.alaska.edu` and `cumulus.asf.earthdatacloud.nasa.gov`.
#   The sweep keeps the more frequently published host
#   (`cumulus.asf.alaska.edu`); both appear to be aliases for the same
#   Cumulus deployment, but only the former is used below.
# * `ghrcwuat-protected` and `ob-cumulus-sit-public` are UAT/SIT buckets
#   that GHRC and OB.DAAC publish in *production* CMR. They're kept
#   because the bucket and its endpoint are consistently paired, so
#   resolving one to the other is still correct.
BUCKET_ENDPOINTS: dict[str, str] = {
    "asdc-prod-protected": "https://data.asdc.earthdata.nasa.gov/s3credentials",
    "asdc2-prod-protected": "https://data.asdc.earthdata.nasa.gov/s3credentials",
    "asf-cumulus-prod-alos2-products": "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials",
    "asf-cumulus-prod-aria-browse": "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials",
    "asf-cumulus-prod-aria-products": "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials",
    "asf-cumulus-prod-ecmwf": "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials",
    "asf-cumulus-prod-opera-browse": "https://cumulus.asf.alaska.edu/s3credentials",
    "asf-cumulus-prod-opera-products": "https://cumulus.asf.alaska.edu/s3credentials",
    "asf-cumulus-prod-seasat-products": "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials",
    "asf-ngap2w-p-s1-grd-7d1b4348": "https://sentinel1.asf.alaska.edu/s3credentials",
    "asf-ngap2w-p-s1-ocn-1e29d408": "https://sentinel1.asf.alaska.edu/s3credentials",
    "asf-ngap2w-p-s1-raw-98779950": "https://sentinel1.asf.alaska.edu/s3credentials",
    "asf-ngap2w-p-s1-slc-7b420b89": "https://sentinel1.asf.alaska.edu/s3credentials",
    "asf-ngap2w-p-s1-xml-8cf7476b": "https://sentinel1.asf.alaska.edu/s3credentials",
    "csda-cumulus-prod-protected-5047": "https://data.csdap.earthdata.nasa.gov/s3credentials",
    "gesdisc-cumulus-prod-protected": "https://data.gesdisc.earthdata.nasa.gov/s3credentials",
    "ghrcw-protected": "https://data.ghrc.earthdata.nasa.gov/s3credentials",
    "ghrcwuat-protected": "https://data.ghrc.uat.earthdata.nasa.gov/s3credentials",
    "lp-prod-protected": "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
    "lp-prod-public": "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
    "lp-protected": "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
    "lp-public": "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
    "nsidc-cumulus-prod-protected": "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials",
    "nsidc-cumulus-prod-public": "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials",
    "ob-cumulus-prod-public": "https://obdaac-tea.earthdatacloud.nasa.gov/s3credentials",
    "ob-cumulus-sit-public": "https://obdaac-tea.sit.earthdatacloud.nasa.gov/s3credentials",
    "ornl-cumulus-prod-protected": "https://data.ornldaac.earthdata.nasa.gov/s3credentials",
    "ornl-cumulus-prod-public": "https://data.ornldaac.earthdata.nasa.gov/s3credentials",
    "podaac-ops-cumulus-docs": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
    "podaac-ops-cumulus-protected": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
    "podaac-ops-cumulus-public": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
    "podaac-swot-ops-cumulus-protected": "https://archive.swot.podaac.earthdata.nasa.gov/s3credentials",
    "podaac-swot-ops-cumulus-public": "https://archive.swot.podaac.earthdata.nasa.gov/s3credentials",
    "prod-lads": "https://data.laadsdaac.earthdatacloud.nasa.gov/s3credentials",
    "sds-n-cumulus-prod-nisar-products": "https://nisar.asf.earthdatacloud.nasa.gov/s3credentials",
    "sds-n-cumulus-prod-nisar-ur-products": "https://nisar.asf.earthdatacloud.nasa.gov/s3credentials",
}


def find_endpoint_by_bucket(bucket: str) -> str | None:
    """Look up the `s3credentials` endpoint for a bare S3 bucket name.

    Unlike [`find_provider`][earthaccess_auth.daac.find_provider], this
    resolves buckets directly, including ones with no corresponding
    [`DAACS`][earthaccess_auth.daac.DAACS] entry (e.g. CSDA) or where the
    endpoint varies by mission rather than by DAAC (e.g. some ASF/PODAAC
    buckets).

    Parameters:
        bucket: A bare S3 bucket name, e.g. `"podaac-ops-cumulus-protected"`
            (not `s3://podaac-ops-cumulus-protected/...`).

    Returns:
        The bucket's `s3credentials` endpoint, or `None` if the bucket
        isn't in [`BUCKET_ENDPOINTS`][earthaccess_auth.daac.BUCKET_ENDPOINTS].
    """
    return BUCKET_ENDPOINTS.get(bucket)


def find_provider(
    daac_short_name: str | None = None,
    cloud_hosted: bool | None = None,  # noqa: FBT001
) -> str | None:
    """Look up a DAAC's CMR provider code by its short name.

    Parameters:
        daac_short_name: A DAAC's short name, e.g. `"NSIDC"` or `"PODAAC"`.
        cloud_hosted: If `True`, prefer the DAAC's cloud provider code over
            its on-prem one, falling back to on-prem if the DAAC has no
            cloud provider.

    Returns:
        The matching provider code (e.g. `"NSIDC_CPRD"`), or `None` if
        `daac_short_name` isn't in the
        [DAAC registry][earthaccess_auth.daac.DAACS].
    """
    for daac in DAACS:
        if daac_short_name == daac["short-name"]:
            if cloud_hosted:
                if len(daac["cloud-providers"]) > 0:
                    return daac["cloud-providers"][0]
                # We found the DAAC, but it does not have cloud data
                return daac["on-prem-providers"][0]
            # return on prem provider code
            return daac["on-prem-providers"][0]
    return None


def find_provider_by_shortname(short_name: str, cloud_hosted: bool) -> str | None:  # noqa: FBT001
    """Look up a collection's CMR provider code by querying CMR directly.

    Unlike [`find_provider`][earthaccess_auth.daac.find_provider], this
    queries CMR itself instead of the local DAAC registry, so it also works
    for collections whose provider isn't listed in
    [`DAACS`][earthaccess_auth.daac.DAACS].

    Parameters:
        short_name: A collection's short name, e.g. `"ATL03"`.
        cloud_hosted: Whether to search for the cloud-hosted or on-prem
            version of the collection.

    Returns:
        The provider ID of the first matching collection, or `None` if no
        collection with that short name was found.
    """
    base_url = "https://cmr.earthdata.nasa.gov/search/collections.umm_json?"
    providers = requests.get(
        f"{base_url}&cloud_hosted={cloud_hosted}&short_name={short_name}",
        timeout=15,
    ).json()
    if int(providers["hits"]) > 0:
        return str(providers["items"][0]["meta"]["provider-id"])
    return None
