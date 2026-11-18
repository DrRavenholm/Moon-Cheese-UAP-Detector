/* Moon Cheese v1.0.1.4 zone editor: single-click + Finish, never double click. */
(()=>{'use strict';
const root=document.getElementById('zones-editor');if(!root)return;
const $=id=>document.getElementById(id);
const canvas=$('zones-canvas'),ctx=canvas.getContext('2d'),status=$('zones-status'),img=new Image();
const MAX_POINTS=256,MAX_ZONES=24;
let zones=[],draft=[],dragStart=null,tool='rectangle',enabled=false,undo=[],redo=[];
let movingIndex=-1,movingVertex=-1,dragging=false;
canvas.style.touchAction='none';
function notify(s){status.textContent=s;}
function point(e){const r=canvas.getBoundingClientRect();return [Math.round(Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*1e6)/1e6,Math.round(Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))*1e6)/1e6];}
function px(p){return [p[0]*canvas.width,p[1]*canvas.height];}
function saveHistory(){undo.push(JSON.stringify(zones));if(undo.length>50)undo.shift();redo=[];}
function line(points,close){if(points.length<2)return;ctx.beginPath();points.forEach((p,i)=>{const q=px(p);i?ctx.lineTo(...q):ctx.moveTo(...q);});if(close)ctx.closePath();}
function render(){
  if(!canvas.width){canvas.width=960;canvas.height=540;}
  ctx.fillStyle='#081421';ctx.fillRect(0,0,canvas.width,canvas.height);
  if(img.complete&&img.naturalWidth)ctx.drawImage(img,0,0,canvas.width,canvas.height);
  zones.forEach((z,index)=>{
    line(z.points,true);const positive=z.type==='include';
    ctx.fillStyle=positive?'rgba(28,215,159,.20)':'rgba(252,84,91,.29)';ctx.strokeStyle=positive?'#49e5ba':'#ff777c';ctx.lineWidth=2.6;ctx.fill();ctx.stroke();
    ctx.fillStyle='#fff';ctx.font='bold 15px sans-serif';const q=px(z.points[0]);ctx.fillText((positive?'Monitor ':'Ignore ')+(index+1),q[0]+6,q[1]+15);
    if(tool==='edit'&&index===movingIndex){z.points.forEach(p=>{const q=px(p);ctx.beginPath();ctx.arc(q[0],q[1],5,0,2*Math.PI);ctx.fillStyle='#fff';ctx.fill();ctx.strokeStyle='#172538';ctx.stroke();});}
  });
  if(draft.length){
    if(tool==='rectangle'&&dragStart&&draft.length){const a=dragStart,b=draft[0];line([a,[b[0],a[1]],b,[a[0],b[1]]],true);}
    else line(draft,false);
    ctx.strokeStyle=tool==='horizon'?'#ffb1b4':$('zones-type').value==='exclude'?'#ff777c':'#49e5ba';ctx.lineWidth=3;ctx.stroke();
    draft.forEach(p=>{const q=px(p);ctx.beginPath();ctx.arc(q[0],q[1],3,0,2*Math.PI);ctx.fillStyle='#fff';ctx.fill();});
  }
  if($('zones-list'))$('zones-list').innerHTML=zones.map((z,i)=>`<div style="display:flex;gap:8px;align-items:center;justify-content:space-between;padding:3px 0"><span>${z.type==='exclude'?'🔴 Ignore':'🟢 Monitor'} ${i+1} · ${z.points.length} points</span><button type="button" data-remove-zone="${i}">Remove</button></div>`).join('')||'<span class="note">No zones drawn. The entire image is monitored.</span>';
}
function snapshot(){img.src='/preview.jpg?zones='+Date.now();}
img.onload=()=>{canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;render();};
img.onerror=()=>notify('No camera preview yet. Start monitoring and select Refresh preview.');
$('zones-refresh').addEventListener('click',snapshot);
$('zones-enabled').addEventListener('change',e=>{enabled=e.target.checked;notify('Enable setting changed. Save detection zones to apply it.');});
function resetDraft(){draft=[];dragStart=null;dragging=false;render();}
$('zones-tool').addEventListener('change',e=>{tool=e.target.value;movingIndex=-1;resetDraft();notify(tool==='polygon'?'Single-click to add points, then press Finish shape. Do not double-click.':tool==='horizon'?'Click along the treetops from left to right, then Finish shape. Everything below the line will be ignored.':tool==='freehand'?'Press and drag to trace an outline, then release.':'Draw on the camera image.');});
function addZone(points,type){if(zones.length>=MAX_ZONES){notify('Maximum 24 zones. Remove one before drawing another.');return false;}
 if(points.length<3){notify('At least three corners are needed. Your drawing is still here.');return false;}
 if(points.length>MAX_POINTS){notify('This outline is too detailed. Use fewer than 256 points or split it into zones. Nothing has been discarded.');return false;}
 saveHistory();zones.push({type:type||$('zones-type').value,points:points.map(p=>p.slice())});resetDraft();notify('Zone added. Save detection zones to apply it.');return true;
}
function finish(){if(tool==='polygon')return addZone(draft,$('zones-type').value);
 if(tool==='horizon'){
   if(draft.length<2){notify('Click at least two points along the horizon first.');return;}
   // Closing the polygon at the bottom of the photo eliminates the need to
   // draw every tree trunk or ground corner. Left-to-right is recommended.
   const first=draft[0],last=draft[draft.length-1];
   if(first[0]>last[0]){notify('Trace the horizon from left to right, please. Your points are unchanged.');return;}
   // Extend the traced skyline to both edges, excluding all ground below it.
   if(draft.length>MAX_POINTS-4){notify('Too many horizon points. Undo a few before finishing (maximum 252). None were discarded.');return;}
   return addZone([[0,first[1]],...draft,[1,last[1]],[1,1],[0,1]],'exclude');
 }
 if(tool==='freehand'){return addZone(draft,$('zones-type').value);}
 notify('Choose Polygon or Trace Horizon, then press Finish shape.');
}
canvas.addEventListener('pointerdown',e=>{
 if(e.button!==0)return;const p=point(e);
 if(tool==='edit'){
   let best=11*11,zi=-1,vi=-1;
   zones.forEach((z,i)=>z.points.forEach((v,j)=>{const a=px(v),b=px(p),d=(a[0]-b[0])**2+(a[1]-b[1])**2;if(d<best){best=d;zi=i;vi=j;}}));
   if(zi>=0){saveHistory();movingIndex=zi;movingVertex=vi;dragging=true;canvas.setPointerCapture(e.pointerId);notify('Drag the white corner handle, then Save detection zones.');render();}else notify('Select Edit corners and drag a white point on an existing polygon.');
   return;
 }
 if(tool==='rectangle'){dragStart=p;draft=[p];canvas.setPointerCapture(e.pointerId);}
 else if(tool==='freehand'){draft=[p];dragging=true;canvas.setPointerCapture(e.pointerId);}
 else if(tool==='polygon'||tool==='horizon'){
   if(draft.length===MAX_POINTS){notify('256-point limit reached. Finish this zone or Undo some points; no points were deleted.');return;}
   draft.push(p);render();notify(`${draft.length} points. Single-click the next corner, or press Finish shape. Do not double-click.`);
 }
});
canvas.addEventListener('pointermove',e=>{
 const p=point(e);
 if(tool==='edit'&&dragging&&movingIndex>=0){zones[movingIndex].points[movingVertex]=p;render();}
 else if(tool==='rectangle'&&dragStart){draft=[p];render();}
 else if(tool==='freehand'&&dragging&&draft.length<MAX_POINTS){
   const a=px(draft[draft.length-1]),b=px(p);
   if(Math.hypot(a[0]-b[0],a[1]-b[1])>=4){draft.push(p);render();}
 }
});
canvas.addEventListener('pointerup',e=>{
 if(tool==='edit'){dragging=false;render();return;}
 if(tool==='rectangle'&&dragStart){const a=dragStart,b=point(e);dragStart=null;draft=[];
   if(Math.abs(a[0]-b[0])<.008||Math.abs(a[1]-b[1])<.008){render();notify('Drag to create a rectangle.');return;}
   addZone([[Math.min(a[0],b[0]),Math.min(a[1],b[1])],[Math.max(a[0],b[0]),Math.min(a[1],b[1])],[Math.max(a[0],b[0]),Math.max(a[1],b[1])],[Math.min(a[0],b[0]),Math.max(a[1],b[1])]]);}
 else if(tool==='freehand'&&dragging){dragging=false;finish();}
});
canvas.addEventListener('pointercancel',()=>{dragging=false;dragStart=null;render();});
canvas.addEventListener('dblclick',e=>{e.preventDefault();notify('Use the Finish shape button; double-click is not needed.');});
$('zones-complete').addEventListener('click',finish);
$('zones-undo').addEventListener('click',()=>{
 if(draft.length){draft.pop();render();notify('Last unfinished corner removed.');}
 else if(undo.length){redo.push(JSON.stringify(zones));zones=JSON.parse(undo.pop());render();notify('Last edit undone. Save to apply.');}
 else notify('Nothing more to undo.');
});
if($('zones-redo'))$('zones-redo').addEventListener('click',()=>{
 if(redo.length){undo.push(JSON.stringify(zones));zones=JSON.parse(redo.pop());render();notify('Edit restored. Save to apply.');}
});
$('zones-clear').addEventListener('click',()=>{if(!window.confirm('Remove ALL zones from this editor? Save is still required.'))return;saveHistory();zones=[];resetDraft();notify('All zones removed in editor. Save to apply.');});
if($('zones-list'))$('zones-list').addEventListener('click',e=>{const b=e.target.closest('[data-remove-zone]');if(!b)return;saveHistory();zones.splice(Number(b.dataset.removeZone),1);render();notify('Selected zone removed. Save to apply.');});
$('zones-save').addEventListener('click',async()=>{
 const button=$('zones-save');if(draft.length){notify('Finish or undo the incomplete outline before saving.');return;}
 button.disabled=true;
 try{const r=await fetch('/settings/detection-zones',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':root.dataset.csrf},body:JSON.stringify({enabled,zones})});
     const d=await r.json();if(!r.ok)throw Error(d.error||'Could not save zones.');
     notify('Saved. The detector will use these areas shortly. Video remains full-frame.');}
 catch(e){notify('Save failed: '+e.message);}finally{button.disabled=false;}
});
async function load(){try{const r=await fetch('/settings/detection-zones');const d=await r.json();if(!r.ok)throw Error(d.error||'Cannot load zones');
 enabled=d.enabled;zones=d.zones;$('zones-enabled').checked=enabled;render();}
 catch(e){notify('Could not load saved zones: '+e.message);}snapshot();}
load();
})();
