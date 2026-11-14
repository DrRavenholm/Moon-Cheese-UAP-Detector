# Moon Cheese UAP Detector — v1.0.1 Maintenance and Roadmap

**Current prepared maintenance release: v1.0.1 (14 November 2026).** The user confirmed that v1.0.0 was published as stable and upgraded/repaired successfully on the original Pi, while the public anonymous installer succeeded for a separate test installation. v1.0.1 fixes confirmed delivery and presentation issues; its final physical acceptance remains pending.

## Implemented and physically confirmed on Raspberry Pi

- Camera-based sky monitoring, recording, photography and web dashboard are established; Scheduled Video and Time-lapse Studio remain distinct observation tools.
- Observation review, MP4 investigations/fullscreen, direct PNG frame exports, five-tab Storage Management, email/Web Push, user accounts and optional sharing are implemented.
- NPM/Cloudflare/DDNS, Tunnel hostname changes and Wi-Fi enable/disable were tested in the earlier release series; all source code is retained.
- Private GitHub v0.9.9.5.1 → v0.9.9.5.2 upgrade, in-app Check for updates and same-version Repair passed on the user's Pi.
- GitHub upgrade to v0.9.9.5.3 and the redesigned About Moon Cheese page passed user acceptance.
- A public, anonymous version-pinned prerelease installation of v0.9.9.5.3 from a clean SD card **passed**; no GitHub login, token or manual PC transfer was required.
- Entering a deliberately incorrect administrator password produced **Denied** in v0.9.9.5.3.

## v1.0.1 acceptance

1. Commit the matching extracted source to GitHub Code **before** creating the v1.0.1 tag.
2. Upload only `moon-cheese-uap-detector-v1.0.1.tar.gz` and its external `SHA256SUMS` to the new GitHub Release.
3. Verify Delivery History (including empty and populated ledger), SMTP test errors, four visitor themes, public pages and the Cloudflare setup instructions.
4. Check camera/detector monitoring, jobs, networking and preservation of settings on the physical Pi. Test normal Update/Repair with an administrator password when the latest stable release is available.
5. Service-file repair is opt-in only and never blindly restarts the camera or third-party services. Jim's intermittent Cloudflare Error 1033 and Gmail account require real-Pi diagnostics when available; documentation and generic errors cannot prove a fix to those external problems.

## Hardware status

Raspberry Pi 4 on 64-bit Raspberry Pi OS is the proven reference. Pi 5, Pi Zero 2 W / Raspberry Pi OS Lite, the iPhone Home Screen web app experience and other Debian-based SBCs have experimental/unverified aspects and must not be advertised as universally tested. Hardware-specific validation can continue after the Pi 4 stable baseline is accepted.

## Future roadmap

**Reserved for v2.0:** multi-device coordination/sharing; alternate mounted storage locations, NAS storage and related data migration. Do not introduce these into the first stable release.

## Development rules

Each authorised release is a complete install/upgrade/repair package; preserve credentials, databases, media, user configuration, cloud/network state and backups. Keep tests, test reports, development/upload instructions, unused oversized artwork and deployment secrets outside public installer archives and GitHub source. Older Version History entries and Help topics are retained.
