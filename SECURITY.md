# Security Policy

## Supported Versions

Only the latest release of `earthaccess-auth` receives security updates.

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Instead, use GitHub's private vulnerability reporting for this repository:
open the repository's **Security** tab and choose **Report a vulnerability**
(see the [GitHub documentation](https://docs.github.com/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)).

Please include as much of the following as you can:

- The type of issue and its impact
- Affected version(s) and configuration
- Step-by-step instructions or a proof of concept to reproduce the issue

You should receive an acknowledgement within a week. Please allow the
maintainers a reasonable amount of time to resolve the issue before any
public disclosure.

## Scope notes

This package handles NASA Earthdata Login credentials and tokens. Reports
about credential leakage (in logs, error messages, redirects, or the
`.netrc` handling) are particularly appreciated.
