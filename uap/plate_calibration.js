/* Moon Cheese private offline plate-solving review. Catalogue crosses are drawn
   ONLY from verified photo/sky coincidences supplied by the plate worker. */
(()=>{'use strict';
const root=document.getElementById('plate-calibration');if(!root)return;
const $=id=>document.getElementById(id),csrf=root.dataset.csrf;
let token='',job='',overlay=[],north=null,originalHold=80;
const msg=(s,error=false)=>{$('plate-error').textContent=error?s:'';if(!error)$('plate-job-status').textContent=s;};
const post=async(url,payload)=>{const body=new FormData();body.append('csrf',csrf);Object.entries(payload).forEach(([k,v])=>body.append(k,v));
 const response=await fetch(url,{method:'POST',body,credentials:'same-origin'});
 if(!(response.headers.get('content-type')||'').toLowerCase().includes('json'))throw Error('The calibration server returned an unexpected response; check Moon Cheese service logs.');
 const result=await response.json();if(!response.ok)throw Error(result.error||'Calibration action failed');return result;};
const get=async(url)=>{const r=await fetch(url,{credentials:'same-origin',cache:'no-store'});if(!(r.headers.get('content-type')||'').includes('json'))throw Error('The calibration service returned an unexpected response.');
 const v=await r.json();if(!r.ok)throw Error(v.error||'Calibration status unavailable');return v;};
const photoUrl=t=>'/storage/photos/'+encodeURIComponent(t)+'/original';
function choose(t){if(!/^[0-9a-f]{32}$/.test(t))return;
 token=t;job='';$('plate-result').hidden=true;$('plate-save').disabled=false;
 $('plate-selected-area').hidden=false;$('plate-image').src=photoUrl(t);
 $('plate-capture-status').textContent='Ready to solve the selected photograph.';
}
$('plate-saved-photo').addEventListener('change',e=>{if(e.target.value)choose(e.target.value);});
if(root.dataset.initialPhoto){$('plate-saved-photo').value=root.dataset.initialPhoto;choose(root.dataset.initialPhoto);}
let lastReady='';
async function refreshSupport(){try{const status=await get('/sky-maps/calibration/support');
 $('plate-solver-state').textContent=status.solver_installed?'Installed':'Not installed';
 $('plate-index-state').textContent=status.index_installed?'Downloaded':'Not downloaded';
 if(status.setup&&status.setup.message)$('plate-setup-message').textContent=status.setup.message;
 $('plate-solve').disabled=!(status.solver_installed&&status.index_installed);
 const ready=status.solver_installed&&status.index_installed;
 if(ready&&lastReady==='')$('plate-capture-status').textContent='Offline plate-solving support is ready.';
 lastReady=ready?'ready':'missing';
 }catch(e){/* Keep last state during temporary worker downtime. */}}
setInterval(refreshSupport,5000);

$('plate-capture').addEventListener('click',async()=>{const b=$('plate-capture');b.disabled=true;$('plate-error').textContent='';
 try{const exposure=Number($('plate-exposure').value),gain=Number($('plate-gain').value);
  if(!Number.isFinite(exposure)||exposure<0.5||exposure>60||!Number.isFinite(gain)||gain<1||gain>16)throw Error('Choose valid exposure and gain.');
  const data=await post('/sky-maps/calibration/capture',{exposure_s:exposure,gain});
  $('plate-capture-status').textContent='Preparing the camera and taking your calibration photograph…';
  const purl=root.dataset.photographyUrl.replace('__TOKEN__',data.token);
  for(let n=0;n<180;n++){
   await new Promise(res=>setTimeout(res,1500));const state=await get(purl);
   $('plate-capture-status').textContent=state.message||state.state;
   if(state.state==='done'){choose(data.token);return;}
   if(state.state==='error')throw Error(state.message||'Photograph capture failed');
  }
  throw Error('Photograph did not finish within the expected time; check Photography.');
 }catch(e){$('plate-error').textContent=e.message;}finally{b.disabled=false;}});

function renderOverlay(){const layer=$('plate-visual-overlay');layer.replaceChildren();
 const showMarkers=$('plate-show-markers').checked,showNames=$('plate-show-labels').checked;
 for(const star of overlay){if(!showMarkers)break;
  const x=Number(star.x),y=Number(star.y);
  if(!Number.isFinite(x)||!Number.isFinite(y)||x<0||x>100||y<0||y>100)continue;
  const mark=document.createElement('span');mark.className='plate-star-point';mark.style.left=x+'%';mark.style.top=y+'%';
  mark.title=star.name?`${star.name} — cross-checked catalogue star`:'Cross-checked catalogue star';
  if(showNames&&star.name){const caption=document.createElement('span');caption.className='plate-star-name';caption.textContent=star.name;mark.append(caption);}
  layer.append(mark);
 }
 $('plate-centre').hidden=!$('plate-show-centre').checked;
 const showNorth=$('plate-show-north').checked&&Array.isArray(north)&&north.length===2;
 $('plate-north').hidden=!showNorth;
 // Image coordinates point down, so clockwise rotation of a vertical arrow
 // follows atan2(dx,-dy), not the raw celestial position angle.
 if(showNorth){const angle=Math.atan2(north[0],-north[1])*180/Math.PI;
  $('plate-north-arrow').style.display='inline-block';$('plate-north-arrow').style.transform=`rotate(${angle}deg)`;}
 layer.style.opacity=(Number($('plate-overlay-opacity').value)||0)/100;
 $('plate-opacity-label').textContent=$('plate-overlay-opacity').value+'%';
 $('plate-centre').style.opacity=layer.style.opacity;$('plate-north').style.opacity=layer.style.opacity;
}
for(const id of ['plate-show-markers','plate-show-labels','plate-show-centre','plate-show-north','plate-overlay-opacity']){
 $(id).addEventListener('input',renderOverlay);$(id).addEventListener('change',renderOverlay);
}
$('plate-original').addEventListener('click',()=>{const slider=$('plate-overlay-opacity');
 if(Number(slider.value)>0){originalHold=Number(slider.value);slider.value='0';$('plate-original').textContent='Show overlay';}
 else{slider.value=String(originalHold||80);$('plate-original').textContent='Original photo';}
 renderOverlay();});
$('plate-retry').addEventListener('click',()=>{$('plate-result').hidden=true;job='';$('plate-job-status').textContent='Choose a different photograph above, then solve again.'; $('plate-selected-area').scrollIntoView({behavior:'smooth',block:'start'});});

$('plate-solve').addEventListener('click',async()=>{const b=$('plate-solve');b.disabled=true;$('plate-result').hidden=true;$('plate-error').textContent='';
 try{if(!token)throw Error('Select a saved photograph or take a new one first.');
  const queued=await post('/sky-maps/calibration/solve',{token,field_height:$('plate-fov').value});job=queued.job;
  msg('ASTAP is comparing star patterns with the offline index…');
  for(let n=0;n<130;n++){
   await new Promise(res=>setTimeout(res,1500));const v=await get('/sky-maps/calibration/status/'+job);
   if(v.state==='error')throw Error(v.message||'Plate solving failed');
   if(v.state==='solved'){
    const degrees=value=>value==null?'Unavailable':`${Number(value).toFixed(2)}°`;
    $('plate-bearing').textContent=degrees(v.bearing_deg);$('plate-elevation').textContent=degrees(v.elevation_deg);
    $('plate-up').textContent=degrees(v.image_up_heading_deg);$('plate-rotation').textContent=degrees(v.rotation_deg);
    $('plate-radec').textContent=`RA ${degrees(v.ra_deg)} · Dec ${degrees(v.dec_deg)}`;
    $('plate-field').textContent=v.approx_hfov_deg!=null&&v.approx_vfov_deg!=null?`${degrees(v.approx_hfov_deg)} × ${degrees(v.approx_vfov_deg)}`:'Unavailable';
    overlay=Array.isArray(v.overlay?.markers)?v.overlay.markers:[];
    north=v.overlay?.north||null;
    $('plate-marker-status').textContent=(overlay.length?`${overlay.length} independently cross-checked star positions. `:'No star circles available. ')+(v.overlay?.note||'No catalogue/photo cross-check available.');
    $('plate-matched').textContent=overlay.length.toString();$('plate-warning').textContent=v.warning||'';
    $('plate-review-photo').src=photoUrl(token);
    $('plate-result').hidden=false;$('plate-save').disabled=false;
    renderOverlay();msg('ASTAP identified the sky position. Inspect the photo overlay before saving.');return;
   }msg(v.message||'Plate solver is running…');
  }
  throw Error('The solver did not return a result. Check calibration worker status.');
 }catch(e){$('plate-error').textContent=e.message;}finally{b.disabled=false;}});
$('plate-save').addEventListener('click',async()=>{try{if(!job)throw Error('Run a successful plate solve first.');
 await post('/sky-maps/calibration/save',{job});
 msg('Calibration saved. Your existing camera controls have not changed. The approximate camera footprint is now available on Sky Maps.');
 $('plate-save').disabled=true;
 }catch(e){$('plate-error').textContent=e.message;}});
})();
