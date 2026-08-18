# earthaccess-side changes

What changes inside the existing [`earthaccess`](https://github.com/earthaccess-dev/earthaccess) package now that `earthaccess_auth` (this repository) is the single implementation.

## Shim modules

Each extracted module is now a re-export, so every existing import path keeps working:

```python
# earthaccess/auth.py
from earthaccess_auth.auth import (
    Auth,
    BasicAuthResponseHook,
    SessionWithHeaderRedirection,
    netrc_path,
)

# earthaccess/system.py
from earthaccess_auth.system import (
    PROD,
    UAT,
    CMRBaseURL,
    EDLHostname,
    StatusApiURL,
    StatusURL,
    System,
)

# earthaccess/daac.py
from earthaccess_auth.daac import (
    DAAC_TEST_URLS,
    DAACS,
    DAACConfig,
    find_provider,
    find_provider_by_shortname,
)
```

`earthaccess/exceptions.py` keeps its download-stack exceptions (`DownloadFailure`, `ServiceOutage`, `EulaNotAccepted`) as real code and re-exports `LoginStrategyUnavailable` and `LoginAttemptFailure` from `earthaccess_auth.exceptions`, so `except earthaccess.exceptions.LoginAttemptFailure` still catches what the core raises — they are the same class objects.

## Behavior notes

- `earthaccess.api.login` keeps its module-level singleton and `Store` wiring; only the `Auth` class it drives moved. Its `"all"` fallback loop stays (duplicated in `earthaccess_auth.login`, which has no singleton) — 15 lines of orchestration in two places is the accepted cost of the singleton staying out of the core.
- `earthaccess/system.py` on main took CMR URLs from python-cmr (`CMR_OPS`/`CMR_UAT`); the core inlines those values as literals. The shim re-export therefore drops earthaccess's use of python-cmr *for System construction only* — python-cmr remains a full earthaccess dependency for search. If python-cmr ever changes those constants, the literals in `earthaccess_auth/system.py` must follow.
- The `User-Agent` header on EDL requests defaults to `earthaccess-auth v{version}`, but `Auth` now takes a `user_agent` parameter; the earthaccess singleton sets it to `earthaccess v{version}`, so the string server-side metrics may key on is unchanged.
- `earthaccess` depends on the published `earthaccess-auth` distribution; `tinynetrc` dropped out of earthaccess's own direct dependencies since only the extracted `auth.py` used it.
- Auth tests moved to `earthaccess-auth/tests/test_auth.py`; earthaccess keeps a minimal `tests/unit/test_auth.py` asserting the shim resolves to the same objects. Integration tests still exercise auth through `earthaccess.login` and stay put.

## CI

`test.yml` has `auth-core-tests` and `auth-extras-tests` jobs running `earthaccess-auth`'s own tests against its minimal and extras environments — the check that the core imports and passes tests *without* fsspec/obstore/python-cmr installed.

## Releases

`earthaccess-auth` now lives in its own repository and is versioned and
released independently: tagging a release here publishes only this
distribution (via `.github/workflows/publish.yml` and PyPI trusted
publishing), and earthaccess picks up new versions through its normal
dependency requirement rather than lockstep tags.
