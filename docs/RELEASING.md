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

## One canonical release source

For each authorised version, build **one versioned complete `.tar.gz`** from one source tree. The archive contains both the install/runtime files and **every GitHub Code source/documentation file**. Its internal `SHA256SUMS` lists all files except itself. Publish one separate external `SHA256SUMS` for the compressed archive. Do not generate a different GitHub source ZIP: there must be no separate source set to drift out of sync.

To publish, extract **that exact release archive** on the PC. In the GitHub **Code** tab, upload the *contents* of the extracted version directory, preserving relative paths, in batches of at most 100 files; `uap/` can be one batch and the other top-level files/folders another. Commit the complete source **before** creating the version tag, and verify that the tag matches that commit. Then upload **only** the versioned `.tar.gz` and the external `SHA256SUMS` to GitHub Releases. Never upload the `.tar.gz` into the Code tab, the internal checksum as an additional Release asset, or unrelated development reports, test folders, `UPLOAD_INSTRUCTIONS.txt`, credentials or local deployment data.

## GitHub Release format

For test release `v0.9.9.5.3`:

- Tag: `v0.9.9.5.3` (pointing to the **corresponding source commit**, not merely an old starter commit).
- Release checkbox: **Set as a pre-release**.
- Uploaded Assets: `moon-cheese-uap-detector-v0.9.9.5.3.tar.gz` and `SHA256SUMS` only.

For **this** stable `v1.0.0`:

- Tag: `v1.0.0` pointing to the approved corresponding source commit.
- Publish as **stable** when the matching code and checksum assets are ready so anonymous normal-channel installation and Repair can be tested; do not publicly announce final acceptance before those real tests pass.
- Uploaded Assets: `moon-cheese-uap-detector-v1.0.0.tar.gz` and matching `SHA256SUMS` only.

The versioned archive is the **complete installation package**, not GitHub's automatically generated Source code archive. The actual distribution package includes an internal `SHA256SUMS` and all necessary install/runtime files. Keep developer test reports outside public release assets.

## Release acceptance steps

1. Confirm the version is authorised and the application archive was produced from the corresponding approved source.
2. Verify the external `SHA256SUMS` and the internal package checksums, archive safety, installation scripts and release notes.
3. Verify the repo's tag points to the correct complete source commit, under GPLv3 with third-party attributions and no secrets.
4. The public prerelease v0.9.9.5.3 anonymous installer has already passed. For v1.0.0, create its tag from the updated corresponding source and publish a **stable** release so the actual `latest` command can be tested.
5. Test v1.0.0 on a clean SD card with the **normal stable** command:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash
   ```

6. Verify dashboard, camera, login, recording, password-protected update/repair, preservation of data and installer summary as appropriate to fresh/upgrade tests.
7. Also test **Repair current version** on v1.0.0 with a deliberately incorrect password (must be refused) and the signed-in administrator's correct password (must complete). Confirm existing user data survives upgrade/repair. The same stable installation command is:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/DrRavenholm/Moon-Cheese-UAP-Detector/main/moon-cheese-install.sh | sudo bash
   ```

## Integrity and security

The bootstrap validates GitHub's SHA-256 digest and checks archive structure before delegating to `install.sh`. The paired external checksum file and internal package checksums remain required release artefacts. These checks protect integrity but are not a substitute for publisher identity verification. Complete corresponding GPLv3 source and third-party notices must be present under the tag. This static review is not an independent penetration test; evaluate production deployment security before wide distribution.
