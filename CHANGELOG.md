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

[Unreleased]: https://github.com/earthaccess-dev/earthaccess-auth/commits/main/
