/* Dropdowns are overlays, not part of page flow. Allow only one open menu. */
(() => {
  'use strict';
  const menus = [...document.querySelectorAll('[data-nav-menu]')];
  for (const menu of menus) {
    menu.addEventListener('toggle', () => {
      if (menu.open) for (const other of menus) if (other !== menu) other.open = false;
    });
  }
  document.addEventListener('pointerdown', (e) => {
    for (const menu of menus) if (!menu.contains(e.target)) menu.open = false;
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') for (const menu of menus) menu.open = false;
  });
})();
