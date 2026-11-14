/* Browser-local visitor themes; apply saved colour without logging in. */
(()=>{'use strict';
 const allowed=new Set(['blue','red','green','yellow']);
 const key='moon-cheese-colour-theme';
 const buttons=[...document.querySelectorAll('[data-theme-choice]')];
 const palette={blue:'#0c1929',red:'#28111c',green:'#102d23',yellow:'#2e291a'};
 let chosen=allowed.has(document.documentElement.dataset.moonTheme)?document.documentElement.dataset.moonTheme:'blue';
 function apply(value){if(!allowed.has(value))return;
   chosen=value;document.documentElement.dataset.moonTheme=value;
   const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.content=palette[value];
   const marker=document.getElementById('moon-theme-current');if(marker)marker.title=({blue:'Blue',red:'Red',green:'Green',yellow:'Cheese Yellow'})[value];
   for(const button of buttons){const active=button.dataset.themeChoice===value;
     button.setAttribute('aria-pressed',String(active));
     const check=button.querySelector('.theme-check');if(check)check.textContent=active?'✓':'';}
 }
 apply(chosen);
 for(const button of buttons)button.addEventListener('click',()=>{
   const value=button.dataset.themeChoice;apply(value);
   try{localStorage.setItem(key,value);}catch(_){/* Local browser storage disabled. */}
   const menu=button.closest('.theme-menu');if(menu)menu.open=false;
 });
})();
