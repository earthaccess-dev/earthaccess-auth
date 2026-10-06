# Glossary

These are the terms that the API, docstrings, and error messages of this
library use. They are grouped by concept.

## Identity and login

**identity**
: An authenticated Earthdata Login account, represented by an
  [`Auth`][earthaccess_auth.Auth] instance. A process can have more than
  one identity. But most consumers use the one identity of the
  [default manager](#the-process-wide-default).

**Earthdata Login (EDL)**
: NASA's single sign-on service at `urs.earthdata.nasa.gov`. EDL issues
  the tokens that all DAACs accept. [`login`][earthaccess_auth.login] logs
  in to EDL.

**token**
: An EDL bearer token. It is valid for about 60 days. A client sends the
  token to DAAC endpoints to prove an identity.

**login strategy**
: The way that [`Auth`][earthaccess_auth.Auth] finds credentials. The
  strategies are `environment` (`EARTHDATA_TOKEN`, or `EARTHDATA_USERNAME`
  and `EARTHDATA_PASSWORD`), `netrc`, and `interactive`.

**system**
: The EDL deployment that you log in to. It is
  [`PROD`][earthaccess_auth.PROD] (the default) or
  [`UAT`][earthaccess_auth.UAT] (NASA's pre-release environment).

## Credentials and managers

**temporary S3 credentials**
: AWS credentials ([`S3Credentials`][earthaccess_auth.S3Credentials])
  that a DAAC issues in exchange for an identity. They are valid for about
  one hour. Use them to read the DAAC's protected buckets directly from the
  same AWS region.

**s3credentials endpoint**
: The HTTPS endpoint of a DAAC that exchanges an identity for temporary
  credentials, for example
  `https://data.asdc.earthdata.nasa.gov/s3credentials`. The endpoint
  returns 401 when it rejects the identity. It returns 403 when a EULA or
  application approval is missing. See
  [`S3CredentialsRequestFailure`][earthaccess_auth.S3CredentialsRequestFailure].

**credential manager**
: An [`S3CredentialManager`][earthaccess_auth.S3CredentialManager] holds
  one identity. It keeps a cache of temporary credentials for each endpoint,
  and fetches new credentials shortly before they expire. A fetch for one
  endpoint never blocks cached reads for a different endpoint.

**warm / cold**
: A manager's cache is *warm* for an endpoint when it has valid
  credentials for that endpoint. The next read then comes from the cache.
  The cache is *cold* when the next read must fetch credentials over the
  network.

**validate**
: Check if DAACs accept credentials. This is also called a *probe*. After
  a successful probe, the manager's cache is warm for that endpoint.

## The process-wide default

**default manager**
: The one credential manager that the whole process shares.
  [`default_manager`][earthaccess_auth.default_manager] returns it. It is
  created on first use, with the non-interactive login strategies. The
  adapter functions call `default_manager` each time they need credentials.
  They don't keep a reference to a manager. So they can be pickled, and a
  new default applies to all consumers immediately.

**setting the default**
: Making an identity the process-wide default.
  [`set_default_auth`][earthaccess_auth.set_default_auth] takes an identity
  and builds a new manager for it.
  [`set_default_manager`][earthaccess_auth.credentials.set_default_manager]
  takes a manager that you already have, and keeps its cache.

## DAACs and buckets

**DAAC**
: A NASA Distributed Active Archive Center, such as PO.DAAC, ASDC, or
  NSIDC. DAACs host Earthdata collections and operate the s3credentials
  endpoints. [`DAACS`][earthaccess_auth.daac.DAACS] lists them.

**provider**
: The CMR provider code for a DAAC's cloud collections, for example
  `POCLOUD` for PO.DAAC.
  [`find_provider`][earthaccess_auth.daac.find_provider] finds it.

**bucket registry**
: The mapping ([`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY])
  from each protected S3 bucket to its AWS region and s3credentials
  endpoint. It is built from CMR metadata.
  [`resolve_bucket`][earthaccess_auth.daac.resolve_bucket] looks up bucket
  names and `s3://` URLs in it.

**EULA / application approval**
: Agreements that an EDL profile must accept before a DAAC issues
  credentials. Each DAAC has its own. A 403 from an s3credentials endpoint
  usually means that one is missing. To see the pending agreements, open
  your [EDL profile](https://urs.earthdata.nasa.gov/profile) and
  [application search](https://urs.earthdata.nasa.gov/application_search).
