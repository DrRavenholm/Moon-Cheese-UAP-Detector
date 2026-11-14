/* Moon Cheese visitor themes: per-browser only, never sent to server. */
(()=>{'use strict';
 const allowed=new Set(['blue','red','green','yellow']);
 const key='moon-cheese-colour-theme';
 function saved(){try{const value=localStorage.getItem(key);return allowed.has(value)?value:'blue';}catch(_){return 'blue';}}
 function apply(value){document.documentElement.dataset.moonTheme=value;
   const meta=document.querySelector('meta[name="theme-color"]');
   if(meta)meta.content=({blue:'#0c1929',red:'#28111c',green:'#102d23',yellow:'#2e291a'})[value];}
 const choice=document.getElementById('moon-theme-selector');
 const start=saved();apply(start);if(!choice)return;choice.value=start;
 choice.addEventListener('change',()=>{const value=choice.value;if(!allowed.has(value))return;
   apply(value);try{localStorage.setItem(key,value);}catch(_){/* Storage disabled: selection lasts until next page. */}});
})();
