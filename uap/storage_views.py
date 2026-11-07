"""Unified storage overview and consistent, protected per-media administration."""
STORAGE_PAGE = '''<h1>Storage Management</h1>
<p class="note">Manage stored files for every observation type here. Scheduled Video and Time-lapse Studio remain separate, fully functional pages for creating and reviewing jobs.</p>
{% if deleted is not none %}<div class="notice">Updated {{deleted}} item(s). Approximately {{'%.1f'|format(reclaimed/1048576)}} MB reclaimed.</div>{% endif %}
<div class="grid">
<div class="panel"><div class="sub">Available on SD card</div><div class="value">{{'%.2f'|format(space.free/1073741824)}} GiB</div></div>
<div class="panel"><div class="sub">Used on SD card</div><div class="value">{{'%.2f'|format(space.used/1073741824)}} GiB</div></div>
<div class="panel"><div class="sub">Total usable capacity</div><div class="value">{{'%.2f'|format(space.total/1073741824)}} GiB</div></div>
</div>
<div class="panel">
<nav class="row storage-tabs" aria-label="Storage categories" style="margin-bottom:18px">
{% for tab_id,name in [('overview','Overview'),('recordings','Recordings'),('photos','Photographs'),('scheduled_video','Scheduled Videos'),('timelapse','Time-lapses')] %}
<a class="button {{'storage-tab-active' if tab==tab_id else ''}}" href="{{url_for('storage_page',tab=tab_id)}}" {% if tab==tab_id %}aria-current="page"{% endif %}>{{name}}</a>{% endfor %}
</nav>
{% if tab=='overview' %}
<div class="panel" style="background:#102a38"><div class="sub">Potentially reclaimable by confirmed media deletion</div><div class="value">{{'%.2f'|format(report.reclaimable_bytes/1073741824)}} GiB</div><p class="note">Only currently eligible stored media is included. Nothing will be deleted automatically. Review items carefully before choosing to remove them.</p></div>
<h2>Whole-device storage breakdown</h2>
<p class="note">These figures include application files and Raspberry Pi OS. Measurements represent disk space occupied; they are not all safe to delete.</p>
<table><thead><tr><th>Storage type</th><th>On SD card</th></tr></thead><tbody>
{% for label,value in report.categories.items() %}<tr><td>{{label}}</td><td>{% if value is not none %}{{'%.2f'|format(value/1073741824)}} GiB{% else %}Unavailable{% endif %}</td></tr>{% endfor %}
<tr><th>Used space (filesystem)</th><th>{{'%.2f'|format(report.used/1073741824)}} GiB</th></tr>
<tr><th>Available space (filesystem)</th><th>{{'%.2f'|format(report.free/1073741824)}} GiB</th></tr></tbody></table>
<h2 style="margin-top:20px">Scheduled job storage</h2>
<table><thead><tr><th>Type</th><th>Sessions</th><th>Stored data</th></tr></thead><tbody>
<tr><td>Scheduled Videos</td><td>{{report.job_counts.get('scheduled_video',0)}}</td><td>{{'%.2f'|format(report.job_sizes.scheduled_video/1073741824)}} GiB</td></tr>
<tr><td>Time-lapses</td><td>{{report.job_counts.get('timelapse',0)}}</td><td>{{'%.2f'|format(report.job_sizes.timelapse/1073741824)}} GiB</td></tr>
<tr><td>Time-lapse source ZIPs (included above)</td><td>—</td><td>{{'%.2f'|format(report.zip_bytes/1073741824)}} GiB</td></tr>
<tr><td>Finished job MP4s (included above)</td><td>—</td><td>{{'%.2f'|format(report.video_bytes/1073741824)}} GiB</td></tr></tbody></table>
<p class="note">The ZIP and MP4 lines are subdivisions of scheduled-job storage, not additional disk usage. Other system and reserved space is the difference from the filesystem's reported usage, including directories not individually measured. Protected media must not be counted as automatically reclaimable.</p>
<p class="note">For safe cleanup, use the four media tabs. Docker, swap, system packages and unrelated files are shown for information only.</p>
{% else %}
<form class="row storage-filters" method="get" action="{{url_for('storage_page')}}">
<input type="hidden" name="tab" value="{{tab}}">
<label>Search <input type="search" name="q" value="{{query}}" placeholder="Title, notes or ID"></label>
<label>Status <select name="status">{% for s in statuses %}<option value="{{s}}" {% if status==s %}selected{% endif %}>{{s|replace('_',' ')|title}}</option>{% endfor %}</select></label>
<label>Visibility <select name="visibility">{% for s in ['all','public','private'] %}<option value="{{s}}" {% if visibility==s %}selected{% endif %}>{{s|title}}</option>{% endfor %}</select></label>
<label>Protection <select name="protection"><option value="all" {% if protection=='all' %}selected{% endif %}>All items</option><option value="protected" {% if protection=='protected' %}selected{% endif %}>Protected</option><option value="unprotected" {% if protection=='unprotected' %}selected{% endif %}>Eligible</option></select></label>
<label>Sort <select name="sort">{% for s,label in [('newest','Newest first'),('oldest','Oldest first'),('largest','Largest first')] %}<option value="{{s}}" {% if sort==s %}selected{% endif %}>{{label}}</option>{% endfor %}</select></label>
{% if tab=='recordings' %}<label>Older than <select name="older">{% for s in ['0','7','30','60','90','180'] %}<option value="{{s}}" {% if older==s %}selected{% endif %}>{{'Any age' if s=='0' else s+' days'}}</option>{% endfor %}</select></label>{% endif %}
<button type="submit">Apply filters</button>
</form>
<div class="between"><p class="note">{{total}} matching · page {{page}} of {{pages}} · {{'%.1f'|format(tab_bytes/1048576)}} MB in matching files</p>
{% if tab=='scheduled_video' %}<a class="button" href="{{url_for('jobs_list',kind='scheduled_video')}}">Open Scheduled Video</a>{% elif tab=='timelapse' %}<a class="button" href="{{url_for('jobs_list',kind='timelapse')}}">Open Time-lapse Studio</a>{% endif %}
</div>
<form id="storage-delete-form" method="post" action="{{url_for('storage_page',tab=tab)}}">
<input type="hidden" name="csrf" value="{{csrf}}"><input id="storage-action" type="hidden" name="action" value="{{ 'delete_photos' if tab=='photos' else 'delete_jobs' if tab in ('timelapse','scheduled_video') else 'delete' }}">
<input type="hidden" name="confirm" value="DELETE">
<div style="overflow-x:auto"><table><thead><tr><th><input type="checkbox" id="select-all" aria-label="Select eligible items"></th><th>Item</th><th>Status / protection</th><th>Files / size</th><th>Actions</th></tr></thead><tbody>
{% for item in rows %}<tr>
<td>{% if not item.protected %}<input class="item-choice" type="checkbox" name="{{'photo_tokens' if tab=='photos' else 'event_ids' if tab=='recordings' else 'job_ids'}}" value="{{item.ident}}" data-label="{{item.label}}" data-bytes="{{item.bytes}}" aria-label="Select {{item.label}}">{% else %}🔒{% endif %}</td>
<td><a href="{% if tab=='recordings' %}{{url_for('event',event_id=item.id)}}{% elif tab=='photos' %}{{url_for('photo_detail',token=item.token)}}{% else %}{{url_for('job_detail',job_id=item.id)}}{% endif %}">{{item.label}}</a><div class="note">{{item.time|localdt}}{% if tab in ('timelapse','scheduled_video') %} · #{{item.id}}{% endif %}</div></td>
<td>{{'Protected' if item.protected else item.status|title if tab in ('recordings','scheduled_video','timelapse') else 'Eligible'}}{% if tab in ('scheduled_video','timelapse') and item.protected and item.status not in terminal %}<div class="note">Active or not finished</div>{% endif %}</td>
<td>{{'%.1f'|format(item.bytes/1048576)}} MB{% if tab=='timelapse' %}<div class="note">MP4: {{'%.1f'|format(item.mp4_bytes/1048576)}} MB · ZIP: {{'%.1f'|format(item.zip_bytes/1048576)}} MB</div>{% endif %}</td>
<td><div class="row" style="gap:5px"><a class="button" href="{% if tab=='recordings' %}{{url_for('event',event_id=item.id)}}{% elif tab=='photos' %}{{url_for('photo_original',token=item.token,download='1')}}{% else %}{{url_for('job_detail',job_id=item.id)}}{% endif %}">{{'Download' if tab=='photos' else 'View'}}</a>
{% if tab=='timelapse' and item.mp4_bytes %}<a class="button" href="{{url_for('job_media',job_id=item.id,filename='timelapse.mp4',download='1')}}">MP4</a>{% endif %}
{% if tab=='timelapse' and item.zip_bytes %}<a class="button" href="{{url_for('job_media',job_id=item.id,filename='source-frames.zip',download='1')}}">Source ZIP</a>{% endif %}
{% if not item.protected %}<button type="button" class="row-delete danger" data-value="{{item.ident}}" data-action="delete" title="Delete item">🗑</button>{% endif %}
{% if tab=='timelapse' and item.zip_bytes and not item.protected %}<button type="button" class="row-delete" data-value="{{item.ident}}" data-action="delete_sources" data-bytes="{{item.zip_bytes}}" title="Delete source ZIP but keep MP4">Delete ZIP only</button>{% endif %}
</div></td></tr>{% else %}<tr><td colspan="5">No matching items.</td></tr>{% endfor %}
</tbody></table></div>
<div class="storage-selection-bar"><strong id="storage-selected-count">0 selected</strong><span id="storage-selected-size" class="note">0 MB</span><button id="storage-delete-selected" class="danger" type="button" disabled>🗑 Delete selected</button></div>
<dialog id="storage-confirm" class="storage-modal"><h2 id="storage-confirm-title">Delete selected files?</h2><p id="storage-confirm-details"></p>
<p class="note" id="storage-confirm-caution">This is permanent. Protected items are checked again when you confirm.</p>
<div class="row"><button type="button" id="storage-cancel">Cancel</button><button type="submit" class="danger" id="storage-accept">Permanently delete</button></div></dialog>
</form>
<div class="between">{% if page>1 %}<a class="button" href="{{url_for('storage_page',tab=tab,page=page-1,status=status,visibility=visibility,sort=sort,older=older,q=query,protection=protection)}}">← Previous</a>{% endif %}{% if page<pages %}<a class="button" href="{{url_for('storage_page',tab=tab,page=page+1,status=status,visibility=visibility,sort=sort,older=older,q=query,protection=protection)}}">Next →</a>{% endif %}</div>
<p class="note">Pins and public sharing prevent deletion. Flagged, Identified and Unresolved motion events are protected; unfinished jobs are protected. The source ZIP of an eligible time-lapse may be removed separately without deleting its MP4.</p>
{% endif %}</div>
{% if tab!='overview' %}<script src="{{url_for('storage_js')}}" defer></script>{% endif %}'''

GALLERY = '''<h1>Photograph Gallery</h1>
<form method="get" class="row photo-gallery-filters">
<label>Search photographs <input type="search" name="q" value="{{query}}" placeholder="Titles and notes"></label>
<label>Public sharing <select name="visibility"><option value="all" {% if visibility=='all' %}selected{% endif %}>All photographs</option><option value="public" {% if visibility=='public' %}selected{% endif %}>Public only</option><option value="private" {% if visibility=='private' %}selected{% endif %}>Private only</option></select></label>
<label>Pinned <select name="pin"><option value="all" {% if pin=='all' %}selected{% endif %}>All photographs</option><option value="pinned" {% if pin=='pinned' %}selected{% endif %}>Pinned only</option><option value="unpinned" {% if pin=='unpinned' %}selected{% endif %}>Unpinned only</option></select></label>
<button type="submit">Apply filters</button></form>
<p class="note">{{total}} photographs · page {{page}} of {{pages}}</p>
<div class="photo-gallery-grid">{% for item in entries %}<a class="photo-gallery-card" href="{{url_for('photo_detail',token=item.token)}}">
<img loading="lazy" src="{{url_for('photo_gallery_thumb',token=item.token)}}" alt="{{item.title or 'Saved photograph'}}"><strong>{{item.title or 'Photograph '+item.token[:8]}}</strong>
<span class="note">{{item.modified|localday}} · {{item.format|upper}} {% if item.pinned %}· 📌 Pinned{% endif %}{% if item.public %} · Public{% endif %}</span></a>{% else %}<p>No photographs found.</p>{% endfor %}</div>
<div class="between">{% if page>1 %}<a class="button" href="{{url_for('photo_gallery',page=page-1,q=query,visibility=visibility,pin=pin)}}">← Previous</a>{% endif %}{% if page<pages %}<a class="button" href="{{url_for('photo_gallery',page=page+1,q=query,visibility=visibility,pin=pin)}}">Next →</a>{% endif %}</div>'''

PHOTO_DETAIL = '''<p><a href="{{url_for('photo_gallery')}}">← Photograph Gallery</a></p><h1>{{detail.title or 'Photograph '+photo.token[:8]}}</h1>
<div class="cols"><section class="panel"><h2>Photograph</h2><img class="photo-detail-image" src="{{url_for('photo_original',token=photo.token)}}" alt="{{detail.title or 'Photograph'}}"><p class="note">{{photo.format|upper}} · {{'%.1f'|format(photo.bytes/1048576)}} MB · {{photo.modified|localdt}}</p>
<a class="button" href="{{url_for('photo_original',token=photo.token,download='1')}}">Download original</a></section>
<section class="panel"><h2>Photograph details</h2>{% if admin %}<form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="action" value="details">
<label>Title <input maxlength="120" name="title" value="{{detail.title}}"></label><label>Notes <textarea name="note" maxlength="8000">{{detail.note}}</textarea></label>
<label class="checkline"><input type="checkbox" name="public" value="1" {% if detail.public %}checked{% endif %}>Share photograph on the public page</label>
<label class="checkline"><input type="checkbox" name="public_note" value="1" {% if detail.public_note %}checked{% endif %}>Show saved notes publicly</label><p class="note">A public photo is viewable without login. Only a reduced, metadata-stripped image is published.</p>
<button type="submit">Save changes</button></form>
<form method="post" style="margin-top:12px"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="action" value="{{'unpin' if photo.pinned else 'pin'}}"><button type="submit">{{'📌 Unpin photograph' if photo.pinned else '📌 Pin and protect photograph'}}</button></form>
<p class="note">A pinned or public photograph cannot be deleted in Storage Management until protection is removed.</p>
{% else %}<p><strong>Title:</strong> {{detail.title}}</p><p style="white-space:pre-wrap">{{detail.note}}</p>{% endif %}</section></div>'''


GALLERY = '''<h1>Photograph Gallery</h1>
<form method="get" class="row photo-gallery-filters">
<label>Search photographs <input type="search" name="q" value="{{query}}" placeholder="Titles and notes"></label>
<label>Public sharing <select name="visibility"><option value="all" {% if visibility=='all' %}selected{% endif %}>All photographs</option><option value="public" {% if visibility=='public' %}selected{% endif %}>Public only</option><option value="private" {% if visibility=='private' %}selected{% endif %}>Private only</option></select></label>
<label>Pinned <select name="pin"><option value="all" {% if pin=='all' %}selected{% endif %}>All photographs</option><option value="pinned" {% if pin=='pinned' %}selected{% endif %}>Pinned only</option><option value="unpinned" {% if pin=='unpinned' %}selected{% endif %}>Unpinned only</option></select></label>
<button type="submit">Apply filters</button></form>
<p class="note">{{total}} photographs · page {{page}} of {{pages}}</p>
<div class="photo-gallery-grid">{% for item in entries %}<a class="photo-gallery-card" href="{{url_for('photo_detail',token=item.token)}}">
<img loading="lazy" src="{{url_for('photo_gallery_thumb',token=item.token)}}" alt="{{item.title or 'Saved photograph'}}"><strong>{{item.title or 'Photograph '+item.token[:8]}}</strong>
<span class="note">{{item.modified|localday}} · {{item.format|upper}} {% if item.pinned %}· 📌 Pinned{% endif %}{% if item.public %} · Public{% endif %}</span></a>{% else %}<p>No photographs found.</p>{% endfor %}</div>
<div class="between">{% if page>1 %}<a class="button" href="{{url_for('photo_gallery',page=page-1,q=query,visibility=visibility,pin=pin)}}">← Previous</a>{% endif %}{% if page<pages %}<a class="button" href="{{url_for('photo_gallery',page=page+1,q=query,visibility=visibility,pin=pin)}}">Next →</a>{% endif %}</div>'''

PHOTO_DETAIL = '''<p><a href="{{url_for('photo_gallery')}}">← Photograph Gallery</a></p><h1>{{detail.title or 'Photograph '+photo.token[:8]}}</h1>
<div class="cols"><section class="panel"><h2>Photograph</h2><img class="photo-detail-image" src="{{url_for('photo_original',token=photo.token)}}" alt="{{detail.title or 'Photograph'}}"><p class="note">{{photo.format|upper}} · {{'%.1f'|format(photo.bytes/1048576)}} MB · {{photo.modified|localdt}}</p>
<a class="button" href="{{url_for('photo_original',token=photo.token,download='1')}}">Download original</a></section>
<section class="panel"><h2>Photograph details</h2>{% if admin %}<form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="action" value="details">
<label>Title <input maxlength="120" name="title" value="{{detail.title}}"></label><label>Notes <textarea name="note" maxlength="8000">{{detail.note}}</textarea></label>
<label class="checkline"><input type="checkbox" name="public" value="1" {% if detail.public %}checked{% endif %}>Share photograph on the public page</label>
<label class="checkline"><input type="checkbox" name="public_note" value="1" {% if detail.public_note %}checked{% endif %}>Show saved notes publicly</label><p class="note">A public photo is viewable without login. Only a reduced, metadata-stripped image is published.</p>
<button type="submit">Save changes</button></form>
<form method="post" style="margin-top:12px"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="action" value="{{'unpin' if photo.pinned else 'pin'}}"><button type="submit">{{'📌 Unpin photograph' if photo.pinned else '📌 Pin and protect photograph'}}</button></form>
<p class="note">A pinned or public photograph cannot be deleted in Storage Management until protection is removed.</p>
{% else %}<p><strong>Title:</strong> {{detail.title}}</p><p style="white-space:pre-wrap">{{detail.note}}</p>{% endif %}</section></div>'''
