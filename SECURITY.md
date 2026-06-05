# Security Policy

## Supported Versions

This project is in early development (`0.x`). Security fixes are applied to the
latest released version on the default branch. Older `0.x` releases are not
maintained.

## Reporting a Vulnerability

Please **do not** open a public issue for security vulnerabilities.

Instead, report privately using GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability):

1. Go to the repository's **Security** tab.
2. Click **Report a vulnerability** to open a private advisory.

If private reporting is unavailable, contact a maintainer directly rather than
filing a public issue.

Please include:

- A description of the issue and its potential impact.
- Steps to reproduce (proof-of-concept if possible).
- Affected version or commit.

## Scope

ActiveGraph packs are libraries that run inside a host application. Treat any
credentials, tokens, or personal data flowing through a pack as sensitive — the
demo runtime stores events on local disk and is intended for development, not
production. Reports about credential handling, event-log exposure, or injection
through pack inputs are in scope.

## Response

We aim to acknowledge valid reports within a few days and will coordinate a fix
and disclosure timeline with the reporter.
