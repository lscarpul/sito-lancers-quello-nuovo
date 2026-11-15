/* Lancers Baseball Club – interazioni del sito (nessuna libreria esterna) */
(function () {
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---- header: menu mobile, sottomenu, ombra allo scroll ---- */
  var head = $('.site-h'), nav = $('#nav'), burger = $('.burger'), toTop = $('.to-top');
  function setH() { document.documentElement.style.setProperty('--hh', head.offsetHeight + 'px'); }
  function closeNav() {
    nav.classList.remove('open'); document.body.classList.remove('nav-open');
    burger.setAttribute('aria-expanded', 'false'); burger.setAttribute('aria-label', 'Apri il menu');
  }
  burger.addEventListener('click', function () {
    setH();
    var open = nav.classList.toggle('open');
    document.body.classList.toggle('nav-open', open);
    burger.setAttribute('aria-expanded', open); burger.setAttribute('aria-label', open ? 'Chiudi il menu' : 'Apri il menu');
  });
  $$('.sub-t').forEach(function (b) {
    b.addEventListener('click', function () {
      var li = b.parentNode, open = li.classList.toggle('open');
      b.setAttribute('aria-expanded', open);
    });
  });
  window.addEventListener('resize', function () { if (window.innerWidth > 1180) closeNav(); setH(); });
  function onScroll() {
    var y = window.scrollY;
    head.classList.toggle('stuck', y > 40);
    toTop.classList.toggle('show', y > 700);
  }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll(); setH();
  toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  /* ---- comparsa degli elementi allo scroll + contatori ---- */
  function count(el) {
    var end = +el.dataset.count, t0 = null;
    function step(t) {
      if (!t0) t0 = t;
      var p = Math.min((t - t0) / 1200, 1);
      el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.classList.add('in');
        var c = $('[data-count]', en.target); if (c) count(c);
        io.unobserve(en.target);
      });
    }, { rootMargin: '0px 0px -40px 0px' });
    $$('.reveal').forEach(function (el) { io.observe(el); });
  } else { $$('.reveal').forEach(function (el) { el.classList.add('in'); }); }

  /* ---- lightbox per foto e gallerie ---- */
  var lb = $('.lb'), lbImg = $('.lb img'), lbCap = $('.lb figcaption'), group = [], idx = 0;
  function show(i) {
    idx = (i + group.length) % group.length;
    lbImg.src = group[idx].href; lbCap.textContent = group[idx].dataset.lb || '';
    var many = group.length > 1; $('.lb-p').hidden = !many; $('.lb-n').hidden = !many;
  }
  function closeLb() { lb.hidden = true; lbImg.src = ''; document.body.style.overflow = ''; }
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('a[data-lb]');
    if (!a) return;
    ev.preventDefault();
    var box = a.closest('.gallery-x, .slider, .content') || document;
    group = $$('a[data-lb]', box);
    lb.hidden = false; document.body.style.overflow = 'hidden';
    show(group.indexOf(a));
  });
  $('.lb-x').addEventListener('click', closeLb);
  $('.lb-p').addEventListener('click', function () { show(idx - 1); });
  $('.lb-n').addEventListener('click', function () { show(idx + 1); });
  lb.addEventListener('click', function (ev) { if (ev.target === lb || ev.target.tagName === 'FIGURE') closeLb(); });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') { if (!lb.hidden) closeLb(); else closeNav(); }
    if (lb.hidden) return;
    if (ev.key === 'ArrowLeft') show(idx - 1);
    if (ev.key === 'ArrowRight') show(idx + 1);
  });
  var tx = null;
  lb.addEventListener('touchstart', function (ev) { tx = ev.touches[0].clientX; }, { passive: true });
  lb.addEventListener('touchend', function (ev) {
    if (tx === null) return;
    var dx = ev.changedTouches[0].clientX - tx; tx = null;
    if (Math.abs(dx) > 50) show(idx + (dx < 0 ? 1 : -1));
  });

  /* ---- slider di foto ---- */
  $$('.slider').forEach(function (sl) {
    var track = $('.slides', sl), slides = $$('.slide', sl), dots = $('.dots', sl), cur = 0;
    if (slides.length < 2) return;
    function go(i) {
      cur = (i + slides.length) % slides.length;
      track.scrollTo({ left: track.clientWidth * cur, behavior: 'smooth' });
    }
    slides.forEach(function (_, i) {
      var b = document.createElement('button');
      b.type = 'button'; b.setAttribute('aria-label', 'Foto ' + (i + 1));
      b.addEventListener('click', function () { go(i); });
      dots.appendChild(b);
    });
    function mark() {
      cur = Math.round(track.scrollLeft / track.clientWidth);
      $$('button', dots).forEach(function (b, i) { b.classList.toggle('on', i === cur); });
    }
    track.addEventListener('scroll', mark, { passive: true }); mark();
    $('.prev', sl).addEventListener('click', function () { go(cur - 1); });
    $('.next', sl).addEventListener('click', function () { go(cur + 1); });
  });

  /* ---- notizie: filtro per categoria, ricerca, carica altre ---- */
  var news = $('#news');
  if (news) {
    var cards = $$('.post', news), q = $('#news-q'), more = $('#news-more'), empty = $('.empty'), cat = '', limit = 12;
    var m = /[?&]cat=([^&]+)/.exec(location.search);
    function apply() {
      var text = q.value.trim().toLowerCase(), shown = 0, total = 0;
      cards.forEach(function (c) {
        var ok = (!cat || (' ' + c.dataset.cat + ' ').indexOf(' ' + cat + ' ') > -1) && (!text || c.dataset.t.indexOf(text) > -1);
        if (ok) total++;
        var vis = ok && shown < limit;
        if (vis) { shown++; c.classList.add('in'); }
        c.hidden = !vis;
      });
      more.parentNode.hidden = shown >= total; empty.hidden = total > 0;
    }
    $$('.chip').forEach(function (b) {
      b.addEventListener('click', function () {
        cat = b.dataset.cat; limit = 12;
        $$('.chip').forEach(function (x) { x.classList.toggle('on', x === b); });
        apply();
      });
      if (m && b.dataset.cat === m[1]) { cat = m[1]; $$('.chip').forEach(function (x) { x.classList.toggle('on', x === b); }); }
    });
    q.addEventListener('input', function () { limit = 12; apply(); });
    more.addEventListener('click', function () { limit += 12; apply(); });
    apply();
  }

  /* ---- roster: ricerca nella tabella ---- */
  $$('[data-filter-table]').forEach(function (inp) {
    inp.addEventListener('input', function () {
      var t = inp.value.trim().toLowerCase();
      $$('.content table.has-head tr').forEach(function (tr, i) {
        if (i) tr.hidden = t && tr.textContent.toLowerCase().indexOf(t) < 0;
      });
      $$('.player').forEach(function (p) { p.hidden = t && p.textContent.toLowerCase().indexOf(t) < 0; });
    });
  });

  /* ---- modulo contatti: prepara l'email ---- */
  $$('form.contact').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var d = new FormData(f);
      var body = 'Nome: ' + d.get('nome') + '\nTelefono: ' + (d.get('telefono') || '-') + '\n\n' + d.get('messaggio');
      location.href = 'mailto:' + f.dataset.mailto + '?subject=' + encodeURIComponent('Richiesta dal sito Lancers – ' + d.get('nome')) + '&body=' + encodeURIComponent(body);
    });
  });
})();
