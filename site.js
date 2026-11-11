// GerrOS site: the mobile menu, and hash routing for the single-file preview
// (dist/gerros.html), where every page lives in one document.
(function () {
  document.querySelectorAll('.nav-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var open = btn.closest('.nav').classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.textContent = open ? 'Close' : 'Menu';
    });
  });

  var routes = document.querySelectorAll('main.route');
  if (!routes.length) return;
  function show() {
    var path = location.hash.replace(/^#/, '') || '/';
    var found = false;
    routes.forEach(function (m) { m.hidden = m.dataset.route !== path; if (!m.hidden) found = true; });
    if (!found) routes.forEach(function (m) { m.hidden = m.dataset.route !== '/'; });
    window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', show);
  show();
})();
