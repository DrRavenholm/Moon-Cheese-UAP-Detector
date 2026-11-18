/* Administrator-only camera preview zone editor: no extra Picamera2 owner. */
(()=>{'use strict';
 const root=document.getElementById('zones-editor');if(!root)return;
 const canvas=document.getElementById('zones-canvas'),ctx=canvas.getContext('2d'),status=document.getElementById('zones-status');
 const img=new Image();let zones=[],draft=[],dragStart=null,tool='rectangle';
 let enabled=false;
 const $=id=>document.getElementById(id);
 function notify(s){status.textContent=s;}
 function px(p){return [p[0]*canvas.width,p[1]*canvas.height];}
 function point(e){const r=canvas.getBoundingClientRect();return [Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))];}
 function render(){
   if(!canvas.width){canvas.width=960;canvas.height=540;}
   ctx.fillStyle='#081421';ctx.fillRect(0,0,canvas.width,canvas.height);
   if(img.complete&&img.naturalWidth)ctx.drawImage(img,0,0,canvas.width,canvas.height);
   const draw=(zone,idx)=>{
     if(zone.points.length<2)return;
     ctx.beginPath();zone.points.forEach((p,i)=>{const q=px(p);i?ctx.lineTo(...q):ctx.moveTo(...q);});
     if(zone.points.length>=3)ctx.closePath();
     const positive=zone.type==='include';ctx.fillStyle=positive?'rgba(28,215,159,.18)':'rgba(252,84,91,.26)';ctx.strokeStyle=positive?'#49e5ba':'#ff777c';ctx.lineWidth=3;ctx.fill();ctx.stroke();
     if(idx!==null){ctx.fillStyle='#fff';ctx.font='bold 16px sans-serif';const q=px(zone.points[0]);ctx.fillText(`${positive?'Monitor':'Ignore'} ${idx+1}`,q[0]+8,q[1]+18);}
   };
   zones.forEach(draw);
   if(draft.length)draw({type:$('zones-type').value,points:draft},null);
   if(dragStart&&draft.length){const a=dragStart,b=draft[0];
     draw({type:$('zones-type').value,points:[a,[b[0],a[1]],b,[a[0],b[1]]]},null);}
 }
 function snapshot(){img.src='/preview.jpg?zones='+Date.now();}
 img.onload=()=>{canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;render();};img.onerror=()=>notify('No saved camera preview is available yet. Start detector monitoring, then refresh.');
 $('zones-refresh').addEventListener('click',snapshot);
 $('zones-enabled').addEventListener('change',e=>enabled=e.target.checked);
 $('zones-tool').addEventListener('change',e=>{tool=e.target.value;draft=[];dragStart=null;render();});
 function newZone(points){if(zones.length>=24){notify('Maximum 24 zones.');return;}
   zones.push({type:$('zones-type').value,points});draft=[];dragStart=null;render();notify('Zone added. Save Zones to activate it.');}
 canvas.addEventListener('pointerdown',e=>{
   if(e.button!==0)return;
   const p=point(e);
   if(tool==='rectangle'){dragStart=p;draft=[p];canvas.setPointerCapture(e.pointerId);}
   else {draft.push(p);render();}
 });
 canvas.addEventListener('pointermove',e=>{
   if(tool==='rectangle'&&dragStart){draft=[point(e)];render();}
 });
 canvas.addEventListener('pointerup',e=>{
   if(!dragStart||tool!=='rectangle')return;
   const a=dragStart,b=point(e);dragStart=null;draft=[];
   if(Math.abs(a[0]-b[0])<.008||Math.abs(a[1]-b[1])<.008){render();return;}
   const left=Math.min(a[0],b[0]),right=Math.max(a[0],b[0]),top=Math.min(a[1],b[1]),bottom=Math.max(a[1],b[1]);
   newZone([[left,top],[right,top],[right,bottom],[left,bottom]]);
 });
 canvas.addEventListener('dblclick',e=>{
   if(tool==='polygon'){e.preventDefault();if(draft.length>=3)newZone(draft.slice(0,36));else notify('Click three or more points to form a polygon.');}
 });
 $('zones-complete').addEventListener('click',()=>{if(draft.length>=3)newZone(draft.slice(0,36));else notify('Click at least three corners first.');});
 $('zones-undo').addEventListener('click',()=>{if(draft.length)draft.pop();else zones.pop();render();notify('Last point or zone removed. Save to apply changes.');});
 $('zones-clear').addEventListener('click',()=>{zones=[];draft=[];render();notify('Zones cleared in editor. Save to apply.');});
 $('zones-save').addEventListener('click',async()=>{
   const button=$('zones-save');button.disabled=true;
   try{
     const r=await fetch('/settings/detection-zones',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':root.dataset.csrf},body:JSON.stringify({enabled,zones})});
     const d=await r.json();if(!r.ok)throw Error(d.error||'Could not save zones.');
     notify('Detection zones saved. The detector will apply them shortly. Videos remain full-frame.');
   }catch(e){notify('Save failed: '+e.message);}finally{button.disabled=false;}
 });
 async function load(){try{const r=await fetch('/settings/detection-zones');const d=await r.json();if(!r.ok)throw Error(d.error);
   enabled=d.enabled;zones=d.zones;$('zones-enabled').checked=enabled;render();
 }catch(e){notify('Could not load zones: '+e.message);}snapshot();}
 load();
})();
