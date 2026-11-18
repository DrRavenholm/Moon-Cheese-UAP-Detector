# Moon Cheese UAP Detector — Release History

## v1.0.1.3 — Sky Maps Accuracy and Usability Corrections
**Date:** 18 November 2026

- Corrected the object-search HTTP 500 caused by treating three-field deep-sky records as four-field star records. Search now returns a controlled JSON error if another server-side failure occurs.
- Rebuilt the star catalogue selection to choose the brightest stars from the **complete** downloaded catalogue instead of truncating the first 6,500 rows; fixed highlighted deep-sky object lookup.
- Introduced a star-magnitude slider (default 4.5), split constellation lines and names into independent layers, suppressed overlapping constellation labels and defaulted deep-sky symbols off for better readability.
- Separated local-sky horizon filtering from satellite positions on the world map. The Earth map now shows a representative sample from the full catalogue; a searched satellite is included regardless of its local visibility. The map explains sampling rather than claiming to show all satellites.
- Added optional whole-Earth day/night shading and civil, nautical and astronomical twilight bands, calculated from local JPL ephemeris results for the selected time; no extra online service or data is needed.
- Added distinct LIVE, SELECTED TIME and PLAYBACK indicators. Reset to Now follows the current clock; manual dates and event links remain fixed; playback and searches ignore obsolete in-flight position responses.
- Improved map API response/error handling and Help, retaining the Raspberry Pi-confirmed working Photography countdown, event-time links, detector, detection zones, downloads and service recovery from v1.0.1.2.
- **Validation note:** offline unit and browser tests are not a substitute for live Raspberry Pi Skyfield ephemeris validation or actual satellite-data acceptance; verify accuracy on the installed Pi.


## v1.0.1.2 — Sky Maps, Detection Zones and Recovery Corrections
**Released:** 17 November 2026

- Added a dedicated **Sky Maps** main menu with linked local all-sky and Earth maps, object search/highlighting, optional layers, exact date/time entry, +/-24-hour time slider, playback controls and Reset to Now.
- Added **Sky Maps → Data & Updates** with separate, collapsed-by-default sections for star names/catalogue, constellation lines/boundaries, Sun/Moon/planet ephemeris, Earth coastlines, active satellites and optional bright deep-sky objects. Download All retrieves missing datasets. Files are downloaded to persistent local storage **after installation**; no large astronomical datasets or third-party API keys ship in the package.
- Introduced a separate camera-independent download service, daily scheduled CelesTrak OMM/CSV orbital updates at the detector's configured local time, validation, caching, administrator-only download controls, provider cooldown and automatic-request halt after provider failures. Astronomical maps use only local files at runtime; predictions require appropriately dated orbital data and are not confirmed object identifications.
- Added **View sky at this event** on observation pages. New recordings store their latitude/longitude; older recordings without a location are explicitly marked as approximations using the current detector coordinates.
- Added an administrator Detection Zones editor over the last cached camera preview, with include/exclude rectangles and polygons, independent Save Zones, and masks applied to both motion and sky-light triggers. The default remains full-frame detection; saved photos and video are never cropped.
- Changed **Repair services** to an always-available, password-protected, explicitly acknowledged systemd restoration. It backs up matching or modified Moon Cheese-owned unit files, reasserts required Moon Cheese service states and restarts Moon Cheese's dashboard and detector; optional networking and unrelated applications are left untouched.
- Corrected Photography progress to retain visible preparation, exposure estimate, saving and monitoring restoration states, and to record stage-duration diagnostics. Five seconds of shutter exposure does not include camera switching or processing time.
- Added the Debian Skyfield astronomy calculation dependency on upgrade. Astronomical data and existing Pi recordings, credentials, network configuration and observation database are retained across normal upgrades.
- **Validation note:** automated isolated tests and installer/secure-extraction checks apply to the release package; real camera behaviour, initial network downloads, live Skyfield rendering and Raspberry Pi systemd service restarts still require device acceptance.



## v1.0.1.1 — 14 November 2026 (maintenance release)

- Fixed theme flash, completed themed panel colours, and introduced a compact selector for all visitors.
- Added a protected and non-disruptive Repair services action to System Health.
- Renamed Live Camera to Photography in navigation and added a manual still-exposure countdown.
- Updated Help, README and installation documentation without changing detection, networking or recording logic.

## v1.0.1 — 14 November 2026 (maintenance release)

- Corrected the administrator Delivery History page crash; retained filtering and pagination.
- Improved SMTP error explanations for authentication, TLS, connection and provider refusals, without exposing secrets.
- Added four browser-local visitor themes: default Blue, Red, Green and Cheese Yellow.
- Simplified Cloudflare Tunnel token setup guidance and documented exact permission groups, resource scopes and Error 1033 troubleshooting.
- Removed the briefly appearing software-update reload link and improved release-status consistency.
- Published administrator credential retrieval instructions prominently in the README and installer output.
- Corrected outdated Time-lapse, email/Web Push, release-status and installation documentation.
- Added a non-destructive Moon Cheese-owned systemd service inspection and manual repair helper.
- Retained existing detector, camera, recordings, networking and user-data behaviour.

# Moon Cheese UAP Detector — Release History

This page summarises the main development milestones. The application's bundled `VERSION_HISTORY.md` retains the **full, detailed version-by-version history**; earlier entries must not be replaced by this summary.

## v1.0.0 — 7 November 2026 (public stable release)

- First public stable-release package, built directly from the Raspberry Pi-tested v0.9.9.5.3 software.
- Public anonymous GitHub one-line installer now targets the latest stable release when published; the exact prerelease test path was previously proven on a clean Pi.
- Retains password-protected software Update/Repair, full-resolution photos, detector, Scheduled Video, Time-lapse Studio, About page and comprehensive Help/Version History.
- Matching full corresponding GPLv3 source and third-party notices prepared for a tag on the updated Code branch.
- No detector, network, camera or user-data migration changes; correct-password v1.0.0 stable-channel repair subsequently passed on a Raspberry Pi.

## v0.9.9.5.3 — 7 November 2026 (development prerelease)

- Added verification of the signed-in administrator's current password before **Update now** and **Repair current version**; **Check for updates** remains password-free.
- Redesigned Information → About Moon Cheese using the official artwork, first-person creator biography, and grouped, responsive website/social/music/support links with local icons.
- Corrected Help descriptions of the already-operational update system.
- Preserved the latest-open / older-collapsed in-app Version History display and all historical entries.
- Kept the installation archive clean of development tests, reports, upload instructions and unused original artwork.
- GitHub upgrade to v0.9.9.5.3 and the new About page were confirmed on a physical Raspberry Pi. Incorrect-password rejection was user-confirmed; correct-password Repair awaits a discoverable stable release.

## v0.9.9.5.2 — 7 November 2026 (development prerelease)

- Added private GitHub prerelease testing support with separately stored, restricted credentials.
- Improved privileged archive-extraction safety and permissions.
- **Confirmed on Raspberry Pi:** real private GitHub upgrade from v0.9.9.5.1 to v0.9.9.5.2, Check for updates, and Repair current version.

## v0.9.9.5.1 — November 2026 (development prerelease)

- Kept Software updates and System power as separately visible System Health panels.
- Reduced the installation archive by excluding developer-only files and unused oversized artwork.
- Retained internal file checksums.

## v0.9.9.5 — November 2026 (development prerelease)

- Fixed Wi-Fi selection changes being reset by automatic status polling.
- Corrected fullscreen investigation for detection videos, scheduled videos and time-lapses.
- Added official Moon Cheese icon assets, Home Screen/web-app support and the About page.
- Introduced GitHub stable-release checking and controlled update/repair infrastructure.
- Expanded installer hardware-capability checks; non-Pi-4 hardware remains experimental pending testing.

## v0.9.9.4.13 — 31 October 2026 (development prerelease)

- Improved Cloudflare connector package installation, handling of HTTP 403 retrieval failures, and managed Tunnel cleanup.
- Improved Cloudflare Tunnel errors and Help navigation.

## Earlier development

Earlier releases established camera monitoring, video/photograph capture, Scheduled Video, Time-lapse Studio, observation investigations, Storage Management, administrator accounts, notifications, NPM/Cloudflare integration and safe networking controls. See `VERSION_HISTORY.md` inside the corresponding full installation packages for the complete original chronology.

**Reminder:** A development prerelease is not the first stable v1.0 release.
