# Moon Cheese — Software updates and repair

**Implemented and maintained in Moon Cheese v1.0.1.** This page describes the actual Software updates implementation, separate public stable and optional private-testing channels, and the required first-stable Pi acceptance.

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

**Physical Raspberry Pi confirmation:** private GitHub upgrade v0.9.9.5.1 → v0.9.9.5.2, a subsequent update check and a same-version repair passed. v0.9.9.5.3 later upgraded successfully and a public anonymous one-line fresh installation also passed. A deliberately wrong administrator password was rejected. Correct-password Repair with the public v1.0.0 stable release subsequently passed on the original Pi. The v1.0.1 update and repair still need acceptance on real hardware.

## Stable-release acceptance and future maintenance

- Publish matching source and each new stable versioned release archive with its external `SHA256SUMS` after approval.
- Test the **normal** anonymous one-line installer on a clean Raspberry Pi without `--prerelease`; public prerelease installation has already been confirmed.
- Previously passed: v1.0.0 correct-password same-version Repair. For v1.0.1, confirm correct-password Repair and preserved data on real hardware after publication.
- Verify scheduled update notices at the existing administrator-configured observation-summary time, without duplicate alerts; confirm stored settings and backup/rollback after actual upgrade.
- Inspect published source and repository history for private material and review failure paths; checksums alone are not a publisher signature.

GitHub SHA-256 digests and `SHA256SUMS` detect mismatched content, but do not alone establish independent publisher authenticity. Never automatically execute an update merely because a new release appears.

## Service-file diagnostics (separate from normal Repair)

A normal Software updates Repair intentionally preserves locally modified systemd unit definitions. To compare only installed Moon Cheese units to their packaged official templates, run `sudo python3 /opt/uap-detector/uap/service_repair.py --check` on the Pi. The optional `--apply` backs up and restores just those named Moon Cheese units. It calls `systemctl daemon-reload` but does **not** restart the detector or alter unrelated service definitions, custom drop-ins, accounts or network resources. Inspect the output and any other camera application separately before deciding if a service restart is necessary.
