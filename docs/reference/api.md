# API reference

This reference is organized by concept. The [glossary](glossary.md)
defines the terms.

## Identity

An identity is an authenticated Earthdata Login account. The rest of the
library exchanges an identity for something that a storage client can
use.

::: earthaccess_auth.login
    options:
      show_root_heading: true

::: earthaccess_auth.Auth
    options:
      inherited_members: true
      show_root_heading: true

## Temporary S3 credentials

Each DAAC has an `s3credentials` endpoint. It exchanges an identity for
AWS credentials that are valid for about one hour. Use these credentials to
read protected buckets directly from the same AWS region.

::: earthaccess_auth.S3Credentials
    options:
      show_root_heading: true

::: earthaccess_auth.fetch_s3_credentials
    options:
      show_root_heading: true

## Credential managers

A manager holds one identity. It keeps a cache of temporary credentials
for each endpoint, and fetches new credentials shortly before they
expire.

::: earthaccess_auth.S3CredentialManager
    options:
      inherited_members: true
      show_root_heading: true

## The process-wide default

The whole process shares one manager. The adapters call
[`default_manager`][earthaccess_auth.default_manager] each time they need
credentials. So when you set a new default, all consumers use the new
identity immediately. Most callers set the default with
[`set_default_auth`][earthaccess_auth.set_default_auth]. Use
[`set_default_manager`][earthaccess_auth.credentials.set_default_manager]
if you already checked an identity through a manager and want to keep the
credentials that manager has in its cache.

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

A system is the Earthdata deployment that you log in to. Pass it as the
`system` parameter of [`login`][earthaccess_auth.login]. The default is
[`PROD`][earthaccess_auth.PROD]. To test with NASA's pre-release
environment before a change goes to production, pass
[`UAT`][earthaccess_auth.UAT].

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

::: earthaccess_auth.adapters.icechunk.earthdata_containers_credentials
    options:
      show_root_heading: true
