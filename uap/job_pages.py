"""Reusable scheduling, job details, storage and public observation templates."""

JOBS_LIST = '''<h1>{{heading}}</h1>
<p class="note">Schedule and manage {{'continuous camera recordings' if kind=='scheduled_video' else 'time-lapse capture sessions'}}. Only administrators can create, stop or publish jobs.</p>
{% if error %}<div class="notice error">{{error}}</div>{% endif %}
<form method="get" class="row"><label>Search sessions<input name="q" placeholder="Title or notes" value="{{query}}"></label>
<label>Status<select name="status">{% for value in ['all','queued','capturing','rendering','archiving','complete','failed','cancelled','interrupted','missed'] %}
<option value="{{value}}" {% if selected_status==value %}selected{% endif %}>{{value|title}}</option>{% endfor %}</select></label>
<label>Public<select name="visibility"><option value="all">All</option><option value="public" {% if visibility=='public' %}selected{% endif %}>Public only</option><option value="private" {% if visibility=='private' %}selected{% endif %}>Private only</option></select></label>
<label class="checkline"><input type="checkbox" name="pinned" value="1" {% if pinned_only %}checked{% endif %}> Pinned only</label>
<button type="submit">Search / Filter</button></form>
{% if admin %}<details class="panel"><summary style="cursor:pointer;font-weight:700">＋ Create {{'scheduled video' if kind=='scheduled_video' else 'time-lapse'}}</summary>
<form method="post" style="padding-top:10px"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="kind" value="{{kind}}">
<label>Session title<input name="title" maxlength="120" required placeholder="Morning sunrise" value="{{form_values.get('title','')}}"></label>
<div class="options"><div><label>Start date and time<input required type="datetime-local" name="start" value="{{form_values.get('start',suggested_start)}}"></label></div>
<div class="note" style="padding:16px 0">Detector local time: <strong>{{tzname}}</strong><br>Change it under Settings → When to detect.</div></div>
<div class="options"><div><label>Duration (minutes)<input type="number" min="1" max="480" name="duration_minutes" value="{{form_values.get('duration_minutes','60')}}" required></label></div>
{% if kind=='scheduled_video' %}<div><label>Camera profile<select name="profile_slot"><option value="auto">Current saved profile / Automatic</option><option value="day">Day</option><option value="night">Night</option><option value="custom1">Custom 1</option><option value="custom2">Custom 2</option></select></label></div>{% endif %}
{% if kind=='timelapse' %}<div><label>Capture mode<select name="mode" id="job-mode"><option value="basic" {% if form_values.get('mode','basic')=='basic' %}selected{% endif %}>Basic — full-resolution, automatic camera settings</option><option value="advanced" {% if form_values.get('mode')=='advanced' %}selected{% endif %}>Advanced — full-resolution, manual camera controls</option></select></label></div>
<div><label>Capture interval (seconds)<select name="interval_seconds" id="job-interval"><option value="5" {% if form_values.get('interval_seconds','15')=='5' %}selected{% endif %}>5</option><option value="10" {% if form_values.get('interval_seconds','15')=='10' %}selected{% endif %}>10</option><option value="15" {% if form_values.get('interval_seconds','15')=='15' %}selected{% endif %}>15</option><option value="30" {% if form_values.get('interval_seconds','15')=='30' %}selected{% endif %}>30</option><option value="60" {% if form_values.get('interval_seconds','15')=='60' %}selected{% endif %}>60</option><option value="120" {% if form_values.get('interval_seconds','15')=='120' %}selected{% endif %}>120</option><option value="300" {% if form_values.get('interval_seconds','15')=='300' %}selected{% endif %}>300</option></select></label></div>
<div><label>Finished MP4 frame rate<select name="output_fps" id="job-fps"><option {% if form_values.get('output_fps','25')=='15' %}selected{% endif %}>15</option><option {% if form_values.get('output_fps','25')=='24' %}selected{% endif %}>24</option><option {% if form_values.get('output_fps','25')=='25' %}selected{% endif %}>25</option><option {% if form_values.get('output_fps','25')=='30' %}selected{% endif %}>30</option></select></label></div>{% else %}<input type="hidden" name="mode" value="basic">{% endif %}</div>
{% if kind=='timelapse' %}<div class="panel" id="job-advanced" hidden><h2>Advanced photography settings</h2>
<p class="note">Uses the same exposure, gain, focus and white-balance controls as Live Camera. Settings apply to this time-lapse only. Both Basic and Advanced capture full-resolution still photographs.</p>
<div class="options"><div><label>Exposure mode<select name="exposure_mode" id="job-exposure-mode"><option value="auto">Automatic</option><option value="manual" {% if form_values.get('exposure_mode')=='manual' %}selected{% endif %}>Manual long exposure</option></select></label></div>
<div><label>Exposure / shutter (milliseconds, max 112000)<input name="exposure_ms" id="job-exposure" type="number" min="0.1" max="112000" step="any" value="{{form_values.get('exposure_ms','1000')}}"></label></div>
<div><label>Analogue gain (1–16×)<input name="gain" type="number" min="1" max="16" step="any" value="{{form_values.get('gain','4')}}"></label></div>
<div><label>Focus<select name="focus_mode" id="job-focus"><option value="infinity">Infinity</option><option value="auto" {% if form_values.get('focus_mode')=='auto' %}selected{% endif %}>Autofocus</option><option value="manual" {% if form_values.get('focus_mode')=='manual' %}selected{% endif %}>Manual</option></select></label></div>
<div id="job-lens-wrap"><label>Lens position (0 ≈ infinity)<input name="lens_position" type="number" min="0" max="32" step="any" value="{{form_values.get('lens_position','0')}}"></label></div>
<div><label>White balance<select name="awb_enabled" id="job-awb"><option value="1">Automatic</option><option value="0" {% if form_values.get('awb_enabled')=='0' %}selected{% endif %}>Manual</option></select></label></div>
<div class="job-colour-control"><label>Red gain<input name="red_gain" type="number" min="0.1" max="8" step="any" value="{{form_values.get('red_gain','1.5')}}"></label></div>
<div class="job-colour-control"><label>Blue gain<input name="blue_gain" type="number" min="0.1" max="8" step="any" value="{{form_values.get('blue_gain','1.5')}}"></label></div>
<div><label>Brightness (-1 to 1)<input name="brightness" type="number" min="-1" max="1" step="any" value="{{form_values.get('brightness','0')}}"></label></div>
<div><label>Contrast (0.25 to 4)<input name="contrast" type="number" min="0.25" max="4" step="any" value="{{form_values.get('contrast','1')}}"></label></div>
<div><label>Saturation (0 to 3)<input name="saturation" type="number" min="0" max="3" step="any" value="{{form_values.get('saturation','1')}}"></label></div></div>
<p class="note">For manual shutter, exposure plus 1.5 seconds of processing allowance must be shorter than the selected capture interval.</p></div>
<div class="notice" id="job-estimate" role="status">Estimated storage required, available space and MP4 length will appear here.</div><p class="note">Full-resolution stills require space for both the temporary photographs and their source ZIP, plus video rendering and a 2 GiB safety reserve. The scheduler checks recent source-photo sizes; final sizes depend on scene detail. Capture stops if free space falls below 1 GiB.</p>{% endif %}
<p class="note">Jobs take exclusive camera priority. Motion recordings are finalised at the scheduled start; normal detection returns after the job completes. Event-storm limits do not apply to scheduled jobs. Concurrent jobs are refused.</p>
<button type="submit">Schedule {{'video recording' if kind=='scheduled_video' else 'time-lapse'}}</button></form>
<script src="{{url_for('jobs_js')}}" defer></script></details>{% endif %}
<section class="panel"><h2>{{'Saved Time-lapses' if kind=='timelapse' else 'Scheduled Video Sessions'}}</h2><p class="note">{{total}} matching · page {{page}} of {{pages}}</p>
{% if kind=='timelapse' %}<div class="photo-gallery-grid">{% for j in rows %}<a class="photo-gallery-card" href="{{url_for('job_detail',job_id=j.id)}}">
<div class="job-thumbnail">
{% if j.completed_frames or j.status=='complete' %}<img loading="lazy" src="{{url_for('job_thumb',job_id=j.id)}}" alt="{{j.title}} thumbnail" onerror="this.hidden=true;this.nextElementSibling.hidden=false">
<div class="job-thumb-placeholder" hidden><span class="job-thumb-icon" aria-hidden="true">▣</span><span>Thumbnail not available</span></div>
{% else %}<div class="job-thumb-placeholder"><span class="job-thumb-icon" aria-hidden="true">{{'◷' if j.status=='queued' else '▣' if j.status=='capturing' else '✕' if j.status=='cancelled' else '⚠'}}</span><span>{{'Awaiting capture' if j.status=='queued' else 'Capture starting' if j.status=='capturing' else 'No images captured' if j.status=='cancelled' else j.status|title+' — no thumbnail'}}</span></div>{% endif %}</div>
<strong>{{j.title}}</strong><span class="note">{{j.start_utc|localdt}} · {{j.status|title}}</span>
<span class="note">{{j.completed_frames}}{% if j.planned_frames %}/{{j.planned_frames}}{% endif %} frames {% if j.pinned %}· ★ Pinned{% endif %}{% if j.public %} · Public{% endif %}</span></a>
{% else %}<p>No time-lapse sessions match your filters.</p>{% endfor %}</div>
{% else %}<table><thead><tr><th>Title</th><th>Start (local)</th><th>Status</th><th>Progress</th></tr></thead><tbody>
{% for j in rows %}<tr><td><a href="{{url_for('job_detail',job_id=j.id)}}">{{j.title}}</a>{% if j.pinned %} <span class="pin">★ Pinned</span>{% endif %}{% if j.public %} <span class="pill">Public</span>{% endif %}
<div class="note">#{{j.id}} · {{j.profile_slot|title}}</div></td><td>{{j.start_utc|localdt}}</td><td>{{j.status|title}}</td><td>{{j.phase}}</td></tr>{% else %}<tr><td colspan="4">No scheduled sessions match your filters.</td></tr>{% endfor %}</tbody></table>{% endif %}
<div class="between">{% if page>1 %}<a class="button" href="{{url_for('jobs_list',kind=kind,page=page-1,q=query,status=selected_status,visibility=visibility,pinned='1' if pinned_only else None)}}">← Previous</a>{% endif %}
{% if page<pages %}<a class="button" href="{{url_for('jobs_list',kind=kind,page=page+1,q=query,status=selected_status,visibility=visibility,pinned='1' if pinned_only else None)}}">Next →</a>{% endif %}</div></section>'''

JOB_DETAIL = '''<p><a href="{{url_for('jobs_list',kind=job.kind)}}">← {{'Scheduled Video' if job.kind=='scheduled_video' else 'Time-lapse Studio'}}</a></p><h1>{{job.title}}</h1>
<p class="note">{{'Scheduled Video' if job.kind=='scheduled_video' else 'Time-lapse'}} #{{job.id}} · {{job.status|title}} {% if job.pinned %} · ★ Pinned{% endif %} {% if job.public %} · Public{% endif %}</p>
<div class="grid"><div class="panel"><div class="sub">Scheduled start (local)</div><strong>{{job.start_utc|localdt}}</strong></div>
<div class="panel"><div class="sub">Duration</div><strong>{{job.duration_seconds//60}} minutes</strong></div>
<div class="panel"><div class="sub">Progress</div><strong>{{job.phase or job.status}}</strong><p class="note">{{job.completed_frames}}{% if job.planned_frames %} / {{job.planned_frames}}{% endif %} captured frames</p></div></div>
{% if job.error %}<div class="notice error">{{job.error}}</div>{% endif %}
{% if job.status in ['queued','capturing','rendering','archiving','finalising'] and admin %}<form method="post" action="{{url_for('job_cancel',job_id=job.id)}}" onsubmit="return confirm('Stop this scheduled observation? Partial files will be retained.')"><input type="hidden" name="csrf" value="{{csrf}}"><button type="submit" class="danger">Cancel / stop job</button></form>{% endif %}
<div class="cols"><section class="panel"><h2>{{'Time-lapse video' if job.kind=='timelapse' else 'Recorded video segments'}}</h2>
{% if job.kind=='scheduled_video' and segments %}<p class="note">Long videos are recorded in short segments to reduce the risk of losing the entire recording.</p><div class="row">{% for part in segments %}<a class="button" href="{{url_for('job_detail',job_id=job.id,part=loop.index)}}">Part {{loop.index}}</a>{% endfor %}</div>{% endif %}
{% if media_url %}    <section class="investigator" aria-label="Video investigation player" data-investigator data-event-id="{{ job.id }}" data-fps="{{ video_fps }}">
      <div class="investigator-stage" id="investigator-stage" tabindex="0" aria-label="Video image; use the comparison slider when paused">
        <div class="investigator-media" id="investigator-media">
          <video id="investigator-video" playsinline preload="metadata" src="{{ media_url }}" aria-label="Event recording"></video>
          <div class="investigator-compare" id="investigator-compare" hidden aria-hidden="true">
            <canvas class="compare-canvas" id="investigator-compare-left"></canvas>
            <div class="compare-right" id="investigator-compare-right-clip"><canvas class="compare-canvas" id="investigator-compare-right"></canvas></div>
          </div>
        </div>
        <div class="compare-ui" id="investigator-compare-ui" hidden>
          <span class="compare-label compare-label-left" id="investigator-label-left">Original</span>
          <span class="compare-label compare-label-right" id="investigator-label-right">Enhanced</span>
          <span class="compare-divider" id="investigator-compare-divider"></span>
          <input class="compare-slider" type="range" min="0" max="100" step="1" value="50" id="investigator-compare-slider" aria-label="Slide to reveal left or right image">
        </div>
        <div class="investigator-fullscreen-controls"><button type="button" id="investigator-fullscreen-play" aria-label="Play or pause video">▶ / ❚❚</button><button type="button" id="investigator-exit-fullscreen" aria-label="Exit fullscreen">Exit fullscreen ✕</button></div>
      </div>
      <div class="row between"><span id="investigator-time" class="investigator-time">00:00.000 / --:--.---</span><span class="note">Source frame rate: {{ '%.2f'|format(video_fps) }} fps</span></div>
      <label class="sr-only" for="investigator-seek">Seek through recording</label>
      <input type="range" class="investigator-timeline" id="investigator-seek" min="0" max="1000" step="1" value="0" aria-label="Seek through recording">
      <div class="investigator-tools" role="group" aria-label="Playback controls">
        <button type="button" id="investigator-play">▶ Play</button>
        <button type="button" id="investigator-back" title="Step back by one nominal frame">◀ Frame</button>
        <button type="button" id="investigator-next" title="Step forward by one nominal frame">Frame ▶</button>
        <label for="investigator-speed">Speed <select id="investigator-speed"><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label>
      </div>
      <div class="investigator-tools" role="group" aria-label="Playback view">
        <label for="investigator-view">Playback view
          <select id="investigator-view"><option value="original">Original</option><option value="detection">Detection (grayscale)</option><option value="enhanced">Low-light enhanced</option></select>
        </label>
        <span class="note">Selected view plays as one video; the source MP4 is unchanged.</span>
      </div>
      <div class="investigator-compare-controls investigator-compare-row" aria-label="Paused-frame comparison settings">
        <button type="button" id="investigator-compare-toggle" aria-pressed="false" disabled>Compare frame</button>
        <label for="investigator-view-left">Left
          <select id="investigator-view-left"><option value="original">Original</option><option value="detection">Detection (grayscale)</option><option value="enhanced">Low-light enhanced</option></select>
        </label>
        <label for="investigator-view-right">Right
          <select id="investigator-view-right"><option value="original">Original</option><option value="detection">Detection (grayscale)</option><option value="enhanced" selected>Low-light enhanced</option></select>
        </label>
        <span id="investigator-compare-info" class="note" role="status">Pause the recording to compare a frame.</span>
      </div>
      <div class="investigator-tools" role="group" aria-label="Image investigation controls">
        <label for="investigator-zoom">Zoom <input type="range" id="investigator-zoom" min="1" max="4" step="0.25" value="1"><span id="investigator-zoom-label">1×</span></label>
        <button type="button" id="investigator-reset">Reset image</button>
        <button type="button" id="investigator-fullscreen">Fullscreen</button>
      </div>
      <div class="investigator-tools" role="group" aria-label="Image enhancement controls">
        <label for="investigator-brightness">Brightness <input type="range" id="investigator-brightness" min="50" max="200" value="100" step="5"><span id="investigator-brightness-label">100%</span></label>
        <label for="investigator-contrast">Contrast <input type="range" id="investigator-contrast" min="50" max="200" value="100" step="5"><span id="investigator-contrast-label">100%</span></label>
      </div>
      <div class="investigator-tools"><button type="button" id="investigator-snapshot">Save current frame PNG</button>
        <a class="button" href="{{ media_url }}?download=1">Download original MP4</a></div>
      <p class="investigator-status" id="investigator-status" role="status">Player loading…</p>
      <p class="note">Comparison appears only while paused and returns after you pause again. Frame stepping seeks approximately one recorded frame; browser decoding can limit precision. Low-light enhancement is image processing of the mixed visible/infrared NoIR recording, <strong>not</strong> a separate infrared image. Zoom, processing, and saved PNGs do not modify the source MP4.</p>
      <script src="{{ url_for('investigator_js') }}" defer></script>
    </section>
{% else %}<p class="note">{{'Rendering or capture is not finished yet.' if job.status in ['capturing','rendering','archiving','queued'] else 'No finished video is available. Partial files may be retained for recovery.'}}</p>{% endif %}
{% if job.kind=='timelapse' %}<h2>Source photographs</h2><p class="note">Source frames are kept apart from the Photograph Gallery.</p>
{% if zip_ready and admin %}<a class="button" href="{{url_for('job_media',job_id=job.id,filename='source-frames.zip',download=1)}}">Download source photograph ZIP</a>
{% else %}<p class="note">Source ZIP is not available. If rendering failed, loose frames are retained for recovery.</p>{% endif %}{% endif %}
<p class="note">{{job.mode|title}} capture · {% if job.kind=='timelapse' %}{{job.interval_seconds}}-second interval · {{job.output_fps}} fps output · {{job.planned_frames}} planned images{% else %}Continuous video during scheduled window{% endif %}</p></section>
<section class="panel"><h2>Observation details</h2>
{% if admin %}<form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="action" value="save">
<label>Title<input name="title" maxlength="120" required value="{{job.title}}"></label>
<label>Notes<textarea name="note" maxlength="8000">{{job.note}}</textarea></label>
<label class="checkline"><input type="checkbox" name="pinned" value="1" {% if job.pinned %}checked{% endif %}> Pin and protect this session</label>
<label class="checkline"><input type="checkbox" name="public" value="1" {% if job.public %}checked{% endif %} {% if job.status!='complete' %}disabled{% endif %}> Allow finished video on public page</label>
<label class="checkline"><input type="checkbox" name="public_note" value="1" {% if job.public_note %}checked{% endif %}> Show observation notes publicly</label>
<p class="note">Source photographs stay private, even when a time-lapse MP4 is shared publicly.</p><button type="submit">Save details</button></form>
{% else %}<p style="white-space:pre-wrap">{{job.note}}</p>{% endif %}
</section></div>'''

JOB_STORAGE = '''<h1>Storage Management — {{heading}}</h1><p><a href="{{url_for('storage_page')}}">← Storage Management</a></p>
<p class="note">Pinned or publicly shared sessions are protected. Individual session and source-ZIP deletion require confirmation.</p>
<p class="note">{{total}} jobs · page {{page}} of {{pages}}</p>
<section class="panel"><table><thead><tr><th>Session</th><th>Status</th><th>Files</th><th>Actions</th></tr></thead><tbody>
{% for j in rows %}<tr><td><a href="{{url_for('job_detail',job_id=j.id)}}">{{j.title}}</a><div class="note">#{{j.id}} · {{j.start_utc|localdt}}</div></td>
<td>{{j.status|title}}{% if j.pinned or j.public %} · Protected{% endif %}</td>
<td>{{'%.1f'|format(j.size/1048576)}} MB</td>
<td>{% if j.status in terminal and not j.pinned and not j.public %}
<form method="post" onsubmit="return confirm('Permanently delete this session and all of its files?')"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="job_id" value="{{j.id}}"><input type="hidden" name="action" value="delete"><button class="danger" type="submit">🗑 Delete</button></form>
{% if j.kind=='timelapse' and j.has_zip %}<form method="post" style="margin-top:6px" onsubmit="return confirm('Delete source ZIP and keep the finished MP4?')"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="job_id" value="{{j.id}}"><input type="hidden" name="action" value="delete_sources"><button type="submit">Delete source ZIP only</button></form>{% endif %}
{% else %}—{% endif %}</td></tr>{% else %}<tr><td colspan="4">No sessions yet</td></tr>{% endfor %}</tbody></table>
<div class="between">{% if page>1 %}<a class="button" href="{{url_for('job_storage',kind=kind,page=page-1)}}">← Previous</a>{% endif %}
{% if page<pages %}<a class="button" href="{{url_for('job_storage',kind=kind,page=page+1)}}">Next →</a>{% endif %}</div></section>'''
