# Security policy

Moon Cheese UAP Detector v1.0.0 is prepared for first public stable distribution. Public access or a stable GitHub Release does **not** by itself guarantee that every deployment has passed its own network/security acceptance. The official Raspberry Pi 4 reference and published-stable upgrade/repair tests must be distinguished from experimental hardware support.

## Reporting a security issue

Please **do not** disclose a vulnerability, exploit details, passwords, tokens, private signing keys, personal system configuration, home IP addresses, unpublished recordings or database exports in a public Issue.

If the repository has GitHub **Private vulnerability reporting** enabled, use that feature to report a security problem privately. Otherwise contact the maintainer privately through the project creator's official website, [Transparent-Aluminium.net](https://transparent-aluminium.net/), rather than posting sensitive details publicly.

## Deployment security

- Protect administrator accounts with strong, unique passwords; updates and repairs require a signed-in administrator's current password.
- Use the maintained application release and avoid exposing local-only administration interfaces directly to the internet.
- Cloudflare and other external networking integrations are optional. Store API tokens and other credentials on the device only, never in GitHub or in distributed installers.
- Public installers require **no personal GitHub token**.
- Verify downloads and use the project's official repository and release assets. Checksums detect unintended changes; they are not an independent cryptographic signature of the publisher.

The published archive must correspond to the tagged complete GPLv3 source. Review repository history and release assets before publication; static token-pattern checks are not a comprehensive security audit.
