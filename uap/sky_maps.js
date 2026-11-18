/* Moon Cheese offline Sky Maps. Browser draws only data served by this Pi.
   No external tiles, CDN, or browser requests to astronomical providers. */
(()=>{'use strict';
 const root=document.getElementById('sky-map-root');if(!root)return;
 const $=id=>document.getElementById(id),sky=$('sky-local'),earth=$('sky-earth');
 const eventTime=root.dataset.eventTime;
 let live=!eventTime, time=new Date(eventTime||Date.now()),selected='',playing=false,rate=60;
 let lastTick=Date.now(),lastFetch=0,busy=false,dataVersion=0,starLimit=4.5;
 let lat=Number(root.dataset.lat),lon=Number(root.dataset.lon);
 let catalogue={stars:[],lines:[],constellations:[],deep_sky:[],world:[]};
 let positions={planets:[],satellites:[],track:[],solar:null};
 const skyLayers=new Set(['stars','constellation_lines','planets','satellites']);
 const earthLayers=new Set(['land','satellites','track','detector','daynight','twilight']);
 let twilightCache=null;
 const deg=Math.PI/180;
 function out(message){$('sky-status').textContent=message;}
 function drawCircle(ctx,x,y,r,color){ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();}
 function projection(ra,dec){
   // Geometric J2000 RA/Dec projection. Atmospheric refraction and exact
   // calibrated camera overlays are intentionally not claimed here.
   const jd=time.getTime()/86400000+2440587.5,d=jd-2451545;
   const lst=(280.46061837+360.98564736629*d+lon)%360;
   const ha=((lst-ra+540)%360-180)*deg,de=dec*deg,la=lat*deg;
   const alt=Math.asin(Math.sin(la)*Math.sin(de)+Math.cos(la)*Math.cos(de)*Math.cos(ha))/deg;
   const az=(Math.atan2(Math.sin(ha),Math.cos(ha)*Math.sin(la)-Math.tan(de)*Math.cos(la))/deg+540)%360;
   return {alt,az};
 }
 function polar(az,alt,canvas){
   if(alt<0||!Number.isFinite(alt)||!Number.isFinite(az))return null;
   const r=(90-alt)/90*Math.min(canvas.width,canvas.height)*.43,theta=az*deg;
   return [canvas.width/2+r*Math.sin(theta),canvas.height/2-r*Math.cos(theta)];
 }
 function resize(canvas){
   const bounds=canvas.getBoundingClientRect(),scale=Math.min(2,window.devicePixelRatio||1);
   const width=Math.max(200,Math.floor(bounds.width*scale)),height=Math.max(180,Math.floor(bounds.height*scale));
   if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}
   return canvas.getContext('2d');
 }
 function ring(ctx,q){ctx.strokeStyle='#ffdd75';ctx.lineWidth=2.5;ctx.beginPath();ctx.arc(q[0],q[1],10,0,Math.PI*2);ctx.stroke();}
 function paintSky(){
   const ctx=resize(sky),w=sky.width,h=sky.height,R=Math.min(w,h)*.43;
   ctx.fillStyle='#0c1b2b';ctx.fillRect(0,0,w,h);
   ctx.strokeStyle='#284a61';ctx.lineWidth=1;
   for(const alt of [0,30,60]){ctx.beginPath();ctx.arc(w/2,h/2,R*(90-alt)/90,0,Math.PI*2);ctx.stroke();}
   for(const az of [0,45,90,135,180,225,270,315]){
     const th=az*deg;ctx.beginPath();ctx.moveTo(w/2,h/2);ctx.lineTo(w/2+R*Math.sin(th),h/2-R*Math.cos(th));ctx.stroke();
   }
   ctx.fillStyle='#b9d7ef';ctx.font=`${Math.max(12,Math.round(w/44))}px sans-serif`;
   for(const [label,az] of [['N',0],['E',90],['S',180],['W',270]]){
     const a=az*deg;ctx.fillText(label,w/2+(R+12)*Math.sin(a)-5,h/2-(R+12)*Math.cos(a)+5);
   }
   if(skyLayers.has('constellation_lines')){
     ctx.strokeStyle='rgba(90,154,191,.48)';ctx.lineWidth=1;
     for(const line of catalogue.lines||[]){let started=false,prior=null;
       for(const p of line){if(!Array.isArray(p)||p.length<2)continue;
         const pos=projection(p[0],p[1]),q=polar(pos.az,pos.alt,sky);
         if(!q){if(started){ctx.stroke();started=false;}prior=null;continue;}
         if(prior&&Math.hypot(prior[0]-q[0],prior[1]-q[1])>R*.5){ctx.stroke();started=false;}
         if(!started){ctx.beginPath();ctx.moveTo(...q);started=true;}else ctx.lineTo(...q);
         prior=q;
       }if(started)ctx.stroke();
     }
   }
   if(skyLayers.has('stars')){
     for(const [ra,dec,mag] of catalogue.stars||[]){
       if(mag>starLimit)continue;
       const pos=projection(ra,dec),q=polar(pos.az,pos.alt,sky);
       if(q){const radius=Math.max(.65,Math.min(2.7,2.8-mag*.31))*(w/650);
         drawCircle(ctx,q[0],q[1],Math.max(.65,radius),'#e2f1ff');}
     }
   }
   if(skyLayers.has('constellation_names')){
     // Label placement is collision-aware, not dozens of overlapping strings.
     const used=[];ctx.fillStyle='#8fb4d5';ctx.font=`${Math.max(11,Math.round(w/63))}px sans-serif`;
     for(const [ra,dec,name] of catalogue.constellations||[]){
       if(!name)continue;const pos=projection(ra,dec),q=polar(pos.az,pos.alt,sky);
       if(!q)continue;
       const width=ctx.measureText(name).width,x=q[0]-width/2,y=q[1];
       if(x<0||x+width>w||y<13||y>h-4||used.some(b=>x<b[2]&&x+width>b[0]&&y-12<b[3]&&y>b[1]))continue;
       used.push([x-5,y-15,x+width+5,y+4]);ctx.fillText(name,x,y);
     }
   }
   if(skyLayers.has('deep_sky')){
     for(const [ra,dec] of catalogue.deep_sky||[]){const pos=projection(ra,dec),q=polar(pos.az,pos.alt,sky);
       if(q){ctx.strokeStyle='#aa8bd4';ctx.lineWidth=1;ctx.beginPath();ctx.arc(q[0],q[1],3.4,0,Math.PI*2);ctx.stroke();}}
   }
   if(skyLayers.has('planets')){
     ctx.font=`${Math.max(11,Math.round(w/62))}px sans-serif`;
     for(const body of positions.planets||[]){const q=polar(body.az,body.alt,sky);if(!q)continue;
       drawCircle(ctx,...q,body.name==='Sun'?6.5:4.5,body.name==='Moon'?'#eeeecf':'#efb45c');
       ctx.fillStyle='#fbd79a';ctx.fillText(body.name,q[0]+7,q[1]-5);
       if(selected===body.id)ring(ctx,q);
     }
   }
   if(skyLayers.has('satellites')){
     for(const sat of positions.satellites||[]){const q=polar(sat.az,sat.alt,sky);if(!q)continue;
       drawCircle(ctx,...q,selected===sat.id?5:2,'#58daee');
       if(selected===sat.id){ring(ctx,q);ctx.fillStyle='#b4f4ff';ctx.fillText(sat.name,q[0]+9,q[1]-7);}
     }
   }
   const hit=selected.match(/^(star|deep_sky):(.+)$/);
   if(hit){const entries=hit[1]==='star'?catalogue.stars:catalogue.deep_sky;
     const obj=(entries||[]).find(x=>x[hit[1]==='star'?3:2]===hit[2]);
     if(obj){const pos=projection(obj[0],obj[1]),q=polar(pos.az,pos.alt,sky);
       if(q){ring(ctx,q);ctx.fillStyle='#ffdf87';ctx.font='13px sans-serif';ctx.fillText(hit[2],q[0]+12,q[1]-10);}}
   }
 }
 function earthXY(longitude,latitude){return [(longitude+180)/360*earth.width,(90-latitude)/180*earth.height];}
 function shadeEarth(ctx,w,h){
   if(!earthLayers.has('daynight')||!positions.solar)return;
   const solar=positions.solar,twilight=earthLayers.has('twilight');
   const stamp=[solar.latitude,solar.longitude,twilight].join(':');
   if(!twilightCache||twilightCache.stamp!==stamp){
     const c=document.createElement('canvas');c.width=360;c.height=180;
     const cctx=c.getContext('2d'),img=cctx.createImageData(c.width,c.height);
     const sunLat=solar.latitude*deg,sunLon=solar.longitude*deg;
     const sLat=Math.sin(sunLat),cLat=Math.cos(sunLat);
     const colors=twilight?[[188,219,251,25],[85,115,157,63],[45,67,118,122],[20,39,87,177],[3,9,41,207]]:[[188,219,251,25],[3,9,41,207]];
     for(let y=0;y<c.height;y++){
       const la=(90-(y+.5)*180/c.height)*deg,s=Math.sin(la)*sLat,cosTerm=Math.cos(la)*cLat;
       for(let x=0;x<c.width;x++){
         const lo=(-180+(x+.5)*360/c.width)*deg;
         const alt=Math.asin(Math.max(-1,Math.min(1,s+cosTerm*Math.cos(lo-sunLon))))/deg;
         const category=twilight?(alt>=-.833?0:alt>=-6?1:alt>=-12?2:alt>=-18?3:4):(alt>=-.833?0:1);
         const index=(y*c.width+x)*4,color=colors[category];
         img.data[index]=color[0];img.data[index+1]=color[1];img.data[index+2]=color[2];img.data[index+3]=color[3];
       }
     }
     cctx.putImageData(img,0,0);twilightCache={stamp,canvas:c};
   }
   ctx.drawImage(twilightCache.canvas,0,0,w,h);
 }
 function paintEarth(){
   const ctx=resize(earth),w=earth.width,h=earth.height;
   ctx.fillStyle='#0e2438';ctx.fillRect(0,0,w,h);
   ctx.strokeStyle='#28445e';ctx.lineWidth=1;
   for(let l=-150;l<=150;l+=30){const x=earthXY(l,0)[0];ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
   for(let l=-60;l<=60;l+=30){const y=earthXY(0,l)[1];ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
   if(earthLayers.has('land')){
     ctx.fillStyle='#365c65';ctx.strokeStyle='#6098a0';
     for(const poly of catalogue.world||[]){ctx.beginPath();let prior=null,started=false;
       for(const [lo,la] of poly){const q=earthXY(lo,la);
         if(!started||prior&&Math.abs(prior[0]-q[0])>w*.5){if(started){ctx.fill();ctx.stroke();ctx.beginPath();}ctx.moveTo(...q);started=true;}
         else ctx.lineTo(...q);prior=q;
       }if(started){ctx.fill();ctx.stroke();}
     }
   }
   shadeEarth(ctx,w,h);
   if(earthLayers.has('track')&&positions.track?.length){
     ctx.strokeStyle='#6ee8ee';ctx.lineWidth=2.4;ctx.beginPath();let prev=null;
     for(const coordinates of positions.track){const q=earthXY(...coordinates);
       if(!prev||Math.abs(q[0]-prev[0])>w*.5)ctx.moveTo(...q);else ctx.lineTo(...q);prev=q;
     }ctx.stroke();
   }
   if(earthLayers.has('satellites'))for(const sat of positions.satellites||[]){
     if(!Number.isFinite(sat.lon)||!Number.isFinite(sat.lat))continue;
     const q=earthXY(sat.lon,sat.lat);drawCircle(ctx,...q,selected===sat.id?5:2,'#68dbe6');
     if(selected===sat.id){ring(ctx,q);ctx.fillStyle='#e7fff9';ctx.font='13px sans-serif';ctx.fillText(sat.name,q[0]+9,q[1]-8);}
   }
   if(earthLayers.has('detector')){const q=earthXY(lon,lat);drawCircle(ctx,...q,5,'#f7c36b');
     ctx.fillStyle='#f7dbab';ctx.font='13px sans-serif';ctx.fillText('Detector',q[0]+7,q[1]-8);}
 }
 function updateTimeLabel(){
   $('sky-time-mode').textContent=live?'● LIVE — Now':playing?'▶ PLAYBACK':'◷ SELECTED TIME';
   $('sky-time-label').textContent=time.toISOString().replace('T',' ').slice(0,19)+' UTC';
 }
 function paint(){paintSky();paintEarth();updateTimeLabel();}
 function parseDate(d){const x=new Date(d);return Number.isNaN(x.getTime())||x.getUTCFullYear()<1849||x.getUTCFullYear()>2150?null:x;}
 function dateText(){const v=new Date(time.getTime()-time.getTimezoneOffset()*60000);return v.toISOString().slice(0,16);}
 function setInput(){$('sky-datetime').value=dateText();}
 function setPlay(enabled){playing=enabled;lastTick=Date.now();$('sky-play').textContent=playing?'Ⅱ Pause':'▶ Play';}
 function changeTime(value,mode='selected'){
   const dt=parseDate(value);if(!dt){out('Select a valid time between 1849 and 2150.');return;}
   live=mode==='live';time=dt;dataVersion++;paint();setInput();maybeLoad(true);
 }
 function clearResults(){$('sky-results').replaceChildren();}
 async function getJson(url){
   const response=await fetch(url,{cache:'no-store'});
   const contentType=(response.headers&&response.headers.get('content-type')||'').toLowerCase();
   if(!contentType.includes('json'))throw Error(response.ok?'Server returned an unexpected response instead of JSON.':'Sky Maps server returned an error; check system logs.');
   const body=await response.json();
   if(!response.ok)throw Error(body.error||'Sky Maps server request failed.');
   return body;
 }
 async function maybeLoad(force=false){
   if(root.dataset.locationReady==='0'){out('Configure detector latitude and longitude in Detector Settings before using Sky Maps.');return;}
   const minDelay=playing?3800:12000;
   if(busy||(!force&&Date.now()-lastFetch<minDelay))return;
   const version=dataVersion,at=time.toISOString(),chosen=selected;
   busy=true;lastFetch=Date.now();
   try{
     const params=new URLSearchParams({at,selected:chosen,event:root.dataset.eventId||''});
     const data=await getJson('/sky-maps/positions?'+params);
     if(version!==dataVersion)return; // Old response may not overwrite a newly selected time/object.
     positions=data;twilightCache=null;paint();
     const sun=(data.planets||[]).find(body=>body.name==='Sun');
     $('sky-sun-status').textContent=sun&&Number.isFinite(sun.alt)
       ?`Sun: ${Math.abs(sun.alt).toFixed(1)}° ${sun.alt>=0?'above':'below'} the detector horizon at this time.`
       :'Sun position unavailable. Download the planetary ephemeris to check day/night sky visibility.';
     if(!data.solar&&earthLayers.has('daynight'))out('Sky positions loaded. Day/night shading requires the planetary ephemeris in Data & Updates.');
     else out('Sky positions calculated locally. Satellite locations are predictions from cached orbital elements.');
     const sampled=Number(data.satellite_sampled||0),total=Number(data.satellite_total||0);
     $('sky-satellite-summary').textContent=total?`Earth map: representative global sample of ${sampled} from ${total} catalogue objects. Search selects any satellite, even below your horizon.`:'Earth map: no satellite orbital catalogue installed. Download satellite data in Sky Maps → Data & Updates.';
     if(chosen){const picked=data.selected;
       if(picked){$('sky-selection').textContent=picked.alt>=0?`${picked.name} · ${picked.alt}° above the detector horizon · Azimuth ${picked.az}°`:`${picked.name} · ${Math.abs(picked.alt)}° below the detector horizon. Its global location remains highlighted on the Earth map if it is a satellite.`;}
       else $('sky-selection').textContent=chosen.startsWith('star:')||chosen.startsWith('deep_sky:')?'Object highlighted on the local sky map when above the horizon.':'This object is not available in the installed data.';
     }
   }catch(error){if(version===dataVersion)out('Sky positions unavailable: '+error.message);}
   finally{busy=false;if(version!==dataVersion)maybeLoad(true);}
 }
 async function load(){
   try{catalogue=await getJson('/sky-maps/catalogue');paint();await maybeLoad(true);}
   catch(error){out('Catalogue unavailable: '+error.message+' Open Sky Maps → Data & Updates to check the downloads.');paint();}
 }
 for(const prefix of ['sky','earth']){
   const active=prefix==='sky'?skyLayers:earthLayers;
   document.querySelectorAll(`[data-${prefix}-layer]`).forEach(node=>{
     const kind=node.dataset[`${prefix}Layer`];node.checked=active.has(kind);
     node.addEventListener('change',()=>{if(node.checked)active.add(kind);else active.delete(kind);twilightCache=null;paint();});
   });
 }
 $('sky-magnitude').addEventListener('input',()=>{
   starLimit=Number($('sky-magnitude').value);$('sky-magnitude-label').textContent=starLimit.toFixed(1);paintSky();
 });
 const search=$('sky-search');let searchTimer=0,searchSerial=0;
 search.addEventListener('input',()=>{
   clearTimeout(searchTimer);const query=search.value.trim(),version=++searchSerial;clearResults();
   if(query.length<2)return;
   searchTimer=setTimeout(async()=>{
     try{
       const list=await getJson('/sky-maps/search?q='+encodeURIComponent(query));if(version!==searchSerial)return;
       if(!Array.isArray(list))throw Error('Unexpected search format.');
       if(!list.length){const message=document.createElement('span');message.className='note';message.textContent='No matching objects in downloaded catalogues.';$('sky-results').appendChild(message);}
       for(const item of list){const button=document.createElement('button');button.type='button';button.textContent=`${item.name} · ${item.kind}`;
         button.addEventListener('click',()=>{
           selected=item.id;search.value=item.name;searchSerial++;clearResults();dataVersion++;
           $('sky-selection').textContent='Locating '+item.name+'…';paint();maybeLoad(true);
         });$('sky-results').appendChild(button);}
     }catch(error){if(version===searchSerial)out('Search unavailable: '+error.message);}
   },270);
 });
 $('sky-now').addEventListener('click',()=>{setPlay(false);$('sky-offset').value='0';changeTime(Date.now(),'live');});
 $('sky-datetime').addEventListener('change',()=>{setPlay(false);changeTime($('sky-datetime').value);});
 $('sky-offset').addEventListener('input',()=>{setPlay(false);changeTime(Date.now()+Number($('sky-offset').value)*3600000);});
 $('sky-speed').addEventListener('change',()=>{rate=Number($('sky-speed').value)||60;});
 $('sky-play').addEventListener('click',()=>{live=false;setPlay(!playing);updateTimeLabel();});
 setInterval(()=>{
   const now=Date.now();
   if(playing){const advance=(now-lastTick)*rate;lastTick=now;
     if(time.getTime()+advance>Date.UTC(2150,11,31,23,59,59)){setPlay(false);return;}
     time=new Date(time.getTime()+advance);setInput();paint();maybeLoad();
   }else if(live){time=new Date(now);setInput();paint();maybeLoad();}
 },1000);
 window.addEventListener('resize',paint);setInput();paint();load();
})();
