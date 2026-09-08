// GerrOS site: menu, strip arrows, catalogue filters, and hash routing for the
// single-file preview (dist/gerros.html), where every page lives in one document.
(function () {
  const routes = document.querySelectorAll('main.route');

  function wire(root) {
    // mobile menu
    root.querySelectorAll('.nav-toggle').forEach(btn => btn.addEventListener('click', () => btn.closest('.nav').classList.toggle('open')));
    // horizontal strips
    root.querySelectorAll('.strip-outer').forEach(outer => {
      const strip = outer.querySelector('.strip');
      outer.querySelectorAll('.strip-arrow').forEach(btn => btn.addEventListener('click', () => {
        strip.scrollBy({ left: (btn.classList.contains('next') ? 1 : -1) * strip.clientWidth * 0.7, behavior: 'smooth' });
      }));
    });
    // catalogue filters
    root.querySelectorAll('.filters').forEach(filters => {
      const grid = filters.parentElement.querySelector('.grid');
      filters.addEventListener('click', e => {
        const c = e.target.closest('.chip');
        if (!c) return;
        filters.querySelectorAll('.chip').forEach(x => x.setAttribute('aria-pressed', x === c ? 'true' : 'false'));
        const cat = c.dataset.cat;
        grid.querySelectorAll('.app').forEach(a => { a.hidden = !(cat === 'all' || a.dataset.cat === cat); });
        grid.classList.add('is-filtering');
        setTimeout(() => grid.classList.remove('is-filtering'), 400);
      });
    });
  }

  wire(document);
  if (!routes.length) return;

  // ---- single-file preview: show the section whose data-route matches the hash ----
  function show() {
    const path = location.hash.replace(/^#/, '') || '/';
    let found = false;
    routes.forEach(m => { m.hidden = m.dataset.route !== path; if (!m.hidden) found = true; });
    if (!found) routes.forEach(m => { m.hidden = m.dataset.route !== '/'; });
    window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', show);
  show();
})();
