# Moon Cheese installation and upgrades

## Status

**The public GitHub installer is not live yet.** The repository currently has no approved public stable release assets. Keep using the complete authorised versioned distribution and its documented `install.sh` for controlled testing.

## Planned one-command installation

When the first approved stable release is published in a public repository, the intended command will be:

```bash
curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash
```

Do not use that command until the project announces it is ready. Running a downloaded script as root should only be done after trusting the repository and reviewing the installer.

The `moon-cheese-install.sh` bootstrap will:

1. Query the latest approved stable GitHub Release.
2. Download the exact versioned **full installation package** release asset.
3. Check GitHub's SHA-256 release-asset digest.
4. Validate archive paths and locate the packaged `install.sh`.
5. Execute the packaged `install.sh` with administrator privileges.

The bootstrap **does not replace** the main installer. The main installer is responsible for OS dependencies, installation versus upgrade/repair, backup, services, credentials and the installation summary.

The SHA-256 check verifies downloaded content against GitHub's reported digest; publisher-signature verification is a separate security enhancement planned for production.

## Supported hardware

The latest development package currently enforces Raspberry Pi 4 / 64-bit Raspberry Pi OS. Support for other devices is planned, but should not be assumed until its installer and runtime checks have been validated.

## Private repositories

A private GitHub repository cannot provide public anonymous downloads through this installer. Developer test releases require authenticated access and will be handled separately. Do not put a GitHub personal access token inside the app or bootstrap script.
