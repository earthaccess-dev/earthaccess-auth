# API reference

## Core

::: earthaccess_auth.login
    options:
      show_root_heading: true

::: earthaccess_auth.Auth
    options:
      inherited_members: true
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

## Adapters

### fsspec (extra: `earthaccess-auth[fsspec]`)

::: earthaccess_auth.adapters.fsspec.get_fsspec_https_session
    options:
      show_root_heading: true

### obstore (extra: `earthaccess-auth[obstore]`)

::: earthaccess_auth.adapters.obstore.s3_credential_provider
    options:
      show_root_heading: true

::: earthaccess_auth.adapters.obstore.http_client_options
    options:
      show_root_heading: true
