"use strict";
self.addEventListener('push',event=>{
  let notice={title:'Moon Cheese',body:'You have a new notification.',url:'/notifications'};
  if(event.data){try{const value=event.data.json();notice={...notice,...value};}catch(_){}}
  event.waitUntil(self.registration.showNotification(String(notice.title).slice(0,120),{
    body:String(notice.body).slice(0,1500),tag:'uap-detector-'+Date.now(),
    icon:'/favicon.ico',data:{url:(String(notice.url||'').startsWith('/') && !String(notice.url).startsWith('//'))?notice.url:'/notifications'}}));
});
self.addEventListener('notificationclick',event=>{
  event.notification.close();
  const url=event.notification.data?.url || '/notifications';
  event.waitUntil(clients.openWindow(url));
});
