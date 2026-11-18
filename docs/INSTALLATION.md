# Install Moon Cheese UAP Detector

This guide describes the public stable installer, administrator credentials, initial setup and optional prerelease testing. The latest v1.0.1.5 release uses the existing versioned archive/checksum installation process.

## Before installation

- For **prerelease tests**, use a separate microSD card or test Raspberry Pi to protect your working installation.
- Start with a supported, up-to-date **64-bit Raspberry Pi OS** installation, network access, and a compatible camera.
- Raspberry Pi 4 is the tested reference hardware. Pi 5, Pi Zero 2 W / OS Lite and other compatible boards have **experimental or unverified** real-hardware support.
- Internet access is required to fetch the GitHub bootstrap, the release and operating-system dependencies.
- Review the [bootstrap source](../moon-cheese-install.sh) if you wish before executing any script with `sudo`.

## Stable installation — latest public release

On the Raspberry Pi, run:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash
```

Immediately after installation, use the administrator login shown in the terminal, or retrieve the **original** generated credentials with:

```bash
sudo uapctl credentials
```

If the password was changed later, sign in with the changed password; this command only reports the originally generated credentials.

### Optional version-pinned prerelease tests

For maintainers testing an **existing published** public prerelease tag, use the same installer with `--prerelease TAG`. For example, the historical v0.9.9.5.3 anonymous fresh-install test used:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash -s -- --prerelease v0.9.9.5.3
```

Normal installations should use the stable command above. Draft releases cannot be installed publicly, and the stable selector ignores prereleases.

## What the bootstrap does

1. Fetches public GitHub Release metadata (latest stable by default, or the specified prerelease tag).
2. Selects the exact versioned `moon-cheese-uap-detector-v….tar.gz` **uploaded release asset**, not GitHub's automatically generated source archive.
3. Verifies the compressed archive against GitHub's reported SHA-256 asset digest.
4. Rejects unsafe archive paths and archive entries before extraction.
5. Starts the full application `install.sh` bundled in the verified archive. That script handles dependencies, installation or upgrade, backups, services, and the final access/login summary.

The official release also contains an external `SHA256SUMS` asset for independent archive checks and an internal `SHA256SUMS` for its packaged files. The bootstrap currently checks GitHub's API digest, while the packaged installer validates its internal files. A checksum alone is not independent publisher-signature verification.

## Retrieve the first administrator password

If you missed the credentials at the end of installation or closed the terminal, use PuTTY or a local terminal on the Pi:

```bash
sudo uapctl credentials
```

This shows the **original generated** username and password, if still retained. If the password has since been changed, use the new password. Keep this information private.

## After installation

Check the dashboard using the local address printed **after installation completes**. Verify the login details, live camera, capture, recordings and access to **Administration → System Health**. During a prerelease test, verify that the installed version matches the selected tag.

For an existing installation, the dashboard's **Software updates** panel supports Check for updates, administrator-password-protected Update now, and Repair current version, subject to the configured release channel. It does not install updates automatically.

## Important release-channel distinction

- **Public prereleases** can be downloaded anonymously by the one-line command with `--prerelease TAG` after the repository is public.
- The normal **stable** command ignores prereleases.
- A pre-existing device configured for **private GitHub testing** may retain private-channel settings. These are separate from the public bootstrap; switch channels deliberately rather than assuming publishing the repository changes the device's saved configuration.
- **Draft releases** are not public downloads.
- Do not put GitHub tokens or Cloudflare credentials in any installer script, GitHub Issue, or public file.

For the maintainer's source and release preparation requirements, see [Publishing releases](RELEASING.md).

## Cloudflare Tunnel permissions and troubleshooting

Tunnel access is optional. On the dashboard, expand System Administration → Network and remote access → Cloudflare Tunnel → Cloudflare setup guide. It explains where to obtain your Account ID and Zone ID, and to create a custom API token limited to your own Account and DNS Zone. Configure Account → Cloudflare Tunnel → Edit, Zone → DNS → Edit and Zone → Zone → Read. Enter these into Moon Cheese alongside your chosen subdomain; never share an API token or use a Global API Key. Cloudflare Error 1033 usually means a disconnected `cloudflared` connector or a DNS target pointing to the wrong tunnel; consult the same guide before changing any DNS resources.

## Sky Maps first-run data (v1.0.1.2)

The release archive deliberately contains no large star catalogues, JPL ephemerides or orbital datasets. After logging in as an administrator, open **Sky Maps → Data & Updates**, expand **All astronomical data**, and choose **Download all missing data** using an internet-connected Pi. Status and source URLs appear in each individual expandable section. If no data is installed, Moon Cheese camera detection and recording still work.

The star/constellation, Sun/Moon/planet, world map, and optional deep-sky files are cached under `/var/lib/uap-detector/sky-map-data`. Satellite data may be refreshed daily at an administrator-selected time using CelesTrak. The new independent `uap-sky-data.service`, `.path`, and `.timer` run the download manager, not the camera. The installer uses the Raspberry Pi OS/Debian `python3-skyfield` and `python3-sgp4` packages for local calculations; an existing system that lacks these packages requires an internet-connected package-install step before upgrade can proceed. Backups and upgrades preserve the local astronomical cache. Aircraft providers and streaming are not installed.

## Service Repair and detection zones (v1.0.1.2)

**Repair services** is intentionally always clickable for administrators under System Health → Software updates. It requires the current administrator password and interruption acknowledgement before reinstalling backed-up Moon Cheese-owned units and reasserting required service status. It can interrupt a running camera job, and does not stop competing third-party processes. Detector Settings now has **Detection zones**, disabled until explicitly enabled and saved; video remains uncropped.

## First-run checks for v1.0.1.5

After updating, confirm the detector and recordings are functioning, and verify that saved camera profiles and detection zones remain intact. In Detector Settings, try changing the frame rate while an unused Custom profile has a long exposure; only the active manual profile (or Day and Night for automatic switching) should be validated. Check that the selected analysis resolution matches the video aspect ratio at high detail.

Under Detection Methods & Sensitivity, open Live Detection Diagnostics. The new history begins collecting minute summaries after the upgrade; it cannot reconstruct diagnostics that were not previously stored. Select a UTC date to review the chart and export a CSV. The standard camera preview can now be set to Standard, Balanced or Detailed quality independently of the original recordings. Photography and advanced Time-lapse offer ISO-equivalent shortcuts; no new calibrated ISO hardware control is claimed.

For a planned Time-lapse, change its start and duration and check the estimated capture completion time. Rendering and archiving still take additional time. Validate higher analysis resolutions on your own Pi before leaving them unattended; new experimental detection engines can increase false positives.
