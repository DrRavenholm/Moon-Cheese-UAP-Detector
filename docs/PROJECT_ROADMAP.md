# Moon Cheese UAP Detector — Project Roadmap

**Updated for v1.0.1.7 · 19 November 2026**

This roadmap distinguishes working features from features under development or proposed. It is not a troubleshooting diary, release validation report or promise of completion dates. For individual shipped changes, see [CHANGELOG](../CHANGELOG.md) and [VERSION_HISTORY](../VERSION_HISTORY.md).

## Implemented in the current release

- Raspberry Pi camera-based monitoring and automatic event recording with configurable pre-roll, event duration, schedules, manual camera profiles and saved MP4s.
- Independently selectable General Motion, Moving Sky Lights, MOG2 Adaptive Background, and experimental Transient & Streak detectors. Detection sensitivity presets, reset controls and editable detection zones including Trace Horizon.
- Detector diagnostics, including gain/exposure readings where supplied by the camera, a live status panel and a bounded seven-day minute-summary history with CSV download.
- Configurable 320×240 or appropriately aspect-matched 640×360 / 640×480 detector analysis. Performance and sensitivity at high resolution still need actual Pi benchmarking.
- Photography, long-exposure progress, full-resolution image download, browser investigation tools and gain/ISO-equivalent controls.
- Scheduled Video and Time-lapse Studio, including estimated capture completion, image source archives, retention and review.
- Offline-first Sky Maps: linked sky/Earth views, local calculations from downloaded catalogues, satellite orbital downloads, configurable layers and observation-time reconstruction. Optional administrator-only offline ASTAP Camera Calibration from saved/new photographs, a visual reference-star cross-check where genuinely available, and approximate field-of-view display from saved solutions. Real solving accuracy still needs Pi validation.
- Notifications, storage protections, backup/restore, user accounts, opt-in public sharing, in-app Help, and local/optional remote network services.
- Password-protected software updates, same-version repair and administrator-controlled Moon Cheese service restoration.

## Active priorities: reliability and quality

- Test and tune real night-sky detection against known samples of stars, satellites, aircraft, birds, meteors, moving clouds and camera noise. Measure false positives and missed events, not merely the number of clips.
- Confirm camera metadata accuracy and compare 320×240 against 640×360 or 640×480 analysis on the reference Raspberry Pi 4. Keep a CPU-safe default.
- Review recorded diagnostic reports from unattended night sessions. Improve rejection reasons and per-algorithm event attribution as real test data becomes available.
- Improve zone-editor ergonomics, camera profiles, automatic day/night switching and night-image presentation without compromising raw recordings.
- Validate Sky Maps object positions, satellite age/staleness warnings and historical map behaviour against external ephemerides and reference observations.

## Upcoming — separately scoped work

- Extend optional plate solutions into validated wide-angle lens-distortion and optical-centre calibration so predicted object tracks can be accurately compared with event footage (the current solution measures mainly the centre and approximate orientation).
- Evidence-based suggestion labels such as *Likely satellite*, with timestamp, position and uncertainty. A match will **never automatically delete** an observation.
- Optional user-keyed, internet-dependent aircraft tracking and event-time archive. No mandatory ADS-B antennas or receivers; this will not compromise offline core detection.
- A separate full-screen **16:9 Observation Studio** page for use with OBS, with optional celestial overlays. A continuous camera stream must reuse the existing camera pipeline rather than open a competing camera process.
- Optional dew-heater controls after the actual PoE HAT, switching circuit and safe GPIO pins have been verified. No heater circuit is controlled by Moon Cheese v1.0.1.7.

## Longer-term / v2.0 direction

- Optional coordination and collaboration across multiple Moon Cheese installations, with explicit sharing permissions and preservation of local copies.
- Larger research and investigation workflows, including cross-location comparison, reproducible astronomical data snapshots and enhanced event correlation.
- Possible alternate storage and NAS workflows with explicit migrations and data-protection design; not available by default in v1.0.1.7.

## Architectural principles

1. **The detector must keep working offline.** Astronomical maps and future aircraft services must not be dependencies of the camera detection loop.
2. **Preserve original evidence.** Processing, masking, identifications and overlays must not secretly alter original recordings.
3. **Control resource usage on Raspberry Pi.** New algorithms require performance measurements and opt-in defaults.
4. **Protect existing installations.** Updates preserve accounts, settings, credentials, media, service state and cached sky data.
5. **Match the public release source to the binary/install archive.** Each version includes matching source and documentation in one versioned `.tar.gz`, with an external checksum.
6. **Report uncertainty accurately.** Sky positions, aircraft and satellite interpretations are predictions, not automatic confirmation of an object's identity.
