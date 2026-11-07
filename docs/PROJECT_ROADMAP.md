# Moon Cheese — outstanding work before v1.0

**Status at authorised v0.9.9.4.13.** This document records agreed development scope, not changes already delivered.

## Established baseline

- Tested Raspberry Pi 4 application with Flask dashboard, camera monitoring, motion/light events, still photography, scheduled video and time-lapse, investigation and PNG export, storage, notifications and user permissions.
- NPM reverse proxy, Let's Encrypt SSL and Cloudflare DNS/DDNS verified on test hardware.
- Cloudflare Tunnel connectivity, public HTTPS, hostname switching, disable and removal confirmed on test hardware after manual installation of `cloudflared`. A later installer/download fix and automatic retired-tunnel cleanup were packaged in v0.9.9.4.13, but their specific new paths still need live hardware tests.
- IP switching and independent rollback have been tested, with some user-interface improvements included in development builds.
- Help guide regrouped in v0.9.9.4.13.

## Outstanding v1.0 work

1. Correct the Wi-Fi radio dropdown resetting an unsaved selection during background status polling. The pending selection must remain until Apply; the status label must separately reflect real hardware state.
2. Correct fullscreen video investigation for detection recordings, scheduled videos and time-lapses; retain video, controls, comparison, zoom, enhancement and PNG saving in desktop/mobile views.
3. Improve the installer: final URL and credentials summary **after all steps**, Pi 4/5 capability detection while preserving Pi 5 experimental camera frame-rate options, experimental Raspberry Pi Zero 2 W / OS Lite mode without optional Docker/NPM by default, and carefully assessed compatibility for other hardware. Do not claim untested devices work.
4. Add official Moon Cheese favicon, Apple Home Screen icon and web-app manifest; test iPhone standalone Home Screen display.
5. Add Information -> About page with creator biography, grouped social/music/website/community/donation links; use approved copy before publication. GitHub link is `https://github.com/DrRavenholm/Moon-Cheese-UAP-Detector`.
6. Implement public GitHub release infrastructure, single-command bootstrap, System Health update checking/updating/same-version repair, and administrator notifications at existing observation-summary preferences time.
7. Implement/verify initial setup wizard if still required by the agreed release acceptance list.
8. Fix/reconcile the 45 historical non-browser test failures recorded at v0.9.9.4.13, and restore the browser suite. Not every failure proves a bug; distinguish stale fixtures from actual regressions. Test fresh install, upgrade and repair on real hardware.
9. Review licence compatibility, third-party notices, shipped defaults, source for secrets and release authenticity before a stable GPLv3 release.

## Explicitly deferred to v2.0

- Multi-device sharing and coordination.
- Selecting among mounted storage drives and NAS/network storage.

## Development rules

- No numbered release, feature or code changes without explicit administrator/developer authorisation.
- Every approved version is a complete fresh-install, upgrade and repair archive, not a partial patch.
- Preserve all existing working detector, network, UI and permission behaviour unless specifically authorised to alter it.
- Avoid new user-facing checkbox mazes. Signed-in administrators enter desired values; the backend handles recovery and prevents damage to unrelated services.
- Keep internal technical diagnostics behind useful readable error messages in the relevant page section.
