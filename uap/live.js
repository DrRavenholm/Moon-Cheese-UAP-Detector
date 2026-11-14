/* Shared-snapshot admin investigation and temporary still-photography controls. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const canvas = $('live-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const stage = $('live-stage');
  const names = {original:'Original',detection:'Detection (grayscale)',lowlight:'Low-light enhanced'};
  const root = $('live-root');
  let image = null, frozen = false, compare = false, zoom = 1, brightness = 100,
      contrast = 100, offsetX = 0, offsetY = 0, pointer = null, photoPolling = null,
      reviewingPhoto = false, originalSource = null;
  const view = $('live-view'), left = $('live-left'), right = $('live-right'), split = $('live-split');
  const setStatus = message => { $('live-status').textContent = message; };
  // iOS Safari/Chrome do not consistently implement CanvasRenderingContext2D.filter.
  // Render the same pixel processing on every browser, including iOS WebKit.
  const processed=new Map();
  function processedImage(which) {
    const key=`${which}:${brightness}:${contrast}`;
    if(processed.has(key))return processed.get(key);
    const layer=document.createElement('canvas');
    layer.width=image.naturalWidth;layer.height=image.naturalHeight;
    const c=layer.getContext('2d',{willReadFrequently:true});
    c.drawImage(image,0,0);
    const pixels=c.getImageData(0,0,layer.width,layer.height);
    const data=pixels.data;
    const brightnessFactor=brightness/100, contrastFactor=contrast/100;
    for(let i=0;i<data.length;i+=4){
      let r=data[i],g=data[i+1],b=data[i+2];
      if(which!=='original'){
        let y=.2126*r+.7152*g+.0722*b;
        if(which==='lowlight'){
          y=Math.min(255,Math.pow(y/255,.64)*255*1.12);
        } else y=(y-128)*1.30+128;
        r=g=b=y;
      }
      data[i]=Math.min(255,Math.max(0,(r-128)*contrastFactor+128)*brightnessFactor);
      data[i+1]=Math.min(255,Math.max(0,(g-128)*contrastFactor+128)*brightnessFactor);
      data[i+2]=Math.min(255,Math.max(0,(b-128)*contrastFactor+128)*brightnessFactor);
    }
    c.putImageData(pixels,0,0);
    processed.set(key,layer);
    return layer;
  }
  function drawInto(context,width,height,which){
    context.save();
    const source=processedImage(which);
    const iw=source.width,ih=source.height;
    const base=Math.min(width/iw,height/ih);
    const dw=iw*base*zoom,dh=ih*base*zoom;
    context.drawImage(source,(width-dw)/2+offsetX*width,(height-dh)/2+offsetY*height,dw,dh);
    context.restore();
  }
  function paint(output=canvas, annotate=false) {
    const c=output.getContext('2d');
    c.clearRect(0,0,output.width,output.height);
    c.fillStyle='#070d19';c.fillRect(0,0,output.width,output.height);
    if (!image) return;
    const w=output.width,h=output.height;
    if (compare) {
      const x=Math.round(w*Number(split.value)/100);
      c.save();c.beginPath();c.rect(0,0,x,h);c.clip();drawInto(c,w,h,left.value);c.restore();
      c.save();c.beginPath();c.rect(x,0,w-x,h);c.clip();drawInto(c,w,h,right.value);c.restore();
      c.fillStyle='#d5f5ff';c.fillRect(x-1,0,2,h);
      if (annotate) {
        c.font=`bold ${Math.max(16,Math.round(w/55))}px sans-serif`;
        for (const [text,rightEdge] of [[names[left.value],false],[names[right.value],true]]) {
          const px=rightEdge?w-c.measureText(text).width-16:16;
          c.fillStyle='rgba(6,18,31,.85)';c.fillRect(px-9,10,c.measureText(text).width+18,39);
          c.fillStyle='white';c.fillText(text,px,38);
        }
      }
    } else drawInto(c,w,h,view.value);
  }
  function redraw() {
    paint();
    $('live-left-label').hidden = !compare;
    $('live-right-label').hidden = !compare;
    $('live-left-label').textContent = names[left.value];
    $('live-right-label').textContent = names[right.value];
    $('live-split-row').hidden = !compare;
    $('live-split-value').textContent = `${split.value}%`;
    $('live-compare').textContent = compare?'Close comparison':'Compare frame';
  }
  let fetching = false;
  function loadImage(src) {
    return new Promise((resolve,reject)=>{
      const img=new Image();
      img.onload=()=>img.naturalWidth>0 ? resolve(img) : reject(new Error('Empty image'));
      img.onerror=()=>reject(new Error('Image is unavailable'));
      img.src=src;
    });
  }
  function useImage(img, isPhoto=false) {
    image=img;processed.clear();reviewingPhoto=isPhoto;
    const displayScale=isPhoto?Math.min(1,1920/img.naturalWidth):1;
    canvas.width=Math.round(img.naturalWidth*displayScale);
    canvas.height=Math.round(img.naturalHeight*displayScale);
    $('live-back-to-camera').hidden=!isPhoto;
    redraw();
    $('live-source-info').textContent=isPhoto
      ? `Reviewing native still: ${img.naturalWidth} × ${img.naturalHeight}. Processed PNG export is 1920 pixels wide; the original photo remains unchanged.`
      : `Camera snapshot source: ${img.naturalWidth} × ${img.naturalHeight}. Export matches these real source dimensions.`;
  }
  async function refresh(force=false) {
    if ((frozen && !force) || reviewingPhoto && !force || fetching) return;
    fetching=true;
    setStatus('Loading camera snapshot…');
    try {
      // This endpoint wakes the recorder's on-demand HD JPEG cache, without
      // opening another camera. Initial requests may take ~4 seconds.
      let img=null;let reason='';
      for (let attempt=0;attempt<5;attempt++) {
        try {
          const response=await fetch(`/live-camera/hd.jpg?updated=${Date.now()}`,{cache:'no-store'});
          if (response.ok) {
            img=await loadImage(`/live-camera/hd.jpg?updated=${Date.now()}`);
            break;
          }
          if (response.status!==503) throw new Error('HD image unavailable');
          reason='Waiting for first HD frame';
        } catch (error) {reason=error.message;}
        if (attempt<4) await new Promise(resolve=>setTimeout(resolve,1100));
      }
      if (!img) {
        img=await loadImage(`/preview.jpg?updated=${Date.now()}`);
        reason='HD snapshot not ready — using standard preview';
      }
      useImage(img,false);
      setStatus(`${reason ? reason+' · ' : ''}Snapshot updated ${new Date().toLocaleTimeString()}`);
    } catch(error) {setStatus(error.message||'Camera image unavailable');}
    finally {fetching=false;}
  }
  $('live-freeze').addEventListener('click',()=>{
    frozen=!frozen;$('live-freeze').textContent=frozen?'Resume':'Freeze';
    setStatus(frozen?'Snapshot frozen for investigation':'Automatic 10-second refresh resumed');
    if (!frozen) refresh(true);
  });
  $('live-refresh').addEventListener('click',()=>{reviewingPhoto=false;refresh(true);});
  $('live-back-to-camera').addEventListener('click',()=>{reviewingPhoto=false;frozen=false;$('live-freeze').textContent='Freeze';refresh(true);});
  $('live-compare').addEventListener('click',()=>{compare=!compare;redraw();});
  for (const node of [view,left,right,split]) node.addEventListener('input',redraw);
  $('live-zoom').addEventListener('input', e=>{zoom=Number(e.target.value);if (zoom===1){offsetX=0;offsetY=0;}redraw();});
  $('live-brightness').addEventListener('input',e=>{brightness=Number(e.target.value);processed.clear();redraw();});
  $('live-contrast').addEventListener('input',e=>{contrast=Number(e.target.value);processed.clear();redraw();});
  $('live-reset').addEventListener('click',()=>{zoom=1;offsetX=offsetY=0;brightness=contrast=100;
    $('live-zoom').value=1;$('live-brightness').value=100;$('live-contrast').value=100;processed.clear();redraw();});
  stage.addEventListener('pointerdown',e=>{if (zoom<=1) return;pointer={x:e.clientX,y:e.clientY,ox:offsetX,oy:offsetY};stage.setPointerCapture(e.pointerId);});
  stage.addEventListener('pointermove',e=>{if (!pointer) return;
    offsetX=Math.max(-2,Math.min(2,pointer.ox+(e.clientX-pointer.x)/stage.clientWidth));
    offsetY=Math.max(-2,Math.min(2,pointer.oy+(e.clientY-pointer.y)/stage.clientHeight));redraw();});
  stage.addEventListener('pointerup',()=>pointer=null);
  stage.addEventListener('pointercancel',()=>pointer=null);
  async function saveCanvas() {
    if (!image) return setStatus('No snapshot to save');
    const output=document.createElement('canvas');
    // A native 12 MP photo can be reviewed without rendering a huge export
    // canvas on phones. HD recorder frames export at their true resolution.
    const isFullPhoto=reviewingPhoto && image.naturalWidth>1920;
    output.width=isFullPhoto?1920:image.naturalWidth;
    output.height=isFullPhoto?Math.round(image.naturalHeight*1920/image.naturalWidth):image.naturalHeight;
    paint(output,true);
    output.toBlob(async blob=>{
      if (!blob) return setStatus('Could not create the PNG');
      const filename=`sky-camera-${Date.now()}${compare?'-comparison':''}-${output.width}x${output.height}.png`;
      // Always download directly; never invoke the OS/browser share sheet.
      const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;
      document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
      setStatus(`PNG download started (${output.width} × ${output.height})`);
    },'image/png');
  }
  $('live-save').addEventListener('click',saveCanvas);
  const fields={mode:'photo-mode',format:'photo-format',exposure_ms:'photo-exposure',gain:'photo-gain',
    focus:'photo-focus',awb:'photo-awb',red_gain:'photo-red',blue_gain:'photo-blue',
    brightness:'photo-brightness',contrast:'photo-contrast',saturation:'photo-saturation'};
  const exposurePanel=$('photo-progress'),exposureClock=$('photo-countdown'),exposureBar=$('photo-exposure-progress'),exposurePhase=$('photo-phase');
  let exposureTicker=null,exposureState=null;
  function stopExposureTimer(){
    if(exposureTicker)clearInterval(exposureTicker);
    exposureTicker=null;exposureState=null;
    exposurePanel.hidden=true;
  }
  function renderExposure(){
    if(!exposureState)return;
    const elapsed=(performance.now()-exposureState.syncedAt)/1000;
    const left=Math.max(0,exposureState.remaining-elapsed);
    exposureClock.textContent=left>0?`${Math.ceil(left)} s`:'Finishing…';
    exposureBar.value=Math.max(0,Math.min(100,(1-left/exposureState.total)*100));
    if(left===0)exposurePhase.textContent='Completing exposure…';
  }
  function updateExposure(info){
    if(info.state==='exposing'&&Number(info.exposure_seconds)>0&&Number.isFinite(Number(info.remaining_seconds))){
      const total=Number(info.exposure_seconds);
      exposureState={total,remaining:Math.max(0,Number(info.remaining_seconds)),syncedAt:performance.now()};
      exposurePanel.hidden=false;exposurePhase.textContent='Manual exposure in progress';
      exposureBar.max=100;renderExposure();
      if(!exposureTicker)exposureTicker=setInterval(renderExposure,200);
    }else if(info.state==='preparing' || info.state==='queued'){
      exposurePanel.hidden=false;exposurePhase.textContent='Preparing photography camera…';
      exposureClock.textContent='—';exposureBar.removeAttribute('value');
      if(exposureTicker)clearInterval(exposureTicker);exposureTicker=null;exposureState=null;
    }else if(info.state==='saving'){
      exposurePanel.hidden=false;exposurePhase.textContent='Saving photograph…';exposureClock.textContent='—';
      exposureBar.removeAttribute('value');
      if(exposureTicker)clearInterval(exposureTicker);exposureTicker=null;exposureState=null;
    }else stopExposureTimer();
  }
  $('photo-capture').addEventListener('click',async()=>{
    const btn=$('photo-capture');btn.disabled=true;
    $('photo-download').replaceChildren();stopExposureTimer();
    const data=new FormData();data.set('csrf',root.dataset.csrf);
    const advanced=$('live-advanced').open;
    for(const [key,id] of Object.entries(fields)) data.set(key,$(id).value);
    if (!advanced) {data.set('mode','auto');data.set('focus','infinity');data.set('awb','auto');}
    const manualPhoto=data.get('mode')==='manual';
    try {
      const res=await fetch('/live-camera/capture',{method:'POST',body:data,credentials:'same-origin'});
      const contentType=res.headers.get('content-type')||'';
      const result=contentType.includes('application/json') ? await res.json() : null;
      if (!res.ok) throw new Error(result?.error || `Photo request failed (HTTP ${res.status}). Please check System Health or sign in again.`);
      if (!result || !result.token) throw new Error('Camera did not return a capture reference. Please retry.');
      const token=result.token;const started=Date.now();
      $('photo-status').textContent='Waiting for camera, then capturing photograph…';
      if(manualPhoto)updateExposure({state:'queued'});
      if(photoPolling) clearInterval(photoPolling);
      photoPolling=setInterval(async()=>{
        try {
          const resp=await fetch(`/live-camera/photo/${token}/status`,{cache:'no-store'});
          if(!resp.ok) throw new Error('Photo status unavailable');
          const info=await resp.json();$('photo-status').textContent=info.message||info.state;
          if(manualPhoto)updateExposure(info);
          if(info.state==='done') {
            clearInterval(photoPolling);photoPolling=null;btn.disabled=false;stopExposureTimer();
            const a=document.createElement('a');a.className='button';a.textContent=`Download ${info.width} × ${info.height} ${info.format.toUpperCase()} photo`;
            a.href=`/live-camera/photo/${token}/download`;
            const review=document.createElement('button');review.type='button';review.textContent='Review captured photo';
            review.addEventListener('click',async()=>{
              try {
                $('photo-status').textContent='Opening captured photograph for comparison…';
                const img=await loadImage(`/live-camera/photo/${token}/image`);
                useImage(img,true);
                frozen=true;$('live-freeze').textContent='Resume';
                window.scrollTo({top:stage.getBoundingClientRect().top+window.scrollY-100,behavior:'smooth'});
                $('photo-status').textContent='Photo ready for comparison. Save current view PNG exports an enhanced 1080p copy.';
              }catch(error){$('photo-status').textContent='Could not review photo: '+error.message;}
            });
            $('photo-download').replaceChildren(a,document.createTextNode(' '),review);
          } else if(info.state==='error' || Date.now()-started>240000) {
            clearInterval(photoPolling);photoPolling=null;btn.disabled=false;
            stopExposureTimer();
            if(info.state!=='error') $('photo-status').textContent='Capture timed out. Check System Health and camera service before retrying.';
          }
        } catch(e) {clearInterval(photoPolling);photoPolling=null;btn.disabled=false;stopExposureTimer();$('photo-status').textContent=e.message;}
      },1500);
    } catch(e) {stopExposureTimer();$('photo-status').textContent=e.message;btn.disabled=false;}
  });
  setInterval(()=>refresh(),10000);
  refresh();
})();
