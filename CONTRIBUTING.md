# Contributing to earthaccess-auth

Thanks for helping improve the NASA Earthdata Login auth core! Bug reports,
docs fixes, and code contributions are all welcome via issues and pull
requests. By contributing you agree to the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

The project is managed with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/earthaccess-dev/earthaccess-auth
cd earthaccess-auth
uv sync          # installs the package plus the dev dependency group
```

## Day-to-day commands

```bash
uv run pytest                  # run the test suite
uv run mypy                    # strict type checking (src, tests, scripts)
uv run ruff check .            # lint
uv run ruff format .           # format
uv run --group docs mkdocs serve   # live-preview the docs
```

If you keep `UV_EXCLUDE_NEWER` set locally (e.g. to avoid resolving into a
just-published release), scope it to commands that actually re-resolve
(`uv lock`, `uv lock --upgrade`, `uv add`). A plain `uv sync` or `uv run`
with that variable set will silently rewrite `uv.lock` to record the policy;
since CI sets no such variable, the `uv-lock` hook and CI will then fail
with "the lockfile needs to be updated". Prefer `uv sync --locked` /
`uv run --locked` for routine work — they validate the lock instead of
rewriting it.

## Pre-commit hooks

Lint and hygiene checks run via [prek](https://prek.j178.dev/) (a drop-in,
Rust-based pre-commit runner; `pre-commit` itself works too, from the same
`.pre-commit-config.yaml`):

```bash
uvx prek install       # run the hooks on every commit
uvx prek run -a        # or run them across the whole tree once
```

CI runs the same hooks, plus mypy, the test matrix (core-only and with the
`fsspec`/`obstore` extras), a strict docs build, and
[zizmor](https://docs.zizmor.sh) over the workflows — so running the
commands above locally covers everything CI will check.

## Ground rules

- Keep the core's runtime dependencies minimal (`requests`, `tinynetrc`,
  `typing_extensions` — nothing else). Anything heavier belongs behind an
  optional extra under `earthaccess_auth.adapters`.
  `tests/test_import_guard.py` enforces this.
- Public API must stay importable and typed; mypy runs in `strict` mode.
- `BUCKET_ENDPOINTS` in `src/earthaccess_auth/daac.py` is maintained by
  hand from the weekly CMR sweep — see
  `docs/explanation/cmr-s3-buckets.md` before editing it.
- Add a `CHANGELOG.md` entry for user-visible changes.

Releases are cut by maintainers — see [RELEASING.md](RELEASING.md).
