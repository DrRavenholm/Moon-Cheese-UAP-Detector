# Publishing Moon Cheese on GitHub — maintainer guide

Repository: https://github.com/DrRavenholm/Moon-Cheese-UAP-Detector

## Where files go

- **Code tab:** source code, documentation, original `install.sh`, tests, GPLv3 `LICENSE`, and `moon-cheese-install.sh`.
- **Releases:** versioned complete `.tar.gz` archive and its SHA-256 file, together with release notes.
- **Never commit:** credentials, Cloudflare/GitHub tokens, recordings, local databases, full production settings or private signing keys.

GitHub also automatically produces `Source code (zip)` and `Source code (tar.gz)` downloads. These do **not** replace the complete, tested Moon Cheese installation archive.

## Preparing a release

1. Complete functional changes on an authorised development version; update version history.
2. Review source and archive for secrets and sensitive deployment details.
3. Ensure the corresponding source code is committed to the repository; comply with GPLv3 requirements.
4. Run tests and supported-hardware checks. For stable releases, all required checks must pass.
5. Create the full installer archive using the project's authorised build procedure, not a renamed old test file.
6. Use the filename pattern `moon-cheese-uap-detector-v1.0.0.tar.gz` (replace the version as appropriate).
7. Compute its checksum using `sha256sum moon-cheese-uap-detector-v1.0.0.tar.gz > moon-cheese-uap-detector-v1.0.0.tar.gz.sha256`.
8. Sign and verify the artefact with the project's release signing key once the signing process is configured.
9. Open the repository > **Releases** > **Draft a new release**.
10. Create a matching Git tag such as `v1.0.0` **for the source commit corresponding to the package**.
11. Attach the complete archive and checksum file in the **Assets** attachment area, add release notes and verify names.
12. Start as a draft, then publish as a stable release only after acceptance. Development builds should be prereleases, never labelled stable.

## Bootstrap filename agreement

The public bootstrap expects all stable releases to attach precisely:

`moon-cheese-uap-detector-<tag>.tar.gz`

Example tag `v1.0.0` gives `moon-cheese-uap-detector-v1.0.0.tar.gz`.

It refuses to install when the package is missing or GitHub does not report its SHA-256 digest. It does not accept the older `uap-detector-test-...` archive name as a stable release asset.

## Important pre-v1.0 limitations

- v0.9.9.4.13 is an authorised **test build**, not a production release.
- The current main installer is still Pi-4-specific, prints some information too early and has known pre-v1.0 issues.
- The System Health automatic updater/repair and production signing process have not yet been implemented.
- A private repository is not anonymously accessible to user installers.

Do not publish a stable release until these items are addressed.
