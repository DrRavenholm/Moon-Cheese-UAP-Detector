/* Search the help articles and sidebar without transmitting search terms. */
(() => {
  'use strict';
  const input = document.getElementById('help-search');
  if (!input) return;
  const articles = [...document.querySelectorAll('.help-doc-item')];
  const chapters = [...document.querySelectorAll('.help-doc-chapter')];
  const groups = [...document.querySelectorAll('.help-doc-group')];
  const categories = [...document.querySelectorAll('.help-doc-category')];
  const subcategories = [...document.querySelectorAll('.help-doc-subcategory')];
  const count = document.getElementById('help-search-count');
  const empty = document.getElementById('help-no-results');
  const norm = s => (s || '').toLocaleLowerCase().normalize('NFKD');
  const content = articles.map(a => norm(a.textContent));
  const update = () => {
    const terms = norm(input.value).trim().split(/\s+/).filter(Boolean);
    let shown = 0;
    articles.forEach((article, i) => {
      const visible = terms.every(term => content[i].includes(term));
      article.hidden = !visible;
      if (visible) shown++;
    });
    chapters.forEach(chapter => {
      chapter.hidden = !chapter.querySelector('.help-doc-item:not([hidden])');
    });
    groups.forEach(group => {
      let available = 0;
      group.querySelectorAll('.help-doc-link').forEach(link => {
        const target = document.getElementById(link.getAttribute('href').slice(1));
        const visible = Boolean(target && !target.hidden);
        link.hidden = !visible;
        if (visible) available++;
      });
      group.hidden = !available;
      if (terms.length && available) group.open = true;
    });
    subcategories.forEach(subcategory => {
      const available = Boolean(subcategory.querySelector('.help-doc-group:not([hidden])'));
      subcategory.hidden = !available;
      if (terms.length && available) subcategory.open = true;
    });
    categories.forEach(category => {
      const available = Boolean(category.querySelector('.help-doc-group:not([hidden])'));
      category.hidden = !available;
      if (terms.length && available) category.open = true;
    });
    count.textContent = terms.length ? `${shown} matching topics` : `${articles.length} topics in ${chapters.length} sections`;
    empty.hidden = shown > 0;
  };
  input.addEventListener('input', update);
  document.getElementById('help-clear').addEventListener('click', () => { input.value = ''; update(); input.focus(); });
  update();
})();
