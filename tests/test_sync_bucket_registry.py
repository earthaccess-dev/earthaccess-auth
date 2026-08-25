"""Tests for scripts/sync_bucket_registry.py.

The script lives outside the installed package (it's a maintainer tool, not
runtime code), so it's loaded directly from its file path.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any

from earthaccess_auth.daac import BUCKET_REGISTRY

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "sync_bucket_registry.py"

spec = importlib.util.spec_from_file_location("sync_bucket_registry", SCRIPT_PATH)
assert spec is not None
assert spec.loader is not None
sync_bucket_registry = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sync_bucket_registry
spec.loader.exec_module(sync_bucket_registry)

build_bucket_registry = sync_bucket_registry.build_bucket_registry
split_bucket_and_prefix = sync_bucket_registry.split_bucket_and_prefix
BucketEndpoint = sync_bucket_registry.BucketEndpoint
diff_against_vendored = sync_bucket_registry.diff_against_vendored


def _collection(
    provider: str,
    endpoint: str,
    region: str,
    prefixes: list[str],
) -> dict[str, Any]:
    return {
        "meta": {"provider-id": provider},
        "umm": {
            "DirectDistributionInformation": {
                "Region": region,
                "S3BucketAndObjectPrefixNames": prefixes,
                "S3CredentialsAPIEndpoint": endpoint,
            },
        },
    }


def test_split_bucket_and_prefix_with_separator() -> None:
    assert split_bucket_and_prefix("podaac-ops-cumulus-protected/MUR-JPL/") == (
        "podaac-ops-cumulus-protected",
        "MUR-JPL/",
    )


def test_split_bucket_and_prefix_strips_s3_scheme() -> None:
    # ORNL, LPDAAC, GES DISC, ASDC, OB.DAAC, LAADS and CSDA all publish
    # fully-qualified S3 URIs rather than bare "bucket/prefix" entries.
    assert split_bucket_and_prefix("s3://ornl-cumulus-prod-protected/daacdata/") == (
        "ornl-cumulus-prod-protected",
        "daacdata/",
    )


def test_split_bucket_and_prefix_keeps_valid_numeric_suffix_intact() -> None:
    # Regression guard: "csda-cumulus-prod-protected-5047" is a *valid*
    # bucket name, so the missing-separator repair must not fire and chop
    # the numeric suffix off into the prefix.
    assert split_bucket_and_prefix(
        "s3://csda-cumulus-prod-protected-5047/WV03_MSI_L2A___1/",
    ) == ("csda-cumulus-prod-protected-5047", "WV03_MSI_L2A___1/")


def test_split_bucket_and_prefix_recovers_missing_separator() -> None:
    # The real, observed malformed entry: no "/" between bucket and prefix.
    assert split_bucket_and_prefix(
        "gesdisc-cumulus-prod-protectedAqua_AIRS_Level2",
    ) == ("gesdisc-cumulus-prod-protected", "Aqua_AIRS_Level2")


def test_split_bucket_and_prefix_recovers_missing_separator_with_numeric_suffix() -> (
    None
):
    assert split_bucket_and_prefix(
        "csda-cumulus-prod-protected-5047SomeShortName",
    ) == ("csda-cumulus-prod-protected-5047", "SomeShortName")


def test_build_bucket_registry_extracts_bucket_endpoint_region() -> None:
    collections = [
        _collection(
            "POCLOUD",
            "https://archive.podaac.earthdata.nasa.gov/s3credentials",
            "us-west-2",
            ["podaac-ops-cumulus-protected/COLL/"],
        ),
    ]

    registry = build_bucket_registry(collections)

    assert set(registry) == {"podaac-ops-cumulus-protected"}
    entry = registry["podaac-ops-cumulus-protected"]
    assert entry.endpoint == "https://archive.podaac.earthdata.nasa.gov/s3credentials"
    assert entry.region == "us-west-2"
    assert entry.providers == {"POCLOUD"}


def test_build_bucket_registry_drops_test_bucket() -> None:
    collections = [
        _collection(
            "SOME_QA_PROVIDER",
            "https://example.com/s3credentials",
            "us-west-2",
            ["TestBucket/COLL/"],
        ),
    ]

    registry = build_bucket_registry(collections)

    assert registry == {}


def test_build_bucket_registry_normalizes_malformed_entry() -> None:
    collections = [
        _collection(
            "GES_DISC",
            "https://data.gesdisc.earthdata.nasa.gov/s3credentials",
            "us-west-2",
            ["gesdisc-cumulus-prod-protectedAqua_AIRS_Level2"],
        ),
    ]

    registry = build_bucket_registry(collections)

    assert set(registry) == {"gesdisc-cumulus-prod-protected"}


def test_build_bucket_registry_skips_collections_without_direct_distribution() -> None:
    collections = [{"meta": {"provider-id": "SOME_PROVIDER"}, "umm": {}}]

    assert build_bucket_registry(collections) == {}


def test_split_bucket_and_prefix_recovers_missing_separator_in_s3_uri() -> None:
    # The exact entry GES DISC publishes for AIRXBCAL: an S3 URI whose
    # bucket half is missing the separator before the collection prefix.
    assert split_bucket_and_prefix(
        "s3://gesdisc-cumulus-prod-protectedAqua_AIRS_Level2/AIRXBCAL.005/",
    ) == ("gesdisc-cumulus-prod-protected", "Aqua_AIRS_Level2/AIRXBCAL.005/")


def test_build_bucket_registry_drops_non_https_endpoints() -> None:
    # Both observed in production CMR: a placeholder hostname and an S3 URI
    # pasted into the credentials-endpoint field.
    collections = [
        _collection(
            "SCIOPS",
            "www.testexample.com",
            "us-west-2",
            ["podaac-ops-cumulus-protected/COLL/"],
        ),
        _collection(
            "LPCLOUD",
            "s3://lp-prod-public/LPJ_L2_SSREF.002",
            "us-west-2",
            ["lp-prod-public/LPJ_L2_SSREF.002/"],
        ),
    ]

    assert build_bucket_registry(collections) == {}


def test_build_bucket_registry_resolves_conflicts_by_frequency() -> None:
    alaska = "https://cumulus.asf.alaska.edu/s3credentials"
    nasa = "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials"
    prefixes = ["asf-cumulus-prod-opera-products/OPERA_L3/"]
    collections = [
        _collection("ASF", nasa, "us-west-2", prefixes),
        _collection("ASF", alaska, "us-west-2", prefixes),
        _collection("ASF", alaska, "us-west-2", prefixes),
    ]

    registry = build_bucket_registry(collections)

    assert registry["asf-cumulus-prod-opera-products"].endpoint == alaska


def test_build_bucket_registry_breaks_conflict_ties_deterministically() -> None:
    alaska = "https://cumulus.asf.alaska.edu/s3credentials"
    nasa = "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials"
    prefixes = ["asf-cumulus-prod-opera-browse/OPERA_L3/"]
    tied = [
        _collection("ASF", nasa, "us-west-2", prefixes),
        _collection("ASF", alaska, "us-west-2", prefixes),
    ]

    # An even split must not depend on the order CMR happens to return
    # collections in, or the scheduled --check job flaps between the two.
    forward = build_bucket_registry(tied)["asf-cumulus-prod-opera-browse"]
    reversed_ = build_bucket_registry(tied[::-1])["asf-cumulus-prod-opera-browse"]

    assert forward.endpoint == reversed_.endpoint == alaska


def test_diff_flags_region_drift() -> None:
    registry = {
        bucket: BucketEndpoint(
            bucket=bucket,
            endpoint=info.endpoint,
            region="us-west-2",
            providers=set(),
        )
        for bucket, info in BUCKET_REGISTRY.items()
    }
    assert diff_against_vendored(registry) is False

    registry["prod-lads"] = BucketEndpoint(
        bucket="prod-lads",
        endpoint=BUCKET_REGISTRY["prod-lads"].endpoint,
        region="us-east-1",
        providers=set(),
    )
    assert diff_against_vendored(registry) is True
