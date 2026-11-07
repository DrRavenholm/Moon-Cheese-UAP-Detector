/* Moon Cheese v0.9.9.5.3: compact, read-only software update status polling. */
(()=>{'use strict';
 const password=document.getElementById('software-admin-password');
 if(password){window.addEventListener('pageshow',()=>{password.value='';});}
 const node=document.getElementById('software-worker-result');
 const section=document.getElementById('software-updates');
 if(!node||!section)return;
 let previous='';
 async function poll(){
   try{
     const response=await fetch('/system/software/status',{credentials:'same-origin',cache:'no-store',headers:{Accept:'application/json'}});
     if(!response.ok)return;
     const info=await response.json();
     if(!['queued','working','ok','error'].includes(info.state))return;
     const text=`${info.action==='repair'?'Repair':'Update'} — ${info.state}: ${info.message||'No details available.'}`;
     node.hidden=false;node.textContent=text;
     if(info.state==='ok'&&previous!==text){
       const hint=document.createElement('a');hint.href='/system#software-updates';hint.textContent=' Reload to view the installed version';
       node.append(hint);
     }
     previous=text;
   }catch(_){/* Dashboard can restart temporarily during an update. */}
 }
 poll();setInterval(poll,4000);
})();
