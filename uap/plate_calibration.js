/* Administrator-only offline star calibration; no camera access from browser. */
(()=>{'use strict';
const root=document.getElementById('plate-calibration');if(!root)return;
const $=id=>document.getElementById(id),csrf=root.dataset.csrf;
let token='',job='';
const msg=(s,error=false)=>{ $('plate-error').textContent=error?s:'';if(!error)$('plate-job-status').textContent=s;};
const post=async(url,payload)=>{const body=new FormData();body.append('csrf',csrf);Object.entries(payload).forEach(([k,v])=>body.append(k,v));
 const response=await fetch(url,{method:'POST',body,credentials:'same-origin'});
 const type=(response.headers.get('content-type')||'').toLowerCase();
 if(!type.includes('json'))throw Error('The server did not return calibration data. Check the dashboard logs.');
 const result=await response.json();if(!response.ok)throw Error(result.error||'Calibration action failed');return result;};
const get=async(url)=>{const r=await fetch(url,{credentials:'same-origin'});if(!(r.headers.get('content-type')||'').includes('json'))throw Error('The calibration service returned an unexpected response.');const v=await r.json();if(!r.ok)throw Error(v.error||'Calibration status unavailable');return v;};
const choose=t=>{if(!/^[0-9a-f]{32}$/.test(t))return;token=t;$('plate-selected-area').hidden=false;
 $('plate-image').src='/storage/photos/'+encodeURIComponent(t)+'/original';$('plate-capture-status').textContent='Ready to solve the selected photograph.';};
$('plate-saved-photo').addEventListener('change',e=>choose(e.target.value));
if(root.dataset.initialPhoto){$('plate-saved-photo').value=root.dataset.initialPhoto;choose(root.dataset.initialPhoto);}
let lastReady='';
const refreshSupport=async()=>{try{const status=await get('/sky-maps/calibration/support');
  $('plate-solver-state').textContent=status.solver_installed?'Installed':'Not installed';
  $('plate-index-state').textContent=status.index_installed?'Downloaded':'Not downloaded';
  if(status.setup&&status.setup.message)$('plate-setup-message').textContent=status.setup.message;
  $('plate-solve').disabled=!(status.solver_installed&&status.index_installed);
  const ready=status.solver_installed&&status.index_installed;
  if(ready&&lastReady==='')$('plate-capture-status').textContent='Offline plate-solving support is ready.';
  lastReady=ready?'ready':'missing';
 }catch(e){/* Keep the existing status if the dashboard is temporarily busy. */}};
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
     if(state.state==='error')throw Error(state.message||'Photo capture failed');
   }
   throw Error('Photograph did not finish within the expected time. Check Photography.');
 }catch(e){$('plate-error').textContent=e.message;}finally{b.disabled=false;}});
$('plate-solve').addEventListener('click',async()=>{const b=$('plate-solve');b.disabled=true;$('plate-result').hidden=true;$('plate-error').textContent='';
 try{if(!token)throw Error('Select a saved photograph or take a new one first.');
   const queued=await post('/sky-maps/calibration/solve',{token,field_height:$('plate-fov').value});job=queued.job;
   msg('ASTAP is comparing star patterns with the offline index…');
   for(let n=0;n<130;n++){
     await new Promise(res=>setTimeout(res,1500));const v=await get('/sky-maps/calibration/status/'+job);
     if(v.state==='error')throw Error(v.message||'Plate solving failed');
     if(v.state==='solved'){
       const degrees=v=>v===null||v===undefined?'Unavailable':`${Number(v).toFixed(2)}°`;
       $('plate-bearing').textContent=degrees(v.bearing_deg);$('plate-elevation').textContent=degrees(v.elevation_deg);
       $('plate-up').textContent=degrees(v.image_up_heading_deg);$('plate-rotation').textContent=degrees(v.rotation_deg);
       $('plate-radec').textContent=`RA ${degrees(v.ra_deg)} · Dec ${degrees(v.dec_deg)}`;
       $('plate-warning').textContent=v.warning||'';$('plate-result').hidden=false;msg('ASTAP successfully identified the star field. Review the measurements before saving.');return;
     }msg(v.message||'Plate solver is running…');
   }
   throw Error('The solver did not return a result. Check calibration worker status.');
 }catch(e){$('plate-error').textContent=e.message;}finally{b.disabled=false;}});
$('plate-save').addEventListener('click',async()=>{try{const v=await post('/sky-maps/calibration/save',{job});
 msg('Calibration saved separately. Your original camera controls remain unchanged.');
 $('plate-save').disabled=true;
 }catch(e){$('plate-error').textContent=e.message;}});
})();
