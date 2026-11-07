(() => {
  'use strict';
  const form=document.getElementById('storage-delete-form');if(!form)return;
  const choices=[...form.querySelectorAll('.item-choice')];
  const dialog=document.getElementById('storage-confirm');
  const actionInput=document.getElementById('storage-action');
  const selectedButton=document.getElementById('storage-delete-selected');
  const counter=document.getElementById('storage-selected-count');
  const totalText=document.getElementById('storage-selected-size');
  const details=document.getElementById('storage-confirm-details');
  const heading=document.getElementById('storage-confirm-title');
  const caution=document.getElementById('storage-confirm-caution');
  const defaultAction=actionInput.value;
  const checked=()=>choices.filter(c=>c.checked);
  function recalc(){
    const list=checked();const bytes=list.reduce((n,c)=>n+Number(c.dataset.bytes||0),0);
    counter.textContent=`${list.length} selected`;
    totalText.textContent=`${(bytes/1048576).toFixed(1)} MB`;
    selectedButton.disabled=!list.length;
    const all=document.getElementById('select-all');all.checked=choices.length>0 && list.length===choices.length;
  }
  choices.forEach(c=>c.addEventListener('change',recalc));
  document.getElementById('select-all').addEventListener('change',e=>{choices.forEach(c=>c.checked=e.target.checked);recalc();});
  function promptDelete(zipOnly=false,bytesOverride=null){
    const list=checked();if(!list.length)return;
    actionInput.value=zipOnly?'delete_sources':defaultAction;
    const bytes=bytesOverride ?? list.reduce((n,c)=>n+Number(c.dataset.bytes||0),0);
    heading.textContent=zipOnly?'Delete source ZIP only?':'Permanently delete selected items?';
    details.textContent=`${list.length} item(s), approximately ${(bytes/1048576).toFixed(1)} MB. ${list.length===1?list[0].dataset.label:''}`;
    caution.textContent=zipOnly?'This removes only the source ZIP. The finished MP4, observation and notes remain.':'Files and associated observation records will be permanently deleted. This cannot be undone.';
    if(typeof dialog.showModal==='function')dialog.showModal();
    else if(window.confirm(heading.textContent))form.requestSubmit(document.getElementById('storage-accept'));
  }
  form.querySelectorAll('.row-delete').forEach(button=>button.addEventListener('click',()=>{
    choices.forEach(c=>c.checked=c.value===button.dataset.value);
    recalc();promptDelete(button.dataset.action==='delete_sources',button.dataset.action==='delete_sources'?Number(button.dataset.bytes):null);
  }));
  selectedButton.addEventListener('click',()=>promptDelete());
  document.getElementById('storage-cancel').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});
  form.addEventListener('submit',e=>{
    if(!checked().length){e.preventDefault();if(dialog.open)dialog.close();}
    if(dialog.open!==true && typeof dialog.showModal==='function')e.preventDefault();
  });recalc();
})();
