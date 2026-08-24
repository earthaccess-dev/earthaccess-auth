from earthaccess_auth.daac import (
    BUCKET_ENDPOINTS,
    BUCKET_REGISTRY,
    DAACS,
    BucketInfo,
    find_endpoint_by_bucket,
    find_provider,
    resolve_bucket,
)


def test_daacs_registry_is_populated() -> None:
    short_names = {d["short-name"] for d in DAACS}
    assert {"NSIDC", "PODAAC", "LPDAAC"} <= short_names


def test_nsidc_s3_credentials_endpoint() -> None:
    nsidc = next(d for d in DAACS if d["short-name"] == "NSIDC")
    assert (
        nsidc["s3-credentials"]
        == "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials"
    )


def test_find_provider_cloud_hosted() -> None:
    assert find_provider("NSIDC", cloud_hosted=True) == "NSIDC_CPRD"


def test_find_endpoint_by_bucket() -> None:
    assert (
        find_endpoint_by_bucket("podaac-ops-cumulus-protected")
        == "https://archive.podaac.earthdata.nasa.gov/s3credentials"
    )


def test_find_endpoint_by_bucket_unknown_bucket_returns_none() -> None:
    assert find_endpoint_by_bucket("not-a-real-bucket") is None


def test_find_endpoint_by_bucket_covers_daac_with_no_daacs_entry() -> None:
    # CSDA has no entry in DAACS, but its bucket is resolvable via the
    # CMR-derived BUCKET_ENDPOINTS mapping.
    assert "CSDA" not in {d["short-name"] for d in DAACS}
    assert find_endpoint_by_bucket("csda-cumulus-prod-protected-5047") is not None


def test_bucket_endpoints_has_no_dropped_or_malformed_entries() -> None:
    assert "TestBucket" not in BUCKET_ENDPOINTS
    for bucket in BUCKET_ENDPOINTS:
        assert "/" not in bucket


def test_bucket_registry_carries_region() -> None:
    info = BUCKET_REGISTRY["podaac-ops-cumulus-protected"]
    assert info == BucketInfo(
        endpoint="https://archive.podaac.earthdata.nasa.gov/s3credentials",
        region="us-west-2",
    )


def test_bucket_endpoints_derived_from_registry() -> None:
    assert {
        bucket: info.endpoint for bucket, info in BUCKET_REGISTRY.items()
    } == BUCKET_ENDPOINTS


def test_resolve_bucket_bare_name() -> None:
    info = resolve_bucket("lp-prod-protected")
    assert info is not None
    assert info.endpoint == "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials"


def test_resolve_bucket_s3_url() -> None:
    info = resolve_bucket("s3://podaac-ops-cumulus-protected/MUR/file.nc")
    assert info is not None
    assert info.region == "us-west-2"


def test_resolve_bucket_unknown_returns_none() -> None:
    assert resolve_bucket("not-a-real-bucket") is None
    assert resolve_bucket("s3://not-a-real-bucket/key") is None


def test_resolve_bucket_non_s3_scheme_returns_none() -> None:
    assert resolve_bucket("https://example.com/podaac-ops-cumulus-protected") is None
