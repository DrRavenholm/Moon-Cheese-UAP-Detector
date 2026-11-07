/* Moon Cheese Camera and recording: load hardware-valid defaults, do not save automatically. */
(()=>{'use strict';
const panel=document.getElementById('camera-recording-settings');
const button=document.getElementById('camera-recording-reset');
const result=document.getElementById('camera-recording-reset-result');
if(!panel||!button||!result)return;
button.addEventListener('click',()=>{
  if(!window.confirm('Load defaults for Camera and recording only? Values will not be applied until you press Save settings.'))return;
  let values;try{values=JSON.parse(button.dataset.defaults);}catch(_){result.textContent='Defaults unavailable. No changes made.';return;}
  for(const name of ['resolution','fps','pixel_threshold','min_changed_pixels','pre_motion_seconds','post_motion_seconds','max_clip_seconds']){
    const input=panel.querySelector(`[name="${name}"]`);if(!input)continue;
    const target=String(values[name]);
    if(input.tagName==='SELECT'){
      const valid=Array.from(input.options).some(option=>option.value===target&&!option.disabled);
      if(!valid){result.textContent=`${name} is not available on this camera. No unsupported choice was applied.`;continue;}
    }
    input.value=target;input.dispatchEvent(new Event('change',{bubbles:true}));
  }
  result.textContent='Camera and recording defaults loaded. Review the values and press Save settings to apply. All other sections are unchanged.';
});
})();
