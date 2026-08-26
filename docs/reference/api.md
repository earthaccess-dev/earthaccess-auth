# API reference

Organized by concept. Terms are defined in the [glossary](glossary.md).

## Identity

An identity is an authenticated Earthdata Login account. Everything else in
the library exchanges an identity for something a storage client can use.

::: earthaccess_auth.login
    options:
      show_root_heading: true

::: earthaccess_auth.Auth
    options:
      inherited_members: true
      show_root_heading: true

## Temporary S3 credentials

DAACs exchange an identity for hour-scale AWS credentials at their
per-DAAC `s3credentials` endpoint, for direct in-region reads of protected
buckets.

::: earthaccess_auth.S3Credentials
    options:
      show_root_heading: true

::: earthaccess_auth.fetch_s3_credentials
    options:
      show_root_heading: true

## Credential managers

A manager wraps one identity and caches temporary credentials per endpoint,
re-fetching shortly before expiry.

::: earthaccess_auth.S3CredentialManager
    options:
      inherited_members: true
      show_root_heading: true

## The process-wide default

One manager is shared by the whole process. The adapters read it by calling
[`default_manager`][earthaccess_auth.default_manager] at use time, so
setting a new default swaps the identity for every consumer at once. Most
callers set it with [`set_default_auth`][earthaccess_auth.set_default_auth].
[`set_default_manager`][earthaccess_auth.credentials.set_default_manager]
is for the caller that validated an identity through a manager and wants
to keep that manager's warm cache.

::: earthaccess_auth.default_manager
    options:
      show_root_heading: true

::: earthaccess_auth.set_default_auth
    options:
      show_root_heading: true

::: earthaccess_auth.credentials.set_default_manager
    options:
      show_root_heading: true

## DAAC registry

::: earthaccess_auth.daac.DAACS
    options:
      show_root_heading: true
      show_attribute_values: false

::: earthaccess_auth.daac.find_provider
    options:
      show_root_heading: true

::: earthaccess_auth.daac.find_provider_by_shortname
    options:
      show_root_heading: true

::: earthaccess_auth.daac.BUCKET_ENDPOINTS
    options:
      show_root_heading: true
      show_attribute_values: false

::: earthaccess_auth.daac.find_endpoint_by_bucket
    options:
      show_root_heading: true

::: earthaccess_auth.daac.BucketInfo
    options:
      show_root_heading: true

::: earthaccess_auth.daac.BUCKET_REGISTRY
    options:
      show_root_heading: true
      show_attribute_values: false

::: earthaccess_auth.daac.resolve_bucket
    options:
      show_root_heading: true

## Systems

The Earthdata deployment to authenticate against, passed as
[`login`][earthaccess_auth.login]'s `system` parameter. Defaults to `PROD`;
pass `UAT` to test against NASA's pre-release environment before a change
reaches production.

::: earthaccess_auth.System
    options:
      show_root_heading: true

::: earthaccess_auth.PROD
    options:
      show_root_heading: true

::: earthaccess_auth.UAT
    options:
      show_root_heading: true

## Exceptions

::: earthaccess_auth.LoginStrategyUnavailable
    options:
      show_root_heading: true

::: earthaccess_auth.LoginAttemptFailure
    options:
      show_root_heading: true

::: earthaccess_auth.S3CredentialsEndpointUnresolved
    options:
      show_root_heading: true

::: earthaccess_auth.S3CredentialsRequestFailure
    options:
      show_root_heading: true

## Adapters

### fsspec (extra: `earthaccess-auth[fsspec]`)

::: earthaccess_auth.adapters.fsspec.get_fsspec_https_session
    options:
      show_root_heading: true

### obstore (extra: `earthaccess-auth[obstore]`)

::: earthaccess_auth.adapters.obstore.EarthdataS3CredentialProvider
    options:
      show_root_heading: true

::: earthaccess_auth.adapters.obstore.http_client_options
    options:
      show_root_heading: true

### icechunk (extra: `earthaccess-auth[icechunk]`)

::: earthaccess_auth.adapters.icechunk.get_credentials_callable
    options:
      show_root_heading: true

::: earthaccess_auth.adapters.icechunk.earthdata_s3_credentials
    options:
      show_root_heading: true
