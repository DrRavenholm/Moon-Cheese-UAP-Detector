/* Moon Cheese v0.9.9.4.4: submit to the real form action attribute.
   A hidden field named "action" shadows HTMLFormElement.action in browsers;
   form.action can therefore be an INPUT instead of a URL. */
(()=>{'use strict';
const root=document.getElementById('network-admin');
if(!root)return;
const inline=(action)=>root.querySelector(`.network-inline-result[data-network-status="${action}"]`);
const labels={npm_apply:'NPM + Cloudflare',tunnel_apply:'Cloudflare Tunnel',tunnel_abandon:'Tunnel abandonment',tunnel_cleanup:'Unfinished Tunnel cleanup',tunnel_disable:'Tunnel disable',tunnel_remove:'Tunnel removal',npm:'NPM + Cloudflare',ddns_check:'DDNS',local:'Local access',tunnel:'Cloudflare Tunnel',wifi_scan:'Wi-Fi scan',wifi_connect:'Wi-Fi connection',wifi_radio:'Wi-Fi radio',ip_change:'IP address',npm_preview:'Domain preview',npm_change:'Domain change',npm_retire_old:'Previous proxy'};
const active=new Map();
function inform(action,level,message,time){
 const box=inline(action);if(!box)return;
 box.hidden=false;box.replaceChildren();
 const strong=document.createElement('strong');strong.textContent=`${labels[action]||action} — ${level}: `;
 const content=document.createElement('span');content.textContent=String(message||'No details available.');
 box.append(strong,content);
 if(time){const small=document.createElement('small');small.textContent=` (${time})`;box.append(small);}
}
async function jsonResponse(response){
 const type=response.headers.get('Content-Type')||'';
 if(response.redirected || !type.includes('application/json')){
   throw Error(response.redirected||response.status===401||response.status===403?
     'Your administrator session may have expired. Reload this page and sign in again.':
     `Unexpected server response (HTTP ${response.status}). No change has been confirmed. Check the local dashboard logs.`);
 }
 let data;try{data=await response.json();}catch(_){throw Error('The server sent invalid JSON. No operation has been confirmed.');}
 if(!response.ok)throw Error(data.error||`The request failed (HTTP ${response.status}).`);
 return data;
}
async function fetchStatus(){
 const resp=await fetch('/system/network/status',{credentials:'same-origin',cache:'no-store',headers:{Accept:'application/json'}});
 return jsonResponse(resp);
}
function submissionURL(form){
 // Never use form.action here: <input name="action"> shadows that DOM property.
 // Flask emits this same-origin absolute path; reject missing/modified targets.
 const declared=form.getAttribute('action');
 if(declared!=='/system/network/action'){
   throw Error('Unexpected network form destination. No settings were changed.');
 }
 return declared;
}
function statusFor(operations,action,id){return operations.find(item=>item.action===action&&item.request_id===id);}
const radios=document.getElementById('network-wifi-radio-state');
const radioChoice=document.getElementById('network-wifi-radio-choice');
// Keep a pending administrator choice separate from the actual hardware state.
let pendingWifiChoice=false;
if(radioChoice)radioChoice.addEventListener('change',()=>{pendingWifiChoice=true;});
const scanProgress=document.getElementById('network-scan-progress');
const wifiResults=document.getElementById('network-wifi-scan-results');
const ssidInput=document.getElementById('network-wifi-ssid');
function renderScan(item){
 if(!wifiResults)return;
 wifiResults.replaceChildren();
 const records=Array.isArray(item.networks)?item.networks:[];
 const header=document.createElement('p');header.className='note';header.textContent=`Scan completed: ${records.length} visible networks.`;wifiResults.append(header);
 if(!records.length)return;
 const list=document.createElement('ul');
 for(const record of records){
   const li=document.createElement('li');
   const button=document.createElement('button');button.type='button';button.className='network-select-ssid';
   button.dataset.ssid=record.ssid||'';button.textContent=record.ssid||'(Unnamed network)';
   li.append(button,document.createTextNode(` (${record.signal||'?'}% signal, ${record.security||'unknown security'})`));list.append(li);
 }
 wifiResults.append(list);
}
root.addEventListener('click',event=>{
 const button=event.target.closest('.network-select-ssid');
 if(button&&ssidInput){ssidInput.value=button.dataset.ssid||'';ssidInput.focus();}
});
function updateWifi(state){
 if(!['enabled','disabled'].includes(state))return;
 if(radios){const strong=radios.querySelector('strong');if(strong)strong.textContent=state;}
 if(pendingWifiChoice && radioChoice && radioChoice.value===(state==='enabled'?'yes':'no') && !active.has('wifi_radio'))pendingWifiChoice=false;
 if(radioChoice && !pendingWifiChoice && !active.has('wifi_radio'))radioChoice.value=state==='enabled'?'yes':'no';
}
async function poll(){
 const data=await fetchStatus();updateWifi(data.wifi_radio);updatePhysicalInterfaces(data.interfaces);
 const operations=Array.isArray(data.operations)?data.operations:[];
 for(const [action,req] of active){
   const found=statusFor(operations,action,req.id);
   if(found){
     inform(action,found.state,found.message,found.time);
     if(action==='npm_preview'&&found.state==='ready'&&found.preview_id&&changeForm){
       changeForm.querySelector('input[name=preview_id]').value=found.preview_id;
       changeForm.querySelector('input[name=action]').value='npm_change';
       if(changeApproval){changeApproval.hidden=false;changeApproval.querySelector('input').required=true;}
       if(changeButton)changeButton.textContent='Apply reviewed domain change';
       if(resetChange)resetChange.hidden=false;
     }
     if(found.state!=='working'){
       if(action==='wifi_radio' && ['ok','complete','success'].includes(found.state)){
         // Wait for the actual device state to match the selected value before clearing the draft.
         if(radioChoice && radioChoice.value===(data.wifi_radio==='enabled'?'yes':'no'))pendingWifiChoice=false;
       }
       if(action==='wifi_scan'){renderScan(found);if(scanProgress)scanProgress.textContent='Results shown below.';}
       active.delete(action);req.button.disabled=false;
     }
   }else if(Date.now()-req.start>(action==='npm'||action==='npm_change'||action==='npm_apply'?840000:240000)){
     inform(action,'Unconfirmed','No matching completion status was received. Verify the device state before retrying.');
     active.delete(action);req.button.disabled=false;
   }
 }
 return data;
}
const changeForm=document.getElementById('network-domain-change-form');
const changeApproval=document.getElementById('network-domain-approve-line');
const changeButton=document.getElementById('network-domain-change-submit');
const resetChange=document.getElementById('network-domain-change-reset');
function resetReview(){if(!changeForm)return;
 changeForm.querySelector('input[name=action]').value='npm_preview';
 changeForm.querySelector('input[name=preview_id]').value='';
 if(changeApproval){changeApproval.hidden=true;changeApproval.querySelector('input').checked=false;changeApproval.querySelector('input').required=false;}
 if(changeButton)changeButton.textContent='Check replacement domain';
 if(resetChange)resetChange.hidden=true;
}
if(changeForm){
 const watched=['hostname','zone','token','email','adopt_dns'];
 for(const name of watched){const item=changeForm.elements.namedItem(name);if(item)item.addEventListener('change',resetReview);}
 if(resetChange)resetChange.addEventListener('click',resetReview);
}
const ipForm=document.getElementById('network-ip-form');
for(const form of root.querySelectorAll('form')){
 if(form===ipForm)continue;
 form.addEventListener('submit',async(event)=>{
   event.preventDefault();if(!form.reportValidity())return;
   const data=new FormData(form),action=String(data.get('action')||'');
   const button=form.querySelector('button[type="submit"]');
   if(!inline(action)||!button||active.has(action))return;
   button.disabled=true;inform(action,'Submitting',action==='wifi_scan'?'Scanning will start shortly…':'Sending an administrator request…');
   try{
     const res=await jsonResponse(await fetch(submissionURL(form),{method:'POST',body:data,credentials:'same-origin',headers:{Accept:'application/json'}}));
     if(action!=='npm_preview')for(const pwd of form.querySelectorAll('input[type=password]'))pwd.value='';
     if(!res.request_id)throw Error('Server did not provide a request reference. No change is confirmed.');
     active.set(action,{id:res.request_id,button,start:Date.now()});
     inform(action,'Queued','Waiting for the device to finish.');
     poll().catch(()=>{});
   }catch(error){inform(action,'Rejected',error.message);button.disabled=false;}
 });
}
// Non-secret form fields can persist between an interrupted request and a retry.
const npmForm=root.querySelector('form input[name="action"][value="npm"]')?.form;
if(npmForm){
 const keys=['hostname','zone','email'];
 try{const data=JSON.parse(sessionStorage.getItem('moon-cheese-network-fields')||'{}');
   for(const key of keys)if(npmForm.elements[key]&&data[key]&&!npmForm.elements[key].value)npmForm.elements[key].value=data[key];
 }catch(_){}
 npmForm.addEventListener('submit',()=>{
   const data={};for(const key of keys)data[key]=String(npmForm.elements[key]?.value||'');
   try{sessionStorage.setItem('moon-cheese-network-fields',JSON.stringify(data));}catch(_){}
 });
}
const deviceSelect=document.getElementById('network-ip-interface');
const interfaceList=document.getElementById('network-address-list');
let latestInterfaces=[];
function updatePhysicalInterfaces(items){
 if(!Array.isArray(items))return;
 latestInterfaces=items.filter(n=>['ethernet','wifi'].includes(n.kind));
 if(interfaceList){
   interfaceList.replaceChildren();
   let found=false;
   for(const item of latestInterfaces){
     if(!item.connection||!item.address)continue;
     found=true;const line=document.createElement('p');
     const title=document.createElement('strong');title.textContent=`${item.kind==='wifi'?'Wi-Fi':'Ethernet'} (${item.device}): `;
     const a=document.createElement('a');a.href=`http://${item.address}:8000/`;a.target='_blank';a.rel='noopener';a.textContent=item.address;
     line.append(title,a,document.createTextNode(` — ${item.address_mode||'Unknown'}`));interfaceList.append(line);
   }
   if(!found){const message=document.createElement('p');message.className='note';message.textContent='No active physical IPv4 addresses detected.';interfaceList.append(message);}
 }
 refreshSelectedInterface();
}
function refreshSelectedInterface(){
 if(!deviceSelect)return;
 const option=deviceSelect.selectedOptions[0];
 const current=latestInterfaces.find(n=>n.device===deviceSelect.value) ||
   {device:deviceSelect.value,kind:option?.dataset.kind,address:option?.dataset.ip,address_mode:option?.dataset.method,connection:option?.dataset.connection};
 const alternates=document.getElementById('network-ip-alternates');
 if(alternates){
   const all=latestInterfaces.length?latestInterfaces:Array.from(deviceSelect.options).map(opt=>({device:opt.value,kind:opt.dataset.kind,address:opt.dataset.ip,connection:opt.dataset.connection}));
   alternates.replaceChildren();
   alternates.append(document.createTextNode('Alternative local connection if this interface changes: '));
   let count=0;
   for(const other of all){
     if(other.device===current.device||!other.connection||!other.address)continue;
     if(count++)alternates.append(document.createTextNode(' · '));
     const a=document.createElement('a');a.href=`http://${other.address}:8000/system/administration?network=ip_change#network-admin`;
     a.textContent=`${other.kind==='wifi'?'Wi-Fi':'Ethernet'} (${other.device}): ${other.address}`;
     a.target='_blank';a.rel='noopener';alternates.append(a);
   }
   if(!count)alternates.append(document.createTextNode('No other connected physical interface detected. Use a local console or the newly assigned address shown by your router.'));
 }
 for(const [id,value] of Object.entries({
   'network-selected-kind':`${current.kind==='wifi'?'Wi-Fi':'Ethernet'} (${current.device||'unknown'})`,
   'network-selected-ip':current.address||'No IPv4 assigned',
   'network-selected-mode':current.address_mode||'Unknown',
   'network-selected-connection':current.connection||'Not connected'})){
   const node=document.getElementById(id);if(node)node.textContent=value;
 }
}
if(deviceSelect){deviceSelect.addEventListener('change',refreshSelectedInterface);refreshSelectedInterface();}
const modeSelect=document.getElementById('network-ip-mode');
const staticFields=document.getElementById('network-static-fields');
const progress=document.getElementById('network-ip-progress');
const expected=document.getElementById('network-ip-expected');
const expectedLink=document.getElementById('network-ip-expected-link');
const countdown=document.getElementById('network-ip-countdown');
const link=document.getElementById('network-ip-new-link');
const ipMessage=document.getElementById('network-ip-message');
const ipSubmit=ipForm?.querySelector('button[type="submit"]');
if(modeSelect&&staticFields){modeSelect.addEventListener('change',()=>{staticFields.hidden=modeSelect.value!=='static';});}
let ipPolling=null,ipClock=null,ipId='',ipDeadline=0,ipClockOffset=0,ipEverPending=false,ipPollErrors=0;
function showExpectedAddress(){
 if(!expected||!expectedLink||!ipForm)return;
 const candidate=ipForm.querySelector('input[name="ip"]')?.value.trim()||'';
 if(modeSelect?.value==='static' && /^(?:\d{1,3}\.){3}\d{1,3}$/.test(candidate)){
   const target=`http://${candidate}:8000/system/network/confirm`;
   expectedLink.href=target;expectedLink.textContent=target;expected.hidden=false;
 }else{expected.hidden=true;}
}
if(ipForm){ipForm.addEventListener('input',showExpectedAddress);ipForm.addEventListener('change',showExpectedAddress);showExpectedAddress();}
function beginIPPolling(){
 if(ipPolling)clearInterval(ipPolling);
 ipPolling=setInterval(()=>checkIp().then(()=>{ipPollErrors=0;}).catch(()=>{
   if(++ipPollErrors===2 && ipMessage)ipMessage.textContent='Cannot refresh status from this address. If you changed this connection, open the expected new IP link shown above, or use the router/device console. The independent rollback deadline still applies.';
 }),950);
}

function stopIP(text,result){
 if(ipPolling)clearInterval(ipPolling);ipPolling=null;
 if(ipClock)clearInterval(ipClock);ipClock=null;
 if(ipSubmit)ipSubmit.disabled=false;
 if(ipMessage)ipMessage.textContent=text;
 if(result)inform('ip_change',result,text);
 // Never close the administrator's browser tab or another manually opened tab.
}
function updateClock(){
 if(!ipDeadline)return;
 const remaining=Math.max(0,Math.ceil(ipDeadline-(Date.now()/1000+ipClockOffset)));
 countdown.textContent=`${String(Math.floor(remaining/60)).padStart(2,'0')}:${String(remaining%60).padStart(2,'0')}`;
 if(remaining===0){clearInterval(ipClock);ipClock=null;ipMessage.textContent='Confirmation deadline reached. Waiting for the independent recovery service to verify restoration.';}
}
async function checkIp(){
 const data=await fetchStatus();updatePhysicalInterfaces(data.interfaces);
 if(Number.isFinite(Number(data.server_time)))ipClockOffset=Number(data.server_time)-Date.now()/1000;
 const status=data.network||{};
 const pending=data.pending||{};
 // The recovery worker can finish independently and a later request may change
 // the last status. A missing pending record must never leave this page locked.
 if(ipEverPending && !pending.expires){
   if(status.state==='restored'||status.state==='confirmed'){
     countdown.textContent=status.state==='restored'?'Restored':'Confirmed';
     stopIP(status.message||'Network operation finished.',status.state==='restored'?'Restored':'Confirmed');
   }else{
     countdown.textContent='Finished';
     stopIP('There is no longer a pending IP change. Check the current interface address before retrying.','Finished');
   }
   return;
 }
 if(status.request_id&&status.request_id!==ipId&&!pending.expires)return;
 if(!pending.expires && status.state==='recovery_error'){countdown.textContent='Attention needed';stopIP(status.message||'Recovery could not be verified.','Error');return;}
 if(!pending.expires && status.state==='error'){countdown.textContent='Not started';stopIP(status.message||'The request was rejected.','Error');return;}
 if(!pending.expires && status.state==='restored'){countdown.textContent='Restored';stopIP('The original network settings were restored.','Restored');return;}
 if(!pending.expires && status.state==='confirmed'){countdown.textContent='Confirmed';stopIP('The new network configuration was confirmed.','Confirmed');return;}
 if(pending.expires&&pending.new_ip){
   ipEverPending=true;
   if(Number(pending.expires)!==ipDeadline){ipDeadline=Number(pending.expires);if(ipClock)clearInterval(ipClock);updateClock();ipClock=setInterval(updateClock,300);}
   const address=`http://${pending.new_ip}:8000/system/network/confirm`;
   link.href=address;link.hidden=false;link.textContent='Open the new IP confirmation page: '+address;
   ipMessage.textContent='Open the link above in a new tab. If your browser blocks HTTPS-to-local HTTP navigation, copy the full address and paste it into a new tab. Sign in as administrator and confirm before the deadline.';
   inform('ip_change','Awaiting confirmation',`Open ${pending.new_ip}:8000 in the second tab and confirm. The original configuration returns if not confirmed.`);
 }else if(status.state==='working'){
   countdown.textContent='Verifying';ipMessage.textContent='NetworkManager is attempting the change. No countdown will start unless the address is verified.';
 }else if(ipDeadline===0){countdown.textContent='Pending';}
}
if(ipForm){
 ipForm.addEventListener('submit',async event=>{
   event.preventDefault();if(!ipForm.reportValidity()||ipSubmit.disabled)return;
   const data=new FormData(ipForm);
   // Do not open about:blank: popup blockers and HTTPS→HTTP restrictions close it.
   // The original page always provides a permanent user-clicked link instead.
   progress.hidden=false;link.hidden=true;ipSubmit.disabled=true;
   countdown.textContent='Not started';ipDeadline=0;ipEverPending=false;ipId='';ipMessage.textContent='Submitting the network change. No change has been confirmed.';
   inform('ip_change','Submitting','Awaiting acceptance by the server.');
   try{
     const response=await fetch(submissionURL(ipForm),{method:'POST',body:data,credentials:'same-origin',headers:{Accept:'application/json'}});
     const result=await jsonResponse(response);
     ipId=result.request_id||'';if(!ipId)throw Error('No network request reference was returned.');
     for(const input of ipForm.querySelectorAll('input[type=password]'))input.value='';
     inform('ip_change','Queued','Waiting for NetworkManager and address verification.');
     beginIPPolling();
     checkIp().catch(()=>{});
   }catch(error){countdown.textContent='Not started';stopIP(error.message,'Rejected');}
 });
}
// Reopening System Administration while a change is pending must restore the
// live countdown and the local link; don't require the original submitting tab.
if(progress && !progress.hidden){
  beginIPPolling();
  checkIp().catch(()=>{});
}
// Keep status current while the administrator views this network section.
setInterval(()=>{if(root.open)poll().catch(()=>{});},1800);
window.addEventListener('focus',()=>{if(root.open)poll().catch(()=>{});if(ipPolling)checkIp().catch(()=>{});});
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&ipPolling)checkIp().catch(()=>{});});
})();
