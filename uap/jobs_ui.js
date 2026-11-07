'use strict';
(() => {
  const form=document.querySelector('#job-mode')?.closest('form');
  if(!form) return;
  const mode=form.querySelector('#job-mode'),advanced=form.querySelector('#job-advanced');
  const estimate=form.querySelector('#job-estimate'),exposureMode=form.querySelector('#job-exposure-mode');
  const exposure=form.querySelector('#job-exposure'),focus=form.querySelector('#job-focus'),awb=form.querySelector('#job-awb');
  let estimateCounter=0, timer=null, latest=null;
  const number=name=>Number(form.elements.namedItem(name)?.value||0);
  const gib=n=>(n/1073741824).toFixed(2)+' GiB';
  function render(data){
    const interval=number('interval_seconds')||15,fps=number('output_fps')||25;
    const frames=data.frames;
    const source=data.samples?`Recent photographs from ${data.samples} source archive(s)`:'Conservative fallback (no recent source archive)';
    estimate.className=data.fits?'notice':'notice error';
    const grid=document.createElement('div');grid.className='job-estimate-grid';
    const items=[['Planned photographs',frames.toLocaleString()],['Finished MP4',(frames/fps).toFixed(1)+' seconds'],
      ['Space currently free',gib(data.available)],['Working space',gib(data.bytes)],
      ['Safety reserve',gib(data.reserve)],['Total required',gib(data.required)]];
    for(const [label,value] of items){
      const tile=document.createElement('div');
      const caption=document.createElement('div');caption.className='sub';caption.textContent=label;
      const figure=document.createElement('strong');figure.className='value';figure.textContent=value;
      tile.append(caption,figure);grid.append(tile);
    }
    const line=document.createElement('p');line.className='note';
    line.textContent=`${data.fits?'✓ Enough space to schedule.':'⚠ Not enough free storage to schedule.'} `+
      `Estimated source JPEG: ${(data.bytes_per_frame/1048576).toFixed(1)} MiB. ${source}.`;
    estimate.replaceChildren(grid,line);
  }
  function controls(){
    const adv=mode.value==='advanced',manual=adv&&exposureMode.value==='manual';
    const manualFocus=adv&&focus.value==='manual',manualWB=adv&&awb.value==='0';
    advanced.hidden=!adv;
    advanced.querySelectorAll('input,select').forEach(el=>{
      el.disabled=!adv||(el===exposure&&!manual)||(el.name==='gain'&&!manual)||
        (el.name==='lens_position'&&!manualFocus)||
        ((el.name==='red_gain'||el.name==='blue_gain')&&!manualWB);
    });
    form.querySelector('#job-lens-wrap').hidden=!manualFocus;
    form.querySelectorAll('.job-colour-control').forEach(el=>el.hidden=!manualWB);
    const seconds=Number(exposure.value)/1000,interval=number('interval_seconds')||15;
    const invalid=manual&&(!Number.isFinite(seconds)||seconds<0.0001||seconds>112||seconds+1.5>=interval);
    exposure.setCustomValidity(invalid?'Exposure must leave 1.5 seconds for capture processing within the selected interval.':'');
    return invalid;
  }
  async function fetchEstimate(){
    const duration=number('duration_minutes'),interval=number('interval_seconds')||15;
    const token=++estimateCounter;
    if(!Number.isFinite(duration)||duration<=0||duration>480||interval<=0){
      latest=null;estimate.textContent='Enter a valid capture duration and interval to calculate storage.';return;
    }
    estimate.setAttribute('aria-busy','true');
    if(!latest) estimate.textContent='Checking available storage…';
    try{
      const response=await fetch(`/observations/timelapse/estimate?duration_minutes=${Math.ceil(duration)}&interval_seconds=${interval}`,{credentials:'same-origin',cache:'no-store'});
      const data=await response.json();
      if(token!==estimateCounter)return;
      if(!response.ok)throw Error(data.error||'Storage estimate unavailable');
      latest={...data,frames:Math.ceil(duration*60/interval)};
      render(latest);
    }catch(err){if(token===estimateCounter){
      if(!latest)estimate.textContent=`Storage estimate unavailable (${err.message}); the server checks again when scheduling.`;
      else estimate.querySelector('.note')?.append(document.createTextNode(' Could not refresh storage; server will recheck at scheduling.'));
    }}finally{if(token===estimateCounter)estimate.removeAttribute('aria-busy');}
  }
  function queue(){
    clearTimeout(timer);++estimateCounter;
    timer=setTimeout(fetchEstimate,220);
  }
  form.addEventListener('input',event=>{
    if(event.target.name==='duration_minutes') queue();
    else if(event.target.name==='output_fps'&&latest)render(latest);
    else if(event.target===exposure)controls();
  });
  form.addEventListener('change',event=>{
    if(event.target.name==='duration_minutes'||event.target.name==='interval_seconds')queue();
    else if(event.target.name==='output_fps'&&latest)render(latest);
    else if([mode,exposureMode,exposure,focus,awb].includes(event.target))controls();
  });
  form.addEventListener('submit',event=>{
    if(controls()&&!form.checkValidity()){
      event.preventDefault();
      if(mode.value==='advanced')advanced.hidden=false;
      form.reportValidity();
    }
  });
  controls();fetchEstimate();
})();
