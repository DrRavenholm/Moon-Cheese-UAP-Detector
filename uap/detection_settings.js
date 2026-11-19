/* Detector controls: presets and resets do not save until regular form submit. */
(()=>{'use strict';
const panel=document.getElementById('detector-method-settings');if(!panel)return;
const $=id=>document.getElementById(id);
const defaults=JSON.parse(panel.dataset.defaults),presets=JSON.parse(panel.dataset.presets);
const fields={general:['pixel_threshold','min_changed_pixels'],sky_lights:['sky_brightness','sky_confirm_frames','sky_min_area','sky_max_area','sky_min_movement'],
 mog2:['mog2_threshold','mog2_min_area','mog2_confirm_frames'],transient:['transient_threshold','transient_min_area','transient_min_length']};
const all=Object.keys(fields).flatMap(k=>fields[k]);const preset=$('detector_preset'),note=$('detection-reset-result');
// The recording stream and high-detail analysis must share their aspect ratio.
// Keep a user-selected 320×240 (original low-CPU mode) unchanged.
const recordResolution=document.getElementById('camera_resolution');
const analysisResolution=panel.querySelector('[name="analysis_resolution"]');
function syncResolution(){if(!recordResolution||!analysisResolution)return;
 const matched=recordResolution.value==='640x480'?'640x480':'640x360';
 for(const option of analysisResolution.options){option.disabled=option.value!=='320x240'&&option.value!==matched;}
 if(analysisResolution.value!=='320x240'&&analysisResolution.value!==matched)analysisResolution.value=matched;
 const status=document.getElementById('analysis-compatibility-note');
 if(status)status.textContent='High-detail analysis automatically matches the recording aspect ratio: '+matched+'. Standard 320×240 remains available at any recording resolution.';
}
if(recordResolution){recordResolution.addEventListener('change',syncResolution);syncResolution();}

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
 apply(all,defaults);const resolution=panel.querySelector('[name="analysis_resolution"]');if(resolution)resolution.value=defaults.analysis_resolution||'320x240';panel.querySelectorAll('[name="detection_methods"]').forEach(b=>b.checked=b.value==='general');
 preset.value='custom';updateMethods();note.textContent='Detection defaults loaded; camera settings and zones unchanged. Save settings to apply.';
});
const diag=$('detection-diagnostics'),display=$('detection-live-values');
const methodLabels={general:'General Motion',sky_lights:'Moving Sky Lights',mog2:'Adaptive Background (MOG2)',transient:'Transient & Streak'};
const safe=x=>String(x??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function refresh(){if(!diag.open)return;
 try{const r=await fetch('/api/detection-diagnostics',{credentials:'same-origin',cache:'no-store'});const d=await r.json();if(!r.ok)throw Error(d.error||'Unavailable');
 const age=Math.max(0,Math.round((Date.now()-new Date(d.updated).getTime())/1000));
 const counters=d.counts||{},data=d.camera_readings||{};
 const countersRows=Object.entries(methodLabels).map(([key,label])=>`<tr><td>${label}</td><td>${(d.methods||[]).includes(key)?'Enabled':'Off'}</td><td>${d.candidates?.[key]?'Candidate':'—'}</td><td>${safe(d.scores?.[key]??0)}</td><td>${safe(counters['candidate_'+key]??0)}</td><td>${safe(counters['unconfirmed_'+key]??0)}</td></tr>`).join('');
 display.innerHTML=`<p><strong>${age>15?'⚠ Stale — check detector':'● Monitoring snapshot'}</strong> · ${safe(d.reason)} · ${age}s ago</p>
 <div class="job-estimate-grid"><div><div class="sub">Analysis</div><strong>${safe(d.analysis_resolution||'320x240')}</strong></div><div><div class="sub">Frame rate (set / measured)</div><strong>${safe(d.configured_fps)} / ${safe(d.analysis_fps)} fps</strong></div><div><div class="sub">Image brightness</div><strong>${safe(d.brightness_mean)} / 255</strong></div><div><div class="sub">Camera ISO equivalent</div><strong>${safe(data.iso_equivalent||'Not reported')}</strong></div></div>
 <p class="note">Measured exposure: ${safe(data.exposure_ms)} ms · analogue gain: ${safe(data.analogue_gain)}× · digital gain: ${safe(data.digital_gain)}×. ISO is a software-reported equivalent, not calibrated sensor ISO.</p>
 <p>Nearly black: ${safe(d.nearly_black_percent)}% · Nearly white: ${safe(d.nearly_white_percent)}% · Detection area: ${safe(d.active_zone_percent)}%</p>
 <p>Recording ${d.recording?'active':'inactive'} · Recording ${d.record_allowed?'permitted':'not permitted'} · Events started since detector restart: ${safe(counters.events_started||0)} · Candidate frames blocked by schedule/storage/cooldown: ${safe(counters.candidates_blocked||0)}</p>
 <div class="readable"><table><thead><tr><th>Method</th><th>Enabled</th><th>Now</th><th>Score</th><th>Candidate frames since restart</th><th>Signal frames not confirmed</th></tr></thead><tbody>${countersRows}</tbody></table></div>`;
 }catch(e){display.textContent='Detection diagnostics unavailable: '+e.message;}
}
const historyDay=$('detection-history-day'),historyStatus=$('detection-history-status');
const historyChart=$('detection-history-chart'),historySummary=$('detection-history-summary'),historyExport=$('detection-history-export');
const ns='http://www.w3.org/2000/svg';
function svgElement(tag,attrs,text){const node=document.createElementNS(ns,tag);for(const [name,value] of Object.entries(attrs||{}))node.setAttribute(name,String(value));if(text!==undefined)node.textContent=text;return node;}
function chart(samples){historyChart.replaceChildren();
 const buckets=Array.from({length:24},()=>({candidate:0,events:0,brightness:0,count:0,allowed:0}));
 for(const item of samples){const hour=Number((item.minute_utc||'').substring(11,13));if(!Number.isInteger(hour)||hour<0||hour>23)continue;
 const b=buckets[hour],delta=item.delta||{};b.count++;b.candidate+=Object.entries(delta).filter(([key])=>key.startsWith('candidate_')).reduce((a,[,value])=>a+Number(value||0),0);b.events+=Number(delta.events_started||0);b.brightness+=Number(item.brightness_mean||0);b.allowed+=item.record_allowed?1:0;}
 const max=Math.max(1,...buckets.map(x=>x.candidate));
 historyChart.append(svgElement('line',{x1:28,y1:125,x2:695,y2:125,stroke:'currentColor','stroke-opacity':'.3'}));
 buckets.forEach((b,i)=>{const x=30+i*27.3;const height=b.candidate/max*92;
 const rect=svgElement('rect',{x,y:125-height,width:19,height:Math.max(0,height),fill:'var(--cyan, #75dbed)',opacity:b.count?'.9':'.12'});
 rect.append(svgElement('title',{},`${i.toString().padStart(2,'0')}:00 UTC — ${b.candidate} candidate frames, ${b.events} started events, ${b.count} samples`));historyChart.append(rect);
 if(b.events)historyChart.append(svgElement('circle',{cx:x+9,cy:Math.max(5,120-height),r:3.6,fill:'#ffc26f'}));
 if(i%3===0)historyChart.append(svgElement('text',{x:x+7,y:146,fill:'currentColor','font-size':11,'text-anchor':'middle'},`${i.toString().padStart(2,'0')}h`));
 });
 const candidates=buckets.reduce((a,x)=>a+x.candidate,0),events=buckets.reduce((a,x)=>a+x.events,0),allowed=buckets.reduce((a,x)=>a+x.allowed,0);
 historySummary.textContent=`${samples.length} minute summaries · ${candidates} candidate frames · ${events} started events · ${allowed} monitoring-permitted samples. Teal bars = candidates per hour; amber dots = hour with an event. Gaps mean no samples (possible downtime).`;
}
async function loadHistory(){if(!diag.open)return;const day=historyDay.value;
 historyExport.href='/api/detection-history.csv?day='+encodeURIComponent(day);
 historyStatus.textContent='Loading UTC-day history…';
 try{const r=await fetch('/api/detection-history?day='+encodeURIComponent(day),{credentials:'same-origin',cache:'no-store'});
 const data=await r.json();if(!r.ok)throw Error(data.error||'Cannot read history');
 chart(data.samples||[]);historyStatus.textContent=data.samples?.length?`History loaded for ${day} (UTC)`:'No stored samples for this date. New history begins after this upgrade.';
 }catch(e){historyChart.replaceChildren();historySummary.textContent='';historyStatus.textContent='Could not load history: '+e.message;}}
if(historyDay){historyDay.value=new Date().toISOString().slice(0,10);$('detection-history-refresh').addEventListener('click',loadHistory);historyDay.addEventListener('change',loadHistory);}
diag.addEventListener('toggle',()=>{refresh();if(diag.open)loadHistory();});setInterval(refresh,5000);
})();
