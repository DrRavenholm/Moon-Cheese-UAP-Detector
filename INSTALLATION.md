# Install Moon Cheese UAP Detector

This page covers the intended **one-command public installation** and its prerelease testing variant. The latest authorised development version at the time of these instructions is **v0.9.9.5.3**; v1.0 is not yet released.

## Before installation

- Use a **separate microSD card or test Raspberry Pi** for prerelease installation, so an existing working installation is not at risk.
- Start with a supported, up-to-date **64-bit Raspberry Pi OS** installation, network access, and a compatible camera.
- Raspberry Pi 4 is the tested reference hardware. Pi 5, Pi Zero 2 W / OS Lite and other compatible boards have **experimental or unverified** real-hardware support.
- Internet access is required to fetch the GitHub bootstrap, the release and operating-system dependencies.
- Review the [bootstrap source](../moon-cheese-install.sh) if you wish before executing any script with `sudo`.

## Public prerelease test — anonymous, one command

Once this repository is public and the named release is **published** (not draft) and marked **Pre-release**, open a terminal/SSH session on the clean Pi and run:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash -s -- --prerelease v0.9.9.5.3
```

This is a true anonymous GitHub bootstrap and installation test. No GitHub account, token, manual ZIP download, or WinSCP transfer is needed. It uses the GitHub API endpoint for the **exact release tag** because the normal `latest` endpoint excludes prereleases.

If you later want to test a different published prerelease, change only the tag after `--prerelease` to its exact version.

## Public stable installation — v1.0 and later

Once an approved public stable release is published and the clean installation has been accepted, the permanent one-line command is:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash
```

This automatically selects GitHub's **latest stable** release. A repository containing only prereleases will not provide a stable release to this command.

## What the bootstrap does

1. Fetches public GitHub Release metadata (latest stable by default, or the specified prerelease tag).
2. Selects the exact versioned `moon-cheese-uap-detector-v….tar.gz` **uploaded release asset**, not GitHub's automatically generated source archive.
3. Verifies the compressed archive against GitHub's reported SHA-256 asset digest.
4. Rejects unsafe archive paths and archive entries before extraction.
5. Starts the full application `install.sh` bundled in the verified archive. That script handles dependencies, installation or upgrade, backups, services, and the final access/login summary.

The official release also contains an external `SHA256SUMS` asset for independent archive checks and an internal `SHA256SUMS` for its packaged files. The bootstrap currently checks GitHub's API digest, while the packaged installer validates its internal files. A checksum alone is not independent publisher-signature verification.

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
