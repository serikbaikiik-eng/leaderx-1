(function () {
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return;

  // 1. Полоса прогресса прокрутки
  var bar = document.createElement('div');
  bar.className = 'lx-progress';
  document.body.appendChild(bar);
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.transform = 'scaleX(' + (max > 0 ? h.scrollTop / max : 0) + ')';
  }
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // 2. Золотые искры в hero
  var hero = document.querySelector('.hero');
  if (hero) {
    var box = document.createElement('div');
    box.className = 'lx-sparks';
    for (var i = 0; i < 16; i++) {
      var s = document.createElement('i');
      s.style.left = (Math.random() * 100) + '%';
      s.style.animationDuration = (9 + Math.random() * 10) + 's';
      s.style.animationDelay = (-Math.random() * 14) + 's';
      var sz = 2 + Math.random() * 4;
      s.style.width = s.style.height = sz + 'px';
      box.appendChild(s);
    }
    hero.insertBefore(box, hero.firstChild);

    // 3. Лёгкий 3D-наклон картинки за мышью (только на компьютере)
    var img = hero.querySelector('.lx-logo');
    if (img && matchMedia('(hover: hover) and (pointer: fine)').matches) {
      hero.addEventListener('mousemove', function (e) {
        var r = img.getBoundingClientRect();
        var x = (e.clientX - (r.left + r.width / 2)) / r.width;
        var y = (e.clientY - (r.top + r.height / 2)) / r.height;
        img.classList.add('lx-tilt');
        img.style.transform = 'perspective(900px) rotateY(' + (x * 10) + 'deg) rotateX(' + (-y * 10) + 'deg) scale(1.02)';
      });
      hero.addEventListener('mouseleave', function () {
        img.style.transform = 'perspective(900px) rotateY(0) rotateX(0) scale(1)';
      });
    }
  }
})();
