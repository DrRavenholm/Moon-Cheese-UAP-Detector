# Moon Cheese UAP Detector — Release History

## v1.0.1 — 14 November 2026 (maintenance release)

- Corrected the administrator Delivery History page crash; retained filtering and pagination.
- Improved SMTP error explanations for authentication, TLS, connection and provider refusals, without exposing secrets.
- Added four browser-local visitor themes: default Blue, Red, Green and Cheese Yellow.
- Simplified Cloudflare Tunnel token setup guidance and documented exact permission groups, resource scopes and Error 1033 troubleshooting.
- Removed the briefly appearing software-update reload link and improved release-status consistency.
- Published administrator credential retrieval instructions prominently in the README and installer output.
- Corrected outdated Time-lapse, email/Web Push, release-status and installation documentation.
- Added a non-destructive Moon Cheese-owned systemd service inspection and manual repair helper.
- Retained existing detector, camera, recordings, networking and user-data behaviour.

# Moon Cheese UAP Detector — Release History

This page summarises the main development milestones. The application's bundled `VERSION_HISTORY.md` retains the **full, detailed version-by-version history**; earlier entries must not be replaced by this summary.

## v1.0.0 — 7 November 2026 (public stable release)

- First public stable-release package, built directly from the Raspberry Pi-tested v0.9.9.5.3 software.
- Public anonymous GitHub one-line installer now targets the latest stable release when published; the exact prerelease test path was previously proven on a clean Pi.
- Retains password-protected software Update/Repair, full-resolution photos, detector, Scheduled Video, Time-lapse Studio, About page and comprehensive Help/Version History.
- Matching full corresponding GPLv3 source and third-party notices prepared for a tag on the updated Code branch.
- No detector, network, camera or user-data migration changes; correct-password v1.0.0 stable-channel repair subsequently passed on a Raspberry Pi.

## v0.9.9.5.3 — 7 November 2026 (development prerelease)

- Added verification of the signed-in administrator's current password before **Update now** and **Repair current version**; **Check for updates** remains password-free.
- Redesigned Information → About Moon Cheese using the official artwork, first-person creator biography, and grouped, responsive website/social/music/support links with local icons.
- Corrected Help descriptions of the already-operational update system.
- Preserved the latest-open / older-collapsed in-app Version History display and all historical entries.
- Kept the installation archive clean of development tests, reports, upload instructions and unused original artwork.
- GitHub upgrade to v0.9.9.5.3 and the new About page were confirmed on a physical Raspberry Pi. Incorrect-password rejection was user-confirmed; correct-password Repair awaits a discoverable stable release.

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
