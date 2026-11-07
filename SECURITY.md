# Security policy

Moon Cheese UAP Detector is currently in final pre-v1.0 testing. Public GitHub availability and published prereleases **do not imply completed production security acceptance**.

## Reporting a security issue

Please **do not** disclose a vulnerability, exploit details, passwords, tokens, private signing keys, personal system configuration, home IP addresses, unpublished recordings or database exports in a public Issue.

If the repository has GitHub **Private vulnerability reporting** enabled, use that feature to report a security problem privately. Otherwise contact the maintainer privately through the project creator's official website, [Transparent-Aluminium.net](https://transparent-aluminium.net/), rather than posting sensitive details publicly.

## Deployment security

- Protect administrator accounts with strong, unique passwords; updates and repairs require a signed-in administrator's current password.
- Use the maintained application release and avoid exposing local-only administration interfaces directly to the internet.
- Cloudflare and other external networking integrations are optional. Store API tokens and other credentials on the device only, never in GitHub or in distributed installers.
- Public installers require **no personal GitHub token**.
- Verify downloads and use the project's official repository and release assets. Checksums detect unintended changes; they are not an independent cryptographic signature of the publisher.

Source, dependency/licence, fresh-install and release-integrity review remain part of the v1.0 readiness process.
