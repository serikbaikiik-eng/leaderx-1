(function () {
  var b = document.querySelector('.burger'), m = document.getElementById('menu');
  if (!b || !m) return;
  function set(open) {
    m.classList.toggle('open', open);
    b.setAttribute('aria-expanded', String(open));
  }
  b.addEventListener('click', function () { set(!m.classList.contains('open')); });
  m.addEventListener('click', function (e) { if (e.target.closest('a')) set(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
  window.addEventListener('resize', function () { if (window.innerWidth > 820) set(false); });
})();
