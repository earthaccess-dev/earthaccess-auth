from earthaccess_auth.system import PROD, UAT


def test_prod_hostnames() -> None:
    assert PROD.edl_hostname == "urs.earthdata.nasa.gov"
    assert PROD.cmr_base_url == "https://cmr.earthdata.nasa.gov/search/"


def test_uat_hostnames() -> None:
    assert UAT.edl_hostname == "uat.urs.earthdata.nasa.gov"
    assert UAT.cmr_base_url == "https://cmr.uat.earthdata.nasa.gov/search/"
