"use strict";
(()=>{
  const button=document.querySelector('#push-register');
  if(!button)return;
  const status=document.querySelector('#push-feedback');
  button.addEventListener('click',async()=>{
    button.disabled=true;
    try{
      if(!window.isSecureContext||!('serviceWorker' in navigator)||!('PushManager' in window))
        throw Error('This browser needs HTTPS and Web Push support. On iPhone, add the site to your Home Screen.');
      const keyRes=await fetch('/notifications/push/key',{credentials:'same-origin',cache:'no-store'});
      if(!keyRes.ok)throw Error('Could not obtain the detector push key. Ask the administrator to check configuration.');
      const {publicKey}=await keyRes.json();
      const bytes=Uint8Array.from(atob(publicKey.replace(/-/g,'+').replace(/_/g,'/')+'='.repeat((4-publicKey.length%4)%4)),c=>c.charCodeAt(0));
      const reg=await navigator.serviceWorker.register('/push-sw.js',{scope:'/'});
      const permission=await Notification.requestPermission();
      if(permission!=='granted')throw Error('Browser notifications were not allowed.');
      let sub=await reg.pushManager.getSubscription();
      if(!sub)sub=await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:bytes});
      const data=sub.toJSON();
      const res=await fetch('/notifications/push/subscribe',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({csrf:document.querySelector('#push-csrf').value,endpoint:data.endpoint,
          p256dh:data.keys.p256dh,auth:data.keys.auth,device:navigator.platform||'Web browser'})});
      const payload=await res.json();
      if(!res.ok)throw Error(payload.error||'Could not register this browser.');
      status.textContent='Browser subscribed. Save your delivery preferences to enable future push alerts, then refresh to see this device.';
    }catch(err){status.textContent=err.message||'Could not subscribe.';}
    finally{button.disabled=false;}
  });
})();
