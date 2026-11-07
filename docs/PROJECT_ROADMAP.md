# Moon Cheese UAP Detector — v1.0 readiness and future plans

**Current authorised test version: v0.9.9.5.3 (7 November 2026).** This is a status and acceptance checklist, not a claim that v1.0 has been released.

## Already implemented

- Raspberry Pi 4 reference installation; sky-monitoring detector, original MP4s, photographs, observation review, Scheduled Video and Time-lapse Studio.
- Fullscreen investigation on the detection, scheduled-video and time-lapse viewers, with direct frame PNG download.
- Storage Management with its established five tabs, protected media and configurable retention.
- User accounts, per-user notifications/reports, opt-in Web Push and SMTP, and administrator-approved public sharing.
- Cloudflare Tunnel, NPM/SSL/DNS/DDNS integration and network rollback capabilities, with substantial physical Raspberry Pi testing of their established workflows.
- Wi-Fi radio selection fix and official Moon Cheese icon/Home Screen assets.
- Responsive Information → About Moon Cheese page, including approved first-person bio and link cards.
- Administration → System Health GitHub update checking, controlled upgrade and same-version repair. The private v0.9.9.5.1 → v0.9.9.5.2 upgrade/repair passed physical tests; v0.9.9.5.3 upgrade and About page have subsequently been observed working on the physical Pi.
- Administrator password required before Update or Repair in v0.9.9.5.3 (physical confirmation pending).

## Remaining v1.0 acceptance

1. Confirm v0.9.9.5.3 rejects incorrect Update/Repair passwords, accepts the correct password and completes a same-version repair without losing settings or recordings.
2. Test a **clean Raspberry Pi OS installation from an anonymous public GitHub prerelease**, using the single-line bootstrap. Retain the original working SD card untouched.
3. Publish the **complete corresponding application source** at the correct Git release tag under GPLv3; verify licence and third-party notices. The starter repository files alone are **not** complete application source.
4. Check repository and release history for embedded credentials, private deployment details, unwanted instructions and unnecessary media **before switching visibility to public**.
5. Run regression and installer-safety checks, including verification of any genuinely outstanding historical test failures. Confirm update notices and documented backups/repair/recovery paths.
6. Verify the public **stable** one-line bootstrap on a clean Pi after a stable candidate is ready; validate the release asset filename, GitHub digest, internal checksums and correct installation summary.
7. Decide whether a distinct initial setup wizard remains required by the original v1.0 acceptance scope; avoid duplicating already working System Administration workflows.
8. Where practical, test the icon on an iPhone Home Screen shortcut. Do not claim broader hardware support until physical testing.

## Experimental platforms

Raspberry Pi 5, Pi Zero 2 W / Raspberry Pi OS Lite and selected compatible Debian-based single-board computers have capability-aware installation paths but require hardware-specific acceptance. Document experimental status rather than blocking every Raspberry Pi 4 release on all hardware combinations.

## Deferred to v2.0

- Multi-device sharing and coordinated observation.
- Alternative mounted media destinations, expandable storage selection and NAS/network media migration.

## Development and release principles

Preserve tested detector, camera ownership, networking, media and user data; make targeted changes only with explicit authorisation; release complete install/upgrade/repair archives; do not include developer reports, tests, upload-instruction files, personal credentials or unused artwork in public installation assets.
