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
      $$('.player, .gp tbody tr').forEach(function (p) { p.hidden = t && p.textContent.toLowerCase().indexOf(t) < 0; });
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

  /* ---- stagione: prossima partita, risultati, classifica, social (dati in data/stagione.js) ---- */
  var L = window.LANCERS;
  if (L) {
    var MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];
    var GIORNI = ['dom', 'lun', 'mar', 'mer', 'gio', 'ven', 'sab'];
    var esc = function (t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
    var nome = function (k) { return esc(L.squadre[k] || k); };
    var games = L.partite.map(function (g) {
      var o = Object.create(g), hm = /^\d\d:\d\d$/.test(g.ora) ? g.ora : '12:00';
      o.when = new Date(g.data + 'T' + hm + ':00');
      o.played = typeof g.puntiCasa === 'number';
      o.home = g.casa === 'LAN'; o.opp = o.home ? g.ospiti : g.casa;
      o.off = g.nota === 'rinviata' || g.nota === 'annullata';
      if (o.played) { o.us = o.home ? g.puntiCasa : g.puntiOspiti; o.them = o.home ? g.puntiOspiti : g.puntiCasa; o.win = o.us > o.them; }
      return o;
    });
    var played = games.filter(function (g) { return g.played; });
    var now = new Date();
    var next = games.filter(function (g) { return !g.played && !g.off && g.when.getTime() + 3 * 3600e3 > now.getTime(); })[0];
    var W = played.filter(function (g) { return g.win; }).length, Lo = played.length - W;
    var table = L.classifica.map(function (r) { var o = Object.create(r); o.pct = r.v + r.p ? r.v / (r.v + r.p) : 0; return o; })
      .sort(function (a, b) { return b.pct - a.pct || b.v - a.v; });
    var pos = table.map(function (r) { return r.squadra; }).indexOf('LAN') + 1;
    var dstr = function (d) { return GIORNI[d.getDay()] + ' ' + d.getDate() + ' ' + MESI[d.getMonth()].slice(0, 3); };
    function row(g) {
      var cls = g.played ? (g.win ? 'w' : 'l') : '', tag = g.boxscore ? 'a' : 'div';
      var href = g.boxscore ? ' href="' + L.stagione.boxscore + g.boxscore + '" target="_blank" rel="noopener" title="Apri il tabellino su FIBS"' : '';
      var score = g.played ? g.us + ' – ' + g.them + '<i>' + (g.win ? 'V' : 'S') + '</i>' : (g.off ? '<i>' + esc(g.nota) + '</i>' : esc(g.ora));
      var note = g.played && g.nota ? ' · ' + esc(g.nota) : '';
      return '<' + tag + ' class="g-row ' + cls + '"' + href + ' data-side="' + (g.home ? 'casa' : 'fuori') + '"><span class="d">' + dstr(g.when) + '<br>' + esc(g.ora) +
        '</span><span class="t">' + (g.home ? 'vs ' : '@ ') + nome(g.opp) + '<small>' + (g.home ? 'In casa' : 'In trasferta') + ' · ' + esc(g.campo) + note + '</small></span><span class="s">' + score + '</span></' + tag + '>';
    }
    $$('[data-next-game]').forEach(function (el) {
      if (next) {
        el.innerHTML = '<div class="next"><div class="kick">Prossima partita · ' + esc(L.stagione.nome) + '</div><h3>' + nome(next.casa) + ' <span class="vs">vs</span> ' + nome(next.ospiti) +
          '</h3><p>' + dstr(next.when) + ' ' + next.when.getFullYear() + ' · ore ' + esc(next.ora) + ' · ' + esc(next.campo) + '</p><div class="cd"><div><b data-cd="g">0</b><span>giorni</span></div><div><b data-cd="h">0</b><span>ore</span></div><div><b data-cd="m">0</b><span>minuti</span></div><div><b data-cd="s">0</b><span>secondi</span></div></div></div>';
        var tick = function () {
          var t = Math.max(0, next.when - new Date()) / 1000 | 0;
          var v = { g: t / 86400 | 0, h: (t % 86400) / 3600 | 0, m: (t % 3600) / 60 | 0, s: t % 60 };
          Object.keys(v).forEach(function (k) { $('[data-cd=' + k + ']', el).textContent = v[k]; });
        };
        tick(); setInterval(tick, 1000);
      } else {
        el.innerHTML = '<div class="next"><div class="kick">' + esc(L.stagione.nome) + ' · ' + esc(L.stagione.girone) + '</div><h3>Stagione conclusa</h3><p>I Lancers chiudono il campionato al ' + pos +
          '° posto. Il nuovo calendario comparirà qui appena la FIBS lo pubblica.</p><div class="rec"><div><b>' + W + '</b><span>vittorie</span></div><div><b>' + Lo + '</b><span>sconfitte</span></div><div><b>' + pos + '°</b><span>posto</span></div></div></div>';
      }
    });
    $$('[data-results]').forEach(function (el) { el.innerHTML = '<div class="res">' + played.slice(-4).reverse().map(row).join('') + '</div>'; });
    $$('[data-season-head]').forEach(function (el) {
      el.innerHTML = '<h2 class="has-text-align-center">' + esc(L.stagione.nome) + ' – ' + esc(L.stagione.girone) + '</h2><div class="season-h"><div><b>' + W + '</b><span>vittorie</span></div><div><b>' + Lo + '</b><span>sconfitte</span></div><div><b>' + pos + '°</b><span>in classifica</span></div></div>';
    });
    $$('[data-calendar]').forEach(function (el) {
      var h = '<div class="cal-f"><button class="chip on" data-side="">Tutte</button><button class="chip" data-side="casa">In casa</button><button class="chip" data-side="fuori">In trasferta</button></div><div class="cal">', m = -1;
      games.forEach(function (g) {
        if (g.when.getMonth() !== m) { m = g.when.getMonth(); h += '<h3 class="month">' + MESI[m] + '</h3>'; }
        h += row(g);
      });
      el.innerHTML = h + '</div>';
      $$('.cal-f .chip', el).forEach(function (b) {
        b.addEventListener('click', function () {
          $$('.cal-f .chip', el).forEach(function (x) { x.classList.toggle('on', x === b); });
          $$('.g-row', el).forEach(function (r) { r.hidden = b.dataset.side && r.dataset.side !== b.dataset.side; });
          $$('.month', el).forEach(function (mh) {
            var n = mh.nextElementSibling, any = false;
            while (n && !n.classList.contains('month')) { if (!n.hidden) any = true; n = n.nextElementSibling; }
            mh.hidden = !any;
          });
        });
      });
    });
    $$('[data-standings]').forEach(function (el) {
      var mini = el.dataset.standings === 'mini', top = table[0];
      var h = '<div class="stand"><div class="table-wrap"><table><thead><tr><th class="n">#</th><th>Squadra</th><th class="n">V</th><th class="n">P</th>' + (mini ? '' : '<th class="n">G</th>') + '<th class="n">%</th>' + (mini ? '' : '<th class="n">Dist.</th>') + '</tr></thead><tbody>';
      table.forEach(function (r, i) {
        var gb = ((top.v - r.v) + (r.p - top.p)) / 2;
        h += '<tr' + (r.squadra === 'LAN' ? ' class="me"' : '') + '><td class="n">' + (i + 1) + '</td><td>' + nome(r.squadra) + '</td><td class="n">' + r.v + '</td><td class="n">' + r.p + '</td>' + (mini ? '' : '<td class="n">' + (r.v + r.p) + '</td>') +
          '<td class="n">' + r.pct.toFixed(3).replace(/^0/, '') + '</td>' + (mini ? '' : '<td class="n">' + (gb ? String(gb).replace('.', ',') : '–') + '</td>') + '</tr>';
      });
      el.innerHTML = h + '</tbody></table></div></div>';
    });
    $$('[data-source]').forEach(function (el) {
      var d = L.stagione.aggiornato.split('-');
      el.innerHTML = 'Dati aggiornati al ' + (+d[2]) + ' ' + MESI[d[1] - 1] + ' ' + d[0] + '. Fonte: <a href="' + L.stagione.fonte + '" target="_blank" rel="noopener">FIBS</a> · <a href="' + L.stagione.calendarioFibs + '" target="_blank" rel="noopener">calendario ufficiale</a>';
    });
    $$('[data-tab]').forEach(function (b) {
      b.addEventListener('click', function () {
        $$('[data-tab]').forEach(function (x) { x.classList.toggle('on', x === b); });
        $$('[data-tabp]').forEach(function (p) { p.hidden = p.dataset.tabp !== b.dataset.tab; });
      });
    });
    if (location.hash === '#classifica' && $('[data-tab=cls]')) $('[data-tab=cls]').click();
    var ICO = {
      facebook: '<svg viewBox="0 0 24 24"><path d="M13.5 22v-8.2h2.8l.4-3.2h-3.2V8.5c0-.9.3-1.6 1.6-1.6h1.7V4.1C16.500 4 15.500 4 14.400 4 12 4 10.300 5.500 10.300 8.200v2.400H7.500v3.200h2.800V22z"/></svg>',
      instagram: '<svg viewBox="0 0 24 24"><path d="M12 7.300A4.700 4.700 0 1 0 12 16.700 4.700 4.700 0 0 0 12 7.300zm0 7.700a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm6-7.900a1.100 1.100 0 1 1-2.200 0 1.100 1.100 0 0 1 2.200 0zM16.500 3h-9A4.500 4.500 0 0 0 3 7.500v9A4.500 4.500 0 0 0 7.500 21h9a4.500 4.500 0 0 0 4.500-4.500v-9A4.500 4.500 0 0 0 16.500 3zm2.800 13.500a2.800 2.800 0 0 1-2.800 2.800h-9a2.800 2.800 0 0 1-2.800-2.800v-9a2.800 2.800 0 0 1 2.800-2.800h9a2.800 2.800 0 0 1 2.800 2.800z"/></svg>',
      youtube: '<svg viewBox="0 0 24 24"><path d="M21.600 7.200a2.500 2.500 0 0 0-1.800-1.800C18.200 5 12 5 12 5s-6.200 0-7.800.4A2.500 2.500 0 0 0 2.400 7.200 26 26 0 0 0 2 12a26 26 0 0 0 .4 4.800 2.500 2.500 0 0 0 1.800 1.800C5.800 19 12 19 12 19s6.200 0 7.800-.4a2.500 2.500 0 0 0 1.800-1.800A26 26 0 0 0 22 12a26 26 0 0 0-.4-4.800zM10 15V9l5.200 3z"/></svg>'
    };
    var NOMI = { facebook: 'Facebook', instagram: 'Instagram', youtube: 'YouTube' };
    $$('[data-social]').forEach(function (el) {
      var lab = el.dataset.social === 'label';
      el.innerHTML = Object.keys(ICO).filter(function (k) { return L.social && L.social[k]; }).map(function (k) {
        return '<a href="' + esc(L.social[k]) + '" target="_blank" rel="noopener" aria-label="' + NOMI[k] + '">' + ICO[k] + (lab ? '<span>' + NOMI[k] + '</span>' : '') + '</a>';
      }).join('');
    });
  }
  /* ---- statistiche dei giocatori (dati in data/statistiche.js, presi dal sito FIBS) ---- */
  var ST = window.LANCERS_STATS;
  $$('[data-player-stats]').forEach(function (el) {
    var g = ST && ST.giocatori[el.dataset.playerStats];
    var TIPI = [['batting', 'Battuta'], ['pitching', 'Lancio'], ['fielding', 'Difesa']].filter(function (t) { return g && g[t[0]] && g[t[0]].length; });
    if (!TIPI.length) return;
    var e2 = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
    var d = (ST.aggiornato || '').split('-');
    var h = '<h2>Statistiche</h2><p class="pstats-sub">Tutte le stagioni registrate sul sito della FIBS, anno per anno.</p>';
    if (TIPI.length > 1) h += '<div class="tabs" role="tablist">' + TIPI.map(function (t, i) { return '<button class="chip' + (i ? '' : ' on') + '" data-st="' + t[0] + '">' + t[1] + '</button>'; }).join('') + '</div>';
    TIPI.forEach(function (t, i) {
      var cols = ST.colonne[t[0]];
      h += '<div data-stp="' + t[0] + '"' + (i ? ' hidden' : '') + '>' + (TIPI.length > 1 ? '' : '<h3 class="pstats-one">' + t[1] + '</h3>') +
        '<div class="table-wrap"><table><thead><tr><th>Anno</th><th>Campionato</th><th>Squadra</th>' +
        cols.map(function (c) { return '<th class="n"><abbr title="' + e2(c[1]) + '">' + e2(c[0]) + '</abbr></th>'; }).join('') + '</tr></thead><tbody>';
      g[t[0]].forEach(function (r) {
        h += '<tr' + (r.tot ? ' class="tot"' : '') + '><td>' + e2(r.anno) + '</td><td>' + e2(r.camp) + '</td><td>' + e2(r.sq) + '</td>' +
          r.v.map(function (v, k) { return '<td class="n">' + e2(cols[k][0] === 'WHIP' && typeof v === 'number' ? v.toFixed(2) : v) + '</td>'; }).join('') + '</tr>';
      });
      h += '</tbody></table></div><p class="pstats-leg">' + cols.map(function (c) { return '<b>' + e2(c[0]) + '</b> ' + e2(c[1]); }).join(' · ') + '</p></div>';
    });
    h += '<p class="psrc">' + (d.length === 3 ? 'Dati aggiornati al ' + (+d[2]) + '/' + (+d[1]) + '/' + d[0] + '. ' : '') + 'Fonte: <a href="' + e2(g.fibs) + '" target="_blank" rel="noopener">scheda FIBS del giocatore</a></p>';
    el.innerHTML = h;
    $$('[data-st]', el).forEach(function (b) {
      b.addEventListener('click', function () {
        $$('[data-st]', el).forEach(function (x) { x.classList.toggle('on', x === b); });
        $$('[data-stp]', el).forEach(function (x) { x.hidden = x.dataset.stp !== b.dataset.st; });
      });
    });
  });
  /* ---- linea del tempo (pagina Il Club): la riga rossa si riempie scorrendo ---- */
  $$('[data-timeline]').forEach(function (tl) {
    var bar = $('.tl-line i', tl), tick = false;
    function lay() {
      /* su schermi larghi ogni scheda sale accanto alla precedente, senza sovrapporsi a quella sopra dello stesso lato */
      var it = $$('.tl-item', tl), wide = window.innerWidth > 820, side = [0, 0], prevTop = 0, flow = 0;
      it.forEach(function (x) { x.style.marginTop = ''; });
      tl.style.paddingBottom = '';
      if (wide) {
        it.forEach(function (x, i) {
          var t = i ? Math.max(prevTop + 110, side[i % 2]) : 0;
          if (i) x.style.marginTop = (t - flow) + 'px';
          prevTop = t; flow = t + x.offsetHeight; side[i % 2] = flow;
        });
        tl.style.paddingBottom = (30 + Math.max(0, Math.max(side[0], side[1]) - flow)) + 'px';
      }
      upd();
    }
    function upd() {
      tick = false;
      var r = tl.getBoundingClientRect(), mid = window.innerHeight * 0.6;
      var f = Math.max(0, Math.min(1, (mid - r.top) / r.height));
      bar.style.height = (f * 100) + '%';
      $$('.tl-item', tl).forEach(function (it) { it.classList.toggle('past', it.getBoundingClientRect().top + 30 < mid); });
    }
    window.addEventListener('scroll', function () { if (!tick) { tick = true; requestAnimationFrame(upd); } }, { passive: true });
    window.addEventListener('resize', lay);
    window.addEventListener('load', lay);
    $$('img', tl).forEach(function (im) { im.addEventListener('load', lay); });
    lay();
  });

  /* diretta YouTube: il pulsante e la barra compaiono solo se data/diretta.json dice che il canale è in live */
  (function () {
    var sc = document.querySelector('script[src*="js/main.js"]');
    if (!sc || !window.fetch) return;
    var root = sc.getAttribute('src').replace(/js\/main\.js.*$/, '');
    fetch(root + 'data/diretta.json?t=' + Date.now(), { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (d) {
      var dal = Date.parse(d.dal || '');
      if (!d.live || (dal && Date.now() - dal > 6 * 3600e3)) return;
      $$('[data-live]').forEach(function (a) {
        a.href = d.url;
        if (d.titolo) { var em = $('em', a); if (em) em.textContent = d.titolo; }
        a.hidden = false;
      });
      var bar = document.createElement('a');
      bar.className = 'live-bar'; bar.href = d.url; bar.target = '_blank'; bar.rel = 'noopener';
      bar.innerHTML = '<span class="live-dot" aria-hidden="true"></span><b>In diretta ora</b><span>Guarda la partita dei Lancers su YouTube →</span>';
      document.body.insertBefore(bar, document.body.firstChild);
    }).catch(function () {});
  })();
})();
