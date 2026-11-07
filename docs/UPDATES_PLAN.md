# Planned Moon Cheese update and repair system

**Design note only — not implemented in v0.9.9.4.13.**

Official repository: `DrRavenholm/Moon-Cheese-UAP-Detector`.

## System Health user interface

Keep the compact design previously approved: a collapsible **Software updates** section displaying Installed version, Latest available stable release, last check, last update result and release notes. Use three adjacent controls: **Check for updates**, **Update now**, and **Repair current version**. No long checkbox confirmations.

Only authenticated administrators can perform updates or repairs, with server-side permission enforcement. Public/viewer roles must never see update credentials or gain privileges.

## Checks and notifications

- Query the latest published stable GitHub Release over HTTPS. Ignore drafts and prereleases by default.
- Compare version numbers numerically, not lexicographically; use an explicit dev/prerelease channel only when separately enabled.
- Use the configured Observation summary preferences time for scheduled checks and administrator update notifications; avoid duplicate messages about the same release.
- Checking does not automatically install; administrator chooses Update now.

## Safe update / repair

1. Validate administrator authorisation and download only the exact official release asset.
2. Validate version, published metadata, archive contents, SHA-256 and (once introduced) publisher's release signature using a pinned trusted public key.
3. Check disk space and absence of active recordings, time-lapse rendering or other unsafe jobs.
4. Back up current application code, configuration, auth and a consistent SQLite snapshot. Preserve media, credentials, networking and NPM state.
5. Run the already-proven `install.sh` from the release; do not replace it with a new installer.
6. Verify services, dashboard and installed version. Report progress and actionable errors within System Health.
7. On failure, provide a tested rollback/recovery route. Record a local update log; do not expose secrets to the UI.
8. Repair current version re-installs the *same* version from its corresponding verified asset, preserving all user data.

Avoid restarting the application's own dashboard process until the status can be recovered on reload; a privileged independent updater is needed. Never allow the web process to execute arbitrary shell commands or arbitrary user-chosen release URLs.

## Signing keys

- Public releases do not require users to have personal GitHub tokens.
- A separate **release-signing key pair** is recommended for production. Generate it privately on the maintainer's own trusted computer using a supported signing tool, keep the PRIVATE key outside GitHub and application archives, back it up securely, and include only the PUBLIC verification key in the trusted updater/bootstrap.
- Record a key rotation plan. Neither key is required for today's initial repository upload.
- GitHub Actions workflows can generally use their automatically provided `GITHUB_TOKEN` with minimum permissions, rather than a manually created personal access token.
- Private-repository release tests require separately arranged authenticated access; never embed a personal access token in the public installer or a distributed detector.

## Release format

- Git tag: `v1.0.0`
- Complete release asset: `moon-cheese-uap-detector-v1.0.0.tar.gz`
- Checksum asset: `moon-cheese-uap-detector-v1.0.0.tar.gz.sha256`
- Corresponding source included in the repository at the release tag, consistent with GPLv3.

The bootstrap installer bundled with this starter kit only implements **public latest-stable download, GitHub SHA-256 check, safe archive structure validation and hand-off to the existing `install.sh`**. It does not yet implement release-signature verification or the System Health updater.
