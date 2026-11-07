"""Static help and per-release changelog, independent of any installed device."""
from markupsafe import escape

HELP = '<h1>Help &amp; user guide</h1>\n<p class="muted">This guide explains the entire dashboard. Choose a section, or scroll through.</p>\n<div class="panel"><div class="row">\n<a href="#overview">Dashboard</a> · <a href="#events">Recordings</a> · <a href="#recording">Camera &amp; recording</a> ·\n<a href="#timing">Operating times</a> · <a href="#storage">Storage &amp; cleanup</a> ·\n<a href="#access">Access &amp; safety</a> · <a href="#issues">Troubleshooting</a> · <a href="#investigation">Video player</a>\n</div></div>\n<section class="panel" id="overview"><h2>1. Dashboard</h2>\n<p><strong>Camera / detector:</strong> Running means the camera is searching for movement. Recording means a clip is being saved. Paused means you\'ve switched off new detections. Scheduled means it\'s outside the configured recording window. Waiting or Offline indicates the camera or service is unavailable.</p>\n<p><strong>Pause new detections:</strong> Prevents new clips but leaves the dashboard and camera preview available. An ongoing event is allowed to complete. Press Resume to return to your selected operating mode.</p>\n<p><strong>Last camera preview:</strong> The newest still image, refreshed by the camera around every 4 seconds. Select Refresh preview to update it without reloading the page. It is <em>not</em> live video.</p>\n<p><strong>Search and filter:</strong> Find saved recordings by event title or notes, and select a review status. Filter by public sharing, review status or pinned recordings. The search applies to the whole event database, not just the latest recordings. Results appear newest first.</p></section>\n<section class="panel" id="events"><h2>2. Event and recording pages</h2>\n<p>Click an event title or thumbnail to see its preview, play/download the MP4, edit the name, change the status and save your notes. Only events marked New automatically change to Viewed when opened. Manually saved statuses never change simply because you open a recording again.</p>\n<p><strong>New:</strong> not opened yet. <strong>Viewed:</strong> opened but not classified. <strong>Flagged:</strong> worth investigating. <strong>Identified:</strong> you\'ve identified the likely source. <strong>Unresolved:</strong> you couldn\'t establish an explanation. <strong>Dismissed:</strong> no longer of interest.</p>\n<p><strong>Delete event and clip:</strong> Opens a separate confirmation page. Confirming permanently removes the event, its MP4 and its thumbnail. There is no recycle bin.</p></section>\n<section class="panel" id="recording"><h2>3. Settings — Camera and recording</h2>\n<p><strong>Recording resolution:</strong> choose VGA (640 × 480), HD (1280 × 720) or Full HD (1920 × 1080). Higher resolutions may need more storage and processing power. Changing resolution restarts the camera after the current recording finishes.</p>\n<p><strong>Camera frame rate:</strong> target frames per second. Higher values can improve motion detail but make night footage darker because exposure time is shorter.</p>\n<p><strong>Pixel difference threshold:</strong> how much a pixel must change between frames before being counted (smaller means more sensitive).</p>\n<p><strong>Changed pixels to trigger:</strong> number of changed pixels needed for motion; smaller detects more subtle movement but also more camera noise, insects and clouds.</p>\n<p><strong>Seconds before motion:</strong> aims to preserve footage before the trigger from a rolling camera buffer. Exact lead-in can vary.</p>\n<p><strong>Seconds after motion:</strong> the quiet tail after movement stops. <strong>Maximum clip length:</strong> long events are split into further clips rather than cut short.</p>\n<p>Reset to defaults in Camera and recording loads that section’s values in the form; press Save settings to apply. The frame-rate choices still depend on the detected camera hardware. Camera changes apply after the current event finishes. Detected motion does not prove an object is unidentified.</p></section>\n<section class="panel" id="timing"><h2>4. Settings — When to detect</h2>\n<p><strong>Continuous:</strong> detect all day and night. <strong>Scheduled hours:</strong> detect only between the entered start and end times (including overnight, e.g. 20:00–06:00). <strong>Sunset to sunrise:</strong> calculate the recording window automatically for every date, based on the detector\'s coordinates and time zone.</p>\n<p><strong>Location label:</strong> optional friendly name. <strong>Latitude and longitude:</strong> position of the <em>detector</em> in decimal degrees (latitude north positive, longitude east positive). <strong>Timezone:</strong> an IANA timezone, e.g. Europe/London, accounting automatically for daylight saving.</p>\n<p><strong>Use this device\'s location:</strong> may fill the position and timezone automatically if your browser permits. Only use it when you are physically at the detector, otherwise you\'ll set the wrong location. You can always type the values yourself. Neither the detection service nor the solar calculations require an online location API.</p>\n<p><strong>Pause:</strong> overrides every schedule. Resume returns to continuous/timed/sunset mode, rather than turning on 24-hour monitoring.</p>\n<p>Sunrise/sunset calculations are approximate (usually within a few minutes). Very high latitudes can have days without an ordinary sunrise or sunset; in that case detection stays off until you choose another mode.</p></section>\n<section class="panel" id="storage"><h2>5. Settings — Storage and cleanup</h2>\n<p>Storage overview shows used recording space, free disk capacity, total events and protected items. Automatic cleanup defaults <strong>OFF</strong>. If enabled, a daily task may permanently delete events after your chosen retention period.</p>\n<p><strong>New:</strong> aged from recording time. <strong>Viewed:</strong> aged from the first time opened. <strong>Dismissed:</strong> aged from recording time. <strong>Flagged, Identified and Unresolved:</strong> protected and never deleted by automatic cleanup.</p>\n<p><strong>Maximum video storage:</strong> optional <em>soft</em> cap. When cleanup is enabled, older unprotected recordings may be deleted even before their normal age. Protected or actively recording clips can exceed the cap, so monitor free storage and consider an SSD for heavy usage.</p></section>\n<section class="panel" id="access"><h2>6. Sign-in, remote access and privacy</h2>\n<p>The web dashboard requires a login. Use HTTPS for access from outside your home and place it behind a trusted reverse proxy and access policy. Do not publish the NPM admin panel or the Pi\'s management ports. Only administrators can optionally configure Cloudflare DNS and a locally managed NPM/Tunnel from Network Setup. Router forwarding rules must still be configured in the router itself.</p>\n<p>Clips and event notes are stored on your own detector. Internet outages do not stop local motion detection; however remote viewing is unavailable until the network returns.</p></section>\n<section class="panel" id="issues"><h2>7. Troubleshooting</h2>\n<p><strong>Waiting for camera:</strong> confirm the ribbon cable is seated correctly, the camera is listed by <code>rpicam-hello --list-cameras</code>, and the power supply is adequate.</p>\n<p><strong>Recording too often:</strong> increase Changed pixels to trigger or Pixel difference threshold. <strong>Missing motion:</strong> try lowering those values. Outdoors, retest at night; daytime settings often won\'t work well for distant, dim lights.</p>\n<p><strong>No new clips:</strong> check whether the detector is Paused or outside Scheduled hours/Sunset mode. <strong>Empty preview:</strong> refresh once a camera has started; a new still is captured around every eight seconds.</p>\n<p><strong>Storage filling:</strong> review protected clips and the cleanup settings. Auto-cleanup is deliberately conservative and cannot guarantee free disk space.</p>\n<p>See <a href="{{ url_for(\'history\') }}">Version history</a> for changes between builds.</p></section>'
HELP += """<section class='panel' id='protection'><h2>8. Pinned recordings</h2><p>On an event page choose Pin recording to protect it against automatic deletion even if it is still New, Viewed or Dismissed. A pinned event cannot be manually deleted until you explicitly unpin it. You can display only pinned recordings using the filter on Dashboard. Flagged, Identified and Unresolved are already protected from automatic cleanup by review status.</p></section><section class='panel' id='system'><h2>9. System health</h2><p>System health shows remaining disk space, memory availability, CPU temperature, uptime, snapshot freshness and the detector service heartbeat. It is a read-only diagnostic view. A stale heartbeat means the detector may have stopped even if the web dashboard still responds. Sensor readings may be unavailable on some hardware.</p><p>Version history provides an expandable list of changes made in each software release.</p></section>"""

HELP += """<section class='panel' id='investigation'><h2>10. Video investigation player</h2>
<p>Open a saved event and use the Video investigation controls below its preview. Use Play / Pause, the timeline, previous/next frame buttons and the playback-speed selector (0.25× to 2×) to examine movement.</p>
<p><strong>Frame buttons:</strong> pause playback and seek backward/forward by approximately one video frame using the recorded frame rate. MP4 keyframes, variable frame timing and the browser decoder mean single-frame seeking cannot be guaranteed to be exact.</p>
<p><strong>Zoom and pan:</strong> adjust the Zoom slider (up to 4×), then drag the enlarged picture with a mouse, finger or trackpad. Select Reset image to return to the normal view.</p>
<p><strong>Brightness and contrast:</strong> adjust the sliders to make details easier to see. These controls do not recover details that were not captured by the sensor. Fullscreen expands the investigation area.</p>
<p><strong>Save current frame PNG:</strong> produces a full-resolution image of the paused frame with brightness and contrast applied. The exported PNG uses the original frame area, even when zoomed in on screen. The original MP4 is never modified. Download original MP4 always retrieves the unaltered recording.</p>
<p>The player runs in your browser and does not change the detector's current motion-recording speed or camera configuration.</p></section>"""

HELP += """<section class='panel' id='sky-lights'><h2>11. Moving sky lights</h2><p>Under Settings → Detection profile, choose General motion, Moving sky lights, or Combined. General motion uses differences between frames. Moving sky lights tracks compact bright points across multiple frames. Combined runs both detectors and starts one clip if either detects movement.</p><p>Choose a minimum brightness, size range, how many frames must confirm motion and minimum movement per frame. Sky-light controls apply to Moving sky lights and Combined. These values refer to the reduced analysis image, not to the resolution of the saved MP4. Very faint points, rapid streaks or diffuse phenomena may not be detected. Make short nighttime tests and return to General motion if needed. The detector does not identify aircraft, satellites or other sources.</p><p>Public clips display observation notes only when the administrator explicitly selects Show my saved notes beside this public video. Notes on previously shared events remain private until selected.</p></section>"""

# Changelog is bundled with each release; all sites see the same entries.
RELEASES = [
  {'version':'1.0.0','title':'First Public Stable Release','date':'7 Nov 2026',
   'summary':'First public stable release of Moon Cheese UAP Detector, built on the Raspberry Pi-tested v0.9.9.5.3 baseline.',
   'details':[
     'Prepared the complete public installation, update and same-version repair release with versioned GitHub archive and checksum verification.',
     'Retained the tested anonymous one-line GitHub bootstrap, now selecting the latest stable version without a prerelease flag or personal access token.',
     'Retained password-protected Update and Repair, separately password-free Check for updates, and clear inline validation messages.',
     'Kept Information → About Moon Cheese with the approved first-person biography, official artwork and accessible linked icon cards.',
     'Published corresponding application source and licensing notices for GitHub under GPLv3; preserved all earlier release notes and their original dates.',
     'Preserved the installed camera and detector, recording and investigation tools, Scheduled Video, Time-lapse Studio, photographs, user data, account passwords, backups and networking.',
     'The installer continues supporting fresh installation, safe upgrades and same-version repair. Actual v1.0.0 stable-channel upgrade/repair requires final Raspberry Pi acceptance after publication.'
   ]},
  {'version':'0.9.9.5.3','title':'Administrator Update Confirmation and About Page Redesign','date':'7 Nov 2026',
   'summary':'Protect software installation actions with administrator password confirmation and improve the About page and release documentation.',
   'details':[
     'Added one password field in the permanently visible Software updates panel. Check for updates still needs no password; Update now and Repair current version verify the signed-in administrator’s current password on the server before queuing work.',
     'Show missing or incorrect password errors inside the Software updates panel; no privileged operation is requested when verification fails.',
     'Redesigned Information → About Moon Cheese using the existing official 512px artwork, a responsive project description, and the approved five-paragraph first-person About Me text.',
     'Added responsive Creator & Project, Socials, Music and Support link cards using lightweight local SVG icons and readable, underlined service labels.',
     'Kept the exact Transparent-Aluminium.net business name, official project GitHub repository and all approved creator, music, shop and donation destinations.',
     'Corrected outdated Help and System Administration wording for the functioning GitHub update/repair system, and documented the admin password requirement and About page.',
     'Retained latest-open and older-collapsed Version History behaviour, all prior changelog entries, clean packaging with internal SHA256SUMS and the existing full upgrade/repair installer.',
     'Preserved the detector, photos, scheduled video, time-lapse, user accounts, saved media, networking, credentials and private GitHub testing functionality.'
   ]},
  {'version':'0.9.9.5.2','title':'Private GitHub Update and Repair Verification','date':'7 Nov 2026',
   'summary':'Enables controlled verification of real GitHub downloads, updates and repairs while the repository remains private.',
   'details':[
     'Corrected archive permissions rejected by the privileged software updater.',
     'Added root-only, read-only GitHub credential setup for a temporary private prerelease test channel.',
     'Allows private prerelease detection and download via the authenticated official GitHub API.',
     'Provides a one-time test command to update an existing v0.9.9.5.1 installation directly to v0.9.9.5.2 from GitHub.',
     'Keeps the normal stable public channel unchanged when testing access is disabled.',
     'Retained application, recorder, networking, icon and user-data management functionality.'
    ]},
  {'version':'0.9.9.5.1','title':'Release Package Cleanup and Software Updates Layout','date':'7 Nov 2026',
   'summary':'Separate Software updates from System power and prepare a lean end-user release archive.',
   'details':[
    'Moved Check for updates, Update now and Repair current version into a dedicated, permanently visible System Health panel.',
    'Kept System power in its own panel without modifying the existing reboot and shutdown controls.',
    'Excluded development test suites and test reports from the installation archive.',
    'Removed the unused original high-resolution artwork; retained the optimised favicon, Home Screen and application icon assets.',
    'Preserved the required internal checksum manifest and all application, service and installer components.',
    'Preserved the Wi-Fi radio and video fullscreen fixes verified on the reference device.'
   ]},
  {'version':'0.9.9.5','title':'Production Preparation: GitHub Updates, Branding, Installer and Player Corrections','date':'7 Nov 2026',
   'summary':'Official Moon Cheese icon and About page, Wi-Fi selection fix, fullscreen media, installer and GitHub integration.',
   'details':[
    'Preserved an unsaved Wi-Fi radio selection while live interface status continues polling.',
    'Changed investigation fullscreen to focus on the video or paused frame instead of stretching the whole control panel.',
    'Added the official Moon Cheese favicon, Home Screen icons and web app manifest.',
    'Added Information → About Moon Cheese with project details and creator links.',
    'Prepared GitHub release integration, update checking, controlled upgrades and same-version repair in System Health.',
    'Moved final installer access and credentials information after all optional installation steps.',
    'Replaced the Pi 4-only installer guard with hardware detection and experimental low-resource defaults.',
    'Continued to preserve all existing recordings, credentials, network settings and detector features.'
   ]},
  {'version':'0.9.9.4.13','title':'Cloudflare Connector Installation, Managed Tunnel Cleanup and Help Organisation','date':'31 Oct 2026',
   'summary':'Fix automatic Cloudflare connector installation, safely retire superseded managed Tunnels, improve setup errors and organise the complete Help guide.',
   'details':[
     'Replace the Python urllib signing-key request rejected by Cloudflare with the official cloudflared Debian release download route successfully tested on the ARM64 device. Select arm64, armhf or amd64 from dpkg, validate the Debian package name and architecture, install and verify the executable. No shell script is piped from the internet.',
     'After a new managed Tunnel connector is verified active, attempt to retire only the explicitly saved previous Moon Cheese Tunnel and its matching DNS record. Verify Cloudflare reports the predecessor inactive and confirm deletion by read-back; never delete an unrelated or still-active Tunnel. Keep the new connection and saved cleanup metadata if safe deletion cannot be completed.',
     'Make installer failures and the last Tunnel setup stage visible to the administrator in the Tunnel result, without exposing API credentials or connector tokens. Preserve local-only access, NPM certificates and dynamic DNS during Tunnel operations.',
     'Reorganise all 226 existing Help topics into application-aligned navigation: Getting started, Dashboard, Observations, Administration and Information. Place Network and remote access within Administration, consolidate appended network chapters, and keep existing topic anchors and search functionality.',
     'Update outdated Help instructions for NPM, Cloudflare Tunnel, profile reuse and install/repair. Maintain the Moon Cheese visual style, collapsed settings, administrator permissions and every historical Version History entry.',
     'Preserve core camera, event recording, photography, scheduled video, time-lapse, storage, notifications, PNG exports, NPM/SSL/DDNS and existing NetworkManager IP rollback logic. Hardware and public HTTPS acceptance remain separate from simulated testing.'
   ]},
  {'version':'0.9.9.4.12','title':'Simplified NPM and Cloudflare Tunnel Setup','date':'31 Oct 2026',
   'summary':'One-button network setup and updates, with secure saved settings and automatic recovery of verified Moon Cheese resources.',
   'details':[
     'Replace the multiple NPM and Cloudflare Tunnel setup checkboxes and separate hostname approval workflow with a straightforward administrator-authenticated Set up / Update action. Existing non-secret settings are displayed, and saved Cloudflare API tokens can be reused for the same authorised account or zone without exposing them in the browser.',
     'Keep separate, root-protected NPM and Tunnel profiles so switching to Local network only or between remote-access methods does not discard completed configuration or credentials.',
     'Automatically find and resume eligible unfinished Moon Cheese Tunnels. When an existing Tunnel CNAME points at a deleted Tunnel or a verified inactive Moon Cheese predecessor, correct only that selected hostname. Protect unrelated A/AAAA records and active or unrelated Tunnels.',
     'Allow the administrator to change the managed Tunnel hostname through the same setup form; verify a replacement connector before retiring the working connector. Preserve unrelated Cloudflare resources and the independent managed NPM SSL/DDNS path.',
     'Keep destructive Disable / Remove Tunnel controls distinct from setup. Require administrator authentication and verify provider-side deletion before reporting successful removal.',
     'Preserve the established appearance, collapsible sections, user permissions, camera/recordings, scheduled videos, time-lapses, notifications, direct PNG downloads, Storage Management and existing network-address confirmation mechanisms.',
     'Full fresh-install, upgrade and repair distribution. Real Cloudflare API, connector installation, public HTTPS and hostname migration remain to be tested on Raspberry Pi hardware.'
   ]},
  {'version':'0.9.9.4.11','title':'Tunnel Recovery, IP Visibility and Release History','date':'30 Oct 2026',
   'summary':'Verified Tunnel cleanup and recovery, improved DHCP confirmation and live LAN interfaces, repaired release notes.',
   'details':[
     'Preflight Cloudflare Tunnel DNS records before creating new provider resources. Recover exact matching unfinished tunnels, and offer explicit cleanup of verified owned unfinished resources without modifying unrelated DNS records.',
     'Require Cloudflare API verification before reporting Tunnel removal successful; preserve progress for retry if Cloudflare still lists the tunnel or its exact DNS record.',
     'Display live Ethernet and Wi-Fi addresses in Local network only; show the selected interface address and DHCP/static mode in advanced IP management, hiding Docker virtual adapters.',
     'Update interface details in the existing administrator-only polling endpoint. Provide clear DHCP confirmation and alternative local-access instructions when the original connection cannot refresh.',
     'Restore the v0.9.9.4.10 release notes and summary to the existing newest-open Version History page. Preserve all prior entries, styling and working detector, NPM, SSL, DDNS, PNG download and hardware-aware camera defaults.'
   ]},
  {'version':'0.9.9.4.10','title':'Cloudflare Tunnel Management and Live Network Confirmation','date':'30 Oct 2026',
   'summary':'Cloudflare Tunnel controls for recovery, disabling, removal and hostname changes, with improved original-page IP confirmation.',
   'details':[
    'Added administrator-only Cloudflare Tunnel status, unfinished-setup abandonment, managed Tunnel disable/remove and explicitly authorised hostname changes. A replacement connector is checked separately before replacing the working connector; unrelated Cloudflare tunnels are protected.',
    'Show the configured Tunnel hostname and non-secret identifiers in Network Setup. Retain account/zone and saved credentials across upgrades; never reveal connector tokens.',
    'For IP changes, expose the expected static-IP confirmation address before applying the change, improve live polling and recovery messages, and retain the server-controlled rollback and login confirmation.',
    'Preserved the verified NPM/SSL/DDNS, camera and recording, PNG download, time-lapse, scheduled jobs, storage and notification features, styling and complete installation package.',
    'Live Cloudflare API, connector failover, public HTTPS and changing the only network interface require supervised testing on a Pi.'
   ]},
  {'version':'0.9.9.4.9','title':'Tunnel Recovery, IP Confirmation and Camera Defaults','date':'30 Oct 2026',
   'summary':'Recover unfinished Cloudflare Tunnels, improve IP confirmation, restore direct PNG downloads, and add hardware-aware camera reset.',
   'details':[
     'Accept Base64-padded Cloudflare connector tokens and keep a protected progress record immediately after tunnel creation. Recover a legacy incomplete tunnel only with explicit consent and exact hostname, route, DNS and inactive-status verification.',
     'Start the local cloudflared connector and verify that Cloudflare reports an active tunnel before reporting success. Do not change unrelated tunnels or externally managed NPM.',
     'Replace temporary about:blank IP-change popups with a permanent new-IP confirmation link in the original section, including when reconnecting from a public HTTPS domain. Preserve direct administrator-login confirmation and a deadline derived from server time.',
     'After a confirmed address change, update a managed NPM proxy target only when it points to the interface address that actually changed; do not alter an unaffected Ethernet target.',
     'Restore direct PNG downloads in Detection, Scheduled Video and Time-lapse viewers, including comparison mode; do not call the operating-system share API.',
     'Add a Reset to defaults button inside Camera and recording. Hardware-supported frame-rate choices remain unchanged; reset loads section-only values into the form and requires the existing Save settings action.',
     'Preserve the complete existing interface, user permissions, media, notifications, storage, schedules, historical changelog and full install/upgrade/repair packaging. Cloudflare and rollback remain subject to live Pi verification.'
   ]},
  {'version':'0.9.9.4.8','title':'Managed Domain Changes and IP Confirmation Recovery','date':'22 Oct 2026',
   'summary':'Safely change a managed NPM hostname without overwriting the active domain; improve IP rollback verification and CSP-compatible confirmation timers.',
   'details':[
     'Preview and authorise a managed NPM + Cloudflare domain replacement without disturbing the working hostname before verification.',
     'Preserve old certificates and DNS entries; optional explicit disabling of the former managed proxy after successful replacement.',
     'Moved the confirmation countdown to a CSP-compliant script and improved server-clock countdown and recovery messages.',
     'Verify automatic network restoration before clearing pending recovery details; maintain independent timer and admin-only controls.',
     'Full fresh-install, upgrade and repair package; live rollback and public HTTPS need controlled Pi testing.'
   ]},
  {'version':'0.9.9.4.7','title':'NPM UTC Certificate Expiry Compatibility','date':'22 Oct 2026',
   'summary':'Correct NPM 2.16 certificate expiry validation so already issued, unassigned Cloudflare certificates can be recovered for the selected hostname.',
   'details':[
     'Recognise the actual NPM 2.16 certificate expiry format, YYYY-MM-DD HH:MM:SS, as UTC rather than incorrectly rejecting it for lacking an explicit timezone.',
     'Continue to accept timezone-qualified ISO 8601 expiry values and reject malformed or expired certificates.',
     'Preserve exact-hostname matching, Cloudflare DNS-challenge checks, unused-certificate protection and explicit administrator authorisation for recovery.',
     'Retain disabled-host recovery: assign the verified certificate, apply Force SSL and the Cloudflare Access List, enable the proxy, and read back the saved configuration before reporting success.',
     'Add a full mocked NPM recovery regression using the real database timestamp format, alongside timestamp and certificate-safety edge-case tests.',
     'Preserve existing Moon Cheese appearance, camera capture, recordings, time-lapses, notifications, network administration and direct IP-change login confirmation.',
     'Deliver complete fresh-install, upgrade and repair files; live SSL and public HTTPS still require verification on supported hardware.'
   ]},
  {'version':'0.9.9.4.6','title':'NPM Existing-Certificate Recovery and DNS State Repair','date':'22 Oct 2026',
   'changes':[
      'Recover unused exact-hostname Let’s Encrypt / Cloudflare certificates NPM already issued when an earlier Moon Cheese request timed out or had incomplete ownership metadata; require explicit consent for untracked certificates.',
      'Never adopt a certificate for another hostname, an expired certificate, a certificate in use by another proxy, or a certificate issued through an unexpected provider. Never delete existing certificates automatically.',
      'Reconnect to an explicitly authorised, disabled existing Moon Cheese proxy after an interrupted setup, without duplicating it or touching unrelated active proxies.',
      'Assign the verified certificate, enable Force SSL and the managed proxy only after read-back validation. Existing Cloudflare A-record approval and Access List remain unchanged.',
      'Report stale DDNS record IDs as requiring a fresh authorised setup; keep previously recorded network events labelled as historical results.',
      'Preserve the original styling, controls and camera/recording/storage modules. Full-source fresh-install/upgrade/repair release.'
   ]},
  {'version':'0.9.9.4.5','title':'Let’s Encrypt Wait and Recovery; Direct IP Confirmation','date':'22 Oct 2026',
   'summary':'Extended NPM certificate waiting, resumed late Certbot success safely and routed new-IP administrator logins directly to confirmation.',
   'details':[
     'Fixed the 90-second NPM certificate API timeout being shorter than its configured 120-second Cloudflare DNS propagation wait. The new wait accommodates propagation and subsequent ACME verification.',
     'If NPM finishes a certificate request after an HTTP timeout, inspect the registered certificates and recover the matching Moon Cheese certificate instead of issuing duplicates.',
     'Reopen an unfinished Moon Cheese proxy host, verify its registered certificate, assign it, activate Force SSL and enable the proxy host. Verify NPM reports the expected settings before marking the setup complete.',
     'Do not take over unrelated certificates or automatically enable an HTTP-only proxy when SSL cannot be verified; keep partial setups disabled and report a precise result.',
     'After a network address change, an administrator signing in through the pending new IP is sent straight to the confirmation page, without navigating System Administration. Existing authentication and original-address rollback protection remain in effect.',
     'Preserved the existing Moon Cheese styling, collapsible interface, notifications, camera and recording modules, DDNS, Wi-Fi management, historical versions and full installation/upgrade/repair distribution.',
     'Offline tests include successful recovery of a late issued certificate and final NPM host state. Actual HTTPS online status and login redirect still require supervised Raspberry Pi acceptance testing.'
   ]},
  {'version':'0.9.9.4.4','title':'Network Form Submission Routing Repair','date':'22 Oct 2026',
   'summary':'Corrected browser HTTP 404 failures shared by NPM/Cloudflare, DDNS, Wi-Fi and IP-change forms.',
   'details':[
     'Fixed the browser form.action property being shadowed by a hidden form field called action, causing network requests to be sent to an incorrect URL and return HTTP 404.',
     'Both the standard network operations and the IP-address change workflow now read the actual form action attribute, require the exact same-origin action endpoint, rejecting unexpected destinations.',
     'Added a real Chromium browser regression test that renders the actual Network Setup template and verifies that NPM, DDNS, Wi-Fi and IP-change requests POST to /system/network/action.',
     'Kept all network results inside their own expanded sections, retained the Let’s Encrypt contact email and explicit DNS adoption controls, and preserved administrator-only server endpoints.',
     'Preserved original camera, photography, recorder, time-lapse, notifications, shared styles, existing proxy configuration and historical changelog.',
     'Browser request routing can be verified offline; real NPM, Cloudflare, Wi-Fi and IP-change outcomes are still pending Raspberry Pi integration tests.'
   ]},
  {'version':'0.9.9.4.3','title':'Networking Error Feedback and NPM Setup Repairs','date':'22 Oct 2026',
   'summary':'Focused corrections for rejected networking forms, Let’s Encrypt contact handling, unfinished NPM hostname selection and per-panel results.',
   'details':[
     'Restored a Let’s Encrypt contact-email field to the local NPM configuration wizard and added separately authorised synchronization with the local NPM administrator email, without sending deprecated certificate metadata.',
     'Added explicit approval to move from an unfinished previous Moon Cheese hostname without silently modifying or deleting a functioning proxy host, certificate or unrelated DNS record.',
     'Moved NPM, DDNS, Tunnel, local network, Wi-Fi and IP change feedback inside the corresponding collapsible Network Setup sections; removed the global network notification pile-up.',
     'Made rejected administrator requests report specific errors for expired security tokens, incorrect credentials and validation, instead of a generic request-rejected response.',
     'Preserved independent per-action result timestamps, Wi-Fi scanning and radio controls, the address-change rollback mechanism, shared styling and the original camera/recording modules.',
     'This remains an offline-tested correction build. Real NPM, Cloudflare, Wi-Fi and IP-change acceptance tests on a Raspberry Pi are required before claiming success.'
   ]},
  {'version':'0.9.9.4.2','title':'Network Provisioning Compatibility and Status Corrections','date':'22 Oct 2026',
   'summary':'Corrected NPM 2.16 certificate API compatibility and incomplete-hostname retry, improved Wi-Fi verification, IP change feedback and compact network diagnostics.',
   'details':[
     'Removed obsolete Let’s Encrypt certificate metadata rejected by the bundled NPM 2.16 API, while retaining its supported Cloudflare DNS-challenge settings.',
     'Recovered from prior incomplete NPM setup states so a different explicitly chosen test hostname is not blocked by an abandoned configuration without an active proxy or certificate.',
     'Applied Cloudflare DNS and enabled five-minute DDNS independently of certificate issuance; each step preserves its recorded outcome and only edits the explicitly approved hostname.',
     'Created the locally managed proxy host initially disabled, and enabled it only after successful certificate provisioning, to prevent an incomplete HTTP-only public site.',
     'Added safe API error information and progress stages without exposing Cloudflare tokens, Wi-Fi passwords or NPM authentication details.',
     'Replaced accumulating network operation messages with one latest-result display and collapsed previous-activity section; added automatic polling for newly queued actions.',
     'Improved Wi-Fi radio state detection, delayed scan updates and direct selection of scanned networks; extended Wi-Fi connection verification and timeout.',
     'Improved IP-change request correlation and rejection messages so the old-page countdown does not falsely start when an operation has been refused.',
     'Preserved existing application CSS, all camera, recordings, scheduled-video and time-lapse code, notifications, account permissions, version history and complete install/upgrade/repair packaging.',
     'This is an offline-tested correction build. Real certificate issuance, NetworkManager changes and rollback still require supervised acceptance testing.'
   ]},
  {'version':'0.9.9.4.1','title':'Network Corrections and Wi-Fi Administration','date':'22 Oct 2026',
   'summary':'Corrected existing Cloudflare DNS adoption and DDNS feedback, strengthened actual IP-change checks and rollback, and added Wi-Fi tools.',
   'details':[
     'Enabled explicit administrator-authorised adoption of the detector hostname’s existing Cloudflare A record, while preserving unrelated records and proxy status.',
     'Separated DDNS, NPM, Tunnel, Wi-Fi and IP-change status history; DDNS now returns a definite inactive, updated, up-to-date or error outcome.',
     'Allowed retrying local NPM provisioning after partial failures by saving its own provisioned resource IDs, without modifying unrelated proxy hosts.',
     'Verified selected Ethernet or Wi-Fi connection details and live IPv4 changes before prompting for confirmation; added persistent boot-aware network rollback timer.',
     'Added administrator Wi-Fi radio controls, wireless scanning, saved personal-network connection setup, and detection of multiple physical network interfaces.',
     'Improved the original-page countdown, new-address link, recovery status and administrator confirmation workflow.',
     'Preserved non-secret NPM form entries when the page reloads; improved the existing record adoption instructions and DDNS terminology.',
     'Retained the original Moon Cheese styling, collapsible settings, latest-version-expanded changelog, detector/camera code, account roles and notification deduplication.',
     'Distributed full install/upgrade/repair application and systemd units; new network functions still require live Raspberry Pi acceptance testing.'
   ]},
  {'version':'0.9.9.4','title':'Network Setup and Notification Reliability','date':'22 Oct 2026',
   'summary':'Complete package with admin-only network setup, Cloudflare DDNS, local NPM or Tunnel paths, safe IP rollback and duplicate-summary protection.',
   'details':[
     'Fixed duplicate daily/weekly observation summaries, email and Web Push regeneration after a summary was deleted by retaining an independent per-user reporting ledger.',
     'Completed Moon Cheese text branding in outgoing emails, notification tests, browser titles and push notifications; custom graphical icon remains deferred.',
     'Added collapsible System Administration network options for local-only, locally managed NPM with Cloudflare DNS and DNS-challenge Lets Encrypt, external proxies and optional Cloudflare Tunnel.',
     'Added a five-minute Cloudflare IPv4 DNS updater for the Moon Cheese-managed detector hostname, preserving existing proxy settings and unrelated Cloudflare records.',
     'Added separate privileged systemd networking worker, local NPM Cloudflare CIDR access list, router-forward guidance and administrator-only forms; existing external NPM remains untouched.',
     'Added a guarded Pi NetworkManager DHCP/static address workflow with the old-page countdown, new-address administrator confirmation and independent automatic 120-second rollback.',
     'Added local Raspberry Pi OS Desktop application launchers for Moon Cheese and its own NPM, using localhost so LAN address changes do not affect the links.',
     'Preserved existing camera ownership, photo/video/time-lapse recording, users, storage, gallery, notifications and shared UI styles; all earlier changelog entries retained.',
     'Included the complete source, tests, systemd service definitions and optional NPM components for fresh install, upgrade or repair; real networking workflows still require physical Pi acceptance tests.'
   ]},
  {'version':'0.9.9.3','title':'Complete Distribution and Full-Resolution Capture Repair','date':'18 Oct 2026',
   'summary':'Self-contained application distribution, restored complete Pi service/NPM installer and repaired full-resolution still capture, with updated Moon Cheese branding.',
   'details':[
     'Fixed the full-resolution Capture button HTTP 500 regression caused by a missing math import in the camera-request route.',
     'Made the photo request return actionable JSON errors for queue/filesystem failures, instead of an HTML error page causing a JSON parsing failure.',
     'Changed the main header to ✦ MOON CHEESE and the footer to Moon Cheese UAP Detector by Dr Ravanholm.',
     'Bundled every application module, background systemd service, required camera-support module, optional NPM deployment files and offline release history in one archive.',
     'Added an idempotent install-or-upgrade script that backs up configuration/database and preserves existing media, accounts, SMTP/Web Push credentials and NPM deployments.',
     'Restored the systemd Gunicorn writable runtime directory and TMPDIR override for both fresh installations and upgrades.',
     'Preserved the v0.9.9.2 correction release, its full original changelog and all preceding version-history entries.',
     'Retained the existing recording, Scheduled Video, Time-lapse Studio, unified Storage Management, notifications and public-gallery functionality.'
   ]},
  {'version':'0.9.9.2','title':'Interface and Notification Corrections','date':'16 Oct 2026',
   'summary':'Fixed SMTP save acknowledgement, smarter camera scheduling, consistent job placeholders, better email and compact controls.',
   'details':[
     'Fixed false HTTP 400 after saving SMTP or Web Push sender configuration, and tested the administrator form actions.',
     'Collapsed System Administration and Notifications settings; Notifications now opens with the actual notification centre first.',
     'Replaced absent time-lapse thumbnails with uniform 16:9 status placeholders and safe missing-image fallbacks.',
     'Reduced the early camera reservation window for still photography, while retaining active-job lockouts and exposure-aware safety checks.',
     'Rearranged the time-lapse storage estimate into the six requested positions and restricted recalculation to duration/interval changes.',
     'Improved opt-in emails with readable HTML and plain-text fallback; added trusted local/public links to relevant authenticated pages.',
     'Added 10-row diagnostic summaries, filtered paginated history, and 90-day retention for completed technical delivery records.',
     'Updated the self-contained Help chapters; existing camera recorder, Scheduled Video, Time-lapse Studio and storage tabs remain in place.'
    ]},
  {'version':'0.9.9.1','title':'Notification Delivery and Live Storage Planning','date':'16 Oct 2026',
   'summary':'Visible time-lapse disk budget, opt-in SMTP and encrypted browser Web Push, clearer configuration backups and delivery diagnostics.',
   'details':[
     'Added a live read-only storage estimate to the Time-lapse Studio scheduling form, including frame count, playback duration, current free space, measured/fallback JPEG size, temporary space and the 2 GiB scheduling reserve.',
     'Added administrator SMTP sender configuration and test delivery, with encrypted transport, local private credentials and per-user recipient email addresses.',
     'Added browser Web Push subscriptions, per-device tests and removal, and VAPID-signed encrypted push delivery using browser provider services.',
     'Added persistent notification delivery records, retry states and diagnostics. Alerts remain administrator-only; personal digest times keep independent timezone preferences.',
     'Expanded Help with full Email, Browser Push, job interruption, storage estimator and backup/import procedures and provider limitations.',
     'Documented exactly which detector settings and profiles are included in Settings Only and Settings + Users backups; excluded secrets and media remain excluded.',
     'Kept all existing Scheduled Video, Time-lapse Studio, recording, photographs and unified Storage Management pages; recorder and capture engine are unchanged.'
   ]},
  {'version':'0.9.9.0','title':'Unified Storage and System Administration','date':'16 Oct 2026',
   'summary':'One storage-management interface for all media, improved time-lapse storage planning, simpler timezone choices, backup portability and administrative foundations.',
   'details':[
      'Unified Overview, Recordings, Photographs, Scheduled Videos and Time-lapses inside the existing Storage Management page, with common search, status, visibility, sorting, pagination and protected deletion.',
      'Removed only the two duplicate storage administration menu links. Existing Scheduled Video, Time-lapse Studio, their job history and public gallery pages remain intact.',
      'Added MP4 and private source ZIP size breakdowns, downloads and ZIP-only removal to the time-lapse storage tab, with existing protection checks.',
      'Expanded whole-device disk reporting to measured detector media, Raspberry Pi software, container storage, caches, swap and backups, plus remainder.',
      'Estimated future still-photo storage from recent full-resolution JPEG archives, while maintaining the 2 GiB planning reserve and runtime low-space safeguard.',
      'Aligned contextual Help beside page headings and removed the ineffective notification-timezone search field; the selector now shows current UTC offsets.',
      'Added administrator Settings-only export/import and encrypted Settings + Users backups with import preview and merge-only account restoration.',
      'Added a System Administration foundation for network, NPM, Cloudflare, email and future updates, without enabling premature automation.',
      'Expanded contextual help for unified media storage, backup procedures, low-space decisions and supported recovery behaviour.'
   ]},
  {'version':'0.9.8.9','title':'Downloads, Help & Notification Preferences','date':'15 Oct 2026',
   'summary':'Named media downloads, comprehensive contextual help, per-user report timezones and expected camera-job alert handling.',
   'details':[
      'Generated stable, descriptive download filenames for time-lapse MP4s and private source ZIP archives using observation IDs and editable titles.',
      'Added searchable personal notification timezones and an explicit Use my browser timezone action; detector observation times remain detector-local.',
      'Updated camera-snapshot health monitoring to ignore expected snapshot pauses during an active scheduled video or time-lapse job.',
      'Added specific fault and recovery descriptions and richer notification documentation.',
      'Reorganised help into independent, detailed page chapters and added context-sensitive Help links on pages.',
      'Left camera capture, recording, MP4 rendering and ZIP generation unchanged.'
   ]},
  {'version':'0.9.8.8','title':'Local Time & Time-lapse Corrections','date':'15 Oct 2026',
   'summary':'Reliable local-time scheduling and consistent full-resolution time-lapse capture.',
   'details':[
     'Fixed Basic and Advanced time-lapse submission failures caused by invalid hidden input constraints.',
     'Both capture modes now take full-resolution stills and retain a verified source ZIP separately from Photograph Gallery.',
     'Aligned Advanced controls with Live Camera, including exposure in milliseconds, focus and white balance.',
     'Added exposure-versus-interval checks with a processing allowance and visible form errors.',
     'Uses the saved detector timezone for job scheduling; UTC is retained only for internal storage.',
     'Converted event, photo, scheduled-job, notification and public timestamps to readable local times.',
     'Handled invalid and ambiguous daylight-saving scheduling times explicitly.',
     'Added visible public counts for Scheduled Videos and Time-lapses.',
     'Preserved previous videos, photos, account data, settings and external proxy configuration.'
   ]},
  {'version':'0.9.8.7','title':'Scheduled Recording & Time-lapse Studio','date':'15 Oct 2026',
   'summary':'Camera-aware scheduled sessions, Basic/Advanced time-lapses, source ZIPs and observation management.',
   'details':[
     'Added administrator scheduling for continuous video recording and time-lapse capture, with timezone validation and conflict protection.',
     'Scheduled video saves verified five-minute MP4 segments as one session, with a playback and management page.',
     'Added Basic time-lapse using the configured video feed and Advanced time-lapse using still sensor capture.',
     'Advanced time-lapse controls include manual shutter up to hardware limits, analogue gain, focus, white balance and image adjustment.',
     'Displayed estimated source-frame count and resulting video duration from interval, session duration and output FPS.',
     'Rendered a finished MP4 and private downloadable source-photo ZIP; verified both before removing loose frames.',
     'Added a status/progress panel on Dashboard, suspended conflicting Live Camera photography and restored motion detection after jobs.',
     'Added searchable observation libraries, private media playback, titles, notes, pinning and explicit per-session public sharing.',
     'Added Scheduled Videos and Time-lapses tabs on the public page and corresponding Storage Management views.',
     'Integrated jobs into Observation Calendar and local administrator completion/failure notifications.',
     'Retained current motion detection, storm limits for motion events, camera profiles, users and networking configuration.'
   ]},
  {'version':'0.9.8.6','title':'Gallery Filters & Public Media Browsing','date':'15 Oct 2026',
   'summary':'Public and pinned photo filters, compact public media tabs and pagination, and consistent Live Camera labels.',
   'details':[
     'Added Public only and Private only filters to the three-column Photograph Gallery.',
     'Added Pinned only and Unpinned only filters, usable together with title/notes search and public sharing filters.',
     'Removed the unnecessary storage-deletion instruction from the Photograph Gallery heading.',
     'Reorganised the public observation page into Recordings and Photographs tabs.',
     'Limited public recordings to five entries per page and public photographs to six per page, with Previous/Next navigation.',
     'Retained opt-in public sharing, metadata-stripped public photographs and separate approval for public notes.',
     'Standardised Detection (grayscale) throughout the Live Camera and recorded-clip viewers.',
     'Left the detector, storm handling, camera settings, current media, accounts and networking unchanged.'
   ]},
  {'version':'0.9.8.5','title':'Gallery, Storm History & Controls','date':'15 Oct 2026',
   'summary':'Storm notifications, safer media deletion, photograph reviews, system controls and mobile Live Camera fixes.',
   'details':[
     'Added administrator-only storm activation and recovery notices, including a permanent local storm history on System Health.',
     'Rebuilt Storage Management with per-row trash buttons, multi-select, a visible selection bar and an in-place deletion confirmation.',
     'Photographs are managed in the same Storage Management interface as motion recordings; protected media is revalidated on deletion.',
     'Promoted Photograph Gallery into Observations, retained its three-column layout, and added title and notes search.',
     'Added detailed photograph pages with original downloads, editable titles and notes, pinning, and separate public photo and note permissions.',
     'Shared photographs appear on the public page as metadata-stripped reduced-resolution images only after administrator approval.',
     'Restricted System Health to administrators and added password-confirmed reboot and shutdown requests through a separate systemd helper.',
     'Reserved update status space on System Health without introducing an untested software update mechanism.',
     'Replaced unsupported Live Camera canvas filter usage with portable pixel processing for iPhone brightness, contrast and comparison.',
     'Standardised the Live Camera label to Detection (grayscale) and preserved existing recordings, camera settings and accounts.'
   ]},
  {'version':'0.9.8.4','title':'Storm Protection & Storage Management','date':'13 Oct 2026, 16:31 UTC',
   'summary':'Event-storm cooldown, bulk clip cleanup, photograph management and compact notification history.',
   'details':[
     'Added event-storm protection to prevent excessive continuous motion from generating hours of repetitive clips, including five-minute rollovers.',
     'Default circuit breaker: 10 recorded minutes in a 15-minute sliding window triggers a 15-minute cooldown; all three detector profiles are supported.',
     'When the circuit breaker trips, any current MP4 is finalised, its event is annotated, and new detections are paused while camera previews continue.',
     'Added a hard 1 GB disk-free safeguard that stops opening new recordings and saves an active clip without deleting any files.',
     'Added a dedicated administrator-only Storage Management page with clip filters, file sizes, bulk selection, deletion preview and explicit confirmation.',
     'Protected events (pinned, shared publicly, Flagged, Identified or Unresolved) remain excluded from bulk and automatic deletion.',
     'Added a photograph gallery with lazy thumbnails, original downloads, pin/unpin controls and individual deletion.',
     'Added optional photo retention and read-notification retention with independent day limits; both are off by default.',
     'Paginated notifications at ten items per page with status/category filters, individual deletion and Delete all read.',
     'Added Event-storm and retention settings to the browser interface and updated Help.',
     'Preserved existing footage, photographs, account permissions, camera profiles, remote access configuration and reporting schedules.'
   ]},
  {'version':'0.9.8.3','title':'HD Snapshot & Full Photo Comparison','date':'13 Oct 2026, 11:56 UTC',
   'summary':'Demand-driven HD Live Camera snapshots, full-resolution photo review, and processed 1080p comparison export.',
   'details':[
     'Added a separate admin-only full-size JPEG cache sourced from the active video stream without stopping detection.',
     'Kept the Dashboard and public still preview at their existing lightweight resolution.',
     'Made Live Camera save the real source resolution as PNG, up to 1920 × 1080 when recording at 1080p.',
     'Preserved split position, labels, zoom and enhancements when saving the Live Camera PNG.',
     'After a native still photograph, added Review captured photo to inspect it with the same processing controls.',
     'Enabled processed 1080p PNG exports from native full-resolution photos, while retaining the untouched full-resolution original download.',
     'Kept full-resolution photographs separate from normal video recording and restored normal capture after the still.',
     'Prevented viewer accounts and public pages from requesting or downloading admin full-resolution snapshots.',
     'Left recording settings, public sharing, accounts and notification schedules unchanged.'
   ]},
  {'version':'0.9.8.2','title':'Direct PNG Downloads & Help Reference','date':'13 Oct 2026, 11:31 UTC',
   'summary':'Direct Live Camera image downloads, clearer photograph queue errors, searchable documentation and streamlined public navigation.',
   'details':[
     'Save current view PNG now starts an ordinary image download instead of invoking the operating system sharing panel.',
     'Kept the composite image contents, comparison labels and slider position in the PNG export.',
     'Moved the administrator Public page shortcut from the top navigation into Observations; mobile navigation follows the same rule.',
     'Added a watchdog for still-photography requests that remain queued for more than 65 seconds without camera acceptance.',
     'Stalled camera requests now show a direct error and can be retried after the detector recovers, rather than remaining queued indefinitely.',
     'Long manual photo exposures are unaffected by the short queued-request watchdog after the camera accepts the job.',
     'Replaced the brief help page with grouped searchable reference documentation and jump links for individual controls.',
     'Documented the Dashboard, event review, video investigation, calendar, Live Camera, camera profiles, storage, accounts and notifications.',
     'Made documentation search run locally in the browser without sending search terms to another service.',
     'Provided troubleshooting advice for a camera that fails to accept a photo request while still protecting ongoing exposures.',
     'Retained the private administrator-only access rules on Live Camera and photograph downloads.',
     'Kept the motion recorder, detection algorithms, NPM and network configuration unchanged.'
   ]},
  {'version':'0.9.8.1','title':'Navigation & Live Camera Repair','date':'13 Oct 2026, 11:03 UTC',
   'summary':'Restored camera preview and made navigation menus stable and mutually exclusive.',
   'details':[
     'Fixed the Live Camera preview image request to comply with the dashboard content security policy.',
     'Restored interactive preview refreshing, freezing and frame comparison using the regular cached camera image.',
     'Redesigned the header as a stable two-row layout with the camera name and account tools above navigation.',
     'Changed Observations, Administration, Information and Account into floating dropdowns that do not reflow the page.',
     'Only one dropdown remains open at a time; clicking away or pressing Escape closes it.',
     'Improved compact mobile menu behaviour without changing account permissions.',
     'Left camera recording, photography capture controls, existing events and user settings unchanged.',
     'Kept preview images on the authenticated private dashboard endpoint.',
     'Preserved the existing Content Security Policy without allowing additional remote image sources.',
     'Ensured the existing cached camera preview can be reused without starting another camera pipeline.',
     'Kept the basic comparison slider and PNG export controls within the repaired Live Camera page.',
     'Made the notification bell and account menu available in the stable top header.',
     'Preserved permission-based navigation for administrator and viewer accounts.'
   ]},
  {'version':'0.9.8','title':'Navigation & Live Observation','date':'13 Oct 2026, 10:39 UTC',
   'summary':'Responsive menus, private camera photography and accurate rolling reports.',
   'details':[
     'Replaced overflowing header links with floating Observations, Administration and Information dropdown menus.',
     'Added mobile-friendly navigation that does not push page content when menus open.',
     'Added a notification bell displaying the signed-in account’s unread count.',
     'Added an optional public-page shortcut for administrators when public viewing is enabled.',
     'Added an administrator-only Live Camera page using the existing cached camera snapshot.',
     'Added ten-second refresh, Freeze/Resume, manually refreshing, zoom, brightness and contrast.',
     'Added original, detection and low-light processed views with a movable two-view comparison slider.',
     'Enabled saving the composed current live image as PNG with both comparison labels and divider.',
     'Added on-demand full native-resolution still photography without opening a second simultaneous camera owner.',
     'Added temporary camera controls for automatic/manual shutter, long exposure, analogue gain, focus, white balance and image tuning.',
     'The manual still capture request closes and saves an active video clip immediately, temporarily switches camera modes, then restores normal recording.',
     'Full-resolution stills are kept private and saved as chosen JPEG or PNG; camera profile settings are not modified.',
     'Improved iPhone PNG sharing and corrected comparison divider alignment at high zoom in the saved video player.',
     'Daily reports now cover the 24 hours ending at the selected time; weekly reports cover 168 hours.',
     'Updated report text to show the precise reporting window in the selected time zone.',
     'Left email/push delivery and external notification integrations unimplemented.'
   ]},
  {'version':'0.9.7','title':'Observation Calendar & Notification Centre','date':'13 Oct 2026, 00:14 UTC',
   'summary':'Browse recordings by day, see daily statistics, and receive private reports and health notices.',
   'details':[
     'Reserved the full video player height before public shared clips start playback to avoid layout jumps.',
     'Added an Observation Calendar with monthly recording totals and selectable dates.',
     'Added per-day recording lists, review-status totals, public and pinned counts and trigger-type breakdowns.',
     'Groups recordings by the detector time zone, including daylight-saving boundaries.',
     'Added an in-dashboard Notification Centre, with read/unread states and per-account private notices.',
     'Added Off, Daily and Weekly observation report preferences for each administrator or viewer.',
     'Added configurable report time, time zone and weekday for weekly reports.',
     'Daily reports summarise the preceding local calendar day; weekly reports summarise seven complete days.',
     'Added scheduled local report generation with one report per due date, avoiding duplicate notices after restarts.',
     'Added administrator-only notifications for detector heartbeat, camera snapshot and storage problems.',
     'Fault alerts appear once when a problem starts and again when it clears, rather than repeating on every check.',
     'No external notifications are sent in this release.',
     'Kept camera recording, user permissions, existing clips, event reviews and network configuration unchanged.'
   ]},
  {'version':'0.9.6', 'title':'Public Location & Settings Navigation', 'date':'12 Oct 2026, 23:39 UTC',
   'summary':'Cleaner settings and optional public camera location details.',
   'details':[
      'All Settings sections now begin collapsed, giving a clearer overview of configuration categories.',
      'Kept individual camera profile editors collapsed until opened for adjustment.',
      'Added an option to show the saved location name in the public camera heading, for example Sky camera - Hilltop.',
      'Kept the heading as Sky camera when the location is blank or its public display is disabled.',
      'Added a separate option for displaying precise latitude, longitude, detector time zone and camera compass bearing/elevation.',
      'Both public location permissions default to off, including for existing installations.',
      'Added a responsive, read-only camera-location summary to the public page when precise details are approved.',
      'Preserved private location data for local sunrise/sunset scheduling regardless of public visibility.',
      'Kept public playback, manually approved recordings, visitor login and camera snapshot refresh unchanged.',
      'Retained all private event data, detector profiles and original video files.',
      'No changes to reverse proxy, DNS, Docker or recording service behaviour.',
      'Updated Help with guidance on privacy choices and public location visibility.'
   ]},
  {'version':'0.9.5', 'title':'Profile Preview & Settings Layout', 'date':'12 Oct 2026, 23:18 UTC',
   'summary':'Test unsaved camera adjustments, restore profile defaults and navigate settings more easily.',
   'details':[
      'Added one-click reset to factory starting values for Day, Night, Custom 1 and Custom 2.',
      'Added temporary unsaved profile testing from Settings, without saving or activating the profile.',
      'Uses the current camera session for preview testing; no competing camera process is opened.',
      'Restores the active exposure and gain after preview and allows the recording buffer to refill.',
      'Does not interrupt an active clip and keeps test images private.',
      'Converted Settings into expandable sections with a clearer orientation layout.',
      'Made the Compare frame button shorter and aligned both view selectors.',
      'Preserved all user accounts, recordings, settings and review history.',
      'Kept test image files behind administrator authentication instead of publishing them as live camera previews.',
      'Allowed draft tests to wait for active clips rather than interrupting recordings.',
      'Added validation and useful error messages for exposures that exceed the active frame duration.',
      'Kept the chosen profile unchanged until an administrator explicitly saves the form.',
      'Updated Help with profile testing, defaults and the safer preview workflow.'
   ]},

  {'version':'0.9.4','title':'Camera Profiles & Image Orientation','date':'12 Oct 2026, 22:55 UTC',
   'summary':'Editable daylight and nighttime camera profiles, on-page colour preview and orientation setup.',
   'details':[
     'Added Automatic, Day, Night, Custom 1 and Custom 2 camera profile choices, plus automatic sunrise/sunset switching.',
     'Added configurable names for Day, Night and both Custom profiles.',
     'Added per-profile automatic or manual exposure, manual exposure duration in milliseconds and analogue gain.',
     'Added exposure compensation for automatic exposure and automatic/manual white balance with red and blue gains.',
     'Added focus options for automatic focus or infinity where camera hardware supports them.',
     'Added brightness, contrast and saturation adjustments to each camera profile.',
     'Added manual-exposure validation against the selected frame rate to prevent unsatisfiable camera settings.',
     'Added a camera image and Refresh preview button directly inside the camera profile editor.',
     'Changed camera snapshots to include colour information from the recording stream rather than greyscale detection-only frames.',
     'Added 180-degree camera rotation for new recordings, analysis frames and previews.',
     'Added compass bearing of the image top edge and camera elevation as orientation metadata for future sky mapping.',
     'Saved camera profile and orientation metadata with newly captured event recordings.',
     'Preserved existing event data and ensured manual camera changes wait for the current clip to complete.',
     'Added automatic re-selection of Day or Night camera settings after the calculated solar transition.',
     'Kept recording schedules, motion profiles, all public permissions and NPM configuration unchanged.',
     'Updated Help for camera profiles, solar exposure switching and alignment; expanded the release changelog.'
   ]},
  {'version':'0.9.3','title':'Frame Comparison & Multi-view Investigation','date':'12 Oct 2026, 16:22 UTC',
   'summary':'Compare two views of the same paused frame with a movable reveal slider.',
   'details':[
     'Added Original, Detection greyscale and Low-light enhanced playback views.',
     'Added a paused-frame comparison panel with independent Left and Right view selectors.',
     'Added a draggable image-reveal divider with persistent position while stepping through frames.',
     'Kept both views aligned by rendering them from the same decoded video frame.',
     'Automatically returns to the selected single playback view during playback.',
     'Restores frame comparison when playback pauses again.',
     'Supports PNG export of either the selected playback view or the two-sided comparison.',
     'Preserved existing frame stepping, slow motion, timeline seeking, zoom and image controls.',
     'Clarified that Low-light enhanced is image processing of the NoIR recording, not infrared-only capture.',
     'All processing runs in the browser without changing MP4 files or camera detection settings.',
     'The dashboard, recording database, accounts and public sharing settings remain unchanged.'
   ]},

  {'version':'0.9.2','title':'Hardware Awareness & Detection Attribution','date':'12 Oct 2026, 01:00 UTC',
   'summary':'Identify camera hardware, adapt recording-rate choices and show which detector triggered each new clip.',
   'details':[
     'Read the Raspberry Pi model and connected camera sensor on each device without opening a camera stream.',
     'Display detected hardware in Camera and recording settings.',
     'Keep conservative choices up to 30 fps on Raspberry Pi 4 and unidentified configurations.',
     'Expose 45 and 60 fps only as experimental choices when a Pi 5 and IMX708 camera are identified.',
     'Check frame-rate limits when saving settings and starting the camera recorder.',
     'Record whether general motion, moving bright-point tracking, or both triggered a new clip.',
     'Show trigger source on event detail pages and in the Dashboard event list.',
     'Keep existing recordings unchanged; their trigger source was not previously recorded.',
     'Confirmed viewer accounts do not automatically mark new recordings as viewed.',
     'Updated Help with detection-source and hardware capability explanations.'
   ]},
  {'version':'0.9.1','title':'Combined Detection & Public Filters','date':'12 Oct 2026, 00:41 UTC',
   'summary':'Both motion profiles together and easier management of shared recordings.',
   'details':[
     'Added Combined detection, triggering a single recording when either general motion or moving sky-light tracking detects activity.',
     'Kept General motion and Moving sky lights available as separate choices for targeted testing.',
     'Reused one recorder for simultaneous triggers, avoiding duplicate clips from two detector profiles.',
     'Added an All recordings / Public only / Private only sharing filter to Dashboard search.',
     'Added a Public label to approved recordings in the private event list.',
     'Kept sharing filters active when moving between multiple results pages.',
     'Preserved existing detector profiles, settings, recordings, public approvals and user accounts.',
     'Updated Help to explain Combined detection and the sharing filters.',
     'Kept video format and frame-rate limits unchanged; existing camera settings remain supported.'
   ]},
  {'version':'0.9','title':'Sky-Light Detection & Public Clip Notes','date':'12 Oct 2026, 00:26 UTC',
   'summary':'Experimental moving-light tracking and optional public observation notes.',
   'details':[
     'Added a choice between the established General motion detector and experimental Moving sky lights detection.',
     'Added bright-point tracking using the camera’s smaller 320 × 240 greyscale analysis frames.',
     'Required light candidates to move across multiple frames, reducing triggers from stationary stars and random flashes.',
     'Ignored oversized light regions as a first defence against large cloud movements and broad lighting changes.',
     'Added controls for minimum brightness, light area, movement and confirmation frames.',
     'Left General motion as the default; existing deployments and camera recording resolution remain unchanged.',
     'Kept the maximum H.264 recording resolution at 1920 × 1080 for Raspberry Pi 4 compatibility.',
     'Updated shared clip expansion to show the video on the left and optional notes on the right, stacking on narrow screens.',
     'Added explicit per-recording permission for sharing notes publicly; existing shared clips retain private notes by default.',
     'Preserved the no-download-link public layout, user roles, access controls, clips, schedules and review history.',
     'Updated the Help guide for both detection profiles and optional note publishing.'
   ]},
  {'version':'0.8.2','title':'Camera Naming, Resolution & Navigation','date':'12 Oct 2026, 00:15 UTC',
   'summary':'Shared camera name, recording resolution selection and consistent dashboard navigation.',
   'details':[
     'Applied the chosen camera name throughout the site, including signed-in pages and public viewing.',
     'Made Sky Camera the default name whenever the name field is left empty.',
     'Replaced the camera-name setting help text with a straightforward description for users.',
     'Added a camera resolution menu with VGA, HD and Full HD output sizes.',
     'Connected the resolution setting to the camera recorder rather than changing the display alone.',
     'Updated camera restart detection so recording resolution changes apply once the active recording is complete.',
     'Standardised the main navigation and back links to Dashboard.',
     'Updated Help for the shared camera title and new resolution options.',
     'Preserved existing camera names, user accounts, footage, notes, schedules and publishing preferences.'
   ]},
  {'version':'0.8.1','title':'Public Page Improvements','date':'11 Oct 2026, 23:57 UTC',
   'summary':'Custom visitor-facing title, expandable shared recordings and public-first landing page.',
   'details':[
     'Added an editable public site title under Settings, separate from the private dashboard title.',
     'Changed the public header to use that title instead of TEST BUILD.',
     'Changed the root address to display the public camera page for signed-out visitors when public viewing is enabled.',
     'Kept the normal login page as the landing experience when public viewing is disabled.',
     'Added a Log in button on the public header that opens the existing private sign-in page.',
     'Replaced the shared-recordings grid with a compact responsive list of titles, UTC timestamps and thumbnails.',
     'Added expandable playback for each approved recording rather than showing all players at once.',
     'Removed download links from the public page and requested that compatible browsers hide the native download control.',
     'Kept public access limited to individually approved clips, without publishing private notes or statuses.',
     'Retained all existing accounts, recordings, event settings, camera services and reverse-proxy configuration.'
   ]},
  {'version':'0.8','title':'Sharing, Accounts & Player Layout','date':'11 Oct 2026, 23:40 UTC',
   'summary':'Improved video layout, user roles and optional public sky page.',
   'details':[
     'Moved the video investigation player above the event still preview.',
     'Moved the thumbnail into the details column beneath event information.',
     'Removed the audio Unmute button; the supported camera has no microphone.',
     'Added My Account to change the login name and password with current-password confirmation.',
     'Migrated the original admin login into an account database without changing credentials.',
     'Added administrator-managed viewer and administrator user accounts.',
     'Protected recording edits, deletion, publishing, configuration and system health with server-side administrator checks.',
     'Allowed viewers to watch private event footage without automatically changing New to Viewed.',
     'Added explicit per-event approval for optional public sharing.',
     'Added an anonymous public page with a 10-second still-image refresh and explicitly shared clips.',
     'Left the public page disabled unless an administrator chooses to enable it.',
     'Excluded shared events from automatic recording cleanup.',
     'Kept existing recordings, metadata, NPM and camera services unchanged.'
   ]},
  {'version':'0.7','title':'Video Investigation Player','date':'11 Oct 2026, 23:22 UTC',
   'summary':'Slow-motion playback, frame stepping, image zoom and frame exports.',
   'details':[
     'Added a browser-based Video investigation section to saved recording pages.',
     'Added playback speed choices: 0.25×, 0.5×, 1×, 1.5× and 2×.',
     'Added previous- and next-frame seeking based on video frame rate reported by FFprobe, with a clearly indicated fallback where needed.',
     'Added a draggable timeline with precise playback time readout.',
     'Added zoom from 1× to 4×, with pointer-drag panning for enlarged footage.',
     'Added brightness and contrast adjustments to inspect dark or bright footage.',
     'Added a one-click reset for all image adjustments.',
     'Added fullscreen mode, mute controls and the ability to save a still PNG frame with adjustments applied.',
     'Kept existing playback, download, pinning, review states, notes, schedules, retention settings and access rules.',
     'Expanded the in-app Help guide with player controls and their browser-seeking limitations.',
     'Added supplied historical UTC timestamps for v0.1 and v0.2 and expanded their changelog details.',
     'Kept original MP4 files untouched: video processing and frame export happen in the browser.'
   ]},
  {'version':'0.6.1','title':'Changelog & System Health Corrections','date':'11 Oct 2026, 23:09 UTC',
   'summary':'Aligned release dates, fuller change lists and working system uptime.',
   'details':[
     'Aligned every release timestamp in a dedicated right-hand column.',
     'Expanded the changelog to describe the features introduced in each release.',
     'Added historical UTC timestamps for v0.3, v0.4 and v0.5 using the available project records.',
     'Left older dates blank where no dependable timestamp was available.',
     'Removed unnecessary explanatory text from the Version history page and Help guide.',
     'Fixed System health uptime reporting by correctly reading the first number in /proc/uptime.',
     'Preserved existing event data, saved searches, recordings, pinned flags and detector settings.'
   ]},
  {'version':'0.6','title':'Reliability & Event Protection','date':'11 Oct 2026, 22:50 UTC',
   'summary':'System health, pinned recordings and improved event management.',
   'details':[
     'Created a read-only System health page with detector heartbeat and current camera state.',
     'Added disk capacity and free-space readings, RAM information, CPU temperature and load averages.',
     'Added camera preview age and an uptime field to help diagnose unattended operation.',
     'Added manual Pin / Unpin controls to protect selected event recordings.',
     'Excluded pinned clips from both retention cleanup and the optional storage cap.',
     'Prevented manual deletion of a pinned event until it is unpinned.',
     'Added a Pinned-only event filter and pinned event count on Overview.',
     'Redesigned Version history with expandable sections for each release.',
     'Expanded the Help guide with recording protection and device health information.'
   ]},
  {'version':'0.5','title':'Scheduling & Discovery','date':'11 Oct 2026, 22:16 UTC',
   'summary':'Detector operating windows, pause controls, search and Help.',
   'details':[
     'Added Continuous mode for around-the-clock monitoring.',
     'Added Scheduled hours mode with configurable start and end times across midnight.',
     'Added Sunset to sunrise mode based on detector latitude, longitude and timezone.',
     'Made calculated sunrise and sunset times adjust for the date and daylight-saving changes.',
     'Added an optional browser location button to populate the detector coordinates.',
     'Added a Pause / Resume control that prevents new events but keeps the dashboard and camera preview available.',
     'Added searching across recorded event titles and review notes.',
     'Added a review-status filter to the event listing.',
     'Created the Help guide and the first Version history screen.',
     'Corrected the display text for the footer website link.'
   ]},
  {'version':'0.4','title':'Settings & Storage','date':'11 Oct 2026, 21:46 UTC',
   'summary':'Browser recording controls, retention policies and event review automation.',
   'details':[
     'Added a Settings page for camera frame rate and motion sensitivity.',
     'Exposed pixel-change threshold and minimum changed-pixel count.',
     'Added editable pre-motion buffer, post-motion tail and maximum clip duration.',
     'Added a Storage overview with event counts, video usage and remaining disk space.',
     'Added optional daily cleanup with configurable retention for New, Viewed and Dismissed events.',
     'Added an optional soft video-storage limit, with reviewed statuses protected.',
     'Made opening a New event automatically change it to Viewed.',
     'Preserved manually assigned Identified, Flagged, Dismissed and Unresolved states.',
     'Added an in-page Refresh preview button.',
     'Replaced the personal address in the application header and introduced project footer branding.'
   ]},
  {'version':'0.3','title':'Motion Recording Improvements','date':'11 Oct 2026, 21:18 UTC',
   'summary':'Pre-motion clips, continuous-event recording and editable event details.',
   'details':[
     'Introduced buffered video so clips can begin before motion is detected.',
     'Extended recordings while movement continues instead of always stopping at a fixed short length.',
     'Added a quiet-time tail to preserve footage immediately after motion stops.',
     'Handled unusually long continuous events by splitting them into additional clips.',
     'Enabled changing event names from the event detail page.',
     'Added review statuses and persistent free-text notes for individual recordings.',
     'Added MP4 playback and download from the event page.',
     'Added a confirmation step for permanently deleting an event, video and thumbnail.'
   ]},
  {'version':'0.2','title':'Simpler Local Access','date':'11 Oct 2026, 15:45 UTC',
   'summary':'Browser-friendly local NPM access and streamlined setup.',
   'details':[
     'Provided a normal local-network URL for the NPM administration page.',
     'Adjusted NPM network bindings to avoid opening its admin port publicly by default.',
     'Updated the installer instructions for everyday browser use.',
     'Kept the detector dashboard and NPM management interfaces separate.',
     'Provided a local dashboard URL on port 8000 and an NPM management URL on port 8181.',
     'Prepared the groundwork for a self-contained Pi installation using Docker Compose.',
     'Made NPM and camera startup tolerant of the camera not being attached yet.'
   ]},
  {'version':'0.1','title':'Initial Test Build','date':'11 Oct 2026, 01:10 UTC',
   'summary':'First camera detector, recording database and browser dashboard.',
   'details':[
     'Added Raspberry Pi camera capture and basic frame-difference motion detection.',
     'Added saved motion events with MP4 video and preview images.',
     'Created the first browser dashboard and login screen.',
     'Added a SQLite database for events and recording metadata.',
     'Introduced the early Docker / Nginx Proxy Manager experiment.',
     'Added background services to run the camera and dashboard on boot.',
     'Added an initial camera-free demonstration event for browser testing.',
     'Included a startup health check and generated credentials for the local test system.',
     'Separated video files and preview thumbnails from the SQLite event index.'
   ]},
]

# Legacy releases used the `changes` key. Normalise them for the existing
# template while keeping every original detail and the newest-open behaviour.
for _release in RELEASES:
    if 'details' not in _release and 'changes' in _release:
        _release['details']=list(_release['changes'])
    if not _release.get('summary'):
        _release['summary']='Release changes and maintenance updates.'

HISTORY = """<h1>Version history</h1>
{% for release in releases %}
<details class='panel change-item' {% if loop.first %}open{% endif %}>
<summary class='change-title'>
  <span class='release-about'><strong>v{{ release.version }} — {{ release.title }}</strong>{% if loop.first %} <span class='pill'>Current</span>{% endif %}<br><span class='note'>{{ release.summary }}</span></span>
  <span class='release-when'>{% if release.date %}{{ release.date }}{% endif %}</span>
</summary>
<div class='change-details'><h2>Changes &amp; additions</h2><ul>{% for detail in release.details %}<li>{{ detail }}</li>{% endfor %}</ul></div>
</details>
{% endfor %}"""

HELP += '''<section class="panel"><h2>Accounts and sharing</h2><p><strong>My account:</strong> change your name or password after confirming the current password.</p><p><strong>Administrators:</strong> can edit detector settings, clips, users and sharing choices. <strong>Viewers:</strong> can see private recordings, but cannot change events or controls.</p><p><strong>Public page:</strong> off by default. An administrator must turn it on in Settings and opt in to publishing each MP4 individually. The latest camera still may reveal private information. By default the public page does not display location details or unshared events. Administrators can separately allow a location name or precise coordinates/orientation in Settings. Notes require separate per-event permission. Anyone able to access /public can see the latest still and shared clips.</p></section>'''

HELP += '''<section class="panel"><h2>Public camera site</h2><p>In Settings you can choose a camera name that appears on both private and public pages. Leave it empty to use Sky Camera. When enabled, signed-out visitors opening the main site see the public camera and only the individual recordings you approved. The Log in button takes authorised users to their private dashboard.</p><p>Shared recordings appear in a collapsible list. Visitors can expand any entry and play the video. The public page does not offer a download button, but anyone who can play a video online may still be able to save or capture it. Share only footage you are comfortable distributing.</p><p>When public viewing is disabled, the main site opens the sign-in page instead.</p></section>'''

HELP += '''<section class="panel"><h2>Public location &amp; privacy</h2>
<p>Settings includes two separate options: Show location name in the public heading, and Show precise latitude, longitude, time zone and camera orientation. Both are off by default. To add a village name, enter it under When to detect, then enable the public name option. Empty locations always display Sky camera.</p>
<p>Sharing precise coordinates can identify the installation site. Only turn this on for an installation you are happy to identify publicly. These display settings never affect sunrise/sunset scheduling or privately recorded camera metadata.</p></section>'''

HELP += '''<section class="panel"><h2>Hardware and trigger information</h2><p>The detector shows the Raspberry Pi model and detected camera sensor in Settings. Frame-rate choices account for the recording encoder as well as the sensor. Higher-rate choices on Pi 5 are experimental and must be verified by playing recorded files and checking System health.</p><p>New event details show which detection method triggered the recording. A bright-point trigger means the software saw moving light in the image; it does not identify a sky object. Older events may not have trigger information.</p><p>Opening New changes it to Viewed only when an administrator opens the event. Viewer accounts do not change review status by watching recordings.</p></section>'''

HELP += """<section class='panel'><h2>Video views and frame comparison</h2><p>Open an event and choose Original, Detection (greyscale), or Low-light enhanced under Playback view. These are ways to display the same camera recording, not separate camera feeds or infrared-only images.</p><p>Pause the video and select Compare paused frame. Choose a Left view and Right view, then move the slider over the picture to reveal each side. The labels on the picture identify both views.</p><p>Frame buttons move both comparison images together and the slider stays where you left it. Playing resumes your selected single view; pausing restores the comparison if it remains enabled.</p><p>Save current frame PNG exports the frame displayed, including its processing or the slider split. All visual adjustments happen in your browser. The saved MP4 is never changed. Frame stepping is approximate and may depend on the browser.</p></section>"""

HELP += """<section class='panel' id='camera-profiles'><h2>Camera profiles and orientation</h2>
<p>Under Settings, choose Automatic, Day, Night, Custom 1, Custom 2 or automatic Day/Night switching at sunrise and sunset. All four named profiles can be edited and renamed. The automatic mode lets the camera choose exposure and gain; Night starts with a short manual exposure suitable for video and may need tuning.</p>
<p>Each profile can control exposure mode, exposure duration, analogue gain, exposure compensation (auto mode), white balance and optional colour gains, focus, brightness, contrast and saturation. Manual exposure must fit within one video frame: 30 fps permits approximately 33 ms; lower the frame rate for longer exposures. Extremely high gain increases image noise.</p>
<p>Open a profile and select Test unsaved profile to capture a temporary preview using the entered values. No settings are saved; the active exposure settings are restored afterwards. If recording is in progress, the preview waits for it to finish. New detections pause briefly during preview and while the recording buffer refills. Choose Reset to defaults to load that profile’s starting values into the form, then Save settings only when satisfied.</p>
<p>Rotate 180° turns future recorded videos, thumbnails and camera previews; it does not modify old recordings. Top of image bearing is the direction (degrees clockwise from North) pointing toward the top of the displayed image after rotation. Camera elevation is the angle from horizontal: 0° is the horizon and 90° is straight up. These are manual estimates only. Precise sky coordinates will require field-of-view and optical calibration later.</p>
<p>Day/Night camera switching and the separate detector recording schedule are independent: switching profiles does not switch motion detection on or off. Solar switching needs detector location and timezone and falls back to automatic camera exposure when ordinary sunrise or sunset cannot be calculated.</p></section>"""

HELP += """<section class='panel' id='calendar-help'><h2>Observation Calendar</h2>
<p>Choose a month and then a date to see saved recordings from that local calendar day. The breakdown shows review statuses and which detection algorithm triggered each recording. A trigger type is not a compass movement direction. Dates use the detector time zone.</p>
</section><section class='panel' id='notices-help'><h2>Notifications and observation summaries</h2>
<p>The Notification Centre is visible after sign-in. Each account can choose Off, Daily or Weekly summaries, a preferred time and time zone. Daily reports cover yesterday in that time zone; weekly reports cover the preceding seven complete dates. Reports are generated locally by the scheduled background task and appear only in that user's dashboard.</p>
<p>Important detector, camera-snapshot and storage warnings are delivered only to administrator accounts. A repeated fault is not posted on each check; recovery is shown when the problem clears. Mark a notice as read when you've reviewed it. This release does not send email or phone notifications.</p></section>"""

HELP += """<section class='panel' id='live-camera'><h2>Live Camera and full-resolution photography</h2><p>The Live Camera page is available only to administrators. Its image comes from the existing detector snapshot and automatically refreshes approximately every ten seconds. Freeze to examine the image, use zoom/brightness/contrast and compare Original, Detection or Low-light enhanced views. Save a PNG of the current view or comparison.</p><p>The Advanced photography controls are temporary. Opening them does not affect the camera. Selecting Capture full resolution cleanly ends any active recording, briefly releases the video pipeline, applies the requested shutter, gain, focus and white balance, then saves a private JPEG or PNG at the camera's native resolution. Long exposures can take more than a minute. The detector automatically restores its previously saved profile afterwards. Photographs taken during normal recording cause a gap in video coverage.</p><p>In Notifications, Daily reports cover the last 24 elapsed hours and Weekly reports cover the last 168 elapsed hours ending at the chosen delivery time. Reports remain private in the dashboard; email and push notifications are not enabled.</p></section>"""
