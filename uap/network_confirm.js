/* Moon Cheese network-confirmation timer, loaded externally to meet strict CSP. */
(()=>{'use strict';
const panel=document.getElementById('network-confirm-timer');if(!panel)return;
const output=document.getElementById('network-confirm-countdown');
const help=document.getElementById('network-confirm-help');
const button=document.querySelector('#network-confirm-form button[type=submit]');
let offset=0,expires=Number(panel.dataset.deadline),final=false;
const terminal={restored:'Previous network configuration restored.',
 confirmed:'New network configuration confirmed.',
 recovery_error:'Automatic rollback could not be verified. Use local access and check the recovery service.',
 error:'The network change failed. Check System Administration.'};
function render(){
 if(final)return;
 const seconds=Math.max(0,Math.ceil(expires-(Date.now()/1000+offset)));
 output.textContent=`${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;
 if(seconds===0){if(button)button.disabled=true;help.textContent='Confirmation time has expired. Waiting for the recovery service to verify the previous settings. Do not assume restoration succeeded.';}
}
async function check(){
 try{
  const r=await fetch('/system/network/status',{cache:'no-store',credentials:'same-origin',headers:{Accept:'application/json'}});
  if(!r.ok)return;const data=await r.json();
  if(Number.isFinite(Number(data.server_time)))offset=Number(data.server_time)-Date.now()/1000;
  const state=data.network||{};
  if(Object.hasOwn(terminal,state.state)){
   final=true;output.textContent=state.state==='confirmed'?'Confirmed':state.state==='restored'?'Restored':'Attention needed';
   help.textContent=state.message||terminal[state.state];if(button)button.disabled=true;return;
  }
  if(data.pending&&data.pending.expires){expires=Number(data.pending.expires);}
  render();
 }catch(_){render();}
}
render();check();setInterval(()=>{render();check();},2000);
})();
