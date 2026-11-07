'use strict';
(() => {
  const chooser=document.getElementById('timezone');
  const detect=document.getElementById('detect-timezone');
  const note=document.getElementById('timezone-note');
  if(!chooser||!detect)return;
  const original=chooser.value;
  const now=new Date();
  for(const option of chooser.options){
    let offset='';
    try{
      offset=new Intl.DateTimeFormat('en-GB',{timeZone:option.value,timeZoneName:'longOffset'})
        .formatToParts(now).find(p=>p.type==='timeZoneName')?.value||'';
      offset=offset.replace(/^GMT/,'UTC');
      if(offset==='UTC')offset='UTC+00:00';
      if(/^UTC[+-]\d{1,2}$/.test(offset))offset+=':00';
    }catch(_){offset='UTC offset unavailable';}
    option.textContent=`${offset} — ${option.value.replaceAll('_',' ')}`;
  }
  chooser.value=original;
  detect.addEventListener('click',()=>{
    let zone='';try{zone=Intl.DateTimeFormat().resolvedOptions().timeZone;}catch(_){}
    if(zone && [...chooser.options].some(o=>o.value===zone)){
      chooser.value=zone;
      note.textContent=`Selected ${zone}. Press Save preferences to confirm.`;
    }else if(note){note.textContent='Your browser timezone could not be matched; please choose from the list.';}
  });
})();
