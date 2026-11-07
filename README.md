# Moon Cheese UAP Detector

**An open-source, camera-based sky-monitoring, recording and investigation system for Raspberry Pi.**

Moon Cheese UAP Detector combines automatic camera monitoring with tools to capture, organise and examine unusual motion or lights in the sky. It is designed for enthusiasts and independent researchers who want to keep the original recordings available for closer investigation.

A detection is **not** identification, and Moon Cheese does not claim to prove that any recorded object or event is unexplained.

> **Release status — v1.0 preparation:** The latest authorised test build is **v0.9.9.5.3**. Public prerelease installations are being tested. **v1.0 is not yet a published stable release.**

## Install Moon Cheese

### One-line installation — latest stable release

Once the first public stable release is published, install on a supported Raspberry Pi OS system with:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash
```

The bootstrap downloads the latest **stable** GitHub Release's complete Moon Cheese installation archive, checks the SHA-256 asset digest, validates the archive structure, then runs the archive's original `install.sh`. It is designed for clean installations as well as existing-installation upgrades; the main installer retains responsibility for backups and service setup.

**This normal command does not select prereleases.** Do not present it as a working stable installer until a stable release has been published and tested.

### One-line installation — public prerelease testing

To test the *actual anonymous GitHub download and fresh-install process* before v1.0, use the prerelease command below on a freshly prepared test Raspberry Pi **after this repository is public and the `v0.9.9.5.3` GitHub Release is published as a prerelease**:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash -s -- --prerelease v0.9.9.5.3
```

This uses the **same bootstrap**, checksum checks and packaged installer as the stable command; the flag selects a specific public prerelease instead of GitHub's latest stable release. **No GitHub login, token, PC download or manual file transfer is required.**

Prereleases are for testing. Use a **separate SD card or test device** until the clean-install checks pass. Public testing does not mean the software has completed v1.0 acceptance.

See [Installation and requirements](docs/INSTALLATION.md) for more information.

## What Moon Cheese does

- **Automatic sky monitoring:** camera analysis for movement, bright moving lights, or combined events, with configurable day/night and custom settings.
- **Record and investigate:** retained MP4 observations, notes, classification, pinning, frame-by-frame inspection, playback controls, image enhancement and still-frame export.
- **Full-resolution photography:** capture and review photographs from the connected camera.
- **Scheduled Video and Time-lapse Studio:** plan recordings and time-lapses, review finished videos, and manage source material.
- **Observation management:** dashboard, galleries, calendar, storage protections and administrative approval for public sharing.
- **Notifications:** user-configurable email, Web Push and observation reports.
- **System administration:** protected user accounts, system health, backups, and optional network features such as Cloudflare Tunnel, DNS/DDNS and reverse-proxy integration.
- **In-app software maintenance:** administrator-controlled Check for updates, Update now and Repair current version. Update and Repair require the signed-in administrator's current password.

Moon Cheese includes contextual Help and a full in-app Version History. Network features are optional; the detector can be used on a local network.

## Hardware and release status

**Primary reference platform:** Raspberry Pi 4 running supported 64-bit Raspberry Pi OS, with compatible camera hardware. The application has been used and upgraded successfully on the physical Pi 4 test system.

Raspberry Pi 5, Pi Zero 2 W / Raspberry Pi OS Lite, and other compatible Debian-based single-board computers have experimental installer support but **have not all passed real-hardware acceptance tests**. Camera capabilities and available frame rates depend on the exact sensor and system.

## Documentation

- [Install Moon Cheese and test a public prerelease](docs/INSTALLATION.md)
- [Release history](CHANGELOG.md)
- [Publishing and verifying releases](docs/RELEASING.md)
- [Software updates and repair](docs/UPDATES_PLAN.md)
- [v1.0 readiness and later roadmap](docs/PROJECT_ROADMAP.md)
- [Security and vulnerability reports](SECURITY.md)

## Creator and project

Created by **Dr Ravenholm**, the person behind [Transparent-Aluminium.net](https://transparent-aluminium.net/).

- [Project repository](https://github.com/DrRavenholm/Moon-Cheese-UAP-Detector)
- [Creator website](https://transparent-aluminium.net/)
- [Blog](https://transparent-aluminium.net/blog/)
- [YouTube](https://www.youtube.com/@Dr_Ravenholm) · [Twitch](https://www.twitch.tv/dr_ravenholm) · [Discord](https://discord.gg/yTj2ucM)

## Licence and source

Moon Cheese UAP Detector is distributed under the **GNU General Public License v3.0**. See [`LICENSE`](LICENSE) and the attribution notices accompanying the application.

The official versioned `.tar.gz` release asset contains the *complete installer and application distribution*; GitHub's automatically generated **Source code** downloads are not substitutes for that installation archive. The complete corresponding application source must be available for **every public distribution, including prereleases**, and matched to the release tag.
