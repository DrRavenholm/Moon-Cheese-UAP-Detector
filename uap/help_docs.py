"""Self-contained searchable user documentation. All displayed content is authored here.

Use a left navigation for the page/feature and specific anchors for controls.
No household-specific domains, credentials or implementation secrets belong here.
"""
from html import escape
from urllib.parse import quote

# chapter -> [(heading, (name, explanation), ...)]
GUIDE = [
 ('Network Setup', [
  ('Who can configure networking', 'Only signed-in administrators can change networking, Cloudflare, NPM, IP configuration or repair settings. Viewer and public pages never expose network credentials. Open System Administration and expand Network and remote access; all subsections begin collapsed.'),
  ('Local only', 'The detector remains available at its local IP address on port 8000; no Cloudflare or router forwarding is required. The local-only selection does not delete any external DNS record or router forwarding configured outside Moon Cheese. Remove old external forwarding manually if retiring a public site.'),
  ('Reserve a router address (recommended)', 'Open the router DHCP reservation settings, find the device by its current IP or MAC, and reserve that address for the device. Moon Cheese cannot change your router. Router-based reservation is safer than assigning a fixed address in Linux.'),
  ('Configure local Nginx Proxy Manager', 'The wizard controls ONLY the local NPM container installed with Moon Cheese on the same device. Enter your Cloudflare hostname, Zone ID and narrowly scoped DNS API Token. Cloudflare displays Zone ID on the domain Overview page; create an API token under Profile → API Tokens, restricted to the detector zone (DNS Edit and Zone Read). NPM 2.16 uses its own account for certificate contact information; confirm with your Moon Cheese administrator password. If the selected hostname already has an A record, Moon Cheese can update that one authorised hostname; unrelated records are never changed. The wizard first authorises the one hostname and DDNS, creates an initially disabled NPM proxy to the local IP port 8000 and a Cloudflare IP Access List, then requests a Lets Encrypt DNS-challenge SSL certificate. Only after SSL succeeds is the proxy enabled; partial failures and their stages remain visible.'),
  ('Change an existing managed domain', 'A managed NPM hostname is not permanent. Expand Cloudflare domain + NPM on this device, change the displayed hostname and any required Cloudflare details, enter your Moon Cheese administrator password and select Set up / Update. Moon Cheese performs the protected domain-check and replacement process automatically; there is no separate checkbox or preview form. Moon Cheese keeps the working hostname and DDNS target active while preparing the new proxy. Only after NPM confirms the replacement SSL certificate, Force SSL, Access List and enabled host does it switch the managed DDNS configuration. External HTTPS must still be checked separately; a completed local NPM configuration is not proof of reachability from the internet. Old DNS records and certificates are preserved. Update the separate Notification email links → Optional HTTPS domain setting yourself after confirming the new public URL works; Moon Cheese does not silently change that link. If you later confirm the replacement HTTPS address works, use the separate Retire previous managed proxy section to disable only the former managed NPM proxy; this never deletes DNS or certificates. The existing external proxy on another machine remains untouched.'),
  ('Router port forwards', 'For the bundled local NPM port mapping, forward external TCP 80 to the device’s TCP 8080, and external TCP 443 to the device’s TCP 8443, on your router’s port-forwarding screen. Never expose Moon Cheese port 8000 or private NPM admin port 8181 publicly. Verify the actual local Docker mappings before changing the router.'),
  ('Access List and Cloudflare security', 'Moon Cheese obtains the official Cloudflare IPv4/IPv6 ranges and assigns an NPM Access List. Cloudflare IP addresses belong to many customers; this alone does not authenticate visitors or fully protect the origin. Retain strong Moon Cheese accounts and restrict direct origin access with appropriate router/firewall protections. Test external access before treating the deployment as safe.'),
  ('NPM administrator on a headless device', 'The NPM admin web interface is deliberately bound to localhost:8181 on the device even when there is no graphical desktop. Administrators can SSH-forward local port 8181 to 127.0.0.1:8181 on the Pi. Never forward port 8181 on the router. Desktop systems receive localhost app-menu launchers for the dashboard and the bundled local NPM.'),
  ('Wi-Fi controls', 'Expand Wi-Fi under Network and remote access. Select the desired Enable/Disable state, and it stays selected while you enter your password and confirmation. Select Apply to change the actual radio. Scan nearby SSIDs (results update when the background scan finishes), select a network from the displayed list or connect to a WPA Personal network. The selected network and password are processed by the protected root worker. NetworkManager stores the resulting connection. Enterprise 802.1X and hidden SSIDs need manual configuration. If Wi-Fi is your only connected interface, disabling it remotely is refused. Where possible connect Ethernet before modifying Wi-Fi.'),
  ('Dynamic Cloudflare DNS', 'For a managed NPM domain the independent systemd timer checks the public IPv4 every five minutes. The Check DDNS now button reports inactive until the selected DNS record has been authorised and configured. DDNS can run even while SSL issuance for the same hostname is still incomplete. When configured it reports updated, already correct or an actionable error. The timer checks, and patches only its own detector A record when needed. Zone ID and scoped API token remain private and are excluded from backup exports. It preserves the existing Cloudflare proxy flag. If your ISP uses CGNAT or disallows forwarding, choose Cloudflare Tunnel instead.'),
  ('Cloudflare Tunnel', 'This is an alternative to NPM and requires no inbound router forwarding or DDNS. Enter the Cloudflare Account ID, Zone ID and a restricted API token with DNS Edit, Zone Read and Tunnel Edit for the selected account. The wizard configures a tunnel to http://127.0.0.1:8000, installs the official Cloudflare Debian package for the device architecture, and checks for an active Cloudflare connector. If an earlier attempt left a partial Tunnel or orphaned Tunnel CNAME, Moon Cheese checks whether it belongs to a verified inactive Moon Cheese setup and automatically resumes or corrects that exact hostname; it will not overwrite an unrelated active service. No recovery checkbox is needed. Never share the connector token; it is stored as a root-protected secret. A public tunnel still needs Moon Cheese sign-in. The existing NPM setup remains separate.'),
  ('Existing proxy on another device', 'Configure your external NPM or other reverse proxy on that device. Moon Cheese will not log into, update or restart it. Put the HTTPS URL in System Administration → Notification email links → Optional HTTPS domain. Changes to the external proxy remain your responsibility.'),
  ('Advanced DHCP or static address', 'The device uses NetworkManager to change DHCP to static, static to DHCP or static to a different address. Select the active Ethernet or Wi-Fi interface. The original browser tab waits for verification and then shows the countdown while a separate recovery timer watches the confirmed deadline, even after reboot; a new tab should open the new LAN address. Sign in as an administrator at the NEW address and confirm with your password within 120 seconds. An independent systemd unit restores old settings when there is no confirmation. Browser JavaScript cannot disable this rollback. You should have physical access during your first test.'),
  ('Confirming an IP change', 'The original Network Setup panel displays a permanent full link to http://NEW-IP:8000/system/network/confirm as soon as the new address is verified. Open it in a new tab. When browsing from a public HTTPS domain, your browser may block automatic navigation to local HTTP; copy and paste the displayed full address if needed. Sign in as administrator at the new address and select Keep new IP before the deadline. The recovery timer runs on the device even with all browser tabs closed. After a confirmed change, only a managed NPM proxy that points to the changed interface IP is updated; other interface targets are left unchanged.'),
  ('After a LAN address change', 'If NPM forwards to the old LAN IP or router rules use it, update those settings. Cloudflare Tunnel uses localhost and usually needs no destination change. When the new IP is unknown after switching to DHCP, consult the routers device list or wait for the old address to return.'),
  ('Troubleshooting external HTTPS', 'Inspect the latest network result and collapsed activity log in System Administration. Confirm Cloudflare zone/token permissions, hostname ownership, local NPM availability and the SSL certificate step; partial setups leave the host disabled until a valid certificate is issued. A successful API response is not proof of public connectivity. A broken HTTPS setup must not disable local dashboard access.'),
 ]),
 ('Getting started', [
  ('What the detector does', 'It watches a camera image for changes or moving bright points, automatically saves MP4 clips and lets you review them. Detection is not identification: an event may be an aircraft, animal, reflection or camera noise.'),
  ('Sign in', 'Open your private site, select Log in if the public page is shown, and enter the account details supplied by the administrator. The Dashboard is the starting page after login.'),
  ('Moving around', 'Dashboard is always available. Observations holds recordings, Calendar and (for administrators) Live Camera. Administration holds settings, accounts and health. Information contains Help, Version History and About Moon Cheese.'),
  ('Permissions', 'Administrators control recording, events, public sharing, camera photography and settings. Viewer accounts can watch private recordings but cannot change them. The optional public page displays only explicitly shared items.'),
 ]),
 ('Scheduled video and time-lapses', [
  ('Create a scheduled video', 'Under Observations → Scheduled Video, administrators can set a title, date, time, duration and timezone. The detector stops ordinary motion detection during the session and saves continuous footage in short MP4 segments.'),
  ('Time-lapse Basic mode', 'Basic uses the normal video-resolution camera feed with automatic/current exposure. It captures frames at the chosen interval and produces an MP4. Motion detection is paused to ensure a single consistent camera owner.'),
  ('Time-lapse Advanced mode', 'Advanced uses camera still mode and can capture at sensor resolution, with optional manual exposure and analogue gain. It suspends normal detection and Live Camera.'),
  ('Time-lapse estimator', 'Select interval, capture duration and finished video FPS. The estimated frame count and MP4 length appear before scheduling. Exposure must fit between frames.'),
  ('Source photograph ZIP', 'After successful rendering and ZIP verification, loose source images are removed. The ZIP stays private and is available on the individual time-lapse page; frames do not enter Photograph Gallery.'),
  ('Job progress and interruptions', 'The Dashboard shows active jobs. When a job begins, any active motion clip is saved. Motion detection restarts after the job finishes, is cancelled, or fails. Failure retains partial source data.'),
  ('Scheduling conflicts', 'The system rejects overlapping scheduled jobs and reserves time for processing. Event-storm protection does not interrupt scheduled jobs. Low disk stops new capture.'),
  ('Job details and public sharing', 'Each scheduled observation has title, notes, pin, share-video and share-notes controls. Only completed MP4 video can be shared publicly. Source ZIPs are never public.'),
  ('Job storage', 'Storage Management has tabs for Scheduled Videos and Time-lapses. Protected sessions cannot be deleted. Unprotected source ZIPs can be deleted while keeping finished MP4s.'),
 ]),
 ('Dashboard', [
  ('Detector status', 'Running means the recorder has recently reported activity. Paused means a manual pause is in effect; Scheduled means the current time is outside an operating window. Photography means a requested still capture has temporarily interrupted detection.'),
  ('Pause and resume', 'Administrators can pause new detections without disabling the website. An already open clip is finished, and Resume restores the selected operating schedule.'),
  ('Last camera preview', 'Shows the latest cached image from the active camera, not a live streaming video. Refresh preview requests the latest available still without changing camera settings.'),
  ('Saved detections', 'The table links to individual event pages and shows an event title, timestamp, review status, thumbnail and any available trigger label.'),
  ('Search', 'Enter words from an event title or saved notes. Search can include older events, not only those first visible on the page.'),
  ('Review status filter', 'Filter recordings by New, Viewed, Flagged, Identified, Unresolved or Dismissed. Opening a New event as an administrator changes it to Viewed; opening it as a viewer does not.'),
  ('Public and pinned filters', 'Use Public only or Private only to narrow the recording list. Pinned only shows events marked for protection against automatic cleanup.'),
  ('Page navigation', 'If there are more recordings than fit on one page, use the pagination controls to move through matching results.'),
 ]),
 ('Recording and review', [
  ('Recording a motion event', 'The recorder keeps a short rolling pre-motion buffer and continues saving while detection is active. It closes the event after quiet time, or rolls over to another file at the configured clip limit.'),
  ('Trigger type', 'General motion is a change between frames; Moving bright point is a small bright object tracked through multiple frames. Combined can report one or both. These labels identify the triggering algorithm, not the object.'),
  ('Event title and notes', 'An administrator can rename a recording, enter investigation notes and save them on its event page. Search looks in titles and notes.'),
  ('New and Viewed', 'New means not opened by an administrator. It becomes Viewed automatically when an administrator opens the event. Saved decisions such as Identified or Flagged are not overwritten by opening it again.'),
  ('Flagged, Identified and Unresolved', 'Flagged marks an event worth further investigation; Identified means you have determined what it is; Unresolved means it has been reviewed without a firm identification. All three are protected from automatic deletion.'),
  ('Dismissed', 'Dismissed marks unimportant or mistaken detections. It can be removed automatically if the administrator enables and configures retention.'),
  ('Pin a clip', 'Pinning protects an event even if it is New, Viewed or Dismissed. Unpin before manually deleting it.'),
  ('Delete an event', 'Administrators can delete an unpinned recording, its thumbnail and its database entry after confirmation. This is permanent; download a copy first if needed.'),
  ('Share a clip', 'Administrators can explicitly allow a recording on the optional public page. This does not automatically share the notes. Public clips are excluded from automatic cleanup.'),
  ('Share observation notes', 'A separate choice controls whether that recording’s notes are shown publicly. Do not share notes containing personal or sensitive information.'),
 ]),
 ('Video investigation', [
  ('Play, pause and timeline', 'Use Play and Pause, or drag the timeline to reach an interesting moment in the original recorded MP4.'),
  ('Frame stepping', 'Previous Frame and Next Frame move by approximately one recorded frame while paused. Browser decoding and MP4 keyframes can make these steps approximate rather than exact.'),
  ('Playback speed', 'Select slow motion or faster playback using the Speed menu. The original MP4 remains unchanged.'),
  ('Zoom and pan', 'Increase Zoom to inspect part of the image; drag the enlarged view with a mouse or finger. Reset image restores the normal zoom and image adjustments.'),
  ('Brightness and contrast', 'Browser image processing can make detail easier to inspect but cannot reconstruct detail that the sensor never captured.'),
  ('Playback view', 'Original shows the recorded colour frame. Detection gives a greyscale processing view. Low-light enhanced digitally boosts dark footage and is not a separate infrared-only capture.'),
  ('Compare frame', 'Pause, select Left and Right views, then drag the reveal slider. Frame stepping updates both sides while keeping the split position.'),
  ('Save a frame PNG', 'Save current frame PNG starts an ordinary PNG download of the selected paused frame, including both processed sides and labels when comparison is enabled. It does not open the system Share menu or modify the source MP4.'),
  ('Download original MP4', 'The download control retrieves the saved recording as captured, without any browser zoom, filters or comparison effects.'),
 ]),
 ('Observation calendar', [
  ('Choose a month', 'Move backwards or forwards through calendar months. A date displays how many recordings belong to that local calendar day.'),
  ('Choose a date', 'Select a date to see its recordings and a breakdown by review status and trigger source.'),
  ('Time zones', 'Calendar days use the detector’s selected timezone. Timestamps are stored internally in UTC and displayed in the configured local time zone.'),
  ('Direction statistics', 'A camera bearing describes where the camera is oriented, not the direction in which an object travelled. Object-direction counts need future sky calibration and are not invented.'),
 ]),
 ('Live Camera', [
  ('Who can use Live Camera', 'This page is administrator-only. Viewers and public visitors can use their permitted small cached previews instead.'),
  ('Preview updates', 'The page displays a cached camera snapshot and refreshes it about every ten seconds. Browsing does not stop or retune the normal recorder.'),
  ('Freeze and resume', 'Freeze holds the existing image for investigation, keeping zoom and comparison in place. Resume enables automatic snapshot updates again.'),
  ('Refresh now', 'Requests the latest available cached still. It does not force the sensor to take a separate full-resolution photograph.'),
  ('Live image adjustments', 'Use the Original, Detection or Low-light enhanced view, plus zoom, brightness, contrast and image reset. These adjustments run in the browser.'),
  ('Live comparison', 'Choose Left and Right processing views and move the reveal slider. Both sides are generated from the same still, not two different captures.'),
  ('Save current view PNG', 'Downloads a PNG of the displayed still with comparison split, labels, zoom and enhancements. When the video source is 1920 × 1080, the admin Live Camera cache and export are true Full HD. Lower-resolution videos are not artificially enlarged.'),
  ('HD snapshot cache', 'The admin Live Camera temporarily requests a full-size frame from the current recording stream. Dashboard and public previews stay lightweight. It may take several seconds for the first HD image to appear.'),
  ('Basic full-resolution photo', 'Select JPEG or PNG and Capture full resolution. The detector cleanly ends an active recording, switches to the camera’s still mode, saves the photograph, then restores its normal recording profile.'),
  ('Advanced photography', 'The advanced controls are temporary and apply only to the next requested photograph. Adjusting the controls alone does not interrupt detection or alter saved camera profiles.'),
  ('Shutter and exposure', 'Manual exposure sets how long the sensor gathers light for the still photo. Long exposures can be tens of seconds and create a temporary gap in detection when Capture is pressed.'),
  ('Analogue gain', 'Gain amplifies the sensor signal. It can help brighten dark scenes but also increases visible noise; it is not a calibrated ISO measurement.'),
  ('Focus and white balance', 'Focus can be automatic or infinity/manual when supported. White balance can be automatic or set with colour gains. The supported controls depend on the camera.'),
  ('Photo capture status', 'Waiting for camera means the detector has not accepted the queued request. Capturing means the still exposure is underway. When finished, a download link and a photo-review button appear. If the camera fails to accept the request, check System Health.'),
  ('Review captured photo', 'After a full-resolution photograph finishes, choose Review captured photo to apply the same single-image or comparison controls. The processed PNG export is limited to 1920 pixels wide to be manageable on phones; Download original photo keeps the native sensor resolution.'),
  ('Return to live snapshot', 'When reviewing a saved photograph, select Return to live snapshot to resume the ten-second camera preview. Existing Day/Night/Custom profiles are unchanged.'),
  ('Original resolution', 'The normal preview may be scaled down to save resources. Full-resolution photo capture requests the sensor’s native still resolution and can take time to switch modes.'),
 ]),
 ('Settings — recording', [
  ('Resolution and frame rate', 'Set the saved MP4 dimensions and target fps. Available fps limits depend on the detected Raspberry Pi and camera. Higher resolution or fps can use more space and reduce light gathered per frame.'),
  ('Motion sensitivity', 'Pixel difference threshold controls how much individual pixels must change. Changed pixels to trigger sets how many pixels must differ. Lower values are more sensitive but can cause more false alarms.'),
  ('Pre-motion and post-motion', 'Set the amount of video leading into and following detected motion. Pre-motion capture uses a rolling video buffer; exact lead-in can differ slightly.'),
  ('Maximum clip length', 'Long continuous movement rolls over into another recording when it reaches the configured limit. A manual full-resolution photograph deliberately ends the current clip early.'),
  ('Detection profile', 'General motion finds larger image changes. Moving sky lights tracks moving bright points. Combined triggers when either algorithm detects something.'),
  ('Sky-light settings', 'Adjust the minimum brightness, smallest/largest object area, confirming frames and required movement. Values apply to the reduced analysis frame.'),
 ]),
 ('Settings — camera profiles', [
  ('Automatic profile', 'The camera automatically selects normal exposure and gain controls. This is a conservative default for testing.'),
  ('Day and Night profiles', 'Day and Night each have independently editable exposure, gain, colour, focus and processing controls. Automatic day/night switching can choose between them at sunrise and sunset.'),
  ('Custom profiles', 'Custom 1 and Custom 2 store named camera control presets for different situations.'),
  ('Reset Camera and recording', 'On Detector settings expand Camera and recording, then choose Reset to defaults. This loads recommended resolution, supported frame rate, motion threshold, pre/post capture and clip duration in that section only. It does not save immediately. Check the displayed values and press the main Save settings button to apply them. Camera hardware detection and supported choices are unchanged.'),
  ('Reset and save', 'Reset to defaults restores a profile’s starting values in the form. They are not made permanent until Save settings is selected.'),
  ('Test unsaved profile', 'Test the values typed into a profile before saving. The detector temporarily applies them, captures a test still and restores the normal active controls. This may wait for a current recording.'),
  ('Rotate 180 degrees', 'Use the 180° option if your camera is mounted upside down. Future previews, analysis and video frames follow the chosen orientation; existing clips remain unchanged.'),
  ('Compass bearing', 'The top-image bearing is a compass direction after rotation correction: north 0°, east 90°, south 180°, west 270°. It is metadata, not a calibrated sky map.'),
  ('Camera elevation', 'Elevation is the pointing angle above the horizon: 0° at the horizon, 90° straight up. True object positions also require lens calibration.'),
 ]),
 ('Settings — schedule and location', [
  ('Continuous monitoring', 'The detector checks for events at all times unless manually paused or interrupted by a still photograph.'),
  ('Scheduled hours', 'Set starting and ending local times. A range such as 20:00 to 06:00 continues over midnight.'),
  ('Sunset to sunrise', 'The detector calculates daily sunrise and sunset from its saved latitude, longitude and timezone, and operates through the night.'),
  ('Location name', 'A friendly name for the installation; it can optionally appear on the public heading if you approve publication.'),
  ('Latitude, longitude and timezone', 'These values control the solar schedule and local dates. Use the device’s location shortcut only when the browser is at the camera location.'),
  ('Public location privacy', 'Two independent switches allow showing the friendly location name, or precise coordinates and orientation. Both are off by default. Publishing precise coordinates reveals the installation location.'),
 ]),
 ('Storage and cleanup', [
  ('Storage overview', 'Shows saved video size, available disk capacity, counts and how many events are protected.'),
  ('Automatic deletion', 'Retention cleanup is off by default. When enabled, it can permanently remove eligible New, Viewed and Dismissed events after configured periods.'),
  ('Protected events', 'Pinned, publicly shared, Flagged, Identified and Unresolved recordings are protected from automatic cleanup.'),
  ('Maximum video storage', 'This is a soft target, not a guarantee. Protected events may keep accumulating and fill the card. System Health warns about low disk space.'),
  ('Backups', 'Download important original MP4s and photographs to a separate device. An SD card can fail even when the health page reports free space.'),
 ]),
 ('Accounts, public access and privacy', [
  ('My account', 'Change your own username and password. Keep credentials separate for each person rather than sharing one administrator account.'),
  ('User management', 'Administrators create, enable/disable and assign roles to accounts. Viewers cannot use settings, deletion or still photography routes.'),
  ('Public camera page', 'An administrator can enable a visitor-facing camera snapshot and approved recordings. The public page is separate from the private Dashboard.'),
  ('Public link', 'When public viewing is enabled, administrators can open the public page from Observations. It is not shown if public viewing is disabled.'),
  ('Videos and privacy', 'A public clip is watchable by anyone with access to the public page and might still be copied even if no Download button appears. Only share footage you are comfortable publishing.'),
  ('Remote network access', 'Use HTTPS and secure authentication before allowing access from the internet. Never forward the Pi dashboard management port or NPM administration port directly to the public internet.'),
 ]),
 ('Notifications and reports', [
  ('Notification bell', 'The bell shows the unread count for the signed-in account. Select it to open the private Notification Centre.'),
  ('Daily report', 'A daily report summarises the previous 24 elapsed hours ending at the chosen report time. The report displays its start and end times.'),
  ('Weekly report', 'A weekly report summarises the previous 168 elapsed hours ending at the configured weekday and time.'),
  ('Report preferences', 'Each administrator or viewer can choose report frequency, local time and timezone. Off disables summaries for that account.'),
  ('System fault notices', 'Only administrators receive in-dashboard alerts about stale camera heartbeat, snapshots or dangerously low storage. Repeat warnings are deduplicated while an issue persists.'),
  ('Delivery methods', 'Reports and alerts currently appear inside the dashboard after login. Email and browser push delivery are not enabled.'),
 ]),
 ('System health and troubleshooting', [
  ('System health readings', 'Check detector heartbeat, latest snapshot age, available memory, free disk, CPU temperature, load averages and uptime. The web server can function even if the camera recorder has stopped.'),
  ('Waiting for camera', 'A queued full-resolution photo has not yet been accepted by the detector. If it stays queued, check System Health and the recorder service before retrying. A normal long exposure should instead show Capturing.'),
  ('No camera preview', 'Check the normal Dashboard preview, then Live Camera. A missing cached image can mean the camera has not started or the recorder has stopped.'),
  ('Unexpectedly many detections', 'Review frame sensitivity, tree and cloud movement, reflections and day/night exposure settings. Lower sensitivity may help suppress noise.'),
  ('No new recordings', 'Check the Pause control, selected operating schedule, current camera profile, disk free space and detector heartbeat.'),
  ('Still capture interruptions', 'A manually requested full-resolution photo intentionally ends the active MP4 and temporarily suspends detection. The detector then attempts to restore its saved profile.'),
  ('Version history', 'Shows fixed software release information and detailed changes for each version. It does not depend on how a particular detector was installed.'),
 ]),
]

GUIDE.extend([
 ('Event-storm protection', [
  ('Why event-storm protection exists', 'Moving clouds, daylight changes and trees can repeatedly trigger five-minute rollover clips. This feature pauses new recordings after too much motion is saved within a recent time window.'),
  ('Storm protection defaults', 'Enabled by default: after ten minutes of recorded activity within fifteen minutes, finish the current MP4 and suppress new motion events for fifteen minutes. The camera preview and dashboard continue working.'),
  ('Low disk safeguard', 'If fewer than 1 GB remain on the SD card, the recorder stops opening new MP4s and saves any active clip. It will resume automatically once enough space has been freed. No files are automatically deleted by this protection.'),
  ('Storm cooldown', 'The Dashboard displays Event-storm protection and the approximate time until recording resumes. The pause ends automatically; events happening during cooldown may be missed.'),
  ('Tuning storm settings', 'Under Settings → Event-storm protection you can change the monitoring window, threshold and cooldown, or disable the feature if uninterrupted event capture is more important than storage protection.'),
 ]),
 ('Storage Management', [
  ('Open Storage Management', 'Administrators can open Administration → Storage Management to see free space, used recording space and saved photograph counts.'),
  ('Delete recordings in Storage Management', 'Select eligible clips and choose Delete selected, or use the trash icon on a single row. A confirmation panel appears without jumping to the bottom of the page. Protection is rechecked at deletion time.'),
  ('Protected events', 'Pinned and publicly shared clips, plus Flagged, Identified and Unresolved statuses, cannot be bulk-deleted. Protection is rechecked immediately before deletion.'),
  ('Photograph Gallery', 'Open Observations → Photograph Gallery. Search image titles and notes, open a large photo, download the original, edit title and notes, pin it or approve public sharing. All deletion takes place in Storage Management.'),
  ('Photo retention', 'Optional photo cleanup starts disabled. When enabled, it removes only old photographs that are neither pinned nor approved for public sharing.'),
  ('Notice retention and pagination', 'Notifications show ten per page and can be filtered by Unread, Reports, Faults and Recovery. Each account may delete its own notices; administrators can enable automatic cleanup of old read notices only.'),
 ])
])

GUIDE.extend([
 ('Storm status and activity history', [
  ('Storm activation', 'When excessive recorded motion triggers cooldown, the detector creates an administrator-only notification and logs when it occurred.'),
  ('Storm recovery', 'When cooldown completes, a separate recovery notification is created. Open Administration → System Health to see recent storm periods.'),
  ('Monitoring gaps', 'Motion events occurring during a cooldown may not be recorded. Check the status and history before treating a quiet period as proof that nothing moved.')]),
 ('Photograph reviews and sharing', [
  ('Photograph Gallery', 'Open Observations → Photograph Gallery. Search by photo title or notes. Each thumbnail opens its full detail page.'),
  ('Edit a photograph', 'Administrators can update title, observation notes, protection and public sharing. Viewer accounts can inspect photographs without making changes.'),
  ('Share a photograph', 'Select Allow on public page to publish a reduced copy with embedded metadata stripped. Separately enable public notes if they should be displayed.'),
  ('Delete a photograph', 'Open Administration → Storage Management, choose Photographs, then use the trash icon or batch selection. Pinned and public items are protected.')]),
 ('System actions', [
  ('Reboot the Pi', 'An administrator confirms their password on System Health before queuing a restart. The privileged helper stops the recorder to finalise any open MP4.'),
  ('Shutdown the Pi', 'A shutdown needs your administrator password and physically powering the Pi on again afterwards. Unattended remote power-on is not provided.'),
  ('Software updates', 'Open System Health → Software updates to check official GitHub releases. Check requires no additional password; Update and Repair require the signed-in administrator’s current password. These actions never start automatically.')]),
])


GUIDE.extend([
 ('Photograph Gallery filters', [
  ('Public photographs filter', 'In Observations → Photograph Gallery, set Public sharing to Public only or Private only. This filters photographs without changing who can view them.'),
  ('Pinned photographs filter', 'In Photograph Gallery, choose Pinned only to find photos protected from automatic cleanup, or Unpinned only to see the rest. Search, Public and Pinned filters work together.'),
 ]),
 ('Public observation pages', [
  ('Shared observations tabs', 'Visitors can switch between Recordings and Photographs on the public page. Only media explicitly approved by an administrator is visible.'),
  ('Public recording pages', 'Each public Recordings page shows at most five clips. Open a clip to play it, then use Next or Previous to browse older entries.'),
  ('Public photograph pages', 'Each public Photographs page displays at most six images. Photos are served at reduced resolution with embedded metadata removed; private originals are not linked.'),
 ])
])

# Every principal page is a self-contained reference: controls are deliberately
# explained again where they appear rather than sending the reader elsewhere.
GUIDE = [(name, topics) for name, topics in GUIDE if name not in (
    'Scheduled video and time-lapses', 'Recording and review', 'Accounts, public access and privacy',
    'Photograph reviews and sharing', 'Photograph Gallery filters', 'Photograph Gallery',
    'Notifications and reports', 'System health and troubleshooting', 'Public observation pages',
    'System actions', 'Storage and cleanup', 'Settings — recording', 'Settings — camera profiles',
    'Settings — schedule and location', 'Storage Management',
)]
GUIDE.extend([
 ('Recorded events', [
  ('Opening and finding clips', 'Dashboard → Saved detections lists event name, timestamp, trigger source, status and thumbnail. Search event titles and saved notes; filters for status, pinned and public state can be combined. Pages show matching older entries.'),
  ('Playing a clip', 'Open an event and press Play. Drag the timeline to jump to a time. Speed offers quarter speed, half speed, normal and faster playback; original MP4 remains unchanged.'),
  ('Frame stepping', 'Pause and use ◀ Frame or Frame ▶ to seek approximately one recorded frame. Depending on MP4 keyframes and browser decoding, the result is not guaranteed frame-exact.'),
  ('Image processing', 'Playback view selects Original, Detection (grayscale), or Low-light enhanced. Brightness and Contrast adjust the browser preview; Zoom magnifies and dragging pans. Reset image restores normal settings. These processes do not modify the video.'),
  ('Compare frame', 'Pause the clip, press Compare frame, choose Left and Right image modes, then drag the reveal slider. Frame stepping updates both sides while preserving the slider position. Playing hides comparison; pausing restores it.'),
  ('Saving and downloading', 'Save current frame PNG downloads the processed still (including a comparison split if selected). Download original MP4 retrieves the saved video, not the temporary browser filters.'),
  ('Review statuses', 'New becomes Viewed only when an administrator opens it. Flagged, Identified and Unresolved are manual decisions protected from automated cleanup; Dismissed can qualify for age-based retention.'),
  ('Title, notes and public sharing', 'Administrators can edit the event title, notes and review status and select Save changes. Pin protects the recording. Public sharing is a separate explicit choice; public notes must be approved separately.'),
  ('Deletion and protection', 'An eligible event can be deleted with confirmation. Pinned or approved media is protected; Storage Management also provides bulk deletion. Deleted media cannot be recovered without a backup.'),
 ]),
 ('Scheduled Video', [
  ('Purpose', 'Scheduled Video captures continuous MP4 footage at a predetermined start time regardless of motion, suitable for sunrise and other planned observations.'),
  ('Title and start', 'Enter a unique, meaningful title and start date and time in the detector’s configured local timezone, shown on the scheduling form. The job stores UTC internally but displays the selected detector-local date and time.'),
  ('Duration and profile', 'Choose a duration from one minute up to the supported maximum and a camera profile (Automatic, Day, Night, Custom 1 or Custom 2). The saved detector profile is restored when the session ends.'),
  ('Scheduling conflicts', 'Only an administrator can schedule or cancel. Overlapping jobs are refused; the recorder must be running the upgraded job engine and the storage check must pass.'),
  ('Recording operation', 'At the scheduled start, any open motion MP4 is completed, ordinary event detection stops, and the camera records the continuous requested session. Event-storm cooldown does not interrupt a scheduled job.'),
  ('Segments', 'A long session is stored in successive short MP4 segments to limit damage if power fails. Part links appear on the individual session page; the original segments can be downloaded.'),
  ('Status and cancellation', 'The Dashboard and Scheduled Video list show Queued, Capturing, Complete, Cancelled or Failed. Administrators can request a stop; completed segments are preserved. The camera resumes normal operation after a job.'),
  ('Video investigation controls', 'Play or pause a segment, change speed, step by approximately one frame, adjust Zoom, Brightness or Contrast, choose Original/Detection (grayscale)/Low-light enhanced or compare a paused frame with a draggable split.'),
  ('Title, notes and public page', 'A completed job has its own editable title and notes, Pin and protect and two independent public approvals (video and notes). Only approved finished segments are offered publicly; private internal resources are not.'),
  ('Storage and calendar', 'Completed jobs appear in the Observation Calendar. Storage Management lists their segments, estimated sizes and bulk-deletion controls. Protected or published jobs cannot be deleted accidentally.'),
  ('Failure warnings', 'If a job fails or camera recovery does not succeed, an administrator-only notice explains the failure. Temporary camera preview suspension while a scheduled job is active is expected, not a camera fault.'),
 ]),
 ('Time-lapse Studio', [
  ('Purpose and scheduling', 'Time-lapse creates a short MP4 from still photographs taken at regular intervals. Enter a title, detector-local start date/time, session duration, photograph interval and finished-video frames per second.'),
  ('Basic mode', 'Basic captures genuine full-resolution still photographs with automatic camera exposure and related camera controls. It is not a scaled-up version of the normal low-resolution detector preview.'),
  ('Advanced mode', 'Advanced also captures full-resolution stills, but provides temporary exposure, gain, focus, white balance and image adjustment settings for this job only. The normal stored Day/Night/Custom profiles are untouched.'),
  ('Exposure and shutter milliseconds', 'Manual Exposure/shutter uses milliseconds, just like Live Camera: 1000 ms equals one second and 15000 ms equals fifteen seconds. A longer exposure gathers more light but risks movement blur and star trails.'),
  ('Exposure versus interval', 'The shutter duration must fit within the image interval, leaving additional time for readout, image processing and writing. A 15000 ms exposure cannot be requested at a ten-second interval. A validation error means the schedule is not created.'),
  ('Analogue gain', 'Gain multiplies sensor brightness and noise; it is not a calibrated ISO rating. Use lower gain under bright light and carefully test increased gain for faint night scenes.'),
  ('Focus and lens position', 'Choose Autofocus, Infinity or Manual. Infinity is appropriate for distant stars, while Manual lets you enter a lens position. Available focus modes depend on your camera.'),
  ('White balance and colour', 'Automatic chooses colour balance from the scene. Manual lets you provide red and blue gains separately. Brightness, Contrast and Saturation adjust camera processing; these are not post-capture modifications.'),
  ('Output video FPS', 'Output FPS is the playback rate of the finished MP4, not the camera frame rate during capture. Expected duration is planned images divided by output FPS: 600 frames / 24 fps = 25 seconds.'),
  ('Frame interval and duration', 'The number of planned source photographs is the session duration divided by capture interval. For 150 minutes at 15-second intervals there are about 600 images, assuming captures succeed.'),
  ('Camera ownership and Dashboard', 'The camera is reserved exclusively for the session; normal event detection and dedicated Live Camera are paused. The Dashboard shows capture progress, then rendering and ZIP archiving. Normal operation is restored on completion or failure.'),
  ('Render and source ZIP', 'When capture ends, source stills are rendered into an MP4, then verified and collected into a private ZIP. Loose frames are deleted only after successful output verification. Failed jobs keep partial sources for recovery.'),
  ('Download names', 'The download name follows Time-lapse-ID-Video-Title.mp4 and Time-lapse-ID-source-frames-Title.zip. Names use the latest saved title; the internal stored files do not need renaming.'),
  ('Source ZIP privacy and size', 'The source ZIP stays private to administrators and the photos do not enter Photograph Gallery. JPEG photos may compress very little further inside ZIP. After downloading, admins can delete the ZIP independently in Storage Management while retaining the MP4.'),
  ('Investigation and split comparison', 'The time-lapse detail page includes Play/Pause, approximate Frame buttons, Speed, timeline, Zoom, Brightness and Contrast, Original/Detection (grayscale)/Low-light enhanced and a paused-frame comparison slider. Save frame PNG includes chosen processing.'),
  ('Title, notes, pin and public sharing', 'Every finished time-lapse has its own title, notes and Pin protection. Approve the finished MP4 for public viewing and separately approve notes if appropriate. The original photo archive is never public.'),
  ('Storage and cleanup', 'Find completed time-lapses under Administration → Storage Management → Time-lapses. Review video and ZIP sizes before deletion. Pinned or published jobs stay protected; deleting source ZIP alone saves storage without deleting the finished MP4.'),
  ('Job fault notifications', 'Started, Completed and Failed job notices appear only inside the dashboard. Missing ordinary preview images during a healthy time-lapse are expected and are not a separate camera fault. If the camera fails to resume after completion, investigate System Health.'),
 ]),
 ('Photograph Gallery', [
  ('Finding photographs', 'Use Observations → Photograph Gallery. Search titles and notes, filter Public/Private and Pinned/Unpinned, and page through thumbnail cards.'),
  ('Open a photograph', 'Select a thumbnail for a large image and capture details. Administrators can rename the photo, add notes, pin it or approve sharing; viewers may inspect but not edit.'),
  ('Downloads', 'Download original saves the recorded sensor photograph rather than a stretched preview. The saved download name includes the photo identifier and latest title.'),
  ('Image comparison', 'Photo investigation can provide Original, Detection (grayscale) or Low-light enhanced views with zoom and processing; where available, comparison is a draggable split between the same frame.'),
  ('Sharing and privacy', 'Public photographs are explicit opt-in. Notes are private unless separately approved. Public previews are reduced-size and metadata stripped; source originals remain private.'),
  ('Pin and delete', 'Pinning protects a photograph; it does not create a second gallery. All photograph deletion takes place in Storage Management rather than the gallery view.'),
 ]),
 ('Camera settings', [
  ('Resolution and frames per second', 'Choose from hardware-supported recording resolutions and FPS. Higher rates improve temporal detail but may limit exposure and increase storage usage. The camera restarts safely when changes are applied.'),
  ('Motion and light profiles', 'Choose General motion, Moving bright points, or Combined. Set thresholds for pixel changes or sky-light intensity, size and consecutive frames. The chosen profile identifies trigger algorithms, not physical objects.'),
  ('Camera presets', 'Automatic exposure, separately editable Day and Night, and Custom 1/Custom 2 profiles control shutter, gain, white balance, focus, colour and brightness. Saved profiles affect ordinary detection; scheduled Advanced photography is temporary.'),
  ('Testing an unsaved profile', 'Choose a profile, edit fields and select Preview unsaved changes; the camera temporarily tests the settings and restores the active profile. Use Reset to defaults then Save settings only when satisfied.'),
  ('Rotation and compass bearing', 'Rotate 180° if the camera is mounted upside down. Top-image bearing (0 North, 90 East, 180 South, 270 West) and elevation (0 horizon, 90 up) are saved metadata, not exact calibrated sky coordinates.'),
  ('Detector-local operating hours', 'Continuous, fixed daily windows and sunset-to-sunrise modes control ordinary detection. An administrator manual Pause overrides them. Set the detector timezone and location in Settings; these also drive observation dates.'),
  ('Event-storm protection', 'When cumulative motion recording exceeds its monitoring threshold, the detector finalises a clip then pauses new motion recordings for a cooldown. The preview continues; scheduled video and time-lapse jobs are not interrupted.'),
  ('Storage and public viewing', 'Enable public viewing only if authorised. Public location and precise coordinates require separate opt-ins. Retention settings can remove eligible unprotected events, while pins, approved sharing and protected statuses prevent automatic deletion.'),
 ]),
 ('Accounts and access', [
  ('My account', 'Change your username or password by providing your current password. Separate accounts make permissions and audit trails clearer.'),
  ('Administrator', 'Administrators may configure capture, change user roles, delete eligible media, approve public clips and use System Health actions, storage controls and Live Camera.'),
  ('Viewer', 'Viewers can read private observation media and their own notification reports, but cannot alter clip titles, notes, sharing, job schedules or system settings.'),
  ('Public viewers', 'Unauthenticated visitors see only explicitly published material when public viewing is enabled. Do not expose administrator routes or NPM management endpoints directly to the internet.'),
 ]),
 ('Notifications and reports', [
  ('Notification bell', 'The notification bell shows unread notices for your own account. Click it to open your private Notification Centre. External email and Web Push remain optional and disabled until you explicitly configure them.'),
  ('Daily and weekly windows', 'A daily summary counts the previous 24 elapsed hours ending at your selected personal report time. Weekly counts the previous 168 elapsed hours and appears on your chosen weekday.'),
  ('Personal report timezone', 'Every administrator and viewer sets their own summary-delivery timezone independently of the detector. Choose a location from the single dropdown showing its current UTC offset (such as UTC+01:00, UTC+00:00 or UTC−01:00), or select Use my browser timezone, then explicitly Save preferences. Your choice does not change saved recording times, observation dates or camera schedules.'),
  ('Browser timezone detection', 'Use my browser timezone reads the browser’s timezone setting, not GPS. This only selects an option in the form; the change applies when you Save preferences and does not silently change when travelling.'),
  ('Detector versus user clock', 'All observation records, sunrise/sunset and camera schedules use the detector timezone. Your personal notification timezone controls when your summaries are generated and the clock used for notification timestamps.'),
  ('Started scheduled job', 'Started: title means the planned Scheduled Video or Time-lapse captured control of the camera and began its operation. Normal motion detection and dedicated Live Camera are intentionally suspended.'),
  ('Completed scheduled job', 'Completed: title means the scheduler finished and produced available outputs. For time-lapses, rendering and source ZIP archiving can add processing time beyond the capture duration. Open the job details to review the resulting MP4 and archive.'),
  ('Failed or interrupted job', 'A Failed, Cancelled or Interrupted notice indicates the job did not finish normally. Open the job details to review retained segments, source frames and any error, and inspect System Health if the recorder did not restart.'),
  ('Event-storm protection activated', 'This admin-only warning means excessive repeated motion recording triggered a cooldown. The active MP4 was finalised and ordinary motion events are temporarily suppressed. Look at Dashboard and System Health for remaining cooldown time.'),
  ('Event-storm monitoring resumed', 'The cooldown ended and normal scheduled detection was allowed to resume. It is a recovery notice, not a new detected sky object.'),
  ('Camera snapshot unavailable or stale', 'The ordinary preview has not updated within the expected time while the detector should be producing snapshots. Check System Health and camera heartbeat. This warning is intentionally suppressed when Scheduled Video or Time-lapse Studio has exclusive camera ownership.'),
  ('Recovered: camera snapshot', 'Fresh snapshots have resumed after an earlier genuine camera-preview fault. You do not need to restart recording if System Health now confirms normal operation.'),
  ('Detector heartbeat missing', 'The camera recorder stopped reporting its health heartbeat or entered a failure state. The web dashboard might still work, but recordings may have stopped. Check System Health and service status.'),
  ('Recovered: detector heartbeat', 'The camera recorder is reporting a healthy heartbeat again. Confirm the preview and recorded activity are returning as expected.'),
  ('Low available recording storage', 'Available disk space reached a warning threshold. Review Storage Management, delete only eligible unprotected media or attach external storage; very low space can prevent further MP4s.'),
  ('Recovered: storage space', 'Disk space rose above the warning threshold after cleanup or expansion. Observe the free-space reading to ensure it remains adequate.'),
  ('Mark read and Delete', 'Mark read only changes your own unread state; Delete removes the notification card, not the media it mentions. Administrators may configure age-based cleanup of already-read notices. Ten notifications appear per page.'),
  ('Notification permissions', 'Only admins receive camera, system, storage and storm alerts; both admins and viewers can opt into their own daily or weekly summaries.'),
  ('External delivery', 'Optional SMTP email and encrypted browser Web Push are available under Notifications; each channel requires its own setup and opt-in. External delivery uses the same personal report schedule and timezone without changing detector observation timestamps.'),
 ]),
 ('System health and troubleshooting', [
  ('Detector and snapshot health', 'The heartbeat shows whether the camera recorder is responding. A snapshot that is old during an intentional scheduled job is expected; when no job is active, old snapshots can indicate a camera problem.'),
  ('Disk, RAM and CPU', 'Free disk, memory usage, load and CPU temperature are indicators of resource pressure. The camera may fail independently of the web dashboard. A low-storage safeguard prevents new recordings before the disk is exhausted.'),
  ('Storm history', 'Storm activity records cooldown starts and recoveries. During cooldown normal motion recordings are suppressed even though the camera preview can keep updating.'),
  ('Reboot and shutdown', 'An administrator must confirm their password before a Pi reboot or shutdown. The privileged helper stops camera capture cleanly when possible. Shutdown requires physical power-on afterwards.'),
  ('Camera after scheduled jobs', 'Scheduled video and time-lapse jobs reserve the camera, so Live Camera and the usual preview stop temporarily. If the job fails to release the camera, open System Health and inspect job errors.'),
  ('Troubleshoot waiting photography', 'A photo request waiting for the camera should transition to Capturing. If it remains queued or reports an error, inspect the detector heartbeat and make sure no scheduled job has exclusive camera ownership.'),
 ]),
 ('Storage Management', [
  ('Tabs and media types', 'Open Administration → Storage Management. The Overview, Recordings, Photographs, Scheduled Videos and Time-lapses tabs now share one administration interface. Select recordings, photographs, scheduled videos or time-lapses. Each category shows candidates, file sizes and protection. Source ZIPs remain separate from the Photograph Gallery.'),
  ('Individual and bulk deletion', 'Use a row trash icon for one eligible item, or check several and choose Delete selected. A confirmation appears in place, showing affected files. Protected or public items cannot be silently deleted.'),
  ('Deleting a time-lapse ZIP', 'You can remove an unprotected time-lapse source ZIP while keeping the rendered MP4. Source photographs are not transferred to the ordinary gallery. Never delete a ZIP before verifying your external downloaded copy.'),
  ('Retention and free space', 'Automatic cleanup is opt-in and can remove eligible unprotected media. Pins, published material and protected review statuses are preserved. An SD card can still fill from protected observations; monitor remaining storage.'),
 ]),
 ('Public observation pages', [
  ('Public camera and privacy', 'The administrator can enable a public camera snapshot and separately approve which observations are published. The ordinary camera preview may be unavailable during a scheduled capture.'),
  ('Public media tabs', 'Visitors can browse Recordings, Photographs, Scheduled Videos and Time-lapses. Only approved, completed media is listed, with pagination and titles.'),
  ('Videos and notes', 'A public approved MP4 can be watched, but approved observation notes require a second permission. Hidden Download buttons cannot prevent a determined visitor from saving an already accessible video.'),
  ('Source photo privacy', 'Time-lapse ZIP archives and private source photos are never public, even when a completed time-lapse MP4 is approved.'),
 ]),
 ('Version history', [
  ('Release notes', 'Expand a version to view its title, fixed publication date and detailed code changes. The release record is shared across all installations rather than describing when an individual device received an upgrade.'),
 ]),
])


GUIDE.extend([
 ('System Administration', [
  ('Purpose and scope', 'Open Administration → System Administration to work with configuration portability, external-access planning, outbound messaging information and future software maintenance. It is restricted to administrators. Detector-specific controls, camera profiles and the capture schedule remain under Camera & Detector Settings; System Health remains the diagnostics and power-control page.'),
  ('Export settings only', 'Under Settings export and import, choose Settings only and select Export backup. The browser downloads a JSON document of supported detector configuration. It does not include recordings, source photo archives, thumbnails, account passwords, sessions, Cloudflare API tokens, SMTP credentials, SSH keys, Raspberry Pi network configuration or NPM administrator credentials. Keep a copy somewhere other than the Pi in case the SD card fails.'),
  ('Export settings and users', 'Choose Settings + Users, enter your CURRENT administrator password and a new backup passphrase of at least 12 characters, then select Export backup. The detector encrypts account password hashes and saved report preferences in an AES-GCM protected file. Keep the passphrase separately and securely: without it the file cannot be imported. This option is intended for administrators migrating an installation to a compatible detector, not for viewers.'),
  ('Preview an import', 'Use Choose file to select a Settings JSON or encrypted UAP backup. Enter its passphrase for encrypted backups and choose Preview import. The review shows how many settings are present, how many differ from the current Pi and whether user accounts exist in the archive. No settings or accounts have changed yet. Verify that camera hardware, timezone, schedules, privacy options and recording limits fit the target detector before continuing.'),
  ('Apply an import', 'After reviewing the preview, provide your CURRENT administrator password, tick the confirmation box and choose Apply imported configuration. Settings are written atomically. For an encrypted backup you may separately tick Add missing users. Existing user accounts, passwords and roles are NOT overwritten; users that do not exist on the target may be added. Imported accounts retain their previous password hashes; ask users to log in and change their passwords after migration. Camera settings can take effect on the next recorder configuration refresh; verify the saved settings and scheduled jobs afterwards.'),
  ('Settings portability limits', 'Import/export transfers eligible detector configuration, not recorded events, photographs, source ZIP archives, system users, NPM containers, email provider access or network credentials. It is not a complete disaster-recovery image and cannot mirror live media between two devices. Device hardware is not auto-provisioned by an imported camera profile; review compatibility manually before applying.'),
  ('Local network and NPM', 'Open System Administration → Network and remote access. Local-only, managed NPM and Cloudflare Tunnel are separate access options. The bundled NPM path manages an HTTPS proxy, Cloudflare DNS and DDNS; use a router DHCP reservation where possible. Never forward the raw dashboard or private NPM administration port directly to the internet.'),
  ('Cloudflare and changing public IP', 'The Network and remote access section now supports scoped Cloudflare API credentials, NPM DNS and five-minute DDNS, or an outbound-only Cloudflare Tunnel without router port forwards. The two saved access profiles remain separate when changing modes. Never share API or connector tokens or paste them into the Help search field.'),
  ('Email and Web Push', 'Outgoing SMTP email and browser Web Push can now be configured here, with an independent Web Push contact address. Each user opts in under Notifications. SMTP uses one administrator-configured sender with individual recipient addresses. Browser Push requires HTTPS, browser consent and individual subscriptions. Existing in-dashboard reports always remain available.'),
  ('Software updates and repair', 'The included install.sh supports fresh installation, upgrades and same-version repair. Use Administration → System Health → Software updates to check official GitHub Releases or start an update or repair after confirming your current administrator password. The private prerelease test channel is separately enabled on the device by an administrator; the default stable channel needs no personal token. Updates never install automatically, and Raspberry Pi OS, Docker and NPM maintenance are separate.'),
 ]),
])

GUIDE.extend([
 ('Storage Management — detailed guide', [
  ('Overview and size units', 'Open Administration → Storage Management → Overview to see filesystem capacity and available space. The page measures motion recordings, scheduled-job media, photographs, software, containerd/Docker, swap, package caches, backups and an Other System category. Displayed gigabytes use GiB units (1 GiB = 1,073,741,824 bytes). The storage totals are actual disk accounting rather than only the media recorded by UAP Detector.'),
  ('Avoiding double-counting', 'Scheduled media includes finished MP4s, private source ZIP archives and small job metadata files. The additional MP4 and ZIP totals beneath it are SUBSETS of the scheduled-media total, not extra space. Docker and containerd may report different image sizes from the filesystem; the overview measures their actual directory use and reconciles remaining disk usage in Other System. System swap and operating-system files are not automatically reclaimable.'),
  ('Search and filters', 'Each media tab has Search, Status, Visibility and Sort controls. Use Apply filters to narrow the list, then Previous or Next to move through matching items. Recordings additionally support an Older than filter. A search and sort is applied before pagination. File sizes are shown per row. Pinned, publicly shared, protected review-status and unfinished-job entries are not eligible for deletion.'),
  ('Deleting one or several files', 'Open the relevant tab and select checkboxes on the rows you wish to delete, or press the trash icon on a single eligible row. The selected count and total estimated size appear at the bottom of the tab. Select Delete selected to open the confirmation dialog, read the warning, and choose Permanently delete. Eligibility is checked AGAIN immediately before deletion; a newly protected item will not be removed. Deleted media and associated records cannot be restored without a backup.'),
  ('Scheduled Videos in Storage Management', 'The Scheduled Videos tab is storage administration ONLY. Its View links take you to the original Scheduled Video session page, which remains under Observations and retains its scheduling and playback tools. The storage tab provides filtering, protection, size and deletion controls for eligible completed, failed or cancelled sessions. Current and queued jobs remain protected.'),
  ('Time-lapses in Storage Management', 'The Time-lapses tab is likewise a separate storage view; the real Time-lapse Studio stays under Observations and remains unchanged. Each row separates MP4 size and ZIP size, and provides MP4 and source ZIP download buttons where available. After you have tested your downloaded ZIP, Delete ZIP only removes the private source archive without changing the finished video, observation notes, public setting or normal time-lapse Studio entry. Deleting the entire eligible session is a different, irreversible action.'),
  ('Photographs and recordings', 'The Recordings tab covers event MP4s from motion detection; the Photographs tab covers stand-alone full-resolution photographs from the camera. Time-lapse source photographs are NOT mixed into Photograph Gallery. Every media type is subject to its own publication and pin protection; unpin and unpublish separately in the observation detail page before deleting it if you are certain it is no longer needed.'),
  ('Time-lapse preflight estimate', 'A time-lapse captures individual full-resolution JPEGs. Before scheduling, the application estimates working space using recent source JPEG sizes if available and a cautious fallback otherwise. It budgets temporary stills plus a ZIP of those stills, output MP4 data, temporary overhead and a separate 2 GiB safety reserve. Unlike a fixed 18 MB per image assumption, this estimate adapts to actual camera results. It remains an estimate: high scene detail can produce larger JPEGs.'),
  ('Low disk and interrupted jobs', 'The running recorder stops a capture if it sees under 1 GiB free to protect the Pi; the recorder retains available partial source images on failure. An interrupted job is marked in the jobs list and its error displayed. The web dashboard cannot safely reassemble or resume a partly captured session without explicit recovery work; download and preserve any important files before retrying or removing the job. A scheduled capture deliberately suspends the normal preview, so that temporary state should not create a snapshot-stale fault.'),
  ('Cleaning the operating system', 'The Overview shows system software, swap, package cache and container storage for diagnosis. It does NOT delete them. Do not manually remove /var/lib/containerd, Docker images in use, or /var/swap without first checking system and swap configuration. The storage investigation on a particular Pi does not prove that other installations have the same disk usage.'),
 ]),
])

def slug(s):
    return ''.join(c if c.isalnum() else '-' for c in s.lower()).strip('-').replace('--','-')



# v0.9.9.1: full, standalone explanations for the new controls and errors.
GUIDE.extend([
 ('Email delivery', [
  ('Where to configure SMTP', 'An administrator opens Administration → System Administration → Outgoing email. Enter the outgoing SMTP hostname, port, sender address, username and the password or app password supplied by the mail provider. Choose STARTTLS (commonly port 587) or implicit TLS (commonly port 465). Ordinary unencrypted SMTP is deliberately not offered. This is one outgoing account for the whole detector, not an inbox account for each Viewer.'),
  ('Gmail setup', 'In your Google account, enable two-step verification and, if your account allows it, create an app password for the detector. Gmail SMTP generally uses smtp.gmail.com with STARTTLS on port 587. Use the full Gmail address as the username and the generated app password. Google account policies may prevent app passwords; if so, use a supported dedicated SMTP provider. Never type a normal account password into troubleshooting screenshots.'),
  ('Outlook/Hotmail setup', 'Many Microsoft consumer email accounts require OAuth2 rather than username-and-password SMTP. The first outgoing-mail implementation supports TLS plus an SMTP credential/app password, not interactive OAuth2 consent. If Microsoft refuses the login, do not disable account security; use an SMTP provider that supports the available method until OAuth is added.'),
  ('Saving and testing SMTP', 'Enter the sender account details and tick Enable outgoing email. Save. Press Send test email to sender; the app reports whether the SMTP provider accepted the message. Also check the spam folder. A successful provider handoff cannot guarantee delivery to a recipient inbox. Test failures can result from the wrong server or port, revoked app passwords, blocked outgoing connections, incompatible authentication or an expired certificate.'),
  ('Personal recipient and delivery schedule', 'Each signed-in user opens Notifications, enters a personal recipient address and enables email delivery. The same Notifications page controls Daily, Weekly or Off, the local send time and personal timezone. Summary windows cover rolling 24 or 168 elapsed hours. The detector timezone continues to label observation records. System faults/recovery notices are created for administrators only.'),
  ('Delivery retries and diagnostics', 'Notifications shows each account its recent provider attempts. System Administration shows administrators all channel states. Pending waits for the delivery worker, Retry is a temporary error, Sent means an external provider accepted the message, and Failed means retries are exhausted. A failed SMTP handshake or DNS outage is not a camera fault. Test delivery can verify configuration after the problem is fixed. Do not put SMTP passwords in bug reports.'),
  ('Credentials and backups', 'The outgoing SMTP secret is stored separately in a private local configuration file and is excluded from both Settings Only and Settings + Users exports. Moving settings to another Pi requires entering the new outgoing SMTP credential again. Users may have email recipient addresses in the encrypted Users backup; external delivery remains disabled on imported accounts until enabled individually.'),
 ]),
 ('Browser Push', [
  ('What Web Push does', 'The Pi encrypts a short message to an individual browser subscription and posts it to that browser provider push endpoint. Push can arrive when the application tab is closed. It requires network access to the push provider but no separate consumer notification account. Messages contain the notice title and short body; they are not a public recording link.'),
  ('Before subscribing', 'Use an HTTPS address and a browser that supports Service Workers, PushManager and notifications. If using an iPhone, add the detector site to your Home Screen and open it as a web app (supported on iOS 16.4 or newer). Normal private browsing may not retain subscriptions. An HTTP LAN IP address is generally not a secure context and cannot register Web Push; continue using the in-dashboard notice centre or SMTP in that case.'),
  ('Subscribe this device', 'Sign in on the actual browser/device that should receive notices, visit Notifications → Email & browser notifications, press Subscribe this browser and approve the operating system/browser notification permission. Enable browser delivery in the preferences and save. Repeat on each device and account separately. Subscribed devices appear by name with a Remove action and a per-device test option.'),
  ('Why a test push might fail', 'The site may not be HTTPS; the permission may be denied in the browser or operating system; a device might have unsubscribed; a firewall may block outbound HTTPS; the push service may reject its keys or expire its subscription. A removed or expired endpoint cannot receive messages. The Web Push administrative contact email in System Administration must be configured for the VAPID protocol; SMTP is not required.'),
  ('Sending and privacy', 'The detector generates an independent signing key and encrypts every Web Push payload to the destination browser key. The provider routes the encrypted message; it does not need the detector password. Notification content may appear on a locked screen, so avoid sharing sensitive observation details with someone who can see device notifications.'),
  ('Disable or remove', 'Untick browser delivery in Notifications to stop sending to this account while retaining its device subscriptions. Use Remove to delete a single saved device. Browser permission can also be revoked in browser/device settings. An administrator cannot silently subscribe another person’s browser.'),
 ]),
 ('Time-lapse storage planning', [
  ('Live estimate before submission', 'Open Observations → Time-lapse Studio → Create time-lapse. Choose a duration and capture interval. The estimate panel requests the latest storage calculation from the detector and shows planned full-resolution JPEG count, playback seconds, estimated job working space, 2 GiB safety reserve, total required and currently available free space. FPS alters MP4 length, not the number of captured JPEGs.'),
  ('JPEG sampling and fallback', 'When recent source-frame ZIP archives exist, the estimator reads photo sizes from their ZIP directory metadata, without extracting them. It adds an allowance to that typical size. Otherwise the calculation assumes 3 MiB per JPEG, not the previous blanket 18 MB. Scene detail, exposure and changing light can increase or decrease actual size.'),
  ('Temporary duplicates and safe reserve', 'During a long time-lapse, loose full-resolution frames need disk space. Archiving creates a private source ZIP, rendering produces an MP4, and temporary processing requires additional room. The total estimate includes these overlaps plus a 2 GiB scheduling reserve. The capture engine also preserves its 1 GiB minimum-space stop; the live estimate is informational and the server validates again at Schedule.'),
  ('Not enough free storage', 'If the live panel shows Not enough free storage, shorten duration, lengthen capture interval, delete eligible old source ZIPs in Storage Management or increase storage capacity. A ZIP-only delete preserves the finished MP4. Do not delete active, pinned or published observations to work around a warning.'),
 ]),
 ('Backup contents and verification', [
  ('Settings Only includes', 'A Settings Only export contains supported Detector Settings and camera profiles, including Day, Night, Custom 1, Custom 2, detection thresholds, recording resolution and FPS, detector timezone, detection schedules, sunrise/sunset location, retention, storm protection, public-page settings and camera orientation. Values are validated on import, and hardware support must be rechecked after migration.'),
  ('Settings Only excludes', 'A portable settings export does not contain users, their passwords, observation records, MP4 files, still photographs, time-lapse source ZIPs, public SSL keys, SMTP credentials, Cloudflare credentials, network configuration or NPM settings. It is not an SD-card image or disaster recovery of all media.'),
  ('Settings + Users', 'Encrypted Settings + Users adds account names, hashed passwords, roles, report timezones and report preferences, plus any saved recipient addresses. Exports require the current administrator password and a separate backup passphrase. Imports preview changes, ask for approval and only add previously missing usernames. Existing accounts and passwords are left alone. Imported accounts do not automatically begin sending external messages.'),
  ('Safe import procedure', 'Save a copy of the existing configuration before importing a new one. Under System Administration select your exported file, enter a backup passphrase when needed and press Preview. Check the counts, confirm the administrator password and explicitly approve. Review the camera profiles and schedule afterwards. Media are not overwritten by this import.'),
 ]),
 ('Scheduled job recovery', [
  ('Power interruption or recorder restart', 'An interrupted scheduled video or time-lapse is marked Interrupted when the recorder restarts. The application keeps any surviving source photographs or already completed segments. It does not claim those files are a complete, playable output. The ordinary camera service should resume detection after the failed job releases ownership.'),
  ('Rendering or archive failure', 'If MP4 rendering or source ZIP verification fails, the job is marked Failed and its error appears in Time-lapse Studio. Partial source frames are retained for inspection instead of discarded, provided the filesystem remains readable. An administrator-only fault notice is generated for failed or interrupted jobs.'),
  ('Checking after an incident', 'Open System Health to verify detector heartbeat and free space. Open the failed scheduled job detail to see its status and error, and Storage Management to inspect any retained media. Retry a new session only after addressing power, disk-space, camera or rendering issues. Cancelling an active job intentionally is not the same as a hardware fault.'),
 ]),
])

GUIDE.extend([
 ('Time-lapse Studio — corrections', [
  ('The six-value storage estimate', 'Time-lapse Studio → Create time-lapse shows a stable two-row, three-column storage estimate. The first row gives Planned photographs, Finished MP4 duration and Space currently free. The second row gives Working space, Safety reserve and Total required. Its values are estimates; the server verifies free space again when you schedule.'),
  ('When storage recalculates', 'Only changing capture Duration or Interval requests another disk estimate. Output FPS changes the video-length number locally. Typing a session title, choosing the start date and time, writing notes, or changing advanced image controls does not ask the server to recalculate the storage estimate. The current figures remain visible while a new estimate is loading.'),
  ('Scheduled and cancelled thumbnails', 'Time-lapse Studio retains queued, cancelled, failed and interrupted jobs in history. A job with no source image shows a 16:9 status placeholder instead of a broken browser image. A partial or completed job uses its thumbnail if available, with the same-sized fallback if the file is missing. This does not delete the job or hide its error details.'),
  ('Safe early still photos', 'Live Camera photographs need exclusive access, but an upcoming scheduled job no longer blocks all stills three minutes beforehand. A normal still is allowed if more than roughly 25 seconds remain; manual long exposures require the requested shutter duration plus camera-transition margin. When already capturing or too near a job start, the photograph is refused to protect on-time recording.')
 ]),
 ('Notification email and links', [
  ('A richer notification email', 'Email uses HTML with a plain-text alternative for compatible mail apps. It shows a clear notice title, the recorded summary or job result and an Open in Moon Cheese link. The link still requires your own account sign-in; it never contains a password or a share token.'),
  ('Choose a trusted dashboard address', 'An administrator opens System Administration → Notification email links and enters a local dashboard URL, optionally also a public HTTPS domain. When a public HTTPS address is configured, links use it; otherwise links use the LAN address. If no local address was entered, the device attempts to determine its current LAN address. Never use a user-supplied browser Host header for these links.'),
  ('Opening local links', 'A local address may look like http://192.168.1.100:8000. It works only when connected to the home network or a correctly configured VPN. From mobile data away from home you need the public HTTPS domain. You can configure the local URL without NPM or Cloudflare.'),
  ('Links for jobs and summaries', 'Scheduled-job notices link to their observation detail page. Daily and weekly observation summaries open Notifications with the Digest filter. Fault and recovery notices open System Health. Browser push opens its target page when selected.'),
  ('Saving outgoing email', 'Under System Administration → Outgoing email (SMTP), enter provider settings and press Save SMTP configuration. A success confirmation appears on the same page. Use Send test email to sender separately; saving alone is not a delivery test. If the page reports a validation error, correct the relevant fields.'),
  ('Authentication and privacy', 'Avoid putting personal information in titles or summary bodies that may appear in push previews or email inboxes. System Administration and System Health require an administrator account. Links are not publicly shared media links.')
 ]),
 ('Delivery history and compact settings', [
  ('System Administration sections', 'All System Administration groups start collapsed: Settings export/import, Outgoing email (SMTP), Web Push contact, Recent delivery diagnostics, Notification email links, Network access and Maintenance. Expand one heading to edit its controls. Alerts and save confirmations remain at the top.'),
  ('Notifications page order', 'Notifications opens directly with the Notification centre at the top. Observation summary preferences and Email & browser notifications are separate collapsed panels below the notices. Expand only the section you need; saved preferences still determine the next report schedule.'),
  ('Recent delivery attempts', 'The System Administration diagnostics panel shows up to ten of the newest attempts. Select View complete delivery history for a separate page showing 20 at a time, with Email/Push and delivery-state filters. Each account also sees ten recent personal attempts under Email & browser notifications.'),
  ('Delivery status and retry', 'Sent means a mail or push provider accepted the message, not necessarily that it was read. Pending/Retry messages are eligible for later attempts. Failed means the retry limit was reached; admins can explicitly request a retry. Errors omit SMTP password contents.'),
  ('Log retention', 'Completed technical delivery records older than the administrator-selected 30, 60, 90 or 180 days (90 by default) are removed by the periodic delivery worker. Actual in-dashboard notifications, media and observation history are not removed by this cleanup. Pending and Retry delivery attempts are retained until processed, though their jobs may be invalidated on opt-out.')
 ])
])

# v0.9.9.5: production-preparation topics are grouped with their real menus.
GUIDE.extend([
 ('Installation and supported hardware', [
   ('Fresh installation', 'Download an approved complete Moon Cheese release or use the official public GitHub bootstrap when stable releases are available. The installer verifies all package files and runs the original complete install.sh. Dashboard addresses and the sudo uapctl credentials command appear at the very end of installation.'),
   ('Experimental low-resource devices', 'Pi 4 is the tested reference hardware. Pi 5 camera frame-rate options remain hardware-aware and experimental. Pi Zero 2 W is an experimental Raspberry Pi OS Lite setup with bundled Docker/NPM disabled by default; weaker hardware may have limited performance. Other Debian-based SBCs need compatible Picamera2 and OS packages, and must be tested separately.'),
   ('Upgrades and repair', 'The complete versioned archive supports fresh install, safe upgrade and same-version repair. Existing user accounts, credentials, recording data, configured services and proxy state are preserved. The installer refuses to proceed while a recording or scheduled rendering job is active.'),
 ]),
 ('Software updates', [
   ('Check for updates', 'Open Administration → System Health → Software updates. Select Check for updates to compare your version with the official public GitHub stable release. A private repository, no release, offline device or GitHub rate limit will be reported rather than silently failing.'),
   ('Update now', 'Available after an eligible newer release with the complete archive and SHA256SUMS has been identified in the selected official release channel. Enter your current administrator password in the Software updates panel before selecting Update now. An incorrect or missing password stops the request inside this panel. The privileged worker verifies the release and manifest, waits for recordings to finish and uses the existing full installer and backup. Updates never run automatically.'),
   ('Repair current version', 'Reinstalls exactly the installed version when its official GitHub release can be verified in the selected channel. Enter your current administrator password in the same Software updates panel before selecting Repair current version. Incorrect passwords do not start a repair. Repair does not reset accounts, configuration, network credentials or recordings. If the current version has no eligible release, the button is disabled.'),
   ('Administrator release notifications', 'Moon Cheese checks for a newer stable release at each administrator’s configured Observation summary time. It creates one notification per new release, with the existing opt-in email and Web Push channels and a permanent delivery ledger. The notification never starts an installation.'),
 ]),
 ('About Moon Cheese', [
   ('About and project links', 'Open Information → About Moon Cheese to see the official Moon Cheese artwork and neutral project description, followed by Dr Ravenholm’s first-person About Me text. Creator & Project, Socials, Music and Support cards provide labelled links to Transparent-Aluminium.net, the official GitHub repository and approved social, streaming, music, shop and donation destinations. All these links are optional external websites.'),
   ('Official icon and Home Screen', 'The official Moon Cheese icon is included as browser icons, iPhone/iPad touch icon and web app manifest icons. On a supported phone, Add to Home Screen can show the icon and launch the browser dashboard in standalone display. Existing shortcuts may need removal and re-adding to refresh a cached old icon.'),
 ]),
 ('Fullscreen video investigation', [
   ('Video in fullscreen', 'On a recorded detection, Scheduled Video or Time-lapse detail page, Fullscreen enlarges only the video/still frame, preserving the original recording. Use Exit fullscreen or Esc to return; play/pause remains available in the fullscreen overlay. Comparisons display only while paused.'),
 ]),
])

def help_html():
    """Organise Help in the same path as the real application menus.

    Source chapters retain their original anchor slugs so contextual links and
    previous bookmarks continue to work after the navigation is regrouped.
    """
    source={name:topics for name,topics in GUIDE}
    # Each group is (menu path, [(display heading, source chapters)]).
    hierarchy=[
      ('Getting started', [('Introduction',['Getting started'])]),
      ('Dashboard', [('Dashboard',['Dashboard']),
                     ('Storm activity',['Storm status and activity history'])]),
      ('Observations', [
        ('Recorded events',['Recorded events']),
        ('Video investigation',['Video investigation','Fullscreen video investigation']),
        ('Observation calendar',['Observation calendar']),
        ('Live Camera',['Live Camera']),
        ('Scheduled Video',['Scheduled Video']),
        ('Time-lapse Studio',['Time-lapse Studio','Time-lapse Studio — corrections','Time-lapse storage planning']),
        ('Photograph Gallery',['Photograph Gallery']),
        ('Public observation pages',['Public observation pages'])]),
      ('Administration', [
        ('Camera & Detector Settings',['Camera settings','Event-storm protection']),
        ('Accounts and access',['Accounts and access']),
        ('Notifications and reports',['Notifications and reports','Email delivery','Browser Push',
                                     'Notification email and links','Delivery history and compact settings']),
        ('Storage Management',['Storage Management','Storage Management — detailed guide']),
        ('System Administration',['System Administration','Backup contents and verification','Installation and supported hardware']),
        ('Network and remote access',['Network Setup','Cloudflare Tunnel management',
                                      'Local network addresses and Tunnel cleanup']),
        ('System Health',['System health and troubleshooting','Scheduled job recovery','Software updates'])]),
      ('Information', [('Version history',['Version history']),('About Moon Cheese',['About Moon Cheese'])])
    ]
    used=[name for _,groups in hierarchy for _,sources in groups for name in sources]
    if set(used)!=set(source) or len(used)!=len(source):
        raise ValueError('Help chapters cannot be lost or duplicated during navigation assembly.')
    menu=[];chapters=[];count=0;sections=0
    for index,(category,groups) in enumerate(hierarchy):
        submenu=[]
        for heading,names in groups:
            links=[];articles=[]
            for original in names:
                for title,description in source[original]:
                    ident=f'doc-{slug(original)}-{slug(title)}'
                    links.append(f'<a class="help-doc-link" href="#{ident}">{escape(title)}</a>')
                    articles.append(f'<article class="help-doc-item" id="{ident}"><h3>{escape(title)}</h3><p>{escape(description)}</p></article>')
                    count+=1
            sections+=1
            old_chapters=''.join(f'<span id="chapter-{slug(original)}" class="help-legacy-anchor"></span>' for original in names[1:])
            submenu.append(f'<details class="help-doc-group"><summary>{escape(heading)} <span>{len(links)}</span></summary><div class="help-doc-links">{"".join(links)}</div></details>')
            chapters.append(f'<section class="help-doc-chapter"><p class="help-doc-path">{escape(category)} / {escape(heading)}</p><h2 id="chapter-{slug(names[0])}">{escape(heading)}</h2>{old_chapters}{"".join(articles)}</section>')
        if category=='Administration':
            # System Administration is itself a menu; networking sits inside it
            # rather than appearing beside the top-level administrative pages.
            first=next(i for i,(title,_) in enumerate(groups) if title=='System Administration')
            second=next(i for i,(title,_) in enumerate(groups) if title=='Network and remote access')
            nested=(f'<details class="help-doc-subcategory"><summary>System Administration</summary>'
                    +submenu[first]+submenu[second]+'</details>')
            submenu=[item for i,item in enumerate(submenu) if i not in (first,second)]
            submenu.insert(first,nested)
        menu.append(f'<details class="help-doc-category"{" open" if index==0 else ""}><summary>{escape(category)}</summary>{"".join(submenu)}</details>')
    return f'''<h1>Help &amp; user guide</h1><p class="muted">Browse the same sections as the application, or search all topics.</p>
    <div class="help-searchbar"><label for="help-search" class="sr-only">Search help</label><input id="help-search" type="search" autocomplete="off" placeholder="Search documentation, e.g. shutter, calendar, tunnel" aria-controls="help-articles"><button type="button" id="help-clear">Clear</button></div>
    <p id="help-search-count" class="note" role="status">{count} topics in {sections} sections</p>
    <div class="help-doc-layout"><aside class="help-doc-sidebar" aria-label="Documentation topics"><div class="help-doc-side-title">DOCUMENTATION</div>{''.join(menu)}</aside>
    <div id="help-articles" class="help-doc-main">{''.join(chapters)}<p id="help-no-results" class="panel" hidden>No matching help topics. Try a different word.</p></div></div>
    <script src="/assets/help.js" defer></script>'''

# v0.9.9.4.10: self-contained networking Help in the established chapter format.
GUIDE.extend([('Cloudflare Tunnel management', [
 ('Managed Tunnel and saved state', 'Only administrators can configure the local cloudflared connector. The Tunnel panel shows the saved hostname, mode and unfinished setup stage. Non-secret account and zone IDs can be recalled; tokens and connector credentials remain hidden.'),
 ('Recovering an unfinished Tunnel', 'Enter the desired hostname and select Set up / Update. Moon Cheese attempts to recover a matching unfinished Moon Cheese Tunnel, or allows a new hostname without making the administrator clear an unrelated old progress record. Cloudflare CNAME records pointing at deleted Tunnels can be corrected for this hostname only. If a manual cleanup is wanted, the separate advanced controls distinguish local abandonment from provider-side deletion.'),
 ('Changing a working Tunnel hostname', 'Enter the replacement hostname in the same Tunnel setup form and select Set up / Update. Moon Cheese prepares a replacement connector and checks its Cloudflare health before switching the existing service. After the replacement connector is verified healthy, Moon Cheese removes the exact superseded Moon Cheese Tunnel and DNS record when Cloudflare confirms they are inactive and owned. If it cannot verify safe removal, the old resources are retained and the interface says cleanup is pending. Verify the new public HTTPS address separately.'),
 ('Disable and remove', 'Disable stops the local connector but retains its Cloudflare Tunnel and DNS record. Re-enable with the same saved hostname and credentials. Permanent removal is possible only after disabling; enter the exact saved hostname and confirm with an administrator password. The worker checks the Tunnel identity, local origin and DNS CNAME before deletion; an interrupted removal may need retry or provider review.'),
 ('IP confirmation when connections change', 'For static IPv4 changes, copy the expected new confirmation URL before applying the settings. The original browser tab may lose access when its sole network interface changes and cannot then keep polling. Use the expected URL or an independent wired or console connection. DHCP leases may receive a different address. The device itself controls confirmation expiry and automatic rollback; a browser countdown is informational.')
])])

# v0.9.9.4.11: place new help within the same searchable, self-contained guide.
GUIDE.extend([('Local network addresses and Tunnel cleanup', [
 ('Which IP address should I use?', 'In System Administration → Network and remote access → Local network only, view the current connected Ethernet and Wi-Fi IPv4 addresses. Docker virtual bridges are excluded. Clicking an address opens the local dashboard; sign-in is still required.'),
 ('Current interface and address assignment', 'Advanced static IPv4 shows the selected physical interface, its current address and whether it uses DHCP or static configuration. Changing the selection updates the summary without saving settings.'),
 ('Returning to DHCP safely', 'A DHCP address is assigned by the router and cannot be predicted before the lease is obtained. After the device verifies the new address, the original page shows a confirmation link if it is still connected. For changes that interrupt the only browser connection, use another local interface or console. Unconfirmed settings should automatically roll back after the deadline.'),
 ('Abandon versus remove unfinished Tunnel', 'Abandon unfinished setup clears only Moon Cheese local progress. To delete matching managed Cloudflare resources, use the separate advanced Remove unfinished Tunnel and its matching DNS record action, providing a scoped Cloudflare token and your administrator password. Moon Cheese verifies the saved Tunnel identity and matching CNAME before deleting, and checks Cloudflare again before reporting success.'),
 ('Existing Tunnel DNS prevents a new one', 'The wizard checks for existing DNS entries before creating a new Tunnel. Moon Cheese verifies that an existing inactive Tunnel belongs to the expected Moon Cheese hostname and localhost route. An orphaned CNAME pointing to a deleted Tunnel can be repaired automatically for the selected hostname. Unrelated active and non-Tunnel services remain protected. An unrelated record is never silently overwritten.'),
 ('Tunnel deletion status', 'Disable Tunnel only stops the local connector and preserves Cloudflare DNS and Tunnel records. Remove managed Tunnel requires disabling it first and deletes only the exact managed resources. If Cloudflare still lists the Tunnel or DNS record, Moon Cheese reports incomplete removal and preserves the record for retry instead of claiming success.')
])])
