#!/usr/bin/env python3
"""Sweep CMR for the authoritative S3 bucket -> credentials-endpoint mapping.

Every cloud-hosted collection in CMR that supports direct S3 access carries
a `DirectDistributionInformation` block in its UMM-C metadata:

    "DirectDistributionInformation": {
      "Region": "us-west-2",
      "S3BucketAndObjectPrefixNames": [
        "podaac-ops-cumulus-protected/MUR-JPL-L4-GLOB-v4.1/",
        "podaac-ops-cumulus-public/MUR-JPL-L4-GLOB-v4.1/"
      ],
      "S3CredentialsAPIEndpoint": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
      "S3CredentialsAPIDocumentationURL": "https://archive.podaac.earthdata.nasa.gov/s3credentialsREADME"
    }

`S3BucketAndObjectPrefixNames` and `S3CredentialsAPIEndpoint` sit side by
side in the same block, so sweeping this field across all collections gives
a bucket -> endpoint mapping straight from CMR, rather than guessing the
DAAC (and therefore the endpoint) from the bucket name.

Usage:
    python sync_bucket_registry.py --output bucket_registry.json
    python sync_bucket_registry.py --check   # diff against the vendored mapping, exit 1 on drift

See docs/explanation/cmr-s3-buckets.md for the full method writeup.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

import requests

from earthaccess_auth.daac import BUCKET_ENDPOINTS

logger = logging.getLogger(__name__)

CMR_COLLECTIONS_URL = "https://cmr.earthdata.nasa.gov/search/collections.umm_json"
PAGE_SIZE = 2000

# Most DAACs write bare "bucket/prefix" entries, but ORNL, LPDAAC, GES DISC,
# ASDC, OB.DAAC, LAADS and CSDA all write fully-qualified "s3://bucket/prefix"
# URLs instead — together the clear majority of entries in CMR. Strip any
# scheme before splitting, or every one of those collapses into a single
# bogus "s3:" bucket.
_SCHEME_RE = re.compile(r"^[a-z0-9+.-]+://")

# S3 bucket naming rules: 3-63 characters, lowercase alphanumerics, dots and
# hyphens only, starting and ending with an alphanumeric. Anything else in
# `S3BucketAndObjectPrefixNames` is either malformed metadata or a
# placeholder (e.g. the literal "TestBucket" in a QA collection), so this
# doubles as the filter for junk entries.
_S3_BUCKET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")

# Some entries are missing the "/" separator between the bucket name and the
# object prefix, e.g. "gesdisc-cumulus-prod-protectedAqua_AIRS_Level2"
# (should be "gesdisc-cumulus-prod-protected/Aqua_AIRS_Level2"). NASA Cumulus
# bucket names consistently end in "-protected" or "-public" (optionally with
# a numeric suffix, e.g. CSDA's "csda-cumulus-prod-protected-5047"), so we can
# recover the intended split even without the separator. This is only applied
# to bucket names that are otherwise invalid, so a legitimate name that
# happens to end in a numeric suffix is never split apart.
_BUCKET_SUFFIX_RE = re.compile(r"^(.*?-(?:protected|public)(?:-\d+)?)(.+)$")


@dataclass
class BucketEndpoint:
    bucket: str
    endpoint: str
    region: str
    providers: set[str] = field(default_factory=set)


def is_valid_bucket_name(bucket: str) -> bool:
    """Whether `bucket` is a syntactically valid S3 bucket name."""
    return _S3_BUCKET_NAME_RE.match(bucket) is not None


def split_bucket_and_prefix(entry: str) -> tuple[str, str]:
    """Split a raw `S3BucketAndObjectPrefixNames` entry into (bucket, prefix).

    The bucket half may still be unusable (see
    [`is_valid_bucket_name`][is_valid_bucket_name]) when the entry is
    malformed beyond repair.
    """
    entry = _SCHEME_RE.sub("", entry)

    bucket, _, prefix = entry.partition("/")
    if is_valid_bucket_name(bucket):
        return bucket, prefix

    # Invalid bucket half: try recovering a missing "bucket/prefix"
    # separator, keeping the repair only if it yields a valid bucket name.
    match = _BUCKET_SUFFIX_RE.match(bucket)
    if match and is_valid_bucket_name(match.group(1)):
        recovered_bucket, recovered_prefix = match.group(1), match.group(2)
        if prefix:
            recovered_prefix = f"{recovered_prefix}/{prefix}"
        return recovered_bucket, recovered_prefix

    return bucket, prefix


def iter_cmr_collections(
    session: requests.Session,
    page_size: int = PAGE_SIZE,
) -> list[dict[str, Any]]:
    """Page through every cloud-hosted CMR collection via CMR-Search-After."""
    collections: list[dict[str, Any]] = []
    headers: dict[str, str] = {}
    params: dict[str, str | int] = {"cloud_hosted": "true", "page_size": page_size}

    while True:
        response = session.get(
            CMR_COLLECTIONS_URL,
            params=params,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items", [])
        if not items:
            break
        collections.extend(items)

        search_after = response.headers.get("CMR-Search-After")
        if not search_after:
            break
        headers["CMR-Search-After"] = search_after

    return collections


def resolve_endpoint(bucket: str, endpoints: Counter[str]) -> str:
    """Pick one endpoint for a bucket that CMR maps to several.

    A handful of buckets (currently ASF's OPERA ones) are published with two
    different `S3CredentialsAPIEndpoint` hosts across collections. Take the
    most frequently published one, breaking ties on the endpoint string, so
    the sweep is reproducible rather than dependent on CMR's result order —
    otherwise the scheduled `--check` job flaps between the two.
    """
    winner = min(endpoints, key=lambda endpoint: (-endpoints[endpoint], endpoint))
    if len(endpoints) > 1:
        logger.warning(
            "bucket %r maps to multiple endpoints %s; keeping %r",
            bucket,
            sorted(f"{endpoint} (x{count})" for endpoint, count in endpoints.items()),
            winner,
        )
    return winner


def build_bucket_registry(
    collections: list[dict[str, Any]],
) -> dict[str, BucketEndpoint]:
    """Reduce CMR collections down to a bucket -> (endpoint, region) mapping."""
    endpoints: dict[str, Counter[str]] = defaultdict(Counter)
    regions: dict[str, str] = {}
    providers: dict[str, set[str]] = defaultdict(set)

    for item in collections:
        meta = item.get("meta", {})
        umm = item.get("umm", {})
        provider = meta.get("provider-id", "UNKNOWN")
        direct_dist = umm.get("DirectDistributionInformation")
        if not direct_dist:
            continue

        endpoint = direct_dist.get("S3CredentialsAPIEndpoint")
        region = direct_dist.get("Region", "")
        prefixes = direct_dist.get("S3BucketAndObjectPrefixNames", [])
        if not endpoint or not prefixes:
            continue
        if not endpoint.startswith("https://"):
            # Observed in the wild: an S3 URI and a "www.testexample.com"
            # placeholder pasted into the endpoint field.
            logger.warning(
                "provider %s: ignoring non-HTTPS S3CredentialsAPIEndpoint %r",
                provider,
                endpoint,
            )
            continue

        for raw_entry in prefixes:
            bucket, _prefix = split_bucket_and_prefix(raw_entry)
            if not is_valid_bucket_name(bucket):
                logger.warning(
                    "provider %s: ignoring unusable bucket entry %r",
                    provider,
                    raw_entry,
                )
                continue

            endpoints[bucket][endpoint] += 1
            providers[bucket].add(provider)
            regions.setdefault(bucket, region)

    return {
        bucket: BucketEndpoint(
            bucket=bucket,
            endpoint=resolve_endpoint(bucket, bucket_endpoints),
            region=regions[bucket],
            providers=providers[bucket],
        )
        for bucket, bucket_endpoints in sorted(endpoints.items())
    }


def diff_against_vendored(registry: dict[str, BucketEndpoint]) -> bool:
    """Log a diff of `registry` against the vendored mapping.

    Returns True if there's drift (for use as a CI exit-code gate).
    """
    vendored = dict(BUCKET_ENDPOINTS)
    swept = {bucket: be.endpoint for bucket, be in registry.items()}

    added = sorted(set(swept) - set(vendored))
    removed = sorted(set(vendored) - set(swept))
    changed = sorted(
        bucket
        for bucket in set(swept) & set(vendored)
        if swept[bucket] != vendored[bucket]
    )

    if not (added or removed or changed):
        logger.info(
            "No drift: vendored BUCKET_ENDPOINTS matches the current CMR sweep."
        )
        return False

    if added:
        logger.info("New buckets in CMR (%d):", len(added))
        for bucket in added:
            logger.info("  + %s -> %s", bucket, swept[bucket])
    if removed:
        logger.info("Buckets no longer in CMR (%d):", len(removed))
        for bucket in removed:
            logger.info("  - %s -> %s", bucket, vendored[bucket])
    if changed:
        logger.info("Buckets with a changed endpoint (%d):", len(changed))
        for bucket in changed:
            logger.info("  ~ %s: %s -> %s", bucket, vendored[bucket], swept[bucket])

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        help="Write the swept registry as JSON to this path.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Diff the sweep against the vendored BUCKET_ENDPOINTS and exit 1 on drift.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=PAGE_SIZE,
        help="CMR page size per request (default: %(default)s).",
    )
    args = parser.parse_args()

    with requests.Session() as session:
        collections = iter_cmr_collections(session, page_size=args.page_size)

    registry = build_bucket_registry(collections)
    logger.info(
        "Swept %d cloud-hosted collections -> %d buckets.",
        len(collections),
        len(registry),
    )

    if args.output:
        serializable = {
            bucket: {
                "endpoint": be.endpoint,
                "region": be.region,
                "providers": sorted(be.providers),
            }
            for bucket, be in sorted(registry.items())
        }
        with open(args.output, "w") as f:  # noqa: PTH123
            json.dump(serializable, f, indent=2, sort_keys=True)
            # Trailing newline, so the regenerated snapshot satisfies the
            # end-of-file-fixer pre-commit hook rather than failing CI on
            # every scheduled run.
            f.write("\n")
        logger.info("Wrote %s", args.output)

    if args.check and diff_against_vendored(registry):
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
