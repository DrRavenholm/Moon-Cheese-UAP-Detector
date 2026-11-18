/* Moon Cheese local-only Sky Maps. Render from data fetched from this Pi;
   no CDN, online map tiles, or third-party browser requests. */
(()=>{'use strict';
 const root=document.getElementById('sky-map-root');if(!root)return;
 const $=id=>document.getElementById(id);
 const sky=$('sky-local'),earth=$('sky-earth');
 let catalogue={stars:[],lines:[],constellations:[],deep_sky:[],world:[]},positions={planets:[],satellites:[]};
 let time=new Date(root.dataset.eventTime||Date.now()),selected='',playing=false,rate=60,lastTick=Date.now(),lastFetch=0,busy=false;
 let lat=Number(root.dataset.lat),lon=Number(root.dataset.lon);
 let skyLayers=new Set(['stars','constellations','planets','satellites','deep_sky']);
 let earthLayers=new Set(['land','satellites','track','detector']);
 function out(text){$('sky-status').textContent=text;}
 function point(canvas,x,y){const w=canvas.width,h=canvas.height;return [w/2+x*w*.44,h/2+y*Math.min(w,h)*.44];}
 function drawCircle(ctx,x,y,r,col){ctx.fillStyle=col;ctx.beginPath();ctx.arc(x,y,r,0,2*Math.PI);ctx.fill();}
 function projection(ra,dec){
   // Approximate J2000 RA/Dec -> geometric alt/az. Suitable for a general chart;
   // not calibrated event identification or corrected for refraction.
   const jd=time.getTime()/86400000+2440587.5, d=jd-2451545;
   const lst=(280.46061837+360.98564736629*d+lon)%360;
   const rad=Math.PI/180, ha=((lst-ra+540)%360-180)*rad, de=dec*rad, la=lat*rad;
   const alt=Math.asin(Math.sin(la)*Math.sin(de)+Math.cos(la)*Math.cos(de)*Math.cos(ha))/rad;
   const az=(Math.atan2(Math.sin(ha),Math.cos(ha)*Math.sin(la)-Math.tan(de)*Math.cos(la))/rad+180+360)%360;
   return {alt,az};
 }
 function polar(az,alt,c){
   if(alt<0||!Number.isFinite(alt))return null;
   const r=(90-alt)/90*Math.min(c.width,c.height)*.43,theta=az*Math.PI/180;
   return [c.width/2+r*Math.sin(theta),c.height/2-r*Math.cos(theta)];
 }
 function resize(c){const b=c.getBoundingClientRect(),dpr=Math.min(2,devicePixelRatio||1);c.width=Math.max(200,Math.floor(b.width*dpr));c.height=Math.max(180,Math.floor(b.height*dpr));return c.getContext('2d');}
 function paintSky(){
   const ctx=resize(sky),w=sky.width,h=sky.height,R=Math.min(w,h)*.43;
   ctx.fillStyle='#0c1b2b';ctx.fillRect(0,0,w,h);
   ctx.strokeStyle='#355878';ctx.lineWidth=1.2;
   for(const alt of [0,30,60]){ctx.beginPath();ctx.arc(w/2,h/2,R*(90-alt)/90,0,2*Math.PI);ctx.stroke();}
   for(const az of [0,45,90,135,180,225,270,315]){
     const th=az*Math.PI/180;ctx.beginPath();ctx.moveTo(w/2,h/2);ctx.lineTo(w/2+R*Math.sin(th),h/2-R*Math.cos(th));ctx.stroke();}
   ctx.fillStyle='#a6c9e2';ctx.font=`${Math.max(12,Math.round(w/44))}px sans-serif`;
   for(const [txt,az] of [['N',0],['E',90],['S',180],['W',270]]){
     const th=az*Math.PI/180;ctx.fillText(txt,w/2+(R+12)*Math.sin(th)-5,h/2-(R+12)*Math.cos(th)+5);
   }
   if(skyLayers.has('constellations')){
     ctx.strokeStyle='#467999';ctx.lineWidth=1.1;
     for(const line of catalogue.lines||[]){let started=false,prior=null;
       for(const p of line){const q=polar(projection(p[0],p[1]).az,projection(p[0],p[1]).alt,sky);
         if(!q){started=false;continue;}
         if(prior&&Math.hypot(prior[0]-q[0],prior[1]-q[1])>R*.5){started=false;}
         if(!started){ctx.beginPath();ctx.moveTo(...q);started=true;}else ctx.lineTo(...q);
         prior=q;
       }if(started)ctx.stroke();
     }
     ctx.fillStyle='#789fcb';ctx.font=`${Math.max(10,Math.round(w/62))}px sans-serif`;
     for(const [ra,dec,name] of catalogue.constellations||[]){const p=projection(ra,dec),q=polar(p.az,p.alt,sky);if(q&&name)ctx.fillText(name,q[0]+3,q[1]);}
   }
   if(skyLayers.has('stars'))for(const [ra,dec,mag] of catalogue.stars||[]){const p=projection(ra,dec),q=polar(p.az,p.alt,sky);if(q)drawCircle(ctx,...q,Math.max(.6,Math.min(3,3.7-mag*.45))*(w/600),'#dceeff');}
   if(skyLayers.has('deep_sky'))for(const [ra,dec,name] of catalogue.deep_sky||[]){const p=projection(ra,dec),q=polar(p.az,p.alt,sky);if(q){ctx.strokeStyle='#bd8ded';ctx.beginPath();ctx.arc(...q,4,0,2*Math.PI);ctx.stroke();}}
   if(skyLayers.has('planets'))for(const body of positions.planets||[]){const q=polar(body.az,body.alt,sky);if(!q)continue;
     drawCircle(ctx,...q,body.name==='Sun'?7:5,body.name==='Moon'?'#eeeece':'#f4ba66');
     ctx.fillStyle='#fcdf9e';ctx.fillText(body.name,q[0]+7,q[1]-5);
     if(selected===body.id)ring(ctx,q);
   }
   if(skyLayers.has('satellites'))for(const sat of positions.satellites||[]){const q=polar(sat.az,sat.alt,sky);if(!q)continue;
     drawCircle(ctx,...q,selected===sat.id?5:2.2,'#58daee');if(selected===sat.id){ring(ctx,q);ctx.fillStyle='#adf6ff';ctx.fillText(sat.name,q[0]+8,q[1]-7);}
   }
   const hit=selected.match(/^(star|deep_sky):(.+)$/);
   if(hit){const list=hit[1]==='star'?catalogue.stars:catalogue.deep_sky;
     const obj=(list||[]).find(x=>x[3]===hit[2]);if(obj){const p=projection(obj[0],obj[1]),q=polar(p.az,p.alt,sky);if(q)ring(ctx,q);}}
 }
 function ring(ctx,q){ctx.strokeStyle='#f9e489';ctx.lineWidth=2.5;ctx.beginPath();ctx.arc(q[0],q[1],9,0,2*Math.PI);ctx.stroke();}
 function earthXY(lon,lat){return [(lon+180)/360*earth.width,(90-lat)/180*earth.height];}
 function paintEarth(){
   const ctx=resize(earth),w=earth.width,h=earth.height;
   ctx.fillStyle='#0e2438';ctx.fillRect(0,0,w,h);
   ctx.strokeStyle='#28445e';ctx.lineWidth=1;
   for(let lon=-150;lon<=150;lon+=30){let x=earthXY(lon,0)[0];ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
   for(let lt=-60;lt<=60;lt+=30){let y=earthXY(0,lt)[1];ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
   if(earthLayers.has('land')){
     ctx.fillStyle='#365c65';ctx.strokeStyle='#6098a0';
     for(const poly of catalogue.world||[]){ctx.beginPath();let prior=null,started=false;
       for(const [lo,la] of poly){const q=earthXY(lo,la);
         if(!started||prior&&Math.abs(prior[0]-q[0])>w*.5){ctx.moveTo(...q);started=true;}
         else ctx.lineTo(...q);prior=q;
       }ctx.fill();ctx.stroke();}
   }
   if(earthLayers.has('track')&&positions.track?.length){ctx.strokeStyle='#61dae9';ctx.lineWidth=2;ctx.beginPath();let prior=null;
     for(const p of positions.track){const q=earthXY(...p);
       if(!prior||Math.abs(q[0]-prior[0])>w*.5)ctx.moveTo(...q);else ctx.lineTo(...q);prior=q;
     }ctx.stroke();}
   if(earthLayers.has('satellites'))for(const sat of positions.satellites||[]){if(!Number.isFinite(sat.lon))continue;
     const p=earthXY(sat.lon,sat.lat);drawCircle(ctx,...p,selected===sat.id?5:2,'#68dbe6');
     if(selected===sat.id){ring(ctx,p);ctx.fillStyle='#e7fff9';ctx.fillText(sat.name,p[0]+6,p[1]-8);}}
   if(earthLayers.has('detector')){const p=earthXY(lon,lat);drawCircle(ctx,...p,5,'#f7c36b');ctx.fillStyle='#f7dbab';ctx.fillText('Detector',p[0]+7,p[1]-7);}
 }
 function paint(){paintSky();paintEarth();$('sky-time-label').textContent=time.toISOString().replace('T',' ').slice(0,19)+' UTC';}
 const parseDate=d=>{const x=new Date(d);if(Number.isNaN(x.getTime())||x.getUTCFullYear()<1849||x.getUTCFullYear()>2150)return null;return x;};
 function setTime(t){const candidate=parseDate(t);if(!candidate){out('Select a valid time between 1849 and 2150.');return;}
   time=candidate;paint();maybeLoad(true);}
 function dateText(){const v=new Date(time.getTime()-time.getTimezoneOffset()*60000);return v.toISOString().slice(0,16);}
 function setInput(){ $('sky-datetime').value=dateText();}
 async function maybeLoad(force=false){
   if(root.dataset.locationReady==='0'){out('Set the detector latitude and longitude in Detector Settings before plotting local sky positions.');return;}
   if(busy||(!force&&Date.now()-lastFetch<2400))return;
   busy=true;lastFetch=Date.now();
   try{
     const params=new URLSearchParams({at:time.toISOString(),selected,event:root.dataset.eventId||''});
     const r=await fetch('/sky-maps/positions?'+params,{cache:'no-store'});
     const data=await r.json();if(!r.ok)throw Error(data.error||'Astronomical calculation unavailable');
     positions=data;paint();out('Sky positions calculated locally. Satellite positions are predictions from cached orbital elements.');
     if(selected){const picked=positions.selected;
       $('sky-selection').textContent=picked?`${picked.name} · Altitude ${picked.alt}° · Azimuth ${picked.az}°`:selected.startsWith('star:')||selected.startsWith('deep_sky:')?'Object highlighted in the local sky map if above the horizon.':'Selection is not above the horizon or data is unavailable.';
     }
   }catch(e){out(e.message);}finally{busy=false;}
 }
 async function load(){
   try{
     const r=await fetch('/sky-maps/catalogue');const d=await r.json();if(!r.ok)throw Error(d.error);
     catalogue=d;paint();await maybeLoad(true);
   }catch(e){out('Astronomical data not ready: '+e.message+' — open Data & Updates to download the catalogues.');paint();}
 }
 for(const [prefix,target] of [['sky','skyLayers'],['earth','earthLayers']]){
   const set=prefix==='sky'?skyLayers:earthLayers;
   document.querySelectorAll(`[data-${prefix}-layer]`).forEach(node=>{
     node.checked=set.has(node.dataset[`${prefix}Layer`]);
     node.addEventListener('change',()=>{if(node.checked)set.add(node.dataset[`${prefix}Layer`]);else set.delete(node.dataset[`${prefix}Layer`]);paint();});
   });
 }
 const search=$('sky-search');let searchTimer;
 search.addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(async()=>{
   $('sky-results').replaceChildren();const query=search.value.trim();if(query.length<2)return;
   try{const r=await fetch('/sky-maps/search?q='+encodeURIComponent(query));const list=await r.json();
     if(!r.ok)return;
     for(const item of list){const b=document.createElement('button');b.type='button';b.textContent=`${item.name} · ${item.kind}`;
       b.addEventListener('click',()=>{selected=item.id;search.value=item.name;$('sky-results').replaceChildren();maybeLoad(true);paint();});
       $('sky-results').appendChild(b);}
   }catch(e){out('Search unavailable: '+e.message);}
 },270);});
 $('sky-now').addEventListener('click',()=>{playing=false;$('sky-play').textContent='▶ Play';setTime(new Date());setInput();$('sky-offset').value=0;});
 $('sky-datetime').addEventListener('change',()=>setTime($('sky-datetime').value));
 $('sky-offset').addEventListener('input',()=>{const delta=Number($('sky-offset').value);setTime(Date.now()+delta*3600000);setInput();});
 $('sky-speed').addEventListener('change',()=>{rate=Number($('sky-speed').value);});
 $('sky-play').addEventListener('click',()=>{playing=!playing;lastTick=Date.now();$('sky-play').textContent=playing?'Ⅱ Pause':'▶ Play';});
 setInterval(()=>{if(!playing)return;const now=Date.now(),delta=(now-lastTick)*rate;lastTick=now;time=new Date(time.getTime()+delta);if(time.getUTCFullYear()>2150){playing=false;return;}setInput();paint();maybeLoad();},1000);
 window.addEventListener('resize',paint);setInput();paint();load();
})();
