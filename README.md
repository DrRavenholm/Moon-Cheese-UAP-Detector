# Moon Cheese UAP Detector

**Open-source sky monitoring, automatic detection, photography and investigation for Raspberry Pi.**

Moon Cheese watches a connected camera for movement and moving points of light, saves event recordings with pre-event footage, and provides tools to review the evidence. You can also take full-resolution photographs, schedule videos and time-lapses, explore offline-first Sky Maps, and choose which observations to share publicly.

**An event is an observation, not proof of a UAP.** Moon Cheese does not automatically identify an aircraft, satellite or unexplained object; astronomical maps provide predictions to help investigations.

## Quick install

On a supported Raspberry Pi running **64-bit Raspberry Pi OS**, with a compatible camera and internet access for installation, open a terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash
```

**To retrieve your original generated administrator username and password**, including after closing the installation terminal:

```bash
sudo uapctl credentials
```

The command displays the **original** password only. If you changed that password after installation, continue using your new password. Do not share administrator credentials. The installer displays how to reach the dashboard when setup completes.

The one-line command installs the **latest published stable GitHub Release**, not necessarily the newest source commit. It does not require a GitHub account, API token, paid subscription or separate download of the program. Read the [installation guide](docs/INSTALLATION.md) for hardware requirements, upgrade details and optional version-pinned prerelease testing.

## What Moon Cheese does

| Feature | Description |
| --- | --- |
| **Automatic sky detection** | General Motion, tracked Moving Sky Lights, optional Adaptive Background (MOG2), and experimental Transient & Streak detection. Choose the methods independently and configure sensitivity. |
| **Event recordings** | Records original MP4 footage with configurable pre- and post-event intervals, duration limits, notifications and storage protections. |
| **Detection Zones** | Draw red exclusions for buildings and trees, or optional green monitoring areas. Trace Horizon helps exclude everything below the skyline. Original recordings remain full frame. |
| **Photography** | Full-resolution still photographs, manual exposure and gain controls, progress countdown, image review and original-file downloads. |
| **Scheduled capture** | Planned video recordings and full-resolution Time-lapse Studio, with advanced photography settings and estimated capture completion time. |
| **Sky Maps** | Linked local sky and Earth satellite maps, searching, layers, time controls, object predictions and View sky at this event. |
| **Investigations** | Event search, notes, status labels, frame inspection, export, galleries and calendar. Preserve originals for comparison. |
| **Remote access and sharing** | Optional Cloudflare Tunnel, DNS and reverse proxy features; opt-in public observation page with per-item sharing. |
| **Administration** | Multi-user accounts, email/Web Push, backup/restore, system health, update/repair, and detector diagnostics with seven-day reports. |

Moon Cheese is **offline-first for monitoring and recording**. Optional network services need internet access. Sky Maps uses local astronomical data after its initial download; satellite predictions become less dependable as cached orbital elements age.

### Detection quality and night photography

The detector analyses short video frames; a bright ten-second time-lapse exposure is **not** equivalent to a frame captured at 5, 15 or 24 frames per second. Higher exposure, gain, sensitivity or analysis resolution may improve faint-object detection but can also create motion blur, sensor noise and false alarms. Moon Cheese supports adjustable analysis resolution and exposure/gain profiles; test changes on your actual camera. A selectable ISO-*equivalent* shortcut uses analogue gain (approximately ISO 100 at 1× digital gain), while measured ISO-equivalent readings depend on both analogue and digital gain. This is not a separately calibrated DSLR ISO control.

## Getting started after installation

1. Open the local dashboard address printed by the installer and sign in with your administrator credentials.
2. Check **Administration → Detector Settings** for the correct camera mode, orientation, sensitivity and recording schedule. Keep the original settings until you understand how the camera behaves.
3. If you want to ignore a treeline or road, use **Detection Zones** and save the red exclusion separately from detector settings.
4. Open **Sky Maps → Data & Updates** and select **Download all missing data** when connected to the internet. Astronomical catalogues are **not** bundled in every release.
5. Use **Observations** to review captured events, their original MP4s and the sky at the recorded time. Public sharing is optional and off by default.

### Supported hardware

**Raspberry Pi 4 running 64-bit Raspberry Pi OS with a compatible camera** is the primary reference system. Supported frame rates and manual camera controls depend on the sensor and system. Pi 5, Pi Zero 2 W, some Raspberry Pi OS Lite configurations and other Debian-based boards have experimental or incompletely verified support; they should not be assumed to work identically without testing. Internet access is needed for initial installation and optional sky-data updates, but is not needed for ordinary local detection.

## Updates, repairs and troubleshooting

For an existing installation, use **Administration → System Health → Software updates** to check for new stable releases. Update and Repair current version require the signed-in administrator's **current** password. Normal releases preserve configuration, accounts, stored astronomical data, network state, databases and recordings; review backups before maintenance on an active installation.

**Repair services** is a separate administrator-authorised service restoration operation. It can interrupt the active camera and restart Moon Cheese-owned services; it never intentionally stops unrelated third-party applications. Do not invoke it in the middle of an important scheduled recording.

If nothing is recorded, check the detector's status, event-storm protection, schedule, camera exposure/gain, detection zones and **Live Detection Diagnostics**. The latter includes recorded minute-by-minute summaries and CSV exports for the previous seven days after upgrading to v1.0.1.5. Adjust high-sensitivity detection modes experimentally; more events do not necessarily mean more genuine objects.

Optional Cloudflare Tunnel setup is documented in the application's **Cloudflare setup guide**, including the scoped Account/Zone token permissions. Never publish Cloudflare credentials or tokens.

## Roadmap and documentation

- [Installation and detailed setup](docs/INSTALLATION.md)
- [Current feature roadmap](docs/PROJECT_ROADMAP.md)
- [Changes in each release](CHANGELOG.md) and [full Version History](VERSION_HISTORY.md)
- [Software updates and repair](docs/UPDATES_PLAN.md)
- [Publishing matching GitHub source and release assets](docs/RELEASING.md)
- [Security policy](SECURITY.md)
- [Third-party attribution](THIRD_PARTY_NOTICES.md)

### Development direction

Current development focuses on making the detector reliable against real night-sky footage, validating higher-resolution analysis on Raspberry Pi hardware, improving camera calibration and object interpretation, and refining the user interfaces. **Future features are not part of the current release:** optional internet-based aircraft tracking, a dedicated 16:9 OBS-ready presentation interface, and multi-detector collaboration. See the [roadmap](docs/PROJECT_ROADMAP.md) for implementation status.

## Creator and community

Created by **Dr Ravenholm**, behind [Transparent-Aluminium.net](https://transparent-aluminium.net/).

[Project on GitHub](https://github.com/DrRavenholm/Moon-Cheese-UAP-Detector) · [Website](https://transparent-aluminium.net/) · [Blog](https://transparent-aluminium.net/blog/) · [YouTube](https://www.youtube.com/@Dr_Ravenholm) · [Twitch](https://www.twitch.tv/dr_ravenholm) · [Discord](https://discord.gg/yTj2ucM)

## Licence and source integrity

Moon Cheese UAP Detector is distributed under the **GNU General Public License v3.0**; see [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Each official versioned `.tar.gz` asset contains **the complete installable release and matching public GitHub source**: the installer, the `uap/` source, service units, documentation and internal checksums. The maintainer publishes matching source commits first and tags that commit when creating the stable GitHub Release. The release's **external `SHA256SUMS`** verifies the uploaded archive; it is not a publisher signature. GitHub's automatically generated source archives are separate from the official installer asset.
