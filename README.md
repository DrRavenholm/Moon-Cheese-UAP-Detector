# Moon Cheese UAP Detector

**Moon Cheese UAP Detector** is an independent, camera-based sky-monitoring and observation system for capturing, reviewing and organising unusual activity in the sky.

It combines camera monitoring with recording, still photography, scheduled video, time-lapses, a browser dashboard, observation management and notifications. Optional network features include local access, reverse-proxy configuration and Cloudflare Tunnel support.

**Development status:** Pre-v1.0. The public one-command installer and in-app GitHub update/repair system are being prepared. They are **not yet available as a tested public release**.

## Installation

The eventual public installation method will be a single command that downloads the official versioned archive, verifies it and runs the `install.sh` already included inside the full Moon Cheese distribution.

**Do not run the GitHub bootstrap yet.** It requires an approved, public, stable GitHub Release. See [Installation](docs/INSTALLATION.md).

## Supported hardware

The current tested release targets Raspberry Pi 4 running supported 64-bit Raspberry Pi OS. Raspberry Pi 5, Pi Zero 2 W and compatible alternative Linux devices are planned for capability-based installation checks, but are **not yet confirmed supported** by the current installer.

Camera functionality depends on compatible hardware and drivers. A recording of unusual motion or light is not, by itself, evidence of an unidentified object.

## Documentation

- [Installation and upgrades](docs/INSTALLATION.md)
- [Releasing a version](docs/RELEASING.md)
- [Release history](CHANGELOG.md)
- [Update-system design](docs/UPDATES_PLAN.md)
- [Pre-v1.0 roadmap](docs/PROJECT_ROADMAP.md)
- [Security](SECURITY.md)

## Creator

Created by [Dr Ravenholm](https://github.com/DrRavenholm). See [Transparent-Aluminium.net](https://transparent-aluminium.net/) for the creator's other projects.

## Licence

Released under the **GNU General Public License v3.0**. See the repository's existing [`LICENSE`](LICENSE) file. Copyright and attribution notices in third-party components remain governed by their respective licences.
