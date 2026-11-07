# Moon Cheese UAP Detector v1.0.0

**First public stable release — complete installation, upgrade and repair package.**
Official GitHub: https://github.com/DrRavenholm/Moon-Cheese-UAP-Detector  
Licence: GNU General Public License v3.0 (`LICENSE`)

Moon Cheese UAP Detector is an independent self-hosted, camera-based sky observation system. It records motion and moving bright points, provides live monitoring and full-resolution photographs, Scheduled Video, Time-lapse Studio, event investigations, notification controls and optional remote access. A detection is not identification and does not prove an object is unidentified.

## What's new in v1.0.0

- First public stable release on the tested v0.9.9.5.3 codebase. **No changes to camera, recording, networking or data-preservation logic.**
- Uses the same tested GitHub bootstrap to install the **latest stable** release in one command without a GitHub token.
- Retains admin-password-protected Update/Repair, the redesigned About page, notifications, optional Cloudflare networking, and the full in-app Version History with the latest release expanded.
- Complete installer and GPLv3 corresponding source are prepared for the same GitHub version tag. Internal and external SHA-256 checksum manifests are required.
- Prior anonymous prerelease installation and earlier upgrades were user-tested on the Pi. The final published stable v1.0.0 installation and correct-password repair still need physical Pi acceptance before broader deployment.

## Public one-line installation

On a supported Raspberry Pi OS installation with internet access, use the official repository bootstrap:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash
```

This selects **the latest published stable GitHub Release**; it will return an error until v1.0.0 is actually published as stable. The bootstrap verifies the GitHub release asset's SHA-256 digest, checks the archive structure and executes this package's `install.sh`. It does not auto-install prereleases and does not require personal GitHub credentials.

For an intentionally published public prerelease test, the same bootstrap can be invoked with `sudo bash -s -- --prerelease vTAG`. The normal public installation command requires no flag.

## Hardware and system requirements

- Tested reference hardware: **Raspberry Pi 4**, 64-bit Raspberry Pi OS Bookworm/Trixie, with compatible camera. Other hardware still requires physical acceptance testing.
- Pi 5: capability-based detection including experimental high frame rates for supported sensors. No guarantee that a particular camera/encoder achieves every setting.
- Pi Zero 2 W: experimental; use Raspberry Pi OS Lite. Low-resource mode skips bundled Docker/NPM by default. Long exposures, rendering, high resolutions and concurrent jobs may be very slow. The original Pi Zero is more constrained and might not meet dependency requirements.
- Other Linux SBCs: experimental Debian-based installation only when a compatible Picamera2 package and camera stack are available. The installer refuses missing required dependencies with an explicit error; it does not promise universal camera support.
- Root/sudo privileges, systemd, `apt`, working camera dependencies, internet for fresh OS package installation, and sufficient storage. An existing installation retains its own packages and system services.

## Install, upgrade or repair from the full archive

Download the official `moon-cheese-uap-detector-v1.0.0.tar.gz` and matching external `SHA256SUMS` from the v1.0.0 GitHub Release. Verify the archive checksum, then run:

```bash
sha256sum -c SHA256SUMS
tar -xzf moon-cheese-uap-detector-v1.0.0.tar.gz
cd moon-cheese-uap-detector-v1.0.0
sudo bash install.sh
```

The same complete `install.sh` handles a new install, an upgrade and a same-version repair. It checks packaged file hashes, ongoing camera jobs, software dependencies and system services, makes protected backups before changing an existing application, and preserves accounts, password hashes, event media, personal settings and the existing network/Cloudflare configuration. Do not interrupt an active installation.

For a new system, the installer prints the dashboard addresses and login instructions **at the very end**. Obtain generated administrator credentials locally with:

```bash
sudo uapctl credentials
```

The dashboard normally listens on local port 8000. Never expose port 8000 or the bundled proxy administration port 8181 directly to the internet. `UAP_INSTALL_NPM=0 sudo bash install.sh` skips optional bundled NPM; this is the default on low-resource platforms.

## GitHub Software updates and Repair

Go to **Administration → System Health → Software updates** and select **Check for updates**. The normal channel checks public **stable** releases anonymously. **Update now** and **Repair current version** require the logged-in administrator's current password and use a root-owned worker, complete release archive, checksum checks and the same original installer. Repair is available only after an official release for the installed version is discoverable. No update is installed automatically.

Existing machines with earlier *private prerelease testing credentials* may still use that separate channel until it is disabled locally. To revert deliberately to the public stable channel when private testing is no longer required:

```bash
sudo python3 /opt/uap-detector/uap/software_updates.py disable-private-testing
```

This removes the locally stored private GitHub test token; it does not change Cloudflare credentials, accounts, recordings or network settings. A normal public installation never requires this step.

## Network, safety and permissions

- NPM + Let's Encrypt/Cloudflare DDNS, Cloudflare Tunnel and local-only access stay independent. Existing working configurations must not be deleted for update testing.
- Administrator-only configuration, network changes, power controls and software updates are enforced on the server; viewers and public visitors cannot issue them. Requests use session CSRF protection.
- Production remote access requires HTTPS and strong accounts. Cloudflare Tunnel, NPM and the device's own administrator login are distinct trust layers.
- IPv4 interface changes retain NetworkManager verification and an independent rollback timer.
- Browser notification email/push setup and local per-user notices continue to operate. New release notices never initiate software installation.

## Initial verification after installing

1. Confirm dashboard sign-in, camera live view and full-resolution photograph capture.
2. Confirm detection recording, scheduled video, time-lapse, thumbnail, playback and PNG export.
3. Check Wi-Fi radio selection persists while editing before Apply; use Ethernet/local console when deliberately disabling Wi-Fi.
4. Check video stage fullscreen and frame comparison for all three kinds of recording, including on a phone where supported.
5. Check the official iPhone Home Screen icon after Add to Home Screen / Open as Web App.
6. Check that NPM/SSL/DDNS or the existing Cloudflare Tunnel still function if previously configured.
7. In Administration → System Health → Software updates, check for the latest stable release. After publishing v1.0.0, confirm wrong-password rejection and successful correct-password Repair on a test system. If an earlier device still has private prerelease credentials configured, disable that private channel to return to stable releases.
8. Review Information → About Moon Cheese and Help / Version History.

## Release and test status

This package includes only the complete application, its installer, service definitions, necessary icon assets, verification manifest, licence and end-user documentation. Developer tests and test reports are kept separately and are not installed. Pi Zero 2 W, Pi 5, other SBCs and iOS Home Screen behaviour remain experimental or unverified on all target devices. The anonymous prerelease one-line install and previous GitHub upgrade/repair have passed physical Raspberry Pi tests, but the published v1.0.0 stable-channel install and correct-password repair still require separate real-hardware verification.

## Project information

- Creator: Dr Ravenholm — https://transparent-aluminium.net/
- Official source and releases: https://github.com/DrRavenholm/Moon-Cheese-UAP-Detector
- License: GNU GPLv3. This software and its corresponding source code are distributed under the terms in `LICENSE`, subject to third-party component licences.

## Third-party artwork

Locally hosted Font Awesome Free 6.7.2 icons on the About page are attributed in `THIRD_PARTY_NOTICES.md`. Brand marks identify linked platforms and do not imply affiliation.
