## v1.0.1.1 — Theme, Service Repair and Photography Countdown
**Date:** 14 November 2026

- Applied saved colours before browser style rendering to avoid default-blue flashes between pages.
- Added compact pop-out theme choices for Blue, Red, Green and Cheese Yellow, available to everyone.
- Updated remaining fixed blue panels across Camera Settings, Help, Public Observations, media and storage pages; maintained black image backgrounds and red danger controls.
- Added password-protected Repair services to System Health using the existing root-owned maintenance queue, with backups, service definition restores, no camera restarts and no changes to unrelated applications.
- Renamed the administrator Live Camera page to Photography without changing existing URLs or camera controls.
- Added an approximate remaining-seconds countdown for manual long exposures, starting only after the still-camera pipeline is ready, followed by a separate saving stage.
- Updated Help, README and GitHub release guidance; no migrations or changes to established recordings, networking, accounts or storage.

## v1.0.1 — Reliability and Visitor Theme Maintenance
**Date:** 14 November 2026

- Fixed the administrator Delivery History HTTP 500 error and preserved filter, page and failed-delivery retry behaviour.
- Improved SMTP failure explanations for connection, TLS, authentication, sender and recipient errors without exposing secrets.
- Added Blue, Red, Green and Cheese Yellow browser-local themes in the site header, available to public visitors.
- Added Cloudflare Tunnel API token instructions, including scoped permissions, ID locations and Error 1033 checks.
- Removed the short-lived update-status reload link and prevented cached release checks from falsely reporting a newer version.
- Added visible installation credential retrieval instructions and made the installer completion message clearer.
- Introduced a separate manual service-file check/restore helper with backups, no third-party service changes and no forced restarts.
- Corrected outdated Basic Time-lapse, email/Web Push and v1.0 publication documentation.
- Retained existing cameras, detection, networking, recordings, account data and settings; hardware acceptance of this maintenance release remains pending.

## v1.0.0 — First Public Stable Release
**Date:** 7 November 2026

- First official public stable release of Moon Cheese UAP Detector, built directly from the authorised v0.9.9.5.3 software package.
- Public one-line installation uses the existing GitHub bootstrap to select the latest stable version, download the complete release archive, verify GitHub's SHA-256 asset digest and run the established full installer. No GitHub login or personal access token is required for public releases.
- Complete source, installer, services, licence and third-party notices prepared for a matching public GitHub source tag. The release archive retains its internal `SHA256SUMS` and the separate compressed-archive checksum.
- Preserved administrator-password confirmation for Update and Repair and password-free Check for updates, with both maintenance panels independently visible.
- Preserved the approved About page, all 15 destination links, Help topics, newest-open/older-collapsed Version History and every preceding version entry.
- No changes to the established camera detector, recording, network worker, Cloudflare/NPM, media database, storage, user credentials or backup/rollback logic.
- **Release validation:** The user confirmed public anonymous prerelease fresh installation and a GitHub upgrade to v0.9.9.5.3; deliberately incorrect passwords were rejected. v1.0.0 stable-channel upgrade and same-version Repair with a correct password require live acceptance after the matching stable release is published. Alternative Pi hardware remains experimental until tested.

## v0.9.9.5.3 — Administrator Update Confirmation and About Page Redesign
**7 November 2026**

- Added one administrator password field inside the visible Software updates panel. **Check for updates** is unchanged; **Update now** and **Repair current version** now verify the signed-in admin's current password on the server before enqueuing a worker request. Missing or invalid passwords display an error inside that panel and do not queue work.
- Redesigned Information → About Moon Cheese to display the existing official 512px artwork alongside a neutral project description, with responsive mobile layout.
- Replaced the third-person biography with the exact approved first-person five-paragraph **About Me** wording and linked the correctly spelt **Transparent-Aluminium.net** business name.
- Added responsive Creator & Project, Socials, Music and Support cards containing all approved destinations with recognisable locally bundled SVG icons and accessible underlined text. Selected Font Awesome Free icons carry a separate third-party licence notice.
- Updated in-app Help, System Administration wording, README, and version history to match the functioning GitHub updater. The latest version remains expanded; earlier entries remain available collapsed without losing release dates or details.
- Kept the complete installer, all runtime components, optimised official artwork, GPLv3 licence, operational documentation and internal `SHA256SUMS`. Omitted test suites, test reports, upload instructions and unused original artwork. An external release checksum file separately verifies the compressed archive.
- Preserved existing account/password hashes, observation media, notes, notification preferences, NPM/Cloudflare/Tunnel state, Wi-Fi/IP rollback code, scheduled video/time-lapse, and the private prerelease test channel. **Live Raspberry Pi acceptance for this new version remains required; previous v0.9.9.5.2 Pi tests remain confirmed.**

## v0.9.9.5.2 — Private GitHub Update and Repair Verification
**Date:** 7 November 2026

- Corrected the archive directory permissions which were rejected by the in-app privileged updater.
- Enabled controlled testing of the *existing private prerelease* using a GitHub fine-grained repository-specific read-only token stored exclusively on the Pi.
- Added a direct test command that uses the complete official GitHub release download, archive checksum verification, extraction, and the existing full installer to upgrade v0.9.9.5.1 to v0.9.9.5.2.
- Enabled Check for updates and Repair current version to use the same verified private prerelease through the installed systemd worker, without making the repository public.
- Kept the normal stable-release channel unchanged; private prerelease testing is removable and requires no additional public releases.
- Retained the existing recordings, network configuration, camera features, optimised icons, and clean release package rules.

---

# Moon Cheese UAP Detector — Complete Version History

## v0.9.9.5.1 — Lean Distribution and System Health Update Layout
**Date:** 7 November 2026

- Software updates are displayed permanently in their own **System Health** panel, with installed and latest versions, Check for updates, Update now and Repair current version. System power remains a separate panel with its existing reboot and shutdown controls.
- Remove development-only test suites, test reports, and the unused high-resolution `moon-cheese-original.png` from the user installation archive. Retain the optimised Moon Cheese icons required for browser and Home Screen use.
- Retain `SHA256SUMS` inside the installation archive because its existing installer verifies it. Distribute a separate archive-level `SHA256SUMS` alongside the GitHub Release asset.
- Continue to preserve all existing user configuration, observations, recordings, camera and networking functions, plus the confirmed Wi-Fi radio and fullscreen fixes from v0.9.9.5.
- Release remains subject to live upgrade testing and GitHub Release validation before being presented as a stable public update.

---

## v0.9.9.5 — Production Preparation, GitHub Updates, Branding and Interface Corrections
**Date:** 7 November 2026

- **Wi-Fi radio controls:** preserve the administrator's pending Enable/Disable selection while NetworkManager status polling continues; only change the physical radio when the existing Apply action is submitted, keeping status distinct from the selected value.
- **Video investigation fullscreen:** fullscreen the video/still-frame stage rather than the complete investigation form; provide accessible exit and playback controls; preserve comparison modes, brightness, contrast, zoom, frame stepping, MP4 originals and PNG export across detection clips, scheduled videos and time-lapses.
- **Official Moon Cheese artwork:** add the user-supplied icon as browser/favicon and Apple touch icon, PWA manifest icons and desktop launcher artwork. Continue to use Moon Cheese as the application brand.
- **Information → About Moon Cheese:** add project description, creator biography, official GitHub repository link, social/community/music sites, website/blog, shop and donation links in grouped layout.
- **GitHub release controls:** new administrator-only Software updates section in System Health with Check for updates, Update now and Repair current version. Check only the official DrRavenholm repository and approved stable GitHub Releases. A separate privileged systemd worker verifies external and internal SHA256SUMS, rejects unsafe archive paths, postpones installation while camera recording is active and invokes the complete existing installer. Missing/private GitHub releases disable the installation actions rather than claiming availability. A dedicated release-signing key and physical end-to-end tests remain necessary before production.
- **Update availability notices:** daily at each administrator's configured observation-summary time; use existing dashboard/email/Web Push delivery preferences and persist a per-version deduplication record. No automatic installation.
- **Installer and hardware:** retain full fresh-install/upgrade/repair packaging while moving local URL and login instructions to the final output; remove arbitrary Pi 4-only rejection in favour of compatible dependency checks and experimental alternative board support. Pi Zero 2 W/low-RAM setups omit Docker/NPM by default; retain sensor-aware Pi 5 experimental frame rates. Device support beyond the tested Pi 4 requires real hardware verification.
- **Documentation:** reorganised Help gains new topic entries under System Health, Information, Observations and Administration; update the README and complete Version History. Keep working NPM/SSL/DDNS, Cloudflare Tunnel, IP rollback, core detector/camera/scheduling and media functions unchanged.
- **Release distribution:** adopt `moon-cheese-uap-detector-v0.9.9.5.tar.gz` as the versioned complete archive name. v0.9.9.5 is a controlled test release, not yet published as a public stable release or independently tested on the target hardware.

---

## v0.9.9.4.13 — Connector Installation, Managed Tunnel Cleanup and Help Organisation
**Date:** 31 October 2026

- Fix the confirmed automatic connector-installation failure: the Cloudflare signing-key server returned HTTP 403 to Python's default User-Agent; use official GitHub Debian release packages via `curl` and `dpkg`, matching installed CPU architecture and verifying package identity and executable.
- After a healthy managed hostname replacement, attempt exact old-resource cleanup. Verify the old Moon Cheese connector has gone inactive and that its saved DNS and origin identities match; remove only the previous Tunnel and DNS record, then read back Cloudflare state. Retain cleanup information and report pending if safe deletion cannot be completed.
- Report connector download, installation, verification and systemd failures by operation/stage inside the Tunnel section rather than an uninformative internal-error string; never expose tokens or raw process output.
- Reorganise the entire Help & User Guide: retain all 226 topics, consolidate appended chapters, nest Network and remote access under Administration → System Administration, keep historic topic anchors and the client-side search.
- Correct obsolete references to future NPM, DDNS and Tunnel features; retain all earlier version-history entries, the existing look and permissions, and verified working camera/recording/storage/notifications/PNG/NPM/SSL/DDNS and network fallback functionality.
- Complete fresh-install / upgrade / repair distribution; require real Pi and Cloudflare verification for the new automatic installation and remote cleanup paths.

---

## v0.9.9.4.12 — Simplified NPM and Cloudflare Tunnel Setup
**Date:** 31 October 2026

- Replace the multiple NPM/Tunnel authorisation checkboxes and separate setup/hostname change forms with one administrator-authenticated **Set up / Update** action per method. The administrator enters the requested hostname and necessary details; backend safety checks stay in place.
- Restore non-secret saved hostname, zone/account IDs and SSL contact information on opening the form. Reuse existing stored credentials only for the matching Cloudflare account/zone; never display API or connector tokens.
- Preserve NPM and Tunnel setup as separate root-protected profiles across Local-only mode and upgrades. Do not rewrite established NPM certificate, SSL, DDNS or media handling.
- Reconcile an unfinished Moon Cheese Tunnel and its CNAME when the DNS record points to an obsolete deleted Tunnel or a verified matching inactive Moon Cheese Tunnel. Refuse unrelated A/AAAA records and active/foreign Tunnel resources; no indiscriminate DNS takeover.
- Support updating the managed NPM hostname through the existing protected preview/verified-replacement backend, now triggered internally by a single submit. Maintain the existing working domain and DDNS while preparing a replacement.
- Preserve separately named, administrator-authenticated destructive Tunnel actions. Remove only verified managed Cloudflare resources; do not report success until provider state agrees.
- Update Network Setup Help to match actual controls, preserve the established collapsible appearance, existing Version History and all prior changes.
- Full install, upgrade and repair distribution. **The new Cloudflare workflows have not yet been live-tested on the user's Pi; controlled acceptance testing is required.**

---


## v0.9.9.4.11 — Tunnel Recovery, Live LAN Addresses and Changelog Fix
**Date:** 30 October 2026

- Preflight Cloudflare DNS before any Tunnel creation; reject a conflicting record before writing new remote resources. Require exact Tunnel, origin and CNAME validation for authorised recovery.
- Add an explicit, administrator-protected **Remove unfinished Cloudflare resources** option distinct from **Abandon local unfinished setup**. Verify the matching Tunnel and DNS record have disappeared from Cloudflare before reporting success; persist interrupted removals for retry.
- Require live Cloudflare read-back for completed managed Tunnel removal, so a successful DELETE request is not mistaken for a successfully deleted remote resource.
- Show connected physical Ethernet and Wi-Fi addresses and local dashboard links under Local network only, excluding Docker bridges.
- Display the selected IP-change interface's current address, saved connection and DHCP/static mode, refreshed from NetworkManager. Show other connected interfaces as fallback paths if the current connection drops.
- Improve DHCP confirmation guidance: after lease verification, show the real new-IP link if the browser remains connected. Preserve the independent 120-second recovery deadline and working administrator login redirect.
- Repair the blank v0.9.9.4.10 entry in the collapsible Version History without deleting any previous release notes. Keep the newest release initially expanded.
- Preserve every established page and styling convention, NPM, Let's Encrypt SSL, Cloudflare DDNS, PNG downloading, camera and recording, time-lapse, scheduled jobs, notifications, security permissions and five-tab Storage Management.
- Full install, upgrade and repair package. **Live Cloudflare and DHCP verification remains necessary**.

---


## v0.9.9.4.10 – Tunnel Management and Live IP Confirmation
**Date:** 30 October 2026

- Show existing non-sensitive managed and unfinished Cloudflare Tunnel configuration inside the existing collapsible, administrator-only Tunnel section immediately after an upgrade. Never display stored API tokens or connector tokens.
- Add explicit **Abandon unfinished Tunnel setup** with administrator password and acknowledgement; it clears only the incomplete local state, preserving any Cloudflare resources for review. The exact original hostname can still be used to recover a verified unfinished tunnel.
- Add managed Tunnel **disable**, **re-enable**, and **remove** controls. Removal requires Local-only mode, hostname confirmation, and verification of the exact saved tunnel and DNS identity. Interrupted deletions retain a recovery marker. Unrelated provider tunnels are protected.
- Allow an administrator-approved hostname change. Start a separate candidate `cloudflared` connector and check it before replacing an active connector; attempt to restore the previous token if the replacement fails. Retain the previous Cloudflare Tunnel and DNS record after a successful switch until manual review.
- Improve the IP-change original page: display a copyable expected new static-IP confirmation URL before submission, check live progress more frequently and retry on browser focus. Explain that the page cannot continue polling if the changed interface was its only connection, and that DHCP addresses cannot be known in advance.
- Preserve the working NPM/SSL/DDNS, direct PNG downloads, Camera and recording hardware-aware defaults, original interface styling, camera, recording, Time-lapse Studio, scheduled videos, notifications and storage management.
- Full fresh-install/upgrade/repair distribution. **Unverified:** real Cloudflare connector and API operations, hostname failover and removal, and live Pi IP switching. Controlled testing is required.


---
## v0.9.9.4.9 — Tunnel Recovery, IP Confirmation and Camera Defaults
**30 October 2026 — complete test distribution**

- Correct Cloudflare connector-token validation to accept Base64 padding, and persist tunnel identity immediately. Recover only a verified, matching, inactive legacy Moon Cheese tunnel with explicit administrator approval; no unrelated tunnel or DNS record is overwritten.
- Verify cloudflared actually connects to Cloudflare before reporting success; retry unfinished steps using the saved tunnel identity rather than creating duplicates.
- Replace short-lived automatic IP popups with a permanent, clickable new-IP confirmation address available from the original page, including after a page reload and from an external HTTPS domain. Keep the recovery service independent and the administrator-login confirmation flow.
- Preserve unchanged NPM forwarding if the switched interface is not the address currently used by the proxy. Update it only after confirmed network changes when applicable.
- Save current frame PNG now always downloads in Detection, Scheduled Video and Time-lapse viewers, normal and comparison modes; removes operating-system Share call.
- Camera and recording gains Reset to defaults, loading defaults only for that section, using the detected camera's supported FPS list, requiring the normal Save settings action. Hardware capability checks remain intact.
- Preserve the inherited shared design, collapsible Version History, application modules, existing accounts, media and install/upgrade/repair data.
- Live Tunnel and network IP confirmation require supervised Raspberry Pi acceptance testing; offline tests do not certify the result.

---

# UAP Detector – Complete Version History

## v0.9.9.4.8 – Safe Domain Changes and Network Confirmation Recovery
**Date:** 22 October 2026

- Added an administrator-only **Change managed domain** panel under the existing Cloudflare + NPM settings. Preview the replacement and explicitly authorise it; no unrelated reverse proxy is managed.
- During a managed-domain switch, retain the existing active NPM hostname and active DDNS configuration until NPM acknowledges the replacement proxy with its certificate, Force SSL and Access List. Preserve the old DNS record and certificate. The former managed proxy remains active by default; a separate administrator confirmation can disable it after personally verifying the replacement public HTTPS address. DNS and certificates are never deleted automatically.
- Keep incomplete new-host state separate from the active configuration and support safe retries. Public status contains only hostnames and diagnostic summaries, never Cloudflare tokens.
- Replaced the CSP-blocked inline network-confirmation timer with an administrator-protected external JavaScript file. Both old and new tabs use the device's recorded deadline; a final recovery status replaces a timer frozen at 00:00/02:00.
- Strengthened the independent rollback service: serialise address changes with recovery, verify restored IPv4 configuration and an acquired address, retain the recovery record when verification fails, and report a clear error instead of silently clearing it. DHCP can legitimately receive a new lease.
- Preserve the working NPM/SSL/DDNS integration, administrator permissions, established styling, five Storage Management tabs, recordings, photography, scheduled jobs and all prior release entries. Complete install / upgrade / repair archive.
- **Acceptance limit:** offline tests do not prove live router/Cloudflare reachability or automatic IP restoration on Raspberry Pi hardware. Test with Ethernet or local console access available.

This document is generated from the built-in release timeline (`uap/pages.py`). All v0.9.9.2 entries and older history are preserved verbatim in the source of v0.9.9.3.

## v0.9.9.4.7 – NPM Certificate Expiry Compatibility
**Date:** 22 Oct 2026

Focused correction for existing Let's Encrypt certificates incorrectly rejected during NPM recovery.

- NPM 2.16 stores certificate expiry dates in its SQLite database as UTC timestamps without timezone suffixes (for example, `2027-01-20 12:22:58`). Earlier recovery validation rejected these values despite successful certificate issuance.
- Interpret naive expiry timestamps received from NPM as UTC. Continue to accept timezone-qualified ISO 8601 expiry values and reject invalid or expired certificates.
- Retain exact-hostname, Let's Encrypt provider, Cloudflare DNS-challenge and certificate-in-use safeguards. Administrator approval is still required when adopting an unused untracked certificate.
- Preserve recovery of a disabled managed proxy and its Cloudflare Access List: bind a validated certificate, enable Force SSL and the proxy, then check the saved settings before declaring success.
- Add dedicated tests using actual NPM 2.16 timestamp formatting, security edge cases and the full disabled-proxy recovery sequence. No fresh certificate or duplicate proxy is requested during eligible recovery.
- Keep existing appearance, other networking controls, direct IP confirmation, camera, recording, notifications, scheduling, Time-lapse Studio and Storage Management unchanged. Full fresh-install / upgrade / repair distribution; live NPM acceptance test still required.

## v0.9.9.4.6 – Existing Certificate Adoption and Network Setup Recovery
**Date:** 22 Oct 2026

A targeted correction to incomplete NPM/Cloudflare setup. Live verification remains necessary.

- Allow an administrator to explicitly authorise reuse of an existing, **unused**, unexpired Let's Encrypt certificate issued through Cloudflare DNS challenge for exactly the selected detector hostname. Preserve all certificates assigned to any other proxy host.
- Recognise NPM's actual hostname-based certificate display name as well as Moon Cheese's requested descriptive name. Recover a certificate issued during a previously recorded pending request even when NPM normalised its name.
- Safely reconnect to a matching **disabled** Moon Cheese-style proxy host following an incomplete setup, with the existing unfinished-setup authorisation. Do not take over working hosts.
- Resume the remaining NPM configuration: bind certificate and Cloudflare Access List, enable Force SSL and the proxy, and read back the saved settings before recording success.
- Report a deleted/replaced DDNS record as **Needs setup**, without changing unrelated records. A newly authorised setup can recreate or reattach only the selected DNS hostname.
- Preserve NPM/Cloudflare progress messages inside the existing collapsible section, with clear labels for last recorded results; no redesign.
- Complete combined fresh-install/upgrade/repair package; no changes to detector, recording, storage and scheduling code.

## v0.9.9.4.5 – Let’s Encrypt Recovery and Direct IP Confirmation
**22 October 2026 · full correction test distribution**

- Extended NPM's certificate-request wait to exceed the 120-second Cloudflare DNS-challenge propagation interval, with additional time for ACME validation.
- Reconciles requests that time out after Certbot has finished: identifies the specifically named Moon Cheese certificate in NPM and reuses it without requesting another certificate.
- Resumes partial setups safely: associates the verified certificate with the existing managed proxy, enables **Force SSL** and the proxy only after confirmation, and verifies the stored NPM host settings.
- Leaves incomplete hosts disabled if SSL cannot be confirmed; never silently assigns a separately managed certificate.
- Administrator sign-ins on the newly assigned IP now lead directly to the pending confirmation page, retaining the 120-second independent rollback and reauthentication requirement.
- Kept the shared interface stylesheet and camera, recording, time-lapse, notifications and storage source intact. Includes full install, upgrade and repair files.
- **Acceptance limit:** simulated NPM/Flask checks are not a replacement for proving live NPM certificate registration, public HTTPS reachability and IP-confirmation flow on the Raspberry Pi.

## v0.9.9.4.4 – Network Form Submission Routing Repair
**22 October 2026 · full correction test distribution**

- Fixed a browser-side `form.action` name collision: every networking form has a hidden field named `action`, which can mask the form's URL property. JavaScript submitted NPM, DDNS and IP changes to the wrong address and received HTTP 404.
- Both ordinary networking forms and the IP-change form now read the actual HTML `action` attribute and require the exact same-origin `/system/network/action` path.
- Added a **real Chromium regression test** using the rendered production Network Setup forms and a mocked fetch backend, confirming the intended POST destination for NPM, DDNS, Wi-Fi and IP configuration rather than only inspecting source strings.
- Retained each network tool's inline result within its own collapsible section, the Let's Encrypt contact email, DNS hostname authorisations, stored credentials safeguards and existing permission controls.
- Preserved the existing design and layout, camera/recording/storage/timelapse/notification code, all previous version-history entries and the complete install/upgrade/repair distribution.
- **Acceptance limit:** correct browser request routing is verified locally. Successful NPM provisioning, Cloudflare updates, Wi-Fi AP connection and DHCP/static IP rollback **cannot be certified** without real device/provider integration tests. Do not retry IP changes without independent local access.

## v0.9.9.4.3 – Networking Error Feedback and NPM Setup Repairs

**22 October 2026 — Offline correction build; unverified against live NPM/Cloudflare and NetworkManager.**

- Restored Let's Encrypt contact email entry; optional explicit synchronisation to the local NPM administrator email for NPM 2.16 (which no longer accepts the old certificate email metadata).
- Allowed an administrator to authorise a new hostname after an incomplete previous setup, while refusing silent modifications to working managed hosts/certificates.
- Moved all networking result notices inside their relevant expandable sections. Removed the global status pile-up; errors should appear directly beside the form.
- Returned actionable JSON errors for network form validation and CSRF rejection; browser distinguishes login redirect/HTML errors from actual success.
- Kept independent operation timestamps and preserved shared appearance, camera, notifications, recordings, scheduled videos, time-lapses and storage.
- Full archive, fresh install/upgrade/repair; live network behaviour not yet validated.

## v0.9.9.4.2 – Network Provisioning Compatibility and Status Corrections
**22 October 2026 · full correction test distribution**

- Updated the NPM certificate request for the bundled NPM 2.16 API, removing old Let's Encrypt email/agreement fields that current NPM no longer accepts.
- Allowed a new hostname after an abandoned *incomplete* attempt where no active proxy/certificate exists; never silently replace a functioning existing host.
- Configured and tracked the explicitly authorised Cloudflare A record and five-minute DDNS even when later NPM certificate issuance fails.
- Created NPM proxy hosts in a **disabled** state first, enabling HTTPS and the host together only after a valid Let's Encrypt certificate is obtained.
- Added stage-specific NPM failures and limited, sanitised provider validation details without ever including credentials.
- Consolidated network feedback into the latest result with earlier per-operation results in a collapsed activity section; added background status polling.
- Displayed the real Wi-Fi radio state, improved scan-result updates and network selection, and extended connection attempts with proper outcome verification.
- Correlated pending IP-change requests with their results; rejected operations no longer display a misleading 02:00 countdown. Preserved the independent rollback service and administrator confirmation requirement.
- Kept the existing Moon Cheese stylesheet, established camera and storage code, roles, layouts, Help and historical changelog unchanged. Full fresh-install/upgrade/repair archive; **live networking has not been certified**.

## v0.9.9.4.1 – Network Corrections and Wi-Fi Administration
**22 October 2026 · full test distribution**

- Corrected the existing Cloudflare A-record situation reported during first v0.9.9.4 testing. With separate explicit approval, Moon Cheese may adopt and update its chosen hostname without touching unrelated records or changing the record's proxy status.
- Corrected DDNS check reporting: inactive configurations are now labelled inactive, and configured checks record up-to-date / updated / error. A five-minute systemd timer continues to perform DDNS checks for managed NPM deployments.
- Kept separate per-action status files instead of losing NPM/IP results when another action runs. Repeated NPM provisioning stores its own completed object IDs so partially finished attempts can be resumed.
- Extended the existing advanced IP address settings to show and select active Ethernet and Wi-Fi interfaces; actual interface IP and method are verified rather than trusting a successful command response.
- Added a systemd recovery timer, including after reboot, for pending network changes without an authenticated confirmation. Both browser tabs retain the safety-message behaviour, with clear success/failure/restored outcomes when status is reachable.
- Added Wi-Fi radio enable/disable, nearby network scanning and WPA Personal Wi-Fi setup. Remote disabling of the only connected wireless interface is refused; credentials are never included in diagnostics.
- Corrected repeated "Pi address" terminology to general IP/network language, displayed DDNS uppercase and preserved non-secret form fields when NPM setup needs another attempt.
- Retained the existing app styling, routes, camera capture code, photography, scheduling, Storage Management, permissions, notifications and older version history. Version History continues opening its latest entry first.
- Complete fresh-install/upgrade/repair archive (not a patch). Live Cloudflare/NPM/certificate issuance, Wi-Fi and address rollback testing remains necessary before production certification.

## v0.9.9.4 – Network Setup and Notification Reliability
**Date:** 22 Oct 2026

Complete install/update/repair source distribution, improved notification deduplication, Moon Cheese text branding and an administrator-only Cloudflare/NPM/Tunnel networking wizard. Live provider and Pi networking acceptance tests remain pending.

- Preserved daily and weekly digest generation records independently of deletable notices to prevent repeated emails and Web Push after deletion.
- Standardised Moon Cheese text branding across email headers, browser page title and test delivery labels.
- Added collapsible local-only, Moon Cheese-managed local NPM + Cloudflare, external proxy and Cloudflare Tunnel network setup sections in System Administration.
- Added guided Zone ID and scoped token entry, NPM DNS-challenge Let's Encrypt creation, managed Cloudflare IP Access List and dedicated detector hostname records.
- Added independent five-minute Cloudflare public IPv4 DNS checks and a protected root-only credentials store.
- Added signed `cloudflared` package onboarding, tunnel creation, hostname route and independent service; no router forwards needed in Tunnel mode.
- Added advanced NetworkManager DHCP/static switching with previous settings backup, local old-page countdown, new-tab administrator confirmation and 120-second independent rollback.
- Added localhost Desktop launchers for Moon Cheese and bundled local NPM; Pi OS Lite remains supported without a GUI.
- Kept all original interfaces, camera-recording features, protection rules, historical changelogs and the complete combined installer sources.
- No GitHub updater, user-selectable branding, final icon, remote NPM administration or router auto-configuration was added.

## v0.9.9.3 – Complete Distribution and Full-Resolution Capture Repair
**Date:** 18 Oct 2026

Self-contained application distribution, restored complete Pi service/NPM installer and repaired full-resolution still capture, with updated Moon Cheese branding.

- Fixed the full-resolution Capture button HTTP 500 regression caused by a missing math import in the camera-request route.
- Made the photo request return actionable JSON errors for queue/filesystem failures, instead of an HTML error page causing a JSON parsing failure.
- Changed the main header to ✦ MOON CHEESE and the footer to Moon Cheese UAP Detector by Dr Ravanholm.
- Bundled every application module, background systemd service, required camera-support module, optional NPM deployment files and offline release history in one archive.
- Added an idempotent install-or-upgrade script that backs up configuration/database and preserves existing media, accounts, SMTP/Web Push credentials and NPM deployments.
- Restored the systemd Gunicorn writable runtime directory and TMPDIR override for both fresh installations and upgrades.
- Preserved the v0.9.9.2 correction release, its full original changelog and all preceding version-history entries.
- Retained the existing recording, Scheduled Video, Time-lapse Studio, unified Storage Management, notifications and public-gallery functionality.

## v0.9.9.2 – Interface and Notification Corrections
**Date:** 16 Oct 2026

Fixed SMTP save acknowledgement, smarter camera scheduling, consistent job placeholders, better email and compact controls.

- Fixed false HTTP 400 after saving SMTP or Web Push sender configuration, and tested the administrator form actions.
- Collapsed System Administration and Notifications settings; Notifications now opens with the actual notification centre first.
- Replaced absent time-lapse thumbnails with uniform 16:9 status placeholders and safe missing-image fallbacks.
- Reduced the early camera reservation window for still photography, while retaining active-job lockouts and exposure-aware safety checks.
- Rearranged the time-lapse storage estimate into the six requested positions and restricted recalculation to duration/interval changes.
- Improved opt-in emails with readable HTML and plain-text fallback; added trusted local/public links to relevant authenticated pages.
- Added 10-row diagnostic summaries, filtered paginated history, and 90-day retention for completed technical delivery records.
- Updated the self-contained Help chapters; existing camera recorder, Scheduled Video, Time-lapse Studio and storage tabs remain in place.

## v0.9.9.1 – Notification Delivery and Live Storage Planning
**Date:** 16 Oct 2026

Visible time-lapse disk budget, opt-in SMTP and encrypted browser Web Push, clearer configuration backups and delivery diagnostics.

- Added a live read-only storage estimate to the Time-lapse Studio scheduling form, including frame count, playback duration, current free space, measured/fallback JPEG size, temporary space and the 2 GiB scheduling reserve.
- Added administrator SMTP sender configuration and test delivery, with encrypted transport, local private credentials and per-user recipient email addresses.
- Added browser Web Push subscriptions, per-device tests and removal, and VAPID-signed encrypted push delivery using browser provider services.
- Added persistent notification delivery records, retry states and diagnostics. Alerts remain administrator-only; personal digest times keep independent timezone preferences.
- Expanded Help with full Email, Browser Push, job interruption, storage estimator and backup/import procedures and provider limitations.
- Documented exactly which detector settings and profiles are included in Settings Only and Settings + Users backups; excluded secrets and media remain excluded.
- Kept all existing Scheduled Video, Time-lapse Studio, recording, photographs and unified Storage Management pages; recorder and capture engine are unchanged.

## v0.9.9.0 – Unified Storage and System Administration
**Date:** 16 Oct 2026

One storage-management interface for all media, improved time-lapse storage planning, simpler timezone choices, backup portability and administrative foundations.

- Unified Overview, Recordings, Photographs, Scheduled Videos and Time-lapses inside the existing Storage Management page, with common search, status, visibility, sorting, pagination and protected deletion.
- Removed only the two duplicate storage administration menu links. Existing Scheduled Video, Time-lapse Studio, their job history and public gallery pages remain intact.
- Added MP4 and private source ZIP size breakdowns, downloads and ZIP-only removal to the time-lapse storage tab, with existing protection checks.
- Expanded whole-device disk reporting to measured detector media, Raspberry Pi software, container storage, caches, swap and backups, plus remainder.
- Estimated future still-photo storage from recent full-resolution JPEG archives, while maintaining the 2 GiB planning reserve and runtime low-space safeguard.
- Aligned contextual Help beside page headings and removed the ineffective notification-timezone search field; the selector now shows current UTC offsets.
- Added administrator Settings-only export/import and encrypted Settings + Users backups with import preview and merge-only account restoration.
- Added a System Administration foundation for network, NPM, Cloudflare, email and future updates, without enabling premature automation.
- Expanded contextual help for unified media storage, backup procedures, low-space decisions and supported recovery behaviour.

## v0.9.8.9 – Downloads, Help & Notification Preferences
**Date:** 15 Oct 2026

Named media downloads, comprehensive contextual help, per-user report timezones and expected camera-job alert handling.

- Generated stable, descriptive download filenames for time-lapse MP4s and private source ZIP archives using observation IDs and editable titles.
- Added searchable personal notification timezones and an explicit Use my browser timezone action; detector observation times remain detector-local.
- Updated camera-snapshot health monitoring to ignore expected snapshot pauses during an active scheduled video or time-lapse job.
- Added specific fault and recovery descriptions and richer notification documentation.
- Reorganised help into independent, detailed page chapters and added context-sensitive Help links on pages.
- Left camera capture, recording, MP4 rendering and ZIP generation unchanged.

## v0.9.8.8 – Local Time & Time-lapse Corrections
**Date:** 15 Oct 2026

Reliable local-time scheduling and consistent full-resolution time-lapse capture.

- Fixed Basic and Advanced time-lapse submission failures caused by invalid hidden input constraints.
- Both capture modes now take full-resolution stills and retain a verified source ZIP separately from Photograph Gallery.
- Aligned Advanced controls with Live Camera, including exposure in milliseconds, focus and white balance.
- Added exposure-versus-interval checks with a processing allowance and visible form errors.
- Uses the saved detector timezone for job scheduling; UTC is retained only for internal storage.
- Converted event, photo, scheduled-job, notification and public timestamps to readable local times.
- Handled invalid and ambiguous daylight-saving scheduling times explicitly.
- Added visible public counts for Scheduled Videos and Time-lapses.
- Preserved previous videos, photos, account data, settings and external proxy configuration.

## v0.9.8.7 – Scheduled Recording & Time-lapse Studio
**Date:** 15 Oct 2026

Camera-aware scheduled sessions, Basic/Advanced time-lapses, source ZIPs and observation management.

- Added administrator scheduling for continuous video recording and time-lapse capture, with timezone validation and conflict protection.
- Scheduled video saves verified five-minute MP4 segments as one session, with a playback and management page.
- Added Basic time-lapse using the configured video feed and Advanced time-lapse using still sensor capture.
- Advanced time-lapse controls include manual shutter up to hardware limits, analogue gain, focus, white balance and image adjustment.
- Displayed estimated source-frame count and resulting video duration from interval, session duration and output FPS.
- Rendered a finished MP4 and private downloadable source-photo ZIP; verified both before removing loose frames.
- Added a status/progress panel on Dashboard, suspended conflicting Live Camera photography and restored motion detection after jobs.
- Added searchable observation libraries, private media playback, titles, notes, pinning and explicit per-session public sharing.
- Added Scheduled Videos and Time-lapses tabs on the public page and corresponding Storage Management views.
- Integrated jobs into Observation Calendar and local administrator completion/failure notifications.
- Retained current motion detection, storm limits for motion events, camera profiles, users and networking configuration.

## v0.9.8.6 – Gallery Filters & Public Media Browsing
**Date:** 15 Oct 2026

Public and pinned photo filters, compact public media tabs and pagination, and consistent Live Camera labels.

- Added Public only and Private only filters to the three-column Photograph Gallery.
- Added Pinned only and Unpinned only filters, usable together with title/notes search and public sharing filters.
- Removed the unnecessary storage-deletion instruction from the Photograph Gallery heading.
- Reorganised the public observation page into Recordings and Photographs tabs.
- Limited public recordings to five entries per page and public photographs to six per page, with Previous/Next navigation.
- Retained opt-in public sharing, metadata-stripped public photographs and separate approval for public notes.
- Standardised Detection (grayscale) throughout the Live Camera and recorded-clip viewers.
- Left the detector, storm handling, camera settings, current media, accounts and networking unchanged.

## v0.9.8.5 – Gallery, Storm History & Controls
**Date:** 15 Oct 2026

Storm notifications, safer media deletion, photograph reviews, system controls and mobile Live Camera fixes.

- Added administrator-only storm activation and recovery notices, including a permanent local storm history on System Health.
- Rebuilt Storage Management with per-row trash buttons, multi-select, a visible selection bar and an in-place deletion confirmation.
- Photographs are managed in the same Storage Management interface as motion recordings; protected media is revalidated on deletion.
- Promoted Photograph Gallery into Observations, retained its three-column layout, and added title and notes search.
- Added detailed photograph pages with original downloads, editable titles and notes, pinning, and separate public photo and note permissions.
- Shared photographs appear on the public page as metadata-stripped reduced-resolution images only after administrator approval.
- Restricted System Health to administrators and added password-confirmed reboot and shutdown requests through a separate systemd helper.
- Reserved update status space on System Health without introducing an untested software update mechanism.
- Replaced unsupported Live Camera canvas filter usage with portable pixel processing for iPhone brightness, contrast and comparison.
- Standardised the Live Camera label to Detection (grayscale) and preserved existing recordings, camera settings and accounts.

## v0.9.8.4 – Storm Protection & Storage Management
**Date:** 13 Oct 2026, 16:31 UTC

Event-storm cooldown, bulk clip cleanup, photograph management and compact notification history.

- Added event-storm protection to prevent excessive continuous motion from generating hours of repetitive clips, including five-minute rollovers.
- Default circuit breaker: 10 recorded minutes in a 15-minute sliding window triggers a 15-minute cooldown; all three detector profiles are supported.
- When the circuit breaker trips, any current MP4 is finalised, its event is annotated, and new detections are paused while camera previews continue.
- Added a hard 1 GB disk-free safeguard that stops opening new recordings and saves an active clip without deleting any files.
- Added a dedicated administrator-only Storage Management page with clip filters, file sizes, bulk selection, deletion preview and explicit confirmation.
- Protected events (pinned, shared publicly, Flagged, Identified or Unresolved) remain excluded from bulk and automatic deletion.
- Added a photograph gallery with lazy thumbnails, original downloads, pin/unpin controls and individual deletion.
- Added optional photo retention and read-notification retention with independent day limits; both are off by default.
- Paginated notifications at ten items per page with status/category filters, individual deletion and Delete all read.
- Added Event-storm and retention settings to the browser interface and updated Help.
- Preserved existing footage, photographs, account permissions, camera profiles, remote access configuration and reporting schedules.

## v0.9.8.3 – HD Snapshot & Full Photo Comparison
**Date:** 13 Oct 2026, 11:56 UTC

Demand-driven HD Live Camera snapshots, full-resolution photo review, and processed 1080p comparison export.

- Added a separate admin-only full-size JPEG cache sourced from the active video stream without stopping detection.
- Kept the Dashboard and public still preview at their existing lightweight resolution.
- Made Live Camera save the real source resolution as PNG, up to 1920 × 1080 when recording at 1080p.
- Preserved split position, labels, zoom and enhancements when saving the Live Camera PNG.
- After a native still photograph, added Review captured photo to inspect it with the same processing controls.
- Enabled processed 1080p PNG exports from native full-resolution photos, while retaining the untouched full-resolution original download.
- Kept full-resolution photographs separate from normal video recording and restored normal capture after the still.
- Prevented viewer accounts and public pages from requesting or downloading admin full-resolution snapshots.
- Left recording settings, public sharing, accounts and notification schedules unchanged.

## v0.9.8.2 – Direct PNG Downloads & Help Reference
**Date:** 13 Oct 2026, 11:31 UTC

Direct Live Camera image downloads, clearer photograph queue errors, searchable documentation and streamlined public navigation.

- Save current view PNG now starts an ordinary image download instead of invoking the operating system sharing panel.
- Kept the composite image contents, comparison labels and slider position in the PNG export.
- Moved the administrator Public page shortcut from the top navigation into Observations; mobile navigation follows the same rule.
- Added a watchdog for still-photography requests that remain queued for more than 65 seconds without camera acceptance.
- Stalled camera requests now show a direct error and can be retried after the detector recovers, rather than remaining queued indefinitely.
- Long manual photo exposures are unaffected by the short queued-request watchdog after the camera accepts the job.
- Replaced the brief help page with grouped searchable reference documentation and jump links for individual controls.
- Documented the Dashboard, event review, video investigation, calendar, Live Camera, camera profiles, storage, accounts and notifications.
- Made documentation search run locally in the browser without sending search terms to another service.
- Provided troubleshooting advice for a camera that fails to accept a photo request while still protecting ongoing exposures.
- Retained the private administrator-only access rules on Live Camera and photograph downloads.
- Kept the motion recorder, detection algorithms, NPM and network configuration unchanged.

## v0.9.8.1 – Navigation & Live Camera Repair
**Date:** 13 Oct 2026, 11:03 UTC

Restored camera preview and made navigation menus stable and mutually exclusive.

- Fixed the Live Camera preview image request to comply with the dashboard content security policy.
- Restored interactive preview refreshing, freezing and frame comparison using the regular cached camera image.
- Redesigned the header as a stable two-row layout with the camera name and account tools above navigation.
- Changed Observations, Administration, Information and Account into floating dropdowns that do not reflow the page.
- Only one dropdown remains open at a time; clicking away or pressing Escape closes it.
- Improved compact mobile menu behaviour without changing account permissions.
- Left camera recording, photography capture controls, existing events and user settings unchanged.
- Kept preview images on the authenticated private dashboard endpoint.
- Preserved the existing Content Security Policy without allowing additional remote image sources.
- Ensured the existing cached camera preview can be reused without starting another camera pipeline.
- Kept the basic comparison slider and PNG export controls within the repaired Live Camera page.
- Made the notification bell and account menu available in the stable top header.
- Preserved permission-based navigation for administrator and viewer accounts.

## v0.9.8 – Navigation & Live Observation
**Date:** 13 Oct 2026, 10:39 UTC

Responsive menus, private camera photography and accurate rolling reports.

- Replaced overflowing header links with floating Observations, Administration and Information dropdown menus.
- Added mobile-friendly navigation that does not push page content when menus open.
- Added a notification bell displaying the signed-in account’s unread count.
- Added an optional public-page shortcut for administrators when public viewing is enabled.
- Added an administrator-only Live Camera page using the existing cached camera snapshot.
- Added ten-second refresh, Freeze/Resume, manually refreshing, zoom, brightness and contrast.
- Added original, detection and low-light processed views with a movable two-view comparison slider.
- Enabled saving the composed current live image as PNG with both comparison labels and divider.
- Added on-demand full native-resolution still photography without opening a second simultaneous camera owner.
- Added temporary camera controls for automatic/manual shutter, long exposure, analogue gain, focus, white balance and image tuning.
- The manual still capture request closes and saves an active video clip immediately, temporarily switches camera modes, then restores normal recording.
- Full-resolution stills are kept private and saved as chosen JPEG or PNG; camera profile settings are not modified.
- Improved iPhone PNG sharing and corrected comparison divider alignment at high zoom in the saved video player.
- Daily reports now cover the 24 hours ending at the selected time; weekly reports cover 168 hours.
- Updated report text to show the precise reporting window in the selected time zone.
- Left email/push delivery and external notification integrations unimplemented.

## v0.9.7 – Observation Calendar & Notification Centre
**Date:** 13 Oct 2026, 00:14 UTC

Browse recordings by day, see daily statistics, and receive private reports and health notices.

- Reserved the full video player height before public shared clips start playback to avoid layout jumps.
- Added an Observation Calendar with monthly recording totals and selectable dates.
- Added per-day recording lists, review-status totals, public and pinned counts and trigger-type breakdowns.
- Groups recordings by the detector time zone, including daylight-saving boundaries.
- Added an in-dashboard Notification Centre, with read/unread states and per-account private notices.
- Added Off, Daily and Weekly observation report preferences for each administrator or viewer.
- Added configurable report time, time zone and weekday for weekly reports.
- Daily reports summarise the preceding local calendar day; weekly reports summarise seven complete days.
- Added scheduled local report generation with one report per due date, avoiding duplicate notices after restarts.
- Added administrator-only notifications for detector heartbeat, camera snapshot and storage problems.
- Fault alerts appear once when a problem starts and again when it clears, rather than repeating on every check.
- No external notifications are sent in this release.
- Kept camera recording, user permissions, existing clips, event reviews and network configuration unchanged.

## v0.9.6 – Public Location & Settings Navigation
**Date:** 12 Oct 2026, 23:39 UTC

Cleaner settings and optional public camera location details.

- All Settings sections now begin collapsed, giving a clearer overview of configuration categories.
- Kept individual camera profile editors collapsed until opened for adjustment.
- Added an option to show the saved location name in the public camera heading, for example Sky camera - Hilltop.
- Kept the heading as Sky camera when the location is blank or its public display is disabled.
- Added a separate option for displaying precise latitude, longitude, detector time zone and camera compass bearing/elevation.
- Both public location permissions default to off, including for existing installations.
- Added a responsive, read-only camera-location summary to the public page when precise details are approved.
- Preserved private location data for local sunrise/sunset scheduling regardless of public visibility.
- Kept public playback, manually approved recordings, visitor login and camera snapshot refresh unchanged.
- Retained all private event data, detector profiles and original video files.
- No changes to reverse proxy, DNS, Docker or recording service behaviour.
- Updated Help with guidance on privacy choices and public location visibility.

## v0.9.5 – Profile Preview & Settings Layout
**Date:** 12 Oct 2026, 23:18 UTC

Test unsaved camera adjustments, restore profile defaults and navigate settings more easily.

- Added one-click reset to factory starting values for Day, Night, Custom 1 and Custom 2.
- Added temporary unsaved profile testing from Settings, without saving or activating the profile.
- Uses the current camera session for preview testing; no competing camera process is opened.
- Restores the active exposure and gain after preview and allows the recording buffer to refill.
- Does not interrupt an active clip and keeps test images private.
- Converted Settings into expandable sections with a clearer orientation layout.
- Made the Compare frame button shorter and aligned both view selectors.
- Preserved all user accounts, recordings, settings and review history.
- Kept test image files behind administrator authentication instead of publishing them as live camera previews.
- Allowed draft tests to wait for active clips rather than interrupting recordings.
- Added validation and useful error messages for exposures that exceed the active frame duration.
- Kept the chosen profile unchanged until an administrator explicitly saves the form.
- Updated Help with profile testing, defaults and the safer preview workflow.

## v0.9.4 – Camera Profiles & Image Orientation
**Date:** 12 Oct 2026, 22:55 UTC

Editable daylight and nighttime camera profiles, on-page colour preview and orientation setup.

- Added Automatic, Day, Night, Custom 1 and Custom 2 camera profile choices, plus automatic sunrise/sunset switching.
- Added configurable names for Day, Night and both Custom profiles.
- Added per-profile automatic or manual exposure, manual exposure duration in milliseconds and analogue gain.
- Added exposure compensation for automatic exposure and automatic/manual white balance with red and blue gains.
- Added focus options for automatic focus or infinity where camera hardware supports them.
- Added brightness, contrast and saturation adjustments to each camera profile.
- Added manual-exposure validation against the selected frame rate to prevent unsatisfiable camera settings.
- Added a camera image and Refresh preview button directly inside the camera profile editor.
- Changed camera snapshots to include colour information from the recording stream rather than greyscale detection-only frames.
- Added 180-degree camera rotation for new recordings, analysis frames and previews.
- Added compass bearing of the image top edge and camera elevation as orientation metadata for future sky mapping.
- Saved camera profile and orientation metadata with newly captured event recordings.
- Preserved existing event data and ensured manual camera changes wait for the current clip to complete.
- Added automatic re-selection of Day or Night camera settings after the calculated solar transition.
- Kept recording schedules, motion profiles, all public permissions and NPM configuration unchanged.
- Updated Help for camera profiles, solar exposure switching and alignment; expanded the release changelog.

## v0.9.3 – Frame Comparison & Multi-view Investigation
**Date:** 12 Oct 2026, 16:22 UTC

Compare two views of the same paused frame with a movable reveal slider.

- Added Original, Detection greyscale and Low-light enhanced playback views.
- Added a paused-frame comparison panel with independent Left and Right view selectors.
- Added a draggable image-reveal divider with persistent position while stepping through frames.
- Kept both views aligned by rendering them from the same decoded video frame.
- Automatically returns to the selected single playback view during playback.
- Restores frame comparison when playback pauses again.
- Supports PNG export of either the selected playback view or the two-sided comparison.
- Preserved existing frame stepping, slow motion, timeline seeking, zoom and image controls.
- Clarified that Low-light enhanced is image processing of the NoIR recording, not infrared-only capture.
- All processing runs in the browser without changing MP4 files or camera detection settings.
- The dashboard, recording database, accounts and public sharing settings remain unchanged.

## v0.9.2 – Hardware Awareness & Detection Attribution
**Date:** 12 Oct 2026, 01:00 UTC

Identify camera hardware, adapt recording-rate choices and show which detector triggered each new clip.

- Read the Raspberry Pi model and connected camera sensor on each device without opening a camera stream.
- Display detected hardware in Camera and recording settings.
- Keep conservative choices up to 30 fps on Raspberry Pi 4 and unidentified configurations.
- Expose 45 and 60 fps only as experimental choices when a Pi 5 and IMX708 camera are identified.
- Check frame-rate limits when saving settings and starting the camera recorder.
- Record whether general motion, moving bright-point tracking, or both triggered a new clip.
- Show trigger source on event detail pages and in the Dashboard event list.
- Keep existing recordings unchanged; their trigger source was not previously recorded.
- Confirmed viewer accounts do not automatically mark new recordings as viewed.
- Updated Help with detection-source and hardware capability explanations.

## v0.9.1 – Combined Detection & Public Filters
**Date:** 12 Oct 2026, 00:41 UTC

Both motion profiles together and easier management of shared recordings.

- Added Combined detection, triggering a single recording when either general motion or moving sky-light tracking detects activity.
- Kept General motion and Moving sky lights available as separate choices for targeted testing.
- Reused one recorder for simultaneous triggers, avoiding duplicate clips from two detector profiles.
- Added an All recordings / Public only / Private only sharing filter to Dashboard search.
- Added a Public label to approved recordings in the private event list.
- Kept sharing filters active when moving between multiple results pages.
- Preserved existing detector profiles, settings, recordings, public approvals and user accounts.
- Updated Help to explain Combined detection and the sharing filters.
- Kept video format and frame-rate limits unchanged; existing camera settings remain supported.

## v0.9 – Sky-Light Detection & Public Clip Notes
**Date:** 12 Oct 2026, 00:26 UTC

Experimental moving-light tracking and optional public observation notes.

- Added a choice between the established General motion detector and experimental Moving sky lights detection.
- Added bright-point tracking using the camera’s smaller 320 × 240 greyscale analysis frames.
- Required light candidates to move across multiple frames, reducing triggers from stationary stars and random flashes.
- Ignored oversized light regions as a first defence against large cloud movements and broad lighting changes.
- Added controls for minimum brightness, light area, movement and confirmation frames.
- Left General motion as the default; existing deployments and camera recording resolution remain unchanged.
- Kept the maximum H.264 recording resolution at 1920 × 1080 for Raspberry Pi 4 compatibility.
- Updated shared clip expansion to show the video on the left and optional notes on the right, stacking on narrow screens.
- Added explicit per-recording permission for sharing notes publicly; existing shared clips retain private notes by default.
- Preserved the no-download-link public layout, user roles, access controls, clips, schedules and review history.
- Updated the Help guide for both detection profiles and optional note publishing.

## v0.8.2 – Camera Naming, Resolution & Navigation
**Date:** 12 Oct 2026, 00:15 UTC

Shared camera name, recording resolution selection and consistent dashboard navigation.

- Applied the chosen camera name throughout the site, including signed-in pages and public viewing.
- Made Sky Camera the default name whenever the name field is left empty.
- Replaced the camera-name setting help text with a straightforward description for users.
- Added a camera resolution menu with VGA, HD and Full HD output sizes.
- Connected the resolution setting to the camera recorder rather than changing the display alone.
- Updated camera restart detection so recording resolution changes apply once the active recording is complete.
- Standardised the main navigation and back links to Dashboard.
- Updated Help for the shared camera title and new resolution options.
- Preserved existing camera names, user accounts, footage, notes, schedules and publishing preferences.

## v0.8.1 – Public Page Improvements
**Date:** 11 Oct 2026, 23:57 UTC

Custom visitor-facing title, expandable shared recordings and public-first landing page.

- Added an editable public site title under Settings, separate from the private dashboard title.
- Changed the public header to use that title instead of TEST BUILD.
- Changed the root address to display the public camera page for signed-out visitors when public viewing is enabled.
- Kept the normal login page as the landing experience when public viewing is disabled.
- Added a Log in button on the public header that opens the existing private sign-in page.
- Replaced the shared-recordings grid with a compact responsive list of titles, UTC timestamps and thumbnails.
- Added expandable playback for each approved recording rather than showing all players at once.
- Removed download links from the public page and requested that compatible browsers hide the native download control.
- Kept public access limited to individually approved clips, without publishing private notes or statuses.
- Retained all existing accounts, recordings, event settings, camera services and reverse-proxy configuration.

## v0.8 – Sharing, Accounts & Player Layout
**Date:** 11 Oct 2026, 23:40 UTC

Improved video layout, user roles and optional public sky page.

- Moved the video investigation player above the event still preview.
- Moved the thumbnail into the details column beneath event information.
- Removed the audio Unmute button; the supported camera has no microphone.
- Added My Account to change the login name and password with current-password confirmation.
- Migrated the original admin login into an account database without changing credentials.
- Added administrator-managed viewer and administrator user accounts.
- Protected recording edits, deletion, publishing, configuration and system health with server-side administrator checks.
- Allowed viewers to watch private event footage without automatically changing New to Viewed.
- Added explicit per-event approval for optional public sharing.
- Added an anonymous public page with a 10-second still-image refresh and explicitly shared clips.
- Left the public page disabled unless an administrator chooses to enable it.
- Excluded shared events from automatic recording cleanup.
- Kept existing recordings, metadata, NPM and camera services unchanged.

## v0.7 – Video Investigation Player
**Date:** 11 Oct 2026, 23:22 UTC

Slow-motion playback, frame stepping, image zoom and frame exports.

- Added a browser-based Video investigation section to saved recording pages.
- Added playback speed choices: 0.25×, 0.5×, 1×, 1.5× and 2×.
- Added previous- and next-frame seeking based on video frame rate reported by FFprobe, with a clearly indicated fallback where needed.
- Added a draggable timeline with precise playback time readout.
- Added zoom from 1× to 4×, with pointer-drag panning for enlarged footage.
- Added brightness and contrast adjustments to inspect dark or bright footage.
- Added a one-click reset for all image adjustments.
- Added fullscreen mode, mute controls and the ability to save a still PNG frame with adjustments applied.
- Kept existing playback, download, pinning, review states, notes, schedules, retention settings and access rules.
- Expanded the in-app Help guide with player controls and their browser-seeking limitations.
- Added supplied historical UTC timestamps for v0.1 and v0.2 and expanded their changelog details.
- Kept original MP4 files untouched: video processing and frame export happen in the browser.

## v0.6.1 – Changelog & System Health Corrections
**Date:** 11 Oct 2026, 23:09 UTC

Aligned release dates, fuller change lists and working system uptime.

- Aligned every release timestamp in a dedicated right-hand column.
- Expanded the changelog to describe the features introduced in each release.
- Added historical UTC timestamps for v0.3, v0.4 and v0.5 using the available project records.
- Left older dates blank where no dependable timestamp was available.
- Removed unnecessary explanatory text from the Version history page and Help guide.
- Fixed System health uptime reporting by correctly reading the first number in /proc/uptime.
- Preserved existing event data, saved searches, recordings, pinned flags and detector settings.

## v0.6 – Reliability & Event Protection
**Date:** 11 Oct 2026, 22:50 UTC

System health, pinned recordings and improved event management.

- Created a read-only System health page with detector heartbeat and current camera state.
- Added disk capacity and free-space readings, RAM information, CPU temperature and load averages.
- Added camera preview age and an uptime field to help diagnose unattended operation.
- Added manual Pin / Unpin controls to protect selected event recordings.
- Excluded pinned clips from both retention cleanup and the optional storage cap.
- Prevented manual deletion of a pinned event until it is unpinned.
- Added a Pinned-only event filter and pinned event count on Overview.
- Redesigned Version history with expandable sections for each release.
- Expanded the Help guide with recording protection and device health information.

## v0.5 – Scheduling & Discovery
**Date:** 11 Oct 2026, 22:16 UTC

Detector operating windows, pause controls, search and Help.

- Added Continuous mode for around-the-clock monitoring.
- Added Scheduled hours mode with configurable start and end times across midnight.
- Added Sunset to sunrise mode based on detector latitude, longitude and timezone.
- Made calculated sunrise and sunset times adjust for the date and daylight-saving changes.
- Added an optional browser location button to populate the detector coordinates.
- Added a Pause / Resume control that prevents new events but keeps the dashboard and camera preview available.
- Added searching across recorded event titles and review notes.
- Added a review-status filter to the event listing.
- Created the Help guide and the first Version history screen.
- Corrected the display text for the footer website link.

## v0.4 – Settings & Storage
**Date:** 11 Oct 2026, 21:46 UTC

Browser recording controls, retention policies and event review automation.

- Added a Settings page for camera frame rate and motion sensitivity.
- Exposed pixel-change threshold and minimum changed-pixel count.
- Added editable pre-motion buffer, post-motion tail and maximum clip duration.
- Added a Storage overview with event counts, video usage and remaining disk space.
- Added optional daily cleanup with configurable retention for New, Viewed and Dismissed events.
- Added an optional soft video-storage limit, with reviewed statuses protected.
- Made opening a New event automatically change it to Viewed.
- Preserved manually assigned Identified, Flagged, Dismissed and Unresolved states.
- Added an in-page Refresh preview button.
- Replaced the personal address in the application header and introduced project footer branding.

## v0.3 – Motion Recording Improvements
**Date:** 11 Oct 2026, 21:18 UTC

Pre-motion clips, continuous-event recording and editable event details.

- Introduced buffered video so clips can begin before motion is detected.
- Extended recordings while movement continues instead of always stopping at a fixed short length.
- Added a quiet-time tail to preserve footage immediately after motion stops.
- Handled unusually long continuous events by splitting them into additional clips.
- Enabled changing event names from the event detail page.
- Added review statuses and persistent free-text notes for individual recordings.
- Added MP4 playback and download from the event page.
- Added a confirmation step for permanently deleting an event, video and thumbnail.

## v0.2 – Simpler Local Access
**Date:** 11 Oct 2026, 15:45 UTC

Browser-friendly local NPM access and streamlined setup.

- Provided a normal local-network URL for the NPM administration page.
- Adjusted NPM network bindings to avoid opening its admin port publicly by default.
- Updated the installer instructions for everyday browser use.
- Kept the detector dashboard and NPM management interfaces separate.
- Provided a local dashboard URL on port 8000 and an NPM management URL on port 8181.
- Prepared the groundwork for a self-contained Pi installation using Docker Compose.
- Made NPM and camera startup tolerant of the camera not being attached yet.

## v0.1 – Initial Test Build
**Date:** 11 Oct 2026, 01:10 UTC

First camera detector, recording database and browser dashboard.

- Added Raspberry Pi camera capture and basic frame-difference motion detection.
- Added saved motion events with MP4 video and preview images.
- Created the first browser dashboard and login screen.
- Added a SQLite database for events and recording metadata.
- Introduced the early Docker / Nginx Proxy Manager experiment.
- Added background services to run the camera and dashboard on boot.
- Added an initial camera-free demonstration event for browser testing.
- Included a startup health check and generated credentials for the local test system.
- Separated video files and preview thumbnails from the SQLite event index.
