"""Dashboard templates for astronomical maps and their own settings."""
SKY_MAPS = '''
<h1>Sky Maps</h1>
<p class="note">Offline astronomy above the configured detector, plus predicted satellite ground tracks on Earth. A map prediction is not proof of an observation's identity.</p>
{% if missing_location %}<p class="error">Detector location is not configured. Open <a href="{{url_for('settings')}}">Detector Settings</a> and enter latitude and longitude before using the maps.</p>{% endif %}
{% if event_location_missing %}<p class="notice">This older observation has no saved GPS coordinates. The maps use the detector's current location as an approximation.</p>{% endif %}
{% if not installed %}<p class="notice">No astronomical datasets are installed. An administrator can start <a href="{{url_for('sky_maps_data')}}">Sky Maps → Data &amp; Updates</a> to download them once; the maps then work offline.</p>{% endif %}
<div id="sky-map-root" data-lat="{{lat}}" data-lon="{{lon}}" data-event-time="{{event_time}}" data-event-id="{{event_id}}" data-location-ready="{{1 if not missing_location else 0}}">
<section class="panel">
  <div class="row between"><h2>Find &amp; track objects</h2><span class="note" id="sky-time-label">—</span></div>
  <div class="row" style="gap:12px;align-items:flex-start;flex-wrap:wrap">
    <div style="flex:2;min-width:210px"><label for="sky-search">Object search</label><input id="sky-search" placeholder="ISS, NORAD number, Mars, Polaris…" autocomplete="off"><div id="sky-results" class="sky-search-results"></div></div>
    <details class="sky-layers"><summary>☷ Local sky layers</summary><div>
      <label class="checkline"><input type="checkbox" data-sky-layer="stars"> Stars</label>
      <label class="checkline"><input type="checkbox" data-sky-layer="constellations"> Constellation lines and names</label>
      <label class="checkline"><input type="checkbox" data-sky-layer="planets"> Sun, Moon and planets</label>
      <label class="checkline"><input type="checkbox" data-sky-layer="satellites"> Satellites</label>
      <label class="checkline"><input type="checkbox" data-sky-layer="deep_sky"> Bright deep-sky objects</label>
    </div></details>
    <details class="sky-layers"><summary>☷ Earth map layers</summary><div>
      <label class="checkline"><input type="checkbox" data-earth-layer="land"> World coastlines</label>
      <label class="checkline"><input type="checkbox" data-earth-layer="satellites"> Satellites</label>
      <label class="checkline"><input type="checkbox" data-earth-layer="track"> Selected satellite ground track</label>
      <label class="checkline"><input type="checkbox" data-earth-layer="detector"> Detector position</label>
    </div></details>
  </div>
  <p class="note" id="sky-selection">Select an object from search to highlight it on the map.</p>
  <p class="note" id="sky-status" role="status">Reading local sky catalogues…</p>
</section>
<div class="sky-map-grid">
  <section class="panel"><h2>Sky above the detector</h2><p class="note">All-sky view · North at top · Zenith at centre · Horizon at edge</p><canvas id="sky-local" class="sky-map-canvas" aria-label="Calculated sky positions"></canvas></section>
  <section class="panel"><h2>Earth &amp; satellite tracking</h2><p class="note">Selected orbital objects and approximate predicted ground tracks</p><canvas id="sky-earth" class="sky-map-canvas" aria-label="Satellite ground track and world map"></canvas></section>
</div>
<section class="panel"><h2>Shared timeline</h2>
  <label for="sky-datetime">Exact date and time (your browser's local timezone)</label>
  <div class="row" style="gap:10px;align-items:end;flex-wrap:wrap">
    <input type="datetime-local" id="sky-datetime" min="1849-01-01T00:00" max="2150-12-31T23:59" style="flex:2;min-width:210px">
    <button type="button" id="sky-now">↺ Reset to Now</button>
    <button type="button" id="sky-play">▶ Play</button>
    <div><label for="sky-speed">Playback speed</label><select id="sky-speed"><option value="1">1×</option><option value="10">10×</option><option value="60" selected>60×</option><option value="300">300×</option><option value="3600">3600×</option></select></div>
  </div>
  <label for="sky-offset">Quick time offset from now (hours)</label><input id="sky-offset" type="range" min="-24" max="24" value="0" step="1">
  <p class="note">Satellite positions are predictions based on orbital elements, not a live GPS feed. Outdated or missing elements reduce confidence; historical records may not have suitable archived data.</p>
</section></div>
<script src="{{url_for('sky_maps_js')}}" defer></script>
'''
SKY_DATA = '''
<h1>Sky Maps — Data &amp; Updates</h1>
<p class="note">All sections are collapsed by default. Astronomical datasets are downloaded to the Pi only when requested or when a scheduled satellite refresh is due. They are kept outside the software release and remain available offline.</p>
{% if saved %}<div class="notice">Satellite update schedule saved.</div>{% endif %}
{% if queued %}<div class="notice">{{queued}} download queued for the background Sky Data worker. Refresh to see its progress and last result.</div>{% endif %}
{% if error %}<p class="error">{{error}}</p>{% endif %}
<details class="panel setting-section"><summary>All astronomical data — Download All</summary><div class="setting-content">
  <p class="note">Download All fetches missing datasets only. Successfully installed files, including the planetary ephemeris, are not downloaded again unnecessarily. Failed downloads retain previously working files.</p>
  <form method="post" action="{{url_for('sky_maps_data_action')}}"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="kind" value="all"><button type="submit">Download all missing data</button></form>
  <p class="note">Installed {{count}} / {{statuses|length}} datasets · {{'%.2f'|format(total_bytes/1048576)}} MB local data.</p>
</div></details>
{% for key,item in statuses.items() %}
<details class="panel setting-section"><summary>{{item.label}} — {{'Installed' if item.installed else ('Download failed' if item.state == 'error' else 'Not yet installed')}}</summary><div class="setting-content">
  <p><strong>Status:</strong> {{item.state or ('Installed' if item.installed else 'Not installed')}} · <strong>On disk:</strong> {{'%.2f'|format(item.bytes/1048576)}} MB</p>
  <p><strong>Last successful download:</strong> {{item.download_utc or 'Never'}} UTC</p>
  <p><strong>Last attempt:</strong> {{item.attempt_utc or 'Never'}} UTC</p>
  {% if item.error %}<p class="error">{{item.error}}</p>{% endif %}
  {% for url in item.source %}<p class="note">Source: <a href="{{url}}" target="_blank" rel="noopener noreferrer">{{url}}</a></p>{% endfor %}
  {% if key == 'satellites' %}
    <form method="post" action="{{url_for('sky_maps_schedule')}}"><input type="hidden" name="csrf" value="{{csrf}}">
      <label class="checkline"><input type="checkbox" name="auto" {% if preferences.auto_satellites %}checked{% endif %}> Refresh satellite orbital data automatically each day</label>
      <div class="options"><div><label>Daily hour (detector local time)</label><input type="number" name="hour" min="0" max="23" value="{{preferences.satellite_hour}}"></div>
      <div><label>Minute</label><input type="number" name="minute" min="0" max="59" value="{{preferences.satellite_minute}}"></div></div>
      <p class="note"><strong>Next eligible satellite check:</strong> {{next_satellite}}</p>
      <p class="note">Timezone: {{timezone}}. CelesTrak may publish some objects with older orbital epochs. The schedule checks at the next worker tick after the selected time. After a provider error, automatic requests pause until you manually retry; provider intervals and throttling still apply.</p>
      <button type="submit">Save satellite schedule</button>
    </form>
  {% else %}<p class="note">No automatic daily download. The stored dataset remains usable until intentionally replaced.</p>{% endif %}
  <form method="post" action="{{url_for('sky_maps_data_action')}}"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="kind" value="{{key}}"><button type="submit">{{'Update now' if item.installed else 'Download now'}}</button></form>
</div></details>
{% endfor %}
<p><a href="{{url_for('sky_maps')}}">← Return to Sky Maps</a></p>
'''
