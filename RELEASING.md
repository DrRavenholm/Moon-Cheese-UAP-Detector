# Publishing Moon Cheese on GitHub — maintainer reference

Official repository: https://github.com/DrRavenholm/Moon-Cheese-UAP-Detector

## Public repository versus public release

A **public repository can contain published prereleases** while v1.0 is under test. These are anonymously downloadable if published (not drafts). GitHub's **latest stable** endpoint does not select prereleases; the bootstrap's `--prerelease TAG` option selects one by exact tag instead.

Changing a repository from private to public exposes the existing Git history, branches, tags and release assets. **Audit them before changing visibility**, particularly for sensitive local settings or historical developer artefacts. Inspect historical files as well as the current branch; do not unintentionally republish removed development-only material.

## Repository Code tab

Before **any public release**, including a prerelease, the repository should contain:

- Complete corresponding application source code for the version, including its real `install.sh`, under the applicable GPLv3 licence. A starter documentation ZIP is not a substitute.
- [`LICENSE`](../LICENSE), the appropriate third-party notices and current README and documentation.
- `moon-cheese-install.sh` at the repository root for the public one-line installer.

Do **not** commit production credentials, private tokens, home IPs, SQLite user databases, personal media, development test reports, oversized unused artwork or `UPLOAD_INSTRUCTIONS.txt`.

## GitHub Release format

For test release `v0.9.9.5.3`:

- Tag: `v0.9.9.5.3` (pointing to the **corresponding source commit**, not merely an old starter commit).
- Release checkbox: **Set as a pre-release**.
- Uploaded Assets: `moon-cheese-uap-detector-v0.9.9.5.3.tar.gz` and `SHA256SUMS` only.

For future stable `v1.0.0`:

- Tag: `v1.0.0` pointing to the approved corresponding source commit.
- Publish as **stable** only after acceptance, not as a draft or prerelease.
- Uploaded Assets: `moon-cheese-uap-detector-v1.0.0.tar.gz` and matching `SHA256SUMS` only.

The versioned archive is the **complete installation package**, not GitHub's automatically generated Source code archive. The actual distribution package includes an internal `SHA256SUMS` and all necessary install/runtime files. Keep developer test reports outside public release assets.

## Release acceptance steps

1. Confirm the version is authorised and the application archive was produced from the corresponding approved source.
2. Verify the external `SHA256SUMS` and the internal package checksums, archive safety, installation scripts and release notes.
3. Verify the repo's tag points to the correct complete source commit, under GPLv3 with third-party attributions and no secrets.
4. Publish a **public prerelease** for the final anonymous one-line installation tests, leaving stable selection unchanged.
5. Test on a clean SD card using:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash -s -- --prerelease v0.9.9.5.3
   ```

6. Verify dashboard, camera, login, recording, password-protected update/repair, preservation of data and installer summary as appropriate to fresh/upgrade tests.
7. Once approved, release `v1.0.0` stable and verify on a clean system using:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash
   ```

## Integrity and security

The bootstrap validates GitHub's SHA-256 digest and checks archive structure before delegating to `install.sh`. The paired external checksum file and internal package checksums remain required release artefacts. These checks protect integrity but are not a substitute for publisher identity verification. Complete source publication, third-party licences and independent security review are v1.0 requirements.
