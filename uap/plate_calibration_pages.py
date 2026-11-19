"""Moon Cheese offline calibration user interface; data remains private."""
CALIBRATION_PAGE = r"""
<h1>Camera Calibration</h1>
<p class="note">Sky Maps → Camera Calibration. Identify the stars in a full-resolution night photograph and measure where the camera is pointing. Entirely offline after initial setup; no API key.</p>
{% if setup_error %}<p class="error">{{ {'password':'Incorrect administrator password.','ack':'Please confirm installation authorisation.','busy':'Installation request is already pending.','download':'A dataset download is already pending or could not be queued.','import':'The uploaded ZIP could not be validated. Use the original official W08 archive, unchanged.'}.get(setup_error,'Calibration setup action was not accepted.') }}</p>{% endif %}
{% if setup_notice %}<p class="notice">{{'ASTAP installation was queued. This page will show its status once the optional package installation finishes.' if setup_notice=='queued' else ('Your W08 ZIP was validated and installed.' if setup_notice=='imported' else 'W08 star index download was queued. Refresh or wait for status to update.')}}</p>{% endif %}
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
 <form id="plate-index-upload" method="post" action="{{url_for('plate_calibration_upload_w08')}}" enctype="multipart/form-data"><input name="csrf" type="hidden" value="{{csrf}}">
  <label>Or upload the original ASTAP W08 ZIP from your computer
   <input type="file" name="archive" accept=".zip,application/zip" required></label>
  <button type="submit">Upload &amp; validate W08 ZIP</button>
  <p class="note">Use this option if SourceForge displays a download page instead of sending the ZIP directly. The file is checked before replacing local data. Maximum 5 MB.</p>
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
  <div class="plate-review-photo-wrap" id="plate-review-wrap">
   <img id="plate-review-photo" alt="Original full-resolution calibration photograph" class="plate-review-photo">
   <div class="plate-visual-overlay" id="plate-visual-overlay" aria-label="Reference-star positions cross-checked with the photograph"></div>
   <div class="plate-centre" id="plate-centre" aria-label="Image centre" title="Solved image centre">+</div>
   <div class="plate-north" id="plate-north" hidden><span id="plate-north-arrow">↑</span> N</div>
  </div>
  <p class="note" id="plate-marker-status">Waiting for reference-star cross-check.</p>
  <div class="row" style="gap:15px;align-items:center;flex-wrap:wrap">
   <label for="plate-overlay-opacity" style="margin:0">Overlay opacity: <strong id="plate-opacity-label">80%</strong></label>
   <input id="plate-overlay-opacity" type="range" min="0" max="100" step="5" value="80" style="flex:1;min-width:150px">
   <button type="button" id="plate-original">Original photo</button>
  </div>
  <div class="row" style="gap:12px;flex-wrap:wrap">
   <label class="checkline"><input type="checkbox" id="plate-show-markers" checked> Cross-checked stars</label>
   <label class="checkline"><input type="checkbox" id="plate-show-labels" checked> Star names</label>
   <label class="checkline"><input type="checkbox" id="plate-show-centre" checked> Image centre</label>
   <label class="checkline"><input type="checkbox" id="plate-show-north" checked> Celestial north</label>
  </div>
  <div class="grid plate-result-grid">
   <div><span class="muted">Camera centre bearing</span><div class="value" id="plate-bearing">—</div></div>
   <div><span class="muted">Camera centre elevation</span><div class="value" id="plate-elevation">—</div></div>
   <div><span class="muted">Image-up heading</span><div class="value" id="plate-up">—</div></div>
   <div><span class="muted">Approximate field of view</span><div class="value" id="plate-field">—</div></div>
  </div>
  <details class="setting-section panel"><summary>Advanced measurements</summary><div class="setting-content">
   <p>Solved sky coordinates: <strong id="plate-radec">—</strong></p>
   <p>ASTAP image rotation: <strong id="plate-rotation">—</strong></p>
   <p>Independent reference/photo star cross-checks: <strong id="plate-matched">—</strong></p>
   <p class="note">A successful ASTAP solution provides WCS coordinates; the green circles are drawn only where the separate star catalogue and actual photograph agree. They are not a claim about ASTAP's internal quad matches.</p>
  </div></details>
  <p id="plate-warning" class="note"></p>
  <div class="row" style="gap:10px;flex-wrap:wrap">
   <button type="button" id="plate-save">Save this calibration</button>
   <button type="button" id="plate-retry">Try another photograph</button>
  </div>
  <p class="note">Saving stores a separate calibration record. Existing camera orientation, exposure, gain and rotation are not overwritten.</p>
 </div>
 {% if support.calibration %}
 <hr><h3>Last saved calibration</h3>
 <p>Saved {{support.calibration.saved_utc[:19]}} UTC · Centre RA {{support.calibration.ra_deg}}°, Dec {{support.calibration.dec_deg}}°
 {% if support.calibration.bearing_deg is not none %}· Bearing {{support.calibration.bearing_deg}}°, elevation {{support.calibration.elevation_deg}}°{% endif %}</p>
 <p class="note">If you physically move or rotate the camera, solve and save again. Precise edge overlays also require lens-distortion calibration.</p>
 {% endif %}
</section>
<style>
 .plate-review-photo-wrap{position:relative;max-width:100%;border:1px solid var(--line,#43566b);border-radius:10px;overflow:hidden;background:#081320;line-height:0;margin:12px 0}
 .plate-review-photo{width:100%;height:auto;display:block;object-fit:contain}
 .plate-visual-overlay{position:absolute;inset:0;pointer-events:none;transition:opacity .1s}
 .plate-star-point{position:absolute;width:14px;height:14px;border:2px solid #3df0ab;border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 4px #071522;background:rgba(40,230,157,.07)}
 .plate-star-name{position:absolute;top:-13px;left:12px;white-space:nowrap;color:#ffe6a8;text-shadow:0 1px 3px #091421;font-size:12px;line-height:1.2;max-width:150px;overflow:hidden}
 .plate-centre{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:32px;color:#6de9fa;text-shadow:0 1px 4px #081320;line-height:1;pointer-events:none}
 .plate-north{position:absolute;top:14px;right:14px;background:rgba(5,17,29,.83);border-radius:6px;padding:6px;color:#8bf3ff;font-size:17px;line-height:1.4;pointer-events:none}
 .plate-result-grid{margin:12px 0}
</style>
<script src="{{url_for('plate_calibration_js')}}" defer></script>
"""
