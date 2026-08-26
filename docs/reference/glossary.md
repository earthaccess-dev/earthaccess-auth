# Glossary

The terms this library's API, docstrings, and error messages use, grouped by
concept.

## Identity and login

**identity**
: An authenticated Earthdata Login account, represented by an
  [`Auth`][earthaccess_auth.Auth] instance. A process can hold several
  identities; most consumers use the single one behind the
  [default manager](#the-process-wide-default).

**Earthdata Login (EDL)**
: NASA's single sign-on at `urs.earthdata.nasa.gov`. Issues the tokens that
  every DAAC accepts. [`login`][earthaccess_auth.login] authenticates
  against it.

**token**
: An EDL bearer token (~60-day lifetime). Presented to DAAC endpoints to
  prove an identity; not itself an AWS credential.

**login strategy**
: How [`Auth`][earthaccess_auth.Auth] finds credentials: `environment`
  (`EARTHDATA_TOKEN`, or `EARTHDATA_USERNAME` + `EARTHDATA_PASSWORD`),
  `netrc`, or `interactive`.

**system**
: The EDL deployment to authenticate against:
  [`PROD`][earthaccess_auth.PROD] (default) or
  [`UAT`][earthaccess_auth.UAT], NASA's pre-release environment.

## Credentials and managers

**temporary S3 credentials**
: Short-lived AWS credentials
  ([`S3Credentials`][earthaccess_auth.S3Credentials]) that a DAAC issues in
  exchange for an identity, good for about an hour of direct in-region
  reads from its protected buckets.

**s3credentials endpoint**
: The per-DAAC HTTPS endpoint that performs that exchange, e.g.
  `https://data.asdc.earthdata.nasa.gov/s3credentials`. Responds 401 when it
  rejects the identity itself and 403 when a EULA or application approval is
  missing (see
  [`S3CredentialsRequestFailure`][earthaccess_auth.S3CredentialsRequestFailure]).

**credential manager**
: An [`S3CredentialManager`][earthaccess_auth.S3CredentialManager]: wraps
  one identity and caches temporary credentials per endpoint, re-fetching
  shortly before they expire. Fetches for one endpoint never block cached
  reads for another.

**warm / cold**
: A manager's per-endpoint cache is *warm* for an endpoint when it holds
  still-valid credentials (the next read is local), *cold* when the next
  read must fetch over the network.

**validate**
: Fetch real credentials through a manager before trusting its identity.
  EDL counts any non-empty token as authenticated without checking it, so
  this is the only way to learn whether DAACs will actually accept one.
  Also called a *probe*. A successful probe leaves the manager's cache warm
  for that endpoint.

## The process-wide default

**default manager**
: The one credential manager shared by the whole process, returned by
  [`default_manager`][earthaccess_auth.default_manager] and created lazily
  from the non-interactive login strategies. Adapter callables call the
  function at use time instead of capturing an instance, which keeps them
  picklable and means a new default reaches every consumer at once.

**setting the default**
: Making an identity the process-wide default.
  [`set_default_auth`][earthaccess_auth.set_default_auth] takes an identity
  and builds a fresh manager for it.
  [`set_default_manager`][earthaccess_auth.credentials.set_default_manager]
  takes a manager you already have, cache included, which matters after
  validating: the credentials the probe fetched don't get fetched again.

## DAACs and buckets

**DAAC**
: A NASA Distributed Active Archive Center, such as PO.DAAC, ASDC, or
  NSIDC: the data centers that host Earthdata collections and operate the
  s3credentials endpoints. Enumerated in
  [`DAACS`][earthaccess_auth.daac.DAACS].

**provider**
: The CMR provider code naming a DAAC's cloud collections (e.g. `POCLOUD`
  for PO.DAAC), resolved by
  [`find_provider`][earthaccess_auth.daac.find_provider].

**bucket registry**
: The CMR-derived mapping
  ([`BUCKET_REGISTRY`][earthaccess_auth.daac.BUCKET_REGISTRY]) from each
  protected S3 bucket to its AWS region and s3credentials endpoint;
  [`resolve_bucket`][earthaccess_auth.daac.resolve_bucket] looks up bucket
  names and `s3://` URLs.

**EULA / application approval**
: Per-DAAC agreements an EDL profile must accept before that DAAC will issue
  credentials. A 403 from an s3credentials endpoint usually means one is
  missing; review the pending lists from your
  [EDL profile](https://urs.earthdata.nasa.gov/profile) and
  [application search](https://urs.earthdata.nasa.gov/application_search).
