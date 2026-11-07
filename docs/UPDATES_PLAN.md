# Moon Cheese — Software updates and repair

**Implemented in the pre-v1.0 application.** This page documents the current functionality and remaining production checks. It is **not** a proposal for a future update system.

## Administration → System Health

**Software updates** and **System power** are separate, always-visible panels.

The Software updates panel displays the installed version, available release information and update/repair status, with:

- **Check for updates:** reads GitHub release information. No extra administrator-password prompt is required.
- **Update now:** installs an approved available version only after verification of the signed-in administrator's current password.
- **Repair current version:** re-runs the verified complete installer for the installed version, again requiring the current administrator password.

An incorrect or missing password prevents the privileged action from being queued and should produce an inline message. Administrators initiate installations themselves; checking does **not** trigger automatic installation. Viewer/public accounts have no permission to run these operations.

## Channels

- **Normal public channel:** checks the latest published **stable** GitHub Release. GitHub excludes prereleases from its latest-stable endpoint.
- **Private testing channel:** uses a restricted, explicitly enabled read-only GitHub access token stored on the Pi, never distributed in archives. It supports authorised private prereleases and was used successfully for the v0.9.9.5.2 acceptance test.
- **Anonymous bootstrap prerelease test:** the separate `moon-cheese-install.sh --prerelease TAG` command selects a *published public prerelease*. This is for a **clean installation test**, and does not itself change the in-app updater's stable/private channel selection.

Before retiring private testing, deliberately switch the test Pi back to the normal stable channel. Do not publish any stored private token.

## Installation and protection

The root-owned update worker downloads the complete versioned application archive and its integrity information, validates the release and archive, checks for unsafe active operations, and delegates to the **same installer** used for fresh installation and repair. The installer preserves configured user data and creates backups according to its upgrade workflow. Status is reported back to the dashboard.

**Physical Raspberry Pi confirmation:** private GitHub upgrade v0.9.9.5.1 → v0.9.9.5.2, a subsequent update check and a same-version repair passed. v0.9.9.5.3 was later installed successfully via GitHub; the new administrator-password and repair interactions still require user acceptance testing.

## Remaining v1.0 verification

- Confirm the v0.9.9.5.3 password flow and same-version repair on the physical Pi.
- Validate anonymous public fresh installation and public stable-channel upgrade/repair behaviour.
- Verify scheduled update notifications follow each administrator's existing configured observation-summary time, without duplicate alerts.
- Review failure/rollback, release-source completeness, release authenticity and secret-handling before publication as stable.

GitHub SHA-256 digests and `SHA256SUMS` detect mismatched content, but do not alone establish independent publisher authenticity. Never automatically execute an update merely because a new release appears.
