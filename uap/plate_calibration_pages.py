"""Moon Cheese offline calibration user interface; data remains private."""
CALIBRATION_PAGE = r"""
<h1>Camera Calibration</h1>
<p class="note">Sky Maps → Camera Calibration. Identify the stars in a full-resolution night photograph and measure where the camera is pointing. Entirely offline after initial setup; no API key.</p>
{% if setup_error %}<p class="error">{{ {'password':'Incorrect administrator password.','ack':'Please confirm installation authorisation.','busy':'Installation request is already pending.','download':'A dataset download is already pending or could not be queued.'}.get(setup_error,'Calibration setup action was not accepted.') }}</p>{% endif %}
{% if setup_notice %}<p class="notice">{{'ASTAP installation was queued. This page will show its status once the optional package installation finishes.' if setup_notice=='queued' else 'W08 star index download was queued. Refresh or wait for status to update.'}}</p>{% endif %}
<section class="panel" id="plate-calibration" data-csrf="{{csrf}}" data-initial-photo="{{initial_photo}}" data-photography-url="{{url_for('photo_status',token='__TOKEN__')}}">
 <h2>1. Plate-solving support</h2>
 <p>ASTAP command-line solver: <strong id="plate-solver-state">{{'Installed' if support.solver_installed else 'Not installed'}}</strong><br>W08 wide-field index: <strong id="plate-index-state">{{'Downloaded' if support.index_installed else 'Not downloaded'}}</strong></p>
 {% if support.setup.message %}<p class="note" id="plate-setup-message">{{support.setup.message}}</p>{% else %}<p class="note" id="plate-setup-message"></p>{% endif %}
 {% if not support.solver_installed %}
 <form id="plate-install-form" method="post" action="{{url_for('plate_calibration_install')}}"><input name="csrf" type="hidden" value="{{csrf}}">
  <p class="note">Install the optional Debian <code>astap-cli</code> package from your configured signed system repository. This does not change the camera or monitoring settings. Internet is required once.</p>
  <label>Administrator password <input type="password" name="password" required autocomplete="current-password"></label>
  <label class="checkline"><input type="checkbox" name="agree" value="yes" required> I authorise installation of the ASTAP package on this Pi.</label>
  <button type="submit">Install ASTAP solver</button>
 </form>
 {% endif %}
 {% if not support.index_installed %}
 <form id="plate-index-form" method="post" action="{{url_for('plate_calibration_index')}}"><input name="csrf" type="hidden" value="{{csrf}}">
  <button type="submit">Download W08 star index (about 330 KB)</button>
  <span class="note">Stored persistently with Sky Maps data; not in the release archive.</span>
 </form>
 {% endif %}
 <p class="note">Solving requires both components. <a href="{{url_for('sky_maps_data')}}">View data download status</a>. ASTAP's W08 index is intended for wide-angle images; very wide or distorted camera images may not solve.</p>
</section>
<section class="panel"><h2>2. Choose a calibration photograph</h2>
 <div class="cols">
 <div>
 <h3>Take calibration photo now</h3><p class="note">Uses the existing exclusive Photography capture system. Recording briefly pauses and then resumes. Only take one when a scheduled camera job isn't about to start.</p>
 <div class="options"><label>Exposure (seconds)<input type="number" id="plate-exposure" min="0.5" max="60" value="8" step="0.5"></label>
 <label>Analogue gain<input type="number" id="plate-gain" min="1" max="16" step="0.5" value="8"></label></div>
 <button type="button" id="plate-capture">Take calibration photo now</button>
 </div>
 <div>
 <h3>Use saved photograph</h3>
 <label>Choose a full-resolution photograph<select id="plate-saved-photo"><option value="">Select a saved photo…</option>{% for photo in saved_photos %}<option value="{{photo.token}}">{{photo.title or photo.modified[:16]}} · {{photo.modified[:16]}} UTC · {{photo.format.upper()}}</option>{% endfor %}</select></label>
 <p class="note"><a href="{{url_for('photo_gallery')}}">Browse saved photographs</a>. Images captured before calibration support was installed can be used too.</p>
 </div>
 </div>
 <p id="plate-capture-status" class="note" role="status"></p>
 <div id="plate-selected-area" hidden>
  <h3>Selected photograph</h3><img id="plate-image" class="eventimg" alt="Saved star photograph selected for offline calibration" style="max-height:520px">
  <label>Approximate vertical field of view in degrees <input type="number" id="plate-fov" min="20" max="85" step="1" value="67"></label>
  <p class="note">Camera Module 3 Wide: start around 67° vertically. ASTAP needs an approximate scale, not a precise preset.</p>
  <button type="button" id="plate-solve" {% if not support.solver_installed or not support.index_installed %}disabled{% endif %}>Calibrate from these stars</button>
 </div>
 <p id="plate-error" class="error" role="alert"></p>
</section>
<section class="panel"><h2>3. Review plate-solving result</h2>
 <p id="plate-job-status" role="status" class="note">No plate solution requested yet.</p>
 <div id="plate-result" hidden>
  <div class="grid"><div><span class="muted">Camera centre bearing</span><div class="value" id="plate-bearing">—</div></div>
   <div><span class="muted">Camera centre elevation</span><div class="value" id="plate-elevation">—</div></div>
   <div><span class="muted">Image-up orientation</span><div class="value" id="plate-up">—</div></div>
   <div><span class="muted">Solved sky coordinates</span><div class="value" id="plate-radec">—</div></div>
   <div><span class="muted">Image rotation (ASTAP)</span><div class="value" id="plate-rotation">—</div></div></div>
  <p id="plate-warning" class="note"></p>
  <button type="button" id="plate-save">Save this calibration</button>
  <span class="note">Only saves a separate calibration record. Existing camera orientation, exposure, gain and rotation are not overwritten.</span>
 </div>
 {% if support.calibration %}
 <hr><h3>Last saved calibration</h3>
 <p>Saved {{support.calibration.saved_utc[:19]}} UTC · Centre RA {{support.calibration.ra_deg}}°, Dec {{support.calibration.dec_deg}}°
 {% if support.calibration.bearing_deg is not none %}· Bearing {{support.calibration.bearing_deg}}°, elevation {{support.calibration.elevation_deg}}°{% endif %}</p>
 <p class="note">If you physically move or rotate the camera, solve and save again. Precise edge overlays also require lens-distortion calibration.</p>
 {% endif %}
</section>
<script src="{{url_for('plate_calibration_js')}}" defer></script>
"""
