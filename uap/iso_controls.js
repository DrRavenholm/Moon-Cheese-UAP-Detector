/* Shared camera ISO-equivalent presentation. Never changes capture control names. */
(()=>{'use strict';
const options=[1,2,4,8,16];
function nearest(value){return options.reduce((a,b)=>Math.abs(b-value)<Math.abs(a-value)?b:a,1);}
for(const select of document.querySelectorAll('[data-iso-for]')){
 const gain=document.getElementById(select.dataset.isoFor);if(!gain)continue;
 function gainChanged(){const v=Number(gain.value);select.value=String(nearest(v));
 const note=select.closest('[data-iso-unit]')?.querySelector('[data-iso-readout]');if(note)note.textContent=Number.isFinite(v)&&v>0?`ISO ${Math.round(v*100)} equivalent at digital gain 1×; actual camera ISO may differ.`:'Enter a valid gain.';}
 select.addEventListener('change',()=>{gain.value=select.value;gain.dispatchEvent(new Event('input',{bubbles:true}));gainChanged();});
 gain.addEventListener('input',gainChanged);gainChanged();
}
const displays=[...document.querySelectorAll('[data-camera-readings]')];
async function fetchReadings(){if(!displays.length)return;
 try{const response=await fetch('/api/detection-diagnostics',{credentials:'same-origin',cache:'no-store'});if(!response.ok)return;
 const d=await response.json(),m=d.camera_readings||{};
 const result=m.iso_equivalent?`Current camera: ISO ${m.iso_equivalent} equivalent · ${m.analogue_gain}× analogue gain · ${m.digital_gain??'—'}× digital gain · ${m.exposure_ms??'—'} ms exposure`:'Live camera sensitivity is unavailable; the detector may be restarting or capturing another job.';
 displays.forEach(el=>el.textContent=result);
 }catch(_){/* Camera information is optional; never block a capture. */}}
if(displays.length){fetchReadings();setInterval(fetchReadings,10000);}
})();
