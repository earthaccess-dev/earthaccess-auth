# Releasing earthaccess-auth

The version is derived from git tags by hatch-vcs; there is no version
string to edit in the source.

## Cutting a release

1. Update `CHANGELOG.md`: rename `## [Unreleased]` to `## [vX.Y.Z] - YYYY-MM-DD`,
   add a fresh empty `## [Unreleased]` section above it, and update the
   link references at the bottom of the file.
2. Open a PR with that change and merge it.
3. Tag the merge commit `vX.Y.Z` (annotated) and push the tag.
4. Publish a GitHub release for the tag. This triggers
   `.github/workflows/publish.yml`, which builds the sdist/wheel and
   uploads them to PyPI via trusted publishing — there is no manual upload
   step and no API token.
5. Check that the new version appears on
   [PyPI](https://pypi.org/p/earthaccess-auth) and that Read the Docs
   built the tagged version.

## One-time repository setup

These live outside the repository and must be configured once by a
maintainer with admin access:

- [ ] **PyPI**: create the `earthaccess-auth` project and configure a
  [trusted publisher](https://docs.pypi.org/trusted-publishers/) for this
  repository, workflow `publish.yml`, environment `pypi`. Create the
  matching `pypi` environment in the GitHub repo settings.
- [ ] **Read the Docs**: import the project (slug `earthaccess-auth`) and
  enable pull request builds.
- [ ] **Branch protection**: protect `main` (require PRs, require the test
  workflows, require review).
- [ ] **CodeQL**: enable default setup under Settings → Code security
  (satisfies the OpenSSF Scorecard SAST check without a workflow).
- [ ] **Scorecard**: after the first push, verify the
  `ossf/scorecard-action` pin in `.github/workflows/scorecard.yml`
  resolves (it was pinned while offline) and that publishing results is
  acceptable to the org.
- [ ] **Code of Conduct contact**: confirm `nsidc@nsidc.org` in
  `CODE_OF_CONDUCT.md` is the intended contact for this repository.
