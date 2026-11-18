# Moon Cheese UAP Detector

**An open-source, camera-based sky-monitoring, recording and investigation system for Raspberry Pi.**

Moon Cheese UAP Detector combines automatic camera monitoring with tools to capture, organise and examine unusual motion or lights in the sky. It is designed for enthusiasts and independent researchers who want to keep the original recordings available for closer investigation.

A detection is **not** identification, and Moon Cheese does not claim to prove that any recorded object or event is unexplained.

> **Current prepared release: v1.0.1.2 (major feature update).** Moon Cheese v1.0.0 was publicly released on 7 November 2026. v1.0.1.2 introduces downloadable offline-first Sky Maps, a full-screen-compatible but not yet OBS-specific two-map explorer, per-dataset management, event-time mapping, configurable detection zones and updated Service Repair and Photography progress. Initial catalogue downloads and full Pi hardware/service acceptance have **not** yet been verified on the target Raspberry Pi.

## Install Moon Cheese

### One-line installation — latest stable release

Install the latest published stable Moon Cheese release on a supported Raspberry Pi OS system with:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash
```

The bootstrap downloads the latest **stable** GitHub Release's complete Moon Cheese installation archive, checks the SHA-256 asset digest, validates the archive structure, then runs the archive's original `install.sh`. It is designed for clean installations as well as existing-installation upgrades; the main installer retains responsibility for backups and service setup.

**This command selects the latest stable release** and does not require a GitHub account or access token. The stable installation path has been tested on Raspberry Pi hardware; check the v1.0.1.2 release notes for its specific acceptance status.

### One-line installation — public prerelease testing

The previous anonymous GitHub fresh-install test **passed** using this exact public v0.9.9.5.3 prerelease command on a clean Raspberry Pi:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash -s -- --prerelease v0.9.9.5.3
```

This uses the **same bootstrap**, checksum checks and packaged installer as the stable command; the flag selects a specific public prerelease instead of GitHub's latest stable release. **No GitHub login, token, PC download or manual file transfer is required.**

Prereleases remain available for testing. They do not substitute for final acceptance of the stable v1.0.0 release.

### Find your administrator password after installation

If you closed PuTTY or the terminal before noting the initial credentials, open a terminal on the Raspberry Pi and run:

```bash
sudo uapctl credentials
```

**This is the command to retrieve the original generated administrator username and password.** If you subsequently changed the password, sign in with the new one instead. Keep these credentials private. The installer also prints this command clearly at completion.

### Cloudflare Tunnel setup

For optional public HTTPS access without port forwarding, open **Administration → System Administration → Network and remote access → Cloudflare Tunnel**, then expand **Cloudflare setup guide**. It explains exactly how to create your own restricted token, choose **Account → Cloudflare Tunnel → Edit**, **Zone → DNS → Edit** and **Zone → Zone → Read**, limit the token to your account/domain and locate the Account ID and Zone ID. Never share your API token or use a Global API Key. Cloudflare Error 1033 means the connector is not healthy; see the in-app guide for safe checks.

### Existing installation service repair

To reassert Moon Cheese's own required services after configuration conflicts or service failures, open **Administration → System Health → Software updates**. **Repair services is always available** to administrators, even if unit files match. Enter your current administrator password, explicitly acknowledge that monitoring will be interrupted, and press Repair services. The root-owned maintenance worker backs up and reinstalls official Moon Cheese-owned systemd unit definitions, reloads systemd, re-enables its required service/timer/path units, and restarts the Moon Cheese detector and dashboard. It does not stop or disable third-party applications, and it preserves the enabled/disabled state of optional Cloudflare/DDNS features. A successful service-file check **does not** prove that the camera is healthy or that another application is not occupying it.

From PuTTY, read-only inspection remains available:

```bash
sudo python3 /opt/uap-detector/uap/service_repair.py --check
```

A backed-up service-file-only restore **without restarting** is still available via `--apply`. The fully active operation is `sudo python3 /opt/uap-detector/uap/service_repair.py --full-reset`. Use the dashboard's password-protected action where possible.

### New Sky Maps menu and astronomical data

**Sky Maps → Explore Sky Maps** displays a linked local-sky chart and Earth satellite map. Search objects, choose local-sky and Earth layers, pick a date/time, play the timeline at selectable speeds and use **Reset to Now**. On a saved observation, select **View sky at this event** to open its recorded moment. These are predicted positions, not automatic identification of an observation.

**Sky Maps → Data & Updates** is administrator-only. The first time you install this version, open **All astronomical data** and choose **Download all missing data**. The Pi must have internet access for this initial download. Astronomical data is stored under `/var/lib/uap-detector/sky-map-data` and is **not** included in the release archive. Stars, constellation names and boundaries, JPL planet/Moon/Sun ephemeris, Earth outlines, optional deep-sky objects and satellites are downloaded individually; all except satellites need only occasional intentional updates. Satellites use keyless CelesTrak OMM/CSV orbital data and an administrator-configurable **daily local download time**. Provider errors suspend automatic satellite requests until a manual retry, subject to the cooldown. No external web maps or paid keys are needed. The detector continues operating if the internet, catalogues or prediction engine are unavailable. The world map currently downloads its compact outline as part of the first-run setup too.

**Detector Settings → Detection Zones** allows administrators to draw rectangles or polygons over the last saved camera preview. Include zones limit triggering to selected areas; exclusions suppress unwanted activity. Save Zones separately from ordinary camera settings. Masks affect triggering in both detector modes, **never crop video or photos**, and default to full-frame unless enabled.

Aircraft tracking and a dedicated 16:9 OBS studio are **not part of this release**.

The administrator **Photography** page (formerly Live Camera) captures full-resolution stills, including manual long exposures with persistent preparation, exposure, saving and restoration stages. The header colour icon opens Blue, Red, Green and Cheese Yellow choices for all visitors.

See [Installation and requirements](docs/INSTALLATION.md) for more information.

## What Moon Cheese does

- **Offline-first Sky Maps:** linked local celestial and Earth satellite maps, expandable data downloads, search, timeline, and observation-time viewing.
- **Detection Zones:** monitored/excluded camera preview areas, without cropping original recordings.
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

**Primary reference platform:** Raspberry Pi 4 running supported 64-bit Raspberry Pi OS, with compatible camera hardware. GitHub upgrades, the previous private repair, and an anonymous one-line prerelease fresh installation have been tested successfully on Raspberry Pi hardware.

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

The official versioned `.tar.gz` is both the **full installation package and the complete matching source snapshot**. It contains the public GitHub landing page, `docs/`, the bootstrap script, the full `uap/`, `systemd/` and `npm/` source, licence and third-party notices, plus the internal checksums. The main installer installs only the runtime components it needs; repository pages are included for source parity. The maintainer updates the GitHub Code page **from that same extracted archive**, in batches if needed, before creating a release tag. The tag must point to that exact source commit. GitHub's automatically generated source downloads are distinct from the versioned installation asset.
