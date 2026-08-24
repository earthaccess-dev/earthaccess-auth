# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Common Changelog](https://common-changelog.org/)
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
`earthaccess-auth` was extracted from
[earthaccess](https://github.com/earthaccess-dev/earthaccess) — see its
changelog for history predating the extraction.

## [Unreleased]

### Added

- Initial release. Extracted from `earthaccess`: EDL login (`login`, `Auth`),
  the DAAC registry, systems (`PROD`/`UAT`), and the two login exceptions.
  Optional `fsspec` and `obstore` extras add an authenticated HTTPS session
  and an S3 credential provider, respectively.
  ([#1423](https://github.com/earthaccess-dev/earthaccess/pull/1423))
- Added `earthaccess_auth.credentials`: `fetch_s3_credentials`,
  `S3Credentials`, thread-safe per-endpoint `S3CredentialManager`, and a
  process-wide `default_manager()` (non-interactive login only).
- `daac.BUCKET_REGISTRY` now vendors each bucket's AWS region alongside
  its `s3credentials` endpoint; `daac.resolve_bucket()` resolves bucket
  names and `s3://` URLs. `BUCKET_ENDPOINTS` is unchanged (now derived).
- Added `adapters.obstore.EarthdataS3CredentialProvider`, implementing
  obstore's structural credential-provider protocol without importing
  obstore; `adapters.obstore.s3_credential_provider` is deprecated.
- Added `adapters.icechunk` (extra: `earthaccess-auth[icechunk]`) with
  picklable refreshable S3 credentials for icechunk stores and virtual
  chunk containers.

### Changed

Behavior differences from the implementation extracted out of `earthaccess`:

- `Auth.login` raises `ValueError` for unknown strategy names instead of
  silently returning an unauthenticated instance.
- `Auth.login` on an already-authenticated instance is now a no-op unless a
  different `system` is requested.
- `Auth.get_s3_credentials` raises instead of returning an empty dict:
  `ValueError` when unauthenticated, and the new
  `S3CredentialsRequestFailure` when the `s3credentials` endpoint rejects
  the request (e.g. unaccepted EULA).
- `find_provider_by_shortname` applies a 15-second timeout to its CMR
  request instead of potentially hanging forever.
- Python 3.12 or newer is required.

[Unreleased]: https://github.com/earthaccess-dev/earthaccess-auth/commits/main/
