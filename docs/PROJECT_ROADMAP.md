# Moon Cheese UAP Detector — v1.0.0 Release Status and Roadmap

**Current prepared release: v1.0.0 (7 November 2026).** This is a public stable-release build awaiting final confirmation on the actual published release. The user-tested v0.9.9.5.3 baseline is preserved.

## Implemented and physically confirmed on Raspberry Pi

- Camera-based sky monitoring, recording, photography and web dashboard are established; Scheduled Video and Time-lapse Studio remain distinct observation tools.
- Observation review, MP4 investigations/fullscreen, direct PNG frame exports, five-tab Storage Management, email/Web Push, user accounts and optional sharing are implemented.
- NPM/Cloudflare/DDNS, Tunnel hostname changes and Wi-Fi enable/disable were tested in the earlier release series; all source code is retained.
- Private GitHub v0.9.9.5.1 → v0.9.9.5.2 upgrade, in-app Check for updates and same-version Repair passed on the user's Pi.
- GitHub upgrade to v0.9.9.5.3 and the redesigned About Moon Cheese page passed user acceptance.
- A public, anonymous version-pinned prerelease installation of v0.9.9.5.3 from a clean SD card **passed**; no GitHub login, token or manual PC transfer was required.
- Entering a deliberately incorrect administrator password produced **Denied** in v0.9.9.5.3.

## Final v1.0.0 stable-release acceptance

1. Commit the matching complete source from this build to the GitHub Code page; check public repository history and release assets for private data. **Create v1.0.0 tag only after the matching source commit.**
2. Upload the complete `moon-cheese-uap-detector-v1.0.0.tar.gz` and its external `SHA256SUMS` as the **only manual GitHub release assets** and publish the release as **stable**, not prerelease.
3. On a clean test SD card, run the ordinary one-line installer **without** `--prerelease`, then confirm dashboard version, sign-in, camera, full-resolution capture and initial installation summary.
4. On the existing/test machine, check v1.0.0's public stable channel. Ensure a deliberately incorrect administrator password is rejected and a **correct** administrator password allows same-version Repair to complete with preserved user data. Existing private testing credentials must be disabled explicitly before testing stable-channel checks on an earlier device.
5. Verify camera recordings, scheduled video/time-lapse, saved media, existing network configuration, notifications, backups and recovery on representative hardware. Keep the established working SD card until the new release is accepted.
6. Confirm no unexpected regressions from historical tests; distinguish source/static validation from actual Pi hardware and network testing. A final security review of public repository history and deployed configuration is still required; a token-pattern scan cannot replace it.

## Hardware status

Raspberry Pi 4 on 64-bit Raspberry Pi OS is the proven reference. Pi 5, Pi Zero 2 W / Raspberry Pi OS Lite, the iPhone Home Screen web app experience and other Debian-based SBCs have experimental/unverified aspects and must not be advertised as universally tested. Hardware-specific validation can continue after the Pi 4 stable baseline is accepted.

## Future roadmap

**Reserved for v2.0:** multi-device coordination/sharing; alternate mounted storage locations, NAS storage and related data migration. Do not introduce these into the first stable release.

## Development rules

Each authorised release is a complete install/upgrade/repair package; preserve credentials, databases, media, user configuration, cloud/network state and backups. Keep tests, test reports, development/upload instructions, unused oversized artwork and deployment secrets outside public installer archives and GitHub source. Older Version History entries and Help topics are retained.
