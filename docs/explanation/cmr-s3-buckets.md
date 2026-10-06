# How the bucket registry is built

[`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY] maps a bare S3
bucket name, such as `podaac-ops-cumulus-protected`, to two values:

- the `s3credentials` endpoint that issues temporary AWS credentials for
  that bucket
- the bucket's AWS region

With this mapping, `earthaccess` can find the correct DAAC for a plain
`s3://some-bucket/...` URL. The caller doesn't have to pass `provider=` or
`credentials_endpoint=`. In the 2026-08-18 sweep, all buckets were in
`us-west-2`. [`BUCKET_ENDPOINTS`][earthaccess_auth.daac.BUCKET_ENDPOINTS]
is the same mapping without the region. It is kept for backwards
compatibility.

## Where the data comes from

Each cloud-hosted CMR collection that supports direct S3 access has a
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

The bucket names and the credentials endpoint are in the same block. A
sweep of this block across all CMR collections gives a bucket-to-endpoint
mapping from the source of truth.

Before, `earthaccess` guessed the DAAC, and so the endpoint, from the
bucket name. It used a `"cumulus" in url` check. That check missed buckets
such as `lp-prod-protected`, `asdc-prod-protected`, `prod-lads`, and all of
ASF's per-mission buckets.

The sweep also resolves buckets that have no entry in the
[`DAACS`][earthaccess_auth.daac.DAACS] registry. Two examples:

- CSDA (`csda-cumulus-prod-protected-5047`). CSDA isn't one of NASA's
  EOSDIS DAACs, so it was never in the DAAC table.
- ASF's per-mission buckets. Their endpoint changes with the mission, so
  one `s3credentials` URL per DAAC isn't enough.

Each `S3BucketAndObjectPrefixNames` entry also has an object prefix after
the bucket name (`bucket/prefix/`). The sweep discards the prefix. One set
of STS credentials from EDL is valid for the whole bucket, so the registry
only needs bucket names.

## Running the sweep

```console
$ python scripts/sync_bucket_registry.py --output bucket_registry.json
Swept 9846 cloud-hosted collections -> 36 buckets.
Wrote bucket_registry.json
```

The script reads `cmr.earthdata.nasa.gov/search/collections.umm_json` with
`cloud_hosted=true`. It pages through the results with the
`CMR-Search-After` header, which CMR recommends for large result sets. It
then reduces the `DirectDistributionInformation` of all collections to one
row for each unique bucket.

`--check` compares the sweep with the vendored
[`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY], including the
regions. It exits with a non-zero status if they differ. These are the
possible differences:

- new buckets, for example from new missions or new DAACs
- buckets that are no longer in CMR
- a bucket with a different credentials endpoint or region

A scheduled CI job runs the sweep every week. If the result changes, the
job opens a pull request. This way, users don't get runtime failures when
CMR changes.

## Cleaning the raw data

Each DAAC writes `DirectDistributionInformation` for its own collections
as free text, so the data is not consistent. The 2026-08-18 sweep read
9,846 collections, and 9,837 of them had the block. The script handles
these cases:

- **Full S3 URIs.** The field should contain `bucket/prefix`. But ORNL,
  LPDAAC, GES DISC, ASDC, OB.DAAC, LAADS and CSDA write
  `s3://bucket/prefix`. There are 10,440 of these entries, which is most of
  the total. The script removes any URI scheme before it splits the entry.
  Without this step, the entries from all seven DAACs become one incorrect
  `s3:` bucket, and all their real buckets are lost.
- **Missing separators.** One entry (GES DISC's `AIRXBCAL`) has no `/`
  between the bucket name and the object prefix:
  `s3://gesdisc-cumulus-prod-protectedAqua_AIRS_Level2/AIRXBCAL.005/`. NASA
  Cumulus bucket names end in `-protected` or `-public`, sometimes with a
  numeric suffix such as CSDA's `-5047`. The script finds this suffix and
  splits the entry after it. It does this only when the bucket part is
  *not* already a valid S3 bucket name. So the script never splits a valid
  name such as `csda-cumulus-prod-protected-5047` at its numeric suffix.
- **Invalid bucket names.** A valid S3 bucket name has 3 to 63 characters:
  lowercase letters, digits, dots, and hyphens. The script drops any name
  that is still invalid after the steps above, and logs a warning. In the
  sweep, the only such name is the `TestBucket` placeholder in one SCIOPS QA
  collection.
- **Credentials endpoints that aren't HTTPS.** Two collections have
  incorrect values in `S3CredentialsAPIEndpoint`. SCIOPS has a
  `www.testexample.com` placeholder. LPCLOUD has an S3 URI in that field.
  The script drops endpoints that aren't `https://` URLs, and logs a
  warning.
- **Conflicting endpoints.** ASF publishes `asf-cumulus-prod-opera-products`
  and `asf-cumulus-prod-opera-browse` under two hosts:
  `cumulus.asf.alaska.edu` and `cumulus.asf.earthdatacloud.nasa.gov`. The
  script keeps the endpoint that occurs most often. If two endpoints occur
  equally often, it sorts them as strings and keeps the first one. The
  result must not depend on the order of CMR's results. Otherwise, the
  weekly `--check` job would switch between the two hosts from one run to
  the next.

GHRC and OB.DAAC publish two UAT/SIT buckets in *production* CMR:
`ghrcwuat-protected` and `ob-cumulus-sit-public`. The registry keeps them.
Each one has its own UAT/SIT credentials endpoint, so the mapping is still
correct.

## Updating `daac.py`

The package doesn't read the sweep output automatically. To update the
registry, copy new or changed rows from `bucket_registry.json` into
[`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY] by hand. You can
also use the diff in the pull request from the weekly CI job. A person
reviews each change, so the vendored table stays easy to read and check.
