# Moon Cheese UAP Detector — Release History

This page summarises the main development milestones. The application's bundled `VERSION_HISTORY.md` retains the **full, detailed version-by-version history**; earlier entries must not be replaced by this summary.

## v1.0 — preparation / not yet released

Public prerelease testing is focused on: an anonymous one-line GitHub installer, a fresh Raspberry Pi OS installation, current administrator-password verification, release-source publication, security checks and reliable stable-channel update/repair behaviour. **No v1.0 release has been declared or published.**

## v0.9.9.5.3 — 7 November 2026 (development prerelease)

- Added verification of the signed-in administrator's current password before **Update now** and **Repair current version**; **Check for updates** remains password-free.
- Redesigned Information → About Moon Cheese using the official artwork, first-person creator biography, and grouped, responsive website/social/music/support links with local icons.
- Corrected Help descriptions of the already-operational update system.
- Preserved the latest-open / older-collapsed in-app Version History display and all historical entries.
- Kept the installation archive clean of development tests, reports, upload instructions and unused original artwork.
- GitHub upgrade to v0.9.9.5.3 and the new About page were confirmed on a physical Raspberry Pi. New password-and-repair acceptance remains to be completed.

## v0.9.9.5.2 — 7 November 2026 (development prerelease)

- Added private GitHub prerelease testing support with separately stored, restricted credentials.
- Improved privileged archive-extraction safety and permissions.
- **Confirmed on Raspberry Pi:** real private GitHub upgrade from v0.9.9.5.1 to v0.9.9.5.2, Check for updates, and Repair current version.

## v0.9.9.5.1 — November 2026 (development prerelease)

- Kept Software updates and System power as separately visible System Health panels.
- Reduced the installation archive by excluding developer-only files and unused oversized artwork.
- Retained internal file checksums.

## v0.9.9.5 — November 2026 (development prerelease)

- Fixed Wi-Fi selection changes being reset by automatic status polling.
- Corrected fullscreen investigation for detection videos, scheduled videos and time-lapses.
- Added official Moon Cheese icon assets, Home Screen/web-app support and the About page.
- Introduced GitHub stable-release checking and controlled update/repair infrastructure.
- Expanded installer hardware-capability checks; non-Pi-4 hardware remains experimental pending testing.

## v0.9.9.4.13 — 31 October 2026 (development prerelease)

- Improved Cloudflare connector package installation, handling of HTTP 403 retrieval failures, and managed Tunnel cleanup.
- Improved Cloudflare Tunnel errors and Help navigation.

## Earlier development

Earlier releases established camera monitoring, video/photograph capture, Scheduled Video, Time-lapse Studio, observation investigations, Storage Management, administrator accounts, notifications, NPM/Cloudflare integration and safe networking controls. See `VERSION_HISTORY.md` inside the corresponding full installation packages for the complete original chronology.

**Reminder:** A development prerelease is not the first stable v1.0 release.
