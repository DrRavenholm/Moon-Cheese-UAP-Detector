/* Detector controls: presets and resets do not save until regular form submit. */
(()=>{'use strict';
const panel=document.getElementById('detector-method-settings');if(!panel)return;
const $=id=>document.getElementById(id);
const defaults=JSON.parse(panel.dataset.defaults),presets=JSON.parse(panel.dataset.presets);
const fields={general:['pixel_threshold','min_changed_pixels'],sky_lights:['sky_brightness','sky_confirm_frames','sky_min_area','sky_max_area','sky_min_movement'],
 mog2:['mog2_threshold','mog2_min_area','mog2_confirm_frames'],transient:['transient_threshold','transient_min_area','transient_min_length']};
const all=Object.keys(fields).flatMap(k=>fields[k]);const preset=$('detector_preset'),note=$('detection-reset-result');
function apply(fieldsToSet,values){for(const name of fieldsToSet){const input=panel.querySelector(`[name="${name}"]`);if(input&&Object.prototype.hasOwnProperty.call(values,name)){input.value=values[name];input.dispatchEvent(new Event('change',{bubbles:true}));}}}
function updateMethods(){const selected=[...panel.querySelectorAll('[name="detection_methods"]:checked')];const warning=$('detection-method-warning');
 warning.textContent=selected.length?'Enabled methods share one recorder. New experimental methods can generate noise alerts.':'Select at least one method before saving.';
 warning.style.color=selected.length?'':'#ff9f9f';}
panel.querySelectorAll('[name="detection_methods"]').forEach(b=>b.addEventListener('change',updateMethods));updateMethods();
panel.querySelectorAll('input[type="number"]').forEach(input=>input.addEventListener('input',()=>{preset.value='custom';}));
preset.addEventListener('change',()=>{if(presets[preset.value]){apply(all,presets[preset.value]);note.textContent=`${preset.options[preset.selectedIndex].text} preset loaded; review and Save settings to apply.`;}});
panel.querySelectorAll('[data-detect-reset]').forEach(b=>b.addEventListener('click',()=>{
 const group=b.dataset.detectReset;if(!window.confirm(`Load default ${group} values? Your other settings will remain unchanged.`))return;
 apply(fields[group],defaults);preset.value='custom';note.textContent=`${group} thresholds restored in form. Save settings to apply.`;
}));
$('detection-reset-all').addEventListener('click',()=>{
 if(!window.confirm('Load DEFAULT detection methods and thresholds? This will not reset camera profiles or detection zones. Save settings to apply.'))return;
 apply(all,defaults);panel.querySelectorAll('[name="detection_methods"]').forEach(b=>b.checked=b.value==='general');
 preset.value='custom';updateMethods();note.textContent='Detection defaults loaded; camera settings and zones unchanged. Save settings to apply.';
});
const diag=$('detection-diagnostics'),display=$('detection-live-values');
async function refresh(){if(!diag.open)return;
 try{const r=await fetch('/api/detection-diagnostics',{credentials:'same-origin',cache:'no-store'});const d=await r.json();if(!r.ok)throw Error(d.error||'Unavailable');
 const age=(Date.now()-new Date(d.updated).getTime())/1000;
 const safe=x=>String(x??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 display.innerHTML=`<p><strong>Status:</strong> ${safe(d.reason)} · ${age>15?'<strong>STALE — check detector service</strong>':'Live'} (${Math.max(0,Math.round(age))} seconds ago)</p>
 <p><strong>Image:</strong> mean brightness ${safe(d.brightness_mean)} / 255 · nearly black ${safe(d.nearly_black_percent)}% · nearly white ${safe(d.nearly_white_percent)}% · available zone ${safe(d.active_zone_percent)}%</p>
 <p><strong>Analysis speed:</strong> ${safe(d.analysis_fps)} fps · Recording ${d.recording?'YES':'No'} · Recording permitted ${d.record_allowed?'YES':'No'}</p>
 <p><strong>Enabled:</strong> ${safe((d.methods||[]).join(', '))}</p>
 <p><strong>Candidates:</strong> ${safe(JSON.stringify(d.candidates))}</p>
 <p><strong>Scores:</strong> ${safe(JSON.stringify(d.scores))}</p>
 <p><strong>Since detector restart:</strong> ${safe(JSON.stringify(d.counts||{}))}</p>`;
 }catch(e){display.textContent='Detection diagnostics: '+e.message;}}
diag.addEventListener('toggle',refresh);setInterval(refresh,5000);
})();
