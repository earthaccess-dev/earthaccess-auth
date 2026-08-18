# How the bucket registry is built

`earthaccess_auth.daac.BUCKET_ENDPOINTS` maps a bare S3 bucket name (e.g.
`podaac-ops-cumulus-protected`) to the `s3credentials` endpoint that issues
temporary AWS credentials scoped to it. It's what lets `earthaccess` resolve
a plain `s3://some-bucket/...` URL to the right DAAC without the caller
having to pass `provider=` or `credentials_endpoint=` themselves.

## Where the data comes from

Every cloud-hosted CMR collection that supports direct S3 access carries a
`DirectDistributionInformation` block in its UMM-C metadata:

```json
"DirectDistributionInformation": {
  "Region": "us-west-2",
  "S3BucketAndObjectPrefixNames": [
    "podaac-ops-cumulus-protected/MUR-JPL-L4-GLOB-v4.1/",
    "podaac-ops-cumulus-public/MUR-JPL-L4-GLOB-v4.1/"
  ],
  "S3CredentialsAPIEndpoint": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
  "S3CredentialsAPIDocumentationURL": "https://archive.podaac.earthdata.nasa.gov/s3credentialsREADME"
}
```

The bucket names and the credentials endpoint sit side by side in the same
block, so sweeping this field across every collection in CMR gives a bucket
-> endpoint mapping straight from the source of truth, rather than guessing
a DAAC (and therefore an endpoint) from the bucket name — the approach
`earthaccess` used previously (a bare `"cumulus" in url` check), which
missed buckets like `lp-prod-protected`, `asdc-prod-protected`,
`prod-lads`, and all of ASF's per-mission buckets.

This also resolves buckets that have no corresponding entry in the
[`DAACS`][earthaccess_auth.daac.DAACS] registry at all — for example CSDA
(`csda-cumulus-prod-protected-5047`), which isn't one of NASA's EOSDIS DAACs
and so was never in the hand-maintained DAAC table, and ASF's per-mission
buckets, where the endpoint varies by mission rather than being one fixed
`s3credentials` URL per DAAC.

`S3BucketAndObjectPrefixNames` entries also carry an object prefix after the
bucket name (`bucket/prefix/`); the prefix is discarded — the registry only
needs to resolve bucket names, not sub-paths within them, since a single set
of EDL-derived STS credentials is valid for the whole bucket regardless of
prefix.

## Running the sweep

```console
$ python earthaccess-auth/scripts/sync_bucket_registry.py --output bucket_registry.json
Swept 9846 cloud-hosted collections -> 36 buckets.
Wrote bucket_registry.json
```

The script pages through `cmr.earthdata.nasa.gov/search/collections.umm_json`
with `cloud_hosted=true` using the `CMR-Search-After` header (CMR's
recommended pagination mechanism for result sets that don't fit in one
page), and reduces every collection's `DirectDistributionInformation` down
to one row per unique bucket.

`--check` diffs the sweep against the mapping currently vendored in
[`BUCKET_ENDPOINTS`][earthaccess_auth.daac.BUCKET_ENDPOINTS] and exits
non-zero if there's drift — new buckets (new missions, new DAACs), buckets
that dropped out of CMR, or a bucket whose credentials endpoint changed.
This is meant to run on a schedule in CI so registry drift shows up as a PR
rather than as a runtime failure for users.

## Cleaning the raw data

`DirectDistributionInformation` is free-text metadata written per collection
by each DAAC, and it shows. As of the 2026-08-18 sweep (9,846 collections,
9,837 of them carrying the block), these are the cases that need handling:

- **Fully-qualified S3 URIs.** The field is nominally `bucket/prefix`, but
  ORNL, LPDAAC, GES DISC, ASDC, OB.DAAC, LAADS and CSDA all write
  `s3://bucket/prefix` instead — 10,440 entries, a clear majority of the
  total. The script strips any URI scheme before splitting. Skipping this
  step collapses all seven DAACs into a single bogus `s3:` bucket and loses
  every one of their real buckets.
- **Missing separators.** One entry (GES DISC's `AIRXBCAL`) is missing the
  `/` between the bucket name and the object prefix:
  `s3://gesdisc-cumulus-prod-protectedAqua_AIRS_Level2/AIRXBCAL.005/`. NASA
  Cumulus bucket names consistently end in `-protected` or `-public`
  (optionally with a numeric suffix, e.g. CSDA's `-5047`), so the script
  recovers the split by locating that suffix rather than the missing
  separator. It only attempts this when the bucket half is *not* already a
  syntactically valid S3 bucket name, so a legitimate name like
  `csda-cumulus-prod-protected-5047` is never chopped apart at its numeric
  suffix.
- **Unusable bucket names.** Anything that still isn't a valid S3 bucket
  name after the above (lowercase alphanumerics, dots and hyphens, 3-63
  characters) is dropped with a warning. In practice this is the literal
  `TestBucket` placeholder in one SCIOPS QA collection.
- **Non-HTTPS credentials endpoints.** Two collections have junk in
  `S3CredentialsAPIEndpoint`: a `www.testexample.com` placeholder (SCIOPS)
  and an S3 URI pasted into the wrong field (LPCLOUD). Endpoints that aren't
  `https://` URLs are dropped with a warning.
- **Endpoint conflicts.** ASF publishes `asf-cumulus-prod-opera-products`
  and `asf-cumulus-prod-opera-browse` under two hosts,
  `cumulus.asf.alaska.edu` and `cumulus.asf.earthdatacloud.nasa.gov`. The
  script keeps the most frequently published endpoint, breaking ties on the
  endpoint string. Resolving this deterministically matters: picking the
  first one seen would depend on CMR's result ordering, and the scheduled
  `--check` job would flap between the two hosts from run to run.

Two UAT/SIT buckets (`ghrcwuat-protected` and `ob-cumulus-sit-public`) are
published in *production* CMR by GHRC and OB.DAAC. They're kept rather than
filtered: each is paired with its own UAT/SIT credentials endpoint, so
resolving one to the other is still correct.

## Feeding the mapping into `daac.py`

The sweep's output isn't consumed automatically — merge new/changed rows
from `bucket_registry.json` into
[`BUCKET_ENDPOINTS`][earthaccess_auth.daac.BUCKET_ENDPOINTS] by hand (or
via the `--check` CI job's diff) so the vendored table stays a reviewed,
human-legible artifact rather than a black box regenerated on every run.
