#!/usr/bin/env python3
"""Genera il sito statico a partire da tools/content.json.  Uso: python3 tools/build.py"""
import os, re, json, hashlib, html as H
from bs4 import BeautifulSoup

_D = os.path.dirname(os.path.abspath(__file__)) + "/../"
VER = hashlib.md5(open(_D + "css/style.css", "rb").read() + open(_D + "js/main.js", "rb").read()).hexdigest()[:8]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, 'tools', 'content.json')))
PAGES = {p['path']: p for p in D['pages']}
POSTS = D['posts']
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre',
        'novembre', 'dicembre']
EMAIL = 'lancers.campo@gmail.com'

NAV = [
    ('Il Club', 'societa/', [('La società', 'societa/'), ('Piazzamenti', 'societa/piazzamenti/'),
                             ('Sponsor', 'societa/sponsor/'),
                             ('Diventa nostro sponsor', 'societa/diventa-nostro-sponsor/'),
                             ('Codice etico', 'societa/codice-etico/'), ('Contatti', 'societa/contatti/')]),
    ('Squadre', 'squadre-senior/', [('Serie B', 'squadre-senior/'), ('Roster Serie B', 'squadre-senior/serie-a2/'),
                                    ('Giocatori passati', 'squadre-senior/giocatori-passati/'),
                                    ('Calendario e classifica', 'squadre-senior/risultati/'),
                                    ('Amatori', 'squadre-senior/amatoriale/'),
                                    ('Torneo Lancers BAZ 40', 'squadre-senior/amatoriale/torneo-lancers-baz-40/')]),
    ('Giovanili', 'giovanili/', [('Settore giovanile', 'giovanili/'), ('Stagioni e risultati', 'giovanili/stagioni/'), ('Under 15', 'giovanili/under-15/'),
                                 ('Calendario U15', 'giovanili/calendario-u15-2020/'),
                                 ('Under 12', 'giovanili/under-12/'),
                                 ('Calendario U12', 'giovanili/calendario-u12-2020/')]),
    ('Lancers Field', 'ballpark/', [('Il campo', 'ballpark/'),
                                    ('Open Field', 'ballpark/open-field-diamanti-inclusivi/'),
                                    ('Orari allenamenti', 'ballpark/orari-allenamenti/')]),
    ('Notizie', 'notizie/', []),
    ('Galleria', 'gallery/', [('Foto', 'gallery/'), ('Foto di squadra', 'gallery/foto-di-squadra/'),
                              ('Video', 'gallery/video/')]),
    ('Il Baseball', 'baseball-2/', [('Il baseball', 'baseball-2/'), ('Le regole', 'baseball-2/baseball/'),
                                    ('Al cinema', 'baseball-2/al-cinema/'), ('Area download', 'area-download/')]),
    ('Shop', 'shop/', []),
]


def e(s):
    return H.escape(s, quote=True)


def link(root, path):
    """Link relativo che funziona sia online sia aprendo i file dal computer."""
    if '?' in path:
        p, q = path.split('?', 1)
        return root + p + 'index.html?' + q
    return root + path + 'index.html'


def fdate(d):
    y, m, g = d.split('-')
    return '%d %s %s' % (int(g), MESI[int(m) - 1], y)


def media_ok(n):
    return os.path.exists(os.path.join(ROOT, 'media', n))


def resolve(html, root):
    """Sostituisce i segnaposto e toglie le immagini non disponibili."""
    s = BeautifulSoup(html, 'html.parser')
    for im in s.find_all('img'):
        m = re.match(r'(MEDIA|THUMB):(.*)', im.get('src', ''))
        if m and not media_ok(m.group(2)):
            a = im.find_parent('a')
            (a or im).decompose()
    for a in s.find_all('a', href=re.compile(r'^https://lancersbaseballclub\.com')):
        a.unwrap()
    for box in s.select('.gallery-x, .slider'):
        if not box.find('img'):
            box.decompose()
    for sl in s.select('.slider'):
        slides = sl.select('.slide')
        track = s.new_tag('div')
        track['class'] = 'slides'
        for x in slides:
            track.append(x.extract())
        sl.append(track)
        if len(slides) > 1:
            for cls, lab, ch in (('prev', 'Precedente', '‹'), ('next', 'Successiva', '›')):
                b = s.new_tag('button', type='button')
                b['class'] = 'sl-btn ' + cls
                b['aria-label'] = lab
                b.string = ch
                sl.append(b)
            dots = s.new_tag('div')
            dots['class'] = 'dots'
            sl.append(dots)
    for ph in s.select('[data-contact-form]'):
        ph.replace_with(BeautifulSoup(contact_form(), 'html.parser'))
    out = str(s)
    out = re.sub(r'ROOT:([^"]*)', lambda m: link(root, m.group(1)) if m.group(1) else root + 'index.html', out)
    out = out.replace('THUMB:', root + 'media/t/').replace('MEDIA:', root + 'media/').replace('FILE:', root + 'files/')
    return out


def contact_form():
    return '''<form class="contact" data-mailto="%s">
<div class="row"><label>Nome e cognome<input name="nome" required autocomplete="name"></label>
<label>Telefono<input name="telefono" type="tel" autocomplete="tel"></label></div>
<label>Messaggio<textarea name="messaggio" rows="5" required></textarea></label>
<button class="btn r" type="submit">Invia il messaggio</button>
<p class="hint">Si aprirà il tuo programma di posta con il messaggio già pronto. In alternativa scrivi a <a href="mailto:%s">%s</a>.</p>
</form>''' % (EMAIL, EMAIL, EMAIL)


def header(root, cur):
    items = []
    for label, path, sub in NAV:
        act = ' class="on"' if cur.startswith(path) else ''
        if sub:
            lis = ''.join('<li><a href="%s">%s</a></li>' % (link(root, p), e(l)) for l, p in sub)
            items.append('<li class="has-sub"><a href="%s"%s>%s</a><button class="sub-t" aria-label="Apri il menu %s" '
                         'aria-expanded="false"></button><ul class="sub">%s</ul></li>'
                         % (link(root, path), act, e(label), e(label), lis))
        else:
            items.append('<li><a href="%s"%s>%s</a></li>' % (link(root, path), act, e(label)))
    return '''<a class="skip" href="#main">Vai al contenuto</a>
<header class="site-h"><div class="wrap">
<a class="logo" href="%sindex.html"><img src="%simages/logo-lancers.png" alt="Lancers Baseball Club 1982" width="122" height="76"></a>
<button class="burger" aria-label="Apri il menu" aria-expanded="false" aria-controls="nav"><span></span><span></span><span></span></button>
<nav id="nav" aria-label="Menu principale"><ul class="menu">%s<li class="cta-li"><a class="cta" href="%s">Gioca con noi</a></li></ul></nav>
</div></header>''' % (root, root, ''.join(items), link(root, 'gioca-anche-tu/'))


def footer(root):
    def col(title, links):
        return '<div><h4>%s</h4>%s</div>' % (title, ''.join('<p><a href="%s">%s</a></p>' % (link(root, p), e(l))
                                                           for l, p in links))
    return '''<footer class="site-f"><div class="wrap"><div class="g">
<div><a class="logo" href="%sindex.html"><img src="%simages/logo-lancers.jpg" alt="Lancers" loading="lazy"></a>
<p class="addr">Lancers Baseball Club A.S.D.<br>Via Livornese, loc. Porto di Mezzo<br>50055 Lastra a Signa (FI)</p>
<p><a href="tel:+390558999832">055 8999832</a><br><a href="mailto:%s">%s</a></p><div class="social" data-social></div></div>
%s%s%s
</div><div class="copy">© 2026 Lancers Baseball Club 1982 · Sito ufficiale dei Lancieri di Lastra a Signa</div></div></footer>
<button class="to-top" aria-label="Torna su">↑</button>
<div class="lb" hidden><button class="lb-x" aria-label="Chiudi">×</button><button class="lb-p" aria-label="Precedente">‹</button>
<figure><img alt=""><figcaption></figcaption></figure><button class="lb-n" aria-label="Successiva">›</button></div>
<script src="%sdata/stagione.js"></script><script src="%sjs/main.js?v=__VER__" defer></script>''' % (
        root, root, EMAIL, EMAIL,
        col('Il Club', [('La società', 'societa/'), ('Piazzamenti', 'societa/piazzamenti/'),
                        ('Sponsor', 'societa/sponsor/'), ('Codice etico', 'societa/codice-etico/'),
                        ('Contatti', 'societa/contatti/')]),
        col('Squadre', [('Serie B', 'squadre-senior/'), ('Amatori', 'squadre-senior/amatoriale/'),
                        ('Under 15', 'giovanili/under-15/'), ('Under 12', 'giovanili/under-12/'),
                        ('Orari allenamenti', 'ballpark/orari-allenamenti/')]),
        col('Scopri', [('Notizie', 'notizie/'), ('Galleria', 'gallery/'), ('Lancers Field', 'ballpark/'),
                       ('Shop', 'shop/'), ('Area download', 'area-download/')]),
        root, root)



# ---- calendario, risultati e classifica già scritti nell'HTML (prima li disegnava solo il JavaScript) ----
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
GIORNI = ['lun', 'mar', 'mer', 'gio', 'ven', 'sab', 'dom']


def _stagione():
    import datetime as DT
    t = open(_D + 'data/stagione.js', encoding='utf-8').read()
    L = json.loads(t[t.index('{'):t.rindex('}') + 1])
    games = []
    for g in L['partite']:
        o = dict(g)
        hm = g['ora'] if re.match(r'^\d\d:\d\d$', g.get('ora', '')) else '12:00'
        o['when'] = DT.datetime.fromisoformat(g['data'] + 'T' + hm)
        o['played'] = isinstance(g.get('puntiCasa'), int)
        o['home'] = g['casa'] == 'LAN'
        o['opp'] = g['ospiti'] if o['home'] else g['casa']
        o['off'] = g.get('nota') in ('rinviata', 'annullata')
        if o['played']:
            o['us'] = g['puntiCasa'] if o['home'] else g['puntiOspiti']
            o['them'] = g['puntiOspiti'] if o['home'] else g['puntiCasa']
            o['win'] = o['us'] > o['them']
        games.append(o)
    table = sorted(({**r, 'pct': r['v'] / (r['v'] + r['p']) if r['v'] + r['p'] else 0} for r in L['classifica']),
                   key=lambda r: (-r['pct'], -r['v']))
    return L, games, table


def prerender(doc):
    """Riempie i segnaposto della stagione con l'HTML vero: si legge anche senza JavaScript (il JavaScript poi lo ridisegna uguale)."""
    if not re.search(r'data-(results|standings|calendar|next-game|season-head|source)', doc):
        return doc
    import datetime as DT
    L, games, table = _stagione()
    nome = lambda k: e(L['squadre'].get(k, k))
    played = [g for g in games if g['played']]
    W = sum(1 for g in played if g['win'])
    Lo = len(played) - W
    pos = next((i + 1 for i, r in enumerate(table) if r['squadra'] == 'LAN'), 0)
    now = DT.datetime.now()
    nxt = next((g for g in games if not g['played'] and not g['off'] and g['when'] + DT.timedelta(hours=3) > now), None)
    dstr = lambda d: '%s %d %s' % (GIORNI[d.weekday()], d.day, MESI[d.month - 1][:3])

    def row(g):
        cls = ('w' if g['win'] else 'l') if g['played'] else ''
        tag = 'a' if g.get('boxscore') else 'div'
        href = (' href="%s%s" target="_blank" rel="noopener" title="Apri il tabellino su FIBS"' % (L['stagione']['boxscore'], g['boxscore'])) if g.get('boxscore') else ''
        if g['played']:
            score = '%s – %s<i>%s</i>' % (g['us'], g['them'], 'V' if g['win'] else 'S')
        else:
            score = '<i>%s</i>' % e(g['nota']) if g['off'] else e(g['ora'])
        note = (' · ' + e(g['nota'])) if g['played'] and g.get('nota') else ''
        return ('<%s class="g-row %s"%s data-side="%s"><span class="d">%s<br>%s</span><span class="t">%s%s<small>%s · %s%s</small></span>'
                '<span class="s">%s</span></%s>') % (tag, cls, href, 'casa' if g['home'] else 'fuori', dstr(g['when']), e(g['ora']),
                                                    'vs ' if g['home'] else '@ ', nome(g['opp']), 'In casa' if g['home'] else 'In trasferta',
                                                    e(g['campo']), note, score, tag)

    def standings(mini):
        top = table[0]
        h = ['<div class="stand"><div class="table-wrap"><table><thead><tr><th class="n">#</th><th>Squadra</th><th class="n">V</th><th class="n">P</th>%s<th class="n">%%</th>%s</tr></thead><tbody>' % (
            '' if mini else '<th class="n">G</th>', '' if mini else '<th class="n">Dist.</th>')]
        for i, r in enumerate(table):
            gb = ((top['v'] - r['v']) + (r['p'] - top['p'])) / 2
            gbs = ('%g' % gb).replace('.', ',') if gb else '–'
            h.append('<tr%s><td class="n">%d</td><td>%s</td><td class="n">%d</td><td class="n">%d</td>%s<td class="n">%s</td>%s</tr>' % (
                ' class="me"' if r['squadra'] == 'LAN' else '', i + 1, nome(r['squadra']), r['v'], r['p'],
                '' if mini else '<td class="n">%d</td>' % (r['v'] + r['p']), ('%.3f' % r['pct']).lstrip('0') if r['pct'] < 1 else '1.000',
                '' if mini else '<td class="n">%s</td>' % gbs))
        return ''.join(h) + '</tbody></table></div></div>'

    def cal():
        h, m = ['<div class="cal-f"><button class="chip on" data-side="">Tutte</button><button class="chip" data-side="casa">In casa</button>'
                '<button class="chip" data-side="fuori">In trasferta</button></div><div class="cal">'], -1
        for g in games:
            if g['when'].month != m:
                m = g['when'].month
                h.append('<h3 class="month">%s</h3>' % MESI[m - 1])
            h.append(row(g))
        return ''.join(h) + '</div>'

    if nxt:
        ng = ('<div class="next"><div class="kick">Prossima partita · %s</div><h3>%s <span class="vs">vs</span> %s</h3><p>%s %d · ore %s · %s</p></div>') % (
            e(L['stagione']['nome']), nome(nxt['casa']), nome(nxt['ospiti']), dstr(nxt['when']), nxt['when'].year, e(nxt['ora']), e(nxt['campo']))
    else:
        ng = ('<div class="next"><div class="kick">%s · %s</div><h3>Stagione conclusa</h3><p>I Lancers chiudono il campionato al %d° posto. Il nuovo calendario comparirà qui appena la FIBS lo pubblica.</p>'
              '<div class="rec"><div><b>%d</b><span>vittorie</span></div><div><b>%d</b><span>sconfitte</span></div><div><b>%d°</b><span>posto</span></div></div></div>') % (
            e(L['stagione']['nome']), e(L['stagione']['girone']), pos, W, Lo, pos)
    head = ('<h2 class="has-text-align-center">%s – %s</h2><div class="season-h"><div><b>%d</b><span>vittorie</span></div><div><b>%d</b><span>sconfitte</span></div>'
            '<div><b>%d°</b><span>in classifica</span></div></div>') % (e(L['stagione']['nome']), e(L['stagione']['girone']), W, Lo, pos)
    y, mo, d = L['stagione']['aggiornato'].split('-')
    src = 'Dati aggiornati al %d %s %s. Fonte: <a href="%s" target="_blank" rel="noopener">FIBS</a> · <a href="%s" target="_blank" rel="noopener">calendario ufficiale</a>' % (
        int(d), MESI[int(mo) - 1], y, L['stagione']['fonte'], L['stagione']['calendarioFibs'])
    res = '<div class="res">%s</div>' % ''.join(row(g) for g in played[-6:][::-1])

    doc = re.sub(r'(<div[^>]*\bdata-next-game(?:="")?[^>]*>)(</div>)', lambda m: m.group(1) + ng + m.group(2), doc)
    doc = re.sub(r'(<div data-results(?:="")?>)(</div>)', lambda m: m.group(1) + res + m.group(2), doc)
    doc = re.sub(r'(<div data-standings="mini">)(</div>)', lambda m: m.group(1) + standings(True) + m.group(2), doc)
    doc = re.sub(r'(<div data-standings(?:="")?>)(</div>)', lambda m: m.group(1) + standings(False) + m.group(2), doc)
    doc = re.sub(r'(<div data-calendar(?:="")?>)(</div>)', lambda m: m.group(1) + cal() + m.group(2), doc)
    doc = re.sub(r'(<div data-season-head(?:="")?>)(</div>)', lambda m: m.group(1) + head + m.group(2), doc)
    doc = re.sub(r'(<p class="src" data-source(?:="")?>)(</p>)', lambda m: m.group(1) + src + m.group(2), doc)
    return doc


def shell(path, title, body, desc='', cls=''):
    depth = path.count('/')
    root = '../' * depth
    full = (title + ' | Lancers Baseball Club 1982') if title else 'Lancers Baseball Club 1982 | Lastra a Signa'
    doc = '''<!doctype html>
<html lang="it" class="no-js"><head><script>document.documentElement.classList.remove("no-js")</script><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><meta name="description" content="%s">
<link rel="icon" href="%simages/logo-lancers.jpg"><link rel="stylesheet" href="%scss/style.css?v=__VER__">
</head><body class="%s">
%s
<main id="main">
%s
</main>
%s
</body></html>
''' % (e(full), e(desc or 'Sito ufficiale dei Lancieri di Lastra a Signa: Serie B, settore giovanile e Lancers Open Field.'),
       root, root, cls, header(root, path), body, footer(root))
    out = os.path.join(ROOT, path, 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(prerender(doc.replace('__VER__', VER).replace('__LIVE__', live_btn())))
    return root


def crumbs(root, path, last=None):
    parts = path.strip('/').split('/')
    out = ['<a href="%sindex.html">Home</a>' % root]
    acc = ''
    for i, seg in enumerate(parts[:-1]):
        acc += seg + '/'
        if acc in PAGES:
            out.append('<a href="%s">%s</a>' % (link(root, acc), e(PAGES[acc]['title'])))
        elif acc == 'notizie/':
            out.append('<a href="%s">Notizie</a>' % link(root, acc))
    if last:
        out.append('<span>%s</span>' % e(last))
    return '<nav class="crumbs" aria-label="Percorso">%s</nav>' % ' <i>/</i> '.join(out)


def band(root, path, title, kicker=''):
    return '''<section class="band"><div class="wrap">%s%s<h1>%s</h1></div></section>''' % (
        crumbs(root, path, title), '<div class="kick">%s</div>' % e(kicker) if kicker else '', e(title))


def children(path):
    return [p for k, p in PAGES.items() if k.startswith(path) and k != path and k.count('/') == path.count('/') + 1]


def child_cards(root, path):
    ch = children(path)
    if not ch or path == 'squadre-senior/serie-a2/':
        return ''
    order = [p for _, _, sub in NAV for _, p in sub]
    ch.sort(key=lambda p: order.index(p['path']) if p['path'] in order else 99)
    cards = []
    for p in ch:
        img = ('<span class="im" style="background-image:url(%smedia/t/%s)"></span>' % (root, p['thumb'])
               if p['thumb'] and media_ok(p['thumb']) else '<span class="im ph"></span>')
        cards.append('<a class="tile reveal" href="%s">%s<span class="t">%s<b>→</b></span></a>'
                     % (link(root, p['path']), img, e(p['title'])))
    return '<section class="alt"><div class="wrap"><div class="sh"><h2>In questa sezione</h2></div><div class="tiles">%s</div></div></section>' % ''.join(cards)


def post_card(root, p, big=False, hidden=False):
    img = ('<span class="im" style="background-image:url(%smedia/t/%s)"></span>' % (root, p['thumb'])
           if p['thumb'] and media_ok(p['thumb']) else '<span class="im ph"></span>')
    cat = p['cats'][0][0] if p['cats'] else 'Varie'
    return ('<a class="post reveal%s" href="%s" data-cat="%s" data-t="%s"%s>%s<span class="b"><span class="date">%s · %s</span>'
            '<h3>%s</h3><span class="ex">%s…</span></span></a>') % (
        ' big' if big else '', link(root, p['path']), ' '.join(c[1] for c in p['cats']), e(p['title'].lower()),
        ' hidden' if hidden else '', img, fdate(p['date']), e(cat), e(p['title']), e(p['excerpt'][:130]))


# ---------------------------------------------------------------- pagine
def build_page(p):
    path, title = p['path'], p['title']
    root = '../' * path.count('/')
    content = resolve(p['html'], root)
    extra = ''
    cls = 'page'
    if path == 'squadre-senior/serie-a2/':
        content = roster(root, path) + '<div class="filter"><input type="search" placeholder="Cerca un giocatore…" ' \
                                       'aria-label="Cerca un giocatore" data-filter-table></div>' + content
        cls += ' wide'
    elif path.startswith('squadre-senior/serie-a2/'):
        _slug = path[len('squadre-senior/serie-a2/'):].strip('/')
        _anni = anni_link(root, GIOC.get(_slug, {}))
        content = player(content) + ('<p class="pl-sea"><b>Stagioni in prima squadra</b> %s</p>' % _anni if _anni else '') + (
            '<div class="pstats" data-player-stats="%s"></div><script src="%sdata/statistiche.js"></script>' % (_slug, root))
        cls += ' wide'
    elif path == 'societa/':
        content = storia(content)
        cls += ' wide'
    content = pagina_speciale(path, content, root)
    content = spezza_a_capo(content, path)
    content = ritocchi_extra(path, content, root)
    if path in ('giovanili/', 'squadre-senior/', 'giovanili/calendario-u12-2020/', 'giovanili/calendario-u15-2020/', 'ballpark/',
                'ballpark/open-field-diamanti-inclusivi/', 'squadre-senior/amatoriale/', 'baseball-2/al-cinema/'):
        cls += ' wide'
    if path == 'giovanili/' and GIOV['stagioni']:
        content += '<div class="gv-box"><h2 class="has-text-align-center">Le stagioni anno per anno</h2>%s<p class="has-text-align-center"><a class="btn r" href="%s">Tutte le stagioni giovanili</a></p></div>' % (
            giov_elenco(root), link(root, 'giovanili/stagioni/'))
        cls += ' wide'
    if path == 'societa/piazzamenti/':
        content = piazzamenti(content, root)
        cls += ' wide'
    if 'gallery-x' in content or path.startswith('gallery') or path == 'shop/':
        cls += ' wide'
    if path == 'squadre-senior/risultati/':
        title = 'Calendario e classifica Serie B'
        content = re.sub(r'<p>\s*in costruzione\s*</p>', '', content)
        content = re.sub(r'<h2.*?</h2>', '', content, count=1, flags=re.S)
        content = ('<div data-season-head></div><div class="live-p">' + live_btn() + '</div><div class="sb-grid"><div class="sb-cal"><h3>Calendario e risultati</h3><div data-calendar></div></div>'
                   '<div class="sb-cls" id="classifica"><h3>Classifica</h3><div data-standings></div>'
                   '<p class="sb-leg">V vinte · P perse · G giocate · Dist. partite di distacco dalla prima. Tocca una partita giocata per aprire il tabellino FIBS.</p></div></div>'
                   '<p class="src" data-source></p><h2 class="has-text-align-center">Il calendario in immagini</h2>') + content
        cls += ' wide'
    if path == 'societa/contatti/':
        extra = ('<section class="alt"><div class="wrap narrow"><div class="sh"><h2>Scrivici</h2></div>%s</div></section>'
                 '<div class="map"><iframe loading="lazy" title="Mappa Lancers Field" '
                 'src="https://www.google.com/maps?q=Campo+da+baseball+Porto+di+Mezzo+Lastra+a+Signa&output=embed"></iframe></div>'
                 % contact_form())
    body = band(root, path, title) + '<section class="body"><div class="wrap"><div class="content reveal">%s</div></div></section>%s%s%s' % (
        content, extra, child_cards(root, path), cta(root) if path != 'gioca-anche-tu/' else '')
    shell(path, title, body, cls=cls)


def info(html):
    d = {}
    for k, v in re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td></tr>', html, re.S):
        d[re.sub(r'<.*?>', '', k).strip().lower()] = re.sub(r'<.*?>', '', v).strip()
    return d


def roster(root, path):
    cards = []
    for p in sorted(children(path), key=lambda x: x['title']):
        d = info(p['html'])
        num = d.get('casacca #', '')
        num = num if re.match(r'^\d+$', num) else ''
        img = ('<span class="im" style="background-image:url(%smedia/t/%s)"></span>' % (root, p['thumb'])
               if p['thumb'] and media_ok(p['thumb']) else '<span class="im ph"></span>')
        cards.append('<a class="player reveal" href="%s">%s<span class="b">%s<strong>%s</strong><em>%s</em></span></a>' % (
            link(root, p['path']), img, '<span class="num">%s</span>' % num if num else '', e(p['title']),
            e(d.get('ruolo', ''))))
    return '<div class="players">%s</div>' % ''.join(cards)


def player(content):
    s = BeautifulSoup(content, 'html.parser')
    fig = s.find('figure') or s.find('img')
    tab = s.select_one('.table-wrap')
    if not (fig and tab):
        return content
    f, t = str(fig.extract()), str(tab.extract())
    return '<div class="pl-top"><div class="pl-photo">%s</div><div class="pl-info">%s</div></div>%s' % (f, t, str(s))


def storia(content):
    """Pagina Il Club: la storia diventa una linea del tempo. I testi restano identici, cambia solo la struttura."""
    from PIL import Image
    from bs4 import NavigableString
    s = BeautifulSoup(content, 'html.parser')
    intro, items, coda, pend = [], [], [], []
    for el in [c for c in s.contents if getattr(c, 'name', None)]:
        testo = el.get_text().strip()
        m = re.match(r'(\d{4}(?:-\d{4})?)\s*//', testo)
        if el.name != 'p':
            intro.append(str(el))
            continue
        figs = []
        for a in el.select('a[data-lb]'):
            img = a.find('img')
            img['class'] = []
            try:
                w, h = Image.open(os.path.join(ROOT, 'media', a['href'].rsplit('media/', 1)[-1])).size
            except Exception:
                w, h = 4, 3
            figs.append('<figure class="tl-ph%s">%s</figure>' % (' pt' if h > w else '', str(a.extract())))
        if not testo:                       # paragrafo con la sola foto: va con l'anno che segue
            pend += figs
            continue
        if m:
            st = el.find('strong')
            if '//' in st.get_text():
                st['class'] = ['tl-y']
            else:                           # "<strong>2019</strong> // testo": la barra entra nell'etichetta dell'anno
                nxt = st.next_sibling
                i = str(nxt).index('//') + 2
                span = s.new_tag('span')
                span['class'] = ['tl-y']
                st.wrap(span)
                span.append(NavigableString(str(nxt)[:i]))
                nxt.replace_with(NavigableString(str(nxt)[i:]))
            items.append({'id': m.group(1), 'figs': pend + figs, 'html': [str(el)]})
            pend = []
        elif items and el.find('strong') is None:
            items[-1]['html'].append(str(el))   # es. il link al video della festa
        else:
            coda.append(str(el))
    out = ''.join(intro) + '<div class="tl" data-timeline><div class="tl-line"><i></i></div>'
    for it in items:
        out += '<article class="tl-item reveal" id="anno-%s"><span class="tl-dot"></span><div class="tl-card">%s<div class="tl-tx">%s</div></div></article>' % (
            it['id'], ''.join(it['figs']), ''.join(it['html']))
    return out + '</div><div class="tl-end reveal">%s</div>' % ''.join(coda)


# ---------------------------------------------------------------- stagioni (dati FIBS in tools/stagioni.json)
_SJ = os.path.join(ROOT, 'tools', 'stagioni.json')
SEAS = json.load(open(_SJ, encoding='utf-8')) if os.path.exists(_SJ) else {'stagioni': {}, 'colonne': {}}
PZ = 'societa/piazzamenti/'
PZ_TXT = {}


def squadra(n):
    """Nome di una squadra come lo scrive la FIBS, reso leggibile."""
    n = re.sub(r'\*+', '', n).strip()
    if n.upper() == n:
        n = n.title()
        n = re.sub(r"(?<=[a-zà-ù])'S\b", "'s", n)
        n = re.sub(r'\b((?:[A-Za-z]\.){2,}[A-Za-z]?)', lambda m: m.group(1).upper(), n)
        n = re.sub(r'\b(Asd|Ssd|Bc|Bsc|Cso|Rj|Bbc|Srl)\b', lambda m: m.group(1).upper(), n)
    return re.sub(r'\s+', ' ', n)


def noi(n):
    return 'LANCERS' in n.upper()


_GJ = os.path.join(ROOT, 'tools', 'giocatori.json')
GIOC = json.load(open(_GJ, encoding='utf-8')) if os.path.exists(_GJ) else {}
GDIR = 'squadre-senior/giocatori/'
GPAS = 'squadre-senior/giocatori-passati/'
ULTIMA = max(SEAS['stagioni']) if SEAS['stagioni'] else ''
GMAP = {}
for _k, _v in GIOC.items():
    _v['path'] = _v.get('pagina') or '%s%s/' % (GDIR, _k)
    for _n in [_v['nome'].lower()] + _v.get('alias', []):
        GMAP[_n] = _v['path']


def passato(v):
    return not v.get('pagina') and ULTIMA not in v.get('stagioni', {})


def giocatore_link(root, nome):
    pth = GMAP.get(nome.lower())
    return '<a href="%s">%s</a>' % (link(root, pth), e(nome)) if pth else e(nome)


def anni_link(root, v):
    return ' · '.join('<a href="%s">%s</a>' % (link(root, '%s%s/' % (PZ, y)), y) for y in sorted(v.get('stagioni', {})))


def intervalli(anni):
    anni = sorted(int(y) for y in anni)
    out, i = [], 0
    while i < len(anni):
        k = i
        while k + 1 < len(anni) and anni[k + 1] == anni[k] + 1:
            k += 1
        out.append(str(anni[i]) if k == i else '%d–%d' % (anni[i], anni[k]))
        i = k + 1
    return ', '.join(out)


def build_giocatore(slug, v):
    path = v['path']
    root = '../' * path.count('/')
    st = v.get('stagioni', {})
    ult = next((st[y] for y in sorted(st, reverse=True) if st[y].get('rosa')), {})
    righe = [('Anno di nascita', e(v.get('nascita', ''))), ('Ruolo', e(ult.get('ruolo', ''))),
             ('Batte / Tira', e(ult.get('bt', ''))), ('Ultima casacca #', e(ult.get('n', ''))),
             ('Stagioni con i Lancers', anni_link(root, v))]
    tab = '<div class="table-wrap"><table><tbody>%s</tbody></table></div>' % ''.join(
        '<tr><td>%s</td><td>%s</td></tr>' % (a, b) for a, b in righe if b)
    pas = passato(v)
    content = ('%s<p class="pstats-leg has-text-align-center">Dati della scheda dal sito FIBS, che pubblica le rose dal 2020.</p>'
               '<div class="pstats" data-player-stats="%s"></div><script src="%sdata/statistiche.js"></script>' % (tab, slug, root))
    back = (GPAS, 'Tutti i giocatori passati') if pas else ('squadre-senior/serie-a2/', 'Roster Serie B')
    body = band(root, path, v['nome'], 'Giocatore passato' if pas else 'Prima squadra %s' % ULTIMA) + \
        '<section class="body"><div class="wrap"><div class="content reveal">%s</div><p class="back"><a class="btn n" href="%s">%s</a></p></div></section>%s' % (
            content, link(root, back[0]), back[1], cta(root))
    shell(path, v['nome'], body, desc='%s, giocatore dei Lancers Baseball Club: stagioni e statistiche dal sito FIBS.' % v['nome'], cls='page wide')


def build_giocatori():
    for slug, v in GIOC.items():
        if not v.get('pagina'):
            build_giocatore(slug, v)
    path = GPAS
    root = '../' * path.count('/')
    pas = sorted([v for v in GIOC.values() if passato(v)], key=lambda v: v['nome'])
    rows = []
    for v in pas:
        st = v.get('stagioni', {})
        ult = next((st[y] for y in sorted(st, reverse=True) if st[y].get('rosa')), {})
        rows.append('<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td></tr>' % (
            link(root, v['path']), e(v['nome']), intervalli(st), e(ult.get('ruolo', '')), e(ult.get('n', '')), e(v.get('nascita', ''))))
    primo = min(SEAS['stagioni'][y]['anno'] for y in SEAS['stagioni'] if SEAS['stagioni'][y].get('rosa')) if rows else ''
    content = ('<p class="sea-lead">I %d giocatori che hanno vestito la maglia della prima squadra dal %s e che non fanno parte della rosa %s.</p>'
               '<p class="has-text-align-center">Ogni nome apre la scheda con le stagioni giocate e le statistiche di carriera prese dal sito FIBS. '
               'L\'elenco parte dal %s perché per gli anni precedenti la FIBS non pubblica le rose online.</p>'
               '<div class="filter"><input type="search" placeholder="Cerca un giocatore…" aria-label="Cerca un giocatore" data-filter-table></div>'
               '<div class="pstats sea-t gp"><div class="table-wrap"><table><thead><tr><th>Giocatore</th><th>Stagioni con i Lancers</th><th>Ruolo</th>'
               '<th class="n">Casacca #</th><th class="n">Anno di nascita</th></tr></thead><tbody>%s</tbody></table></div></div>' % (
                   len(pas), primo, ULTIMA, primo, ''.join(rows)))
    body = band(root, path, 'Giocatori passati', 'Prima squadra') + \
        '<section class="body"><div class="wrap"><div class="content reveal">%s</div><p class="back"><a class="btn n" href="%s">Roster Serie B</a></p></div></section>%s' % (
            content, link(root, 'squadre-senior/serie-a2/'), cta(root))
    shell(path, 'Giocatori passati', body, desc='I giocatori che hanno vestito la maglia dei Lancers negli anni passati, con stagioni e statistiche.', cls='page wide')


ICO = {
    'cal': '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>',
    'tab': '<svg viewBox="0 0 24 24"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>',
    'team': '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.4-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/><circle cx="17" cy="9" r="2.6"/><path d="M16 14.6c2.8-.2 4.8 1.5 5.5 4.4"/></svg>',
    'clock': '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    'star': '<svg viewBox="0 0 24 24"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg>',
    'hist': '<svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></svg>',
    'ball': '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M6 5.5c2.2 3.6 2.2 9.4 0 13M18 5.5c-2.2 3.6-2.2 9.4 0 13"/></svg>',
    'pdf': '<svg viewBox="0 0 24 24"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M12 12v6M9 15l3 3 3-3"/></svg>',
    'mail': '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>',
}


LIVE = 'https://www.youtube.com/@LancersBC-nh4wu/live'


def live_btn(extra=''):
    """Pulsante per la diretta YouTube delle partite (il link /live apre la diretta in corso, se c'è)."""
    return ('<a class="live-btn%s" href="%s" target="_blank" rel="noopener"><span class="live-ico" aria-hidden="true">%s</span>'
            '<span><b>Dirette YouTube</b><em>Segui le partite dei Lancers in streaming sul nostro canale</em></span></a>') % (extra, LIVE, ICO['play'])


ICO['play'] = '<svg viewBox="0 0 24 24"><rect x="2.5" y="5" width="19" height="14" rx="4"/><path d="M10 9v6l5-3z"/></svg>'


def hub(root, items, cls=''):
    """Riquadri di collegamento: (icona, titolo, sottotitolo, percorso)."""
    out = []
    for ic, t, sub, pth in items:
        if pth is None:
            continue
        href = pth if pth.startswith('http') else link(root, pth)
        ext = ' target="_blank" rel="noopener"' if pth.startswith('http') else ''
        out.append('<a class="hub-c reveal" href="%s"%s><i>%s</i><span><b>%s</b>%s</span></a>' % (
            href, ext, ICO[ic], e(t), '<em>%s</em>' % e(sub) if sub else ''))
    return '<div class="hub %s">%s</div>' % (cls, ''.join(out))


def giov_corrente(cat):
    ks = sorted((k for k, v in GIOV['stagioni'].items() if v['categoria'] == cat), reverse=True)
    return (ks[0], GIOV['stagioni'][ks[0]]) if ks else (None, None)


def riepilogo(st):
    fatte = [g for g in st['partite'] if 'puntiCasa' in g]
    v = sum(1 for g in fatte if (g['puntiCasa'] > g['puntiOspiti']) == noi(g['casa']))
    pos = next((r['pos'] for c in st['classifiche'][:1] for r in c['righe'] if r['noi']), '')
    box = [(pos + 'º', 'in Toscana') if pos else None, (v, 'vittorie'), (len(fatte) - v, 'sconfitte')]
    return '<div class="season-h">%s</div>' % ''.join('<div><b>%s</b><span>%s</span></div>' % x for x in box if x)


def prima_img(html, root):
    m = re.search(r'<img[^>]+src="([^"]+)"', resolve(html, root))
    return m.group(1) if m else ''


def pagina_speciale(path, content, root):
    """Ritocchi grafici di singole pagine: i testi della società restano identici, cambia solo l'impaginazione."""
    if path == 'giovanili/':
        sq = BeautifulSoup(content, 'html.parser')
        btns = sq.select_one('.wp-block-buttons')
        cards = []
        if btns:
            for a in btns.find_all('a'):
                href = a['href']
                key = 'u15' if 'under-15' in href else 'u12'
                pg = PAGES.get('giovanili/under-15/' if key == 'u15' else 'giovanili/under-12/')
                img = prima_img(pg['html'], root) if pg else ''
                k, st = giov_corrente(key)
                info = ''
                if st:
                    pos = next((r['pos'] for c in st['classifiche'][:1] for r in c['righe'] if r['noi']), '')
                    info = 'Stagione %s%s' % (st['anno'], (' · %sº posto in Toscana' % pos) if pos else '')
                cards.append('<a class="team-c reveal" href="%s"><span class="im" style="background-image:url(%s)"></span><span class="b"><strong>%s</strong><em>%s</em><i>Roster, calendario e risultati →</i></span></a>' % (
                    href, img, a.get_text(strip=True), e(info)))
            btns.replace_with(BeautifulSoup('<div class="team-g">%s</div>' % ''.join(cards), 'html.parser'))
        # testo e foto affiancati
        ps = [x for x in sq.find_all('p', recursive=False)]
        fig = sq.find('div', recursive=False) if sq.find('div', recursive=False) and sq.find('div', recursive=False).find('figure') else None
        figs = [d for d in sq.find_all('div', recursive=False) if d.find('figure')]
        if ps and figs:
            fig = figs[-1].extract()
            testo = ''.join(str(x.extract()) for x in ps)
            sq.append(BeautifulSoup('<div class="split reveal"><div class="split-t">%s</div><div class="split-i">%s</div></div>' % (testo, fig.decode_contents()), 'html.parser'))
        return str(sq)
    if path in ('giovanili/under-12/', 'giovanili/under-15/'):
        cat = 'u15' if 'under-15' in path else 'u12'
        k, st = giov_corrente(cat)
        cal = 'giovanili/calendario-u15-2020/' if cat == 'u15' else 'giovanili/calendario-u12-2020/'
        extra = ''
        if st:
            extra += '<h2 class="has-text-align-center">Stagione %s</h2>%s' % (st['anno'], riepilogo(st))
        extra += hub(root, [
            ('cal', 'Calendario', 'Le partite della stagione', cal if cal in PAGES else None),
            ('tab', 'Classifica e risultati', 'Scheda della stagione %s' % st['anno'] if st else '', '%s%s/' % (GV, k) if k else None),
            ('hist', 'Le stagioni passate', 'Tutti gli anni dal 2022', GV if GIOV['stagioni'] else None),
            ('clock', 'Orari allenamenti', 'Quando e dove ci alleniamo', 'ballpark/orari-allenamenti/' if 'ballpark/orari-allenamenti/' in PAGES else None),
        ])
        return content.replace('<figure', '<figure class="team-photo"', 1) + extra
    if path in ('giovanili/calendario-u12-2020/', 'giovanili/calendario-u15-2020/'):
        cat = 'u15' if 'u15' in path else 'u12'
        k, st = giov_corrente(cat)
        if st and st['partite']:
            m = re.search(r'(<figure.*?</figure>)', content, re.S)
            if m:
                content = content.replace(m.group(1), '')
                content += ('<div class="cal-split"><div class="cal-img reveal">%s</div><div class="reveal"><h3>Partite e risultati %s</h3>%s'
                            '<div class="cal sea-cal">%s</div><p class="src">Risultati dal sito FIBS · <a href="%s">scheda completa della stagione</a></p></div></div>') % (
                    m.group(1), st['anno'], riepilogo(st), partite_rows(st), link(root, '%s%s/' % (GV, k)))
        return content
    if path == 'squadre-senior/':
        sq = BeautifulSoup(content, 'html.parser')
        h5 = sq.find('h5')
        if h5:
            h5['class'] = ['has-text-align-center', 'team-link']
        figs = sq.find_all('figure')
        if figs:
            figs[0]['class'] = figs[0].get('class', []) + ['team-photo']
        return '<div data-season-head></div>' + str(sq) + hub(root, [
            ('team', 'Roster Serie B', 'I giocatori della prima squadra', 'squadre-senior/serie-a2/'),
            ('cal', 'Calendario e classifica', 'Partite, risultati e girone', 'squadre-senior/risultati/'),
            ('star', 'Piazzamenti', 'Le stagioni dal 2002 a oggi', 'societa/piazzamenti/'),
            ('hist', 'Giocatori passati', 'Chi ha vestito la nostra maglia', GPAS if GIOC else None),
            ('play', 'Dirette YouTube', 'Le partite in streaming', LIVE),
        ])
    if path == 'area-download/':
        sq = BeautifulSoup(content, 'html.parser')
        for a in sq.select('a.download'):
            par = a.find_parent('p')
            if par:
                par['class'] = ['dl-card']
                a.insert(0, BeautifulSoup('<i>%s</i>' % ICO['pdf'], 'html.parser'))
        return str(sq)
    if path == 'squadre-senior/amatoriale/torneo-lancers-baz-40/':
        return '<div class="soon reveal"><i>%s</i>%s</div>' % (ICO['ball'], content)
    return content



ICO.update({
    'pin': '<svg viewBox="0 0 24 24"><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
    'film': '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/></svg>',
    'book': '<svg viewBox="0 0 24 24"><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 21h15"/></svg>',
    'heart': '<svg viewBox="0 0 24 24"><path d="M12 20s-7.5-4.6-9-9.4C2 7.1 4.3 4 7.6 4c2 0 3.4 1.1 4.4 2.6C13 5.1 14.4 4 16.4 4 19.7 4 22 7.1 21 10.6 19.5 15.4 12 20 12 20z"/></svg>',
    'phone': '<svg viewBox="0 0 24 24"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z"/></svg>',
})

SEZ_NAV = {
    'baseball-2/': [('baseball-2/', 'Qualcosa sul baseball'), ('baseball-2/baseball/', 'Le regole'), ('baseball-2/al-cinema/', 'Al cinema')],
    'ballpark/': [('ballpark/', 'Lancers Field'), ('ballpark/open-field-diamanti-inclusivi/', 'Open Field'), ('ballpark/orari-allenamenti/', 'Orari allenamenti')],
}


def sez_nav(path, root):
    for k, items in SEZ_NAV.items():
        if path.startswith(k):
            return '<nav class="secnav" aria-label="In questa sezione">%s</nav>' % ''.join(
                '<a class="chip%s" href="%s"%s>%s</a>' % (' on' if p == path else '', link(root, p), ' aria-current="page"' if p == path else '', e(t))
                for p, t in items if p in PAGES)
    return ''


# posizioni in difesa sul diamante (coordinate su 300x300, casa base in basso)
POS_XY = {1: (150, 205), 2: (150, 286), 3: (216, 186), 4: (182, 148), 5: (84, 186), 6: (118, 148), 7: (74, 118), 8: (150, 98), 9: (226, 118)}


def diamante():
    """Disegno del campo visto dall'alto: casa base in basso, posizioni numerate da 1 a 9."""
    pts = ''.join('<g><circle cx="%d" cy="%d" r="13"/><text x="%d" y="%d">%d</text></g>' % (x, y, x, y + 5, n) for n, (x, y) in POS_XY.items())
    base = lambda x, y: '<rect class="base" x="%.1f" y="%.1f" width="9" height="9" transform="rotate(45 %.1f %.1f)"/>' % (x - 4.5, y - 4.5, x, y)
    return ('<svg class="dia" viewBox="0 64 300 240" role="img" aria-label="Le posizioni in difesa sul campo">'
            '<path class="grass" d="M150 262 L20 132 A184 184 0 0 1 280 132 Z"/>'
            '<path class="dirt" d="M150 262 L61.6 173.6 A125 125 0 0 1 238.4 173.6 Z"/>'
            '<path class="infield" d="M150 250 L194 206 L150 162 L106 206 Z"/>'
            '<path class="foul" d="M150 262 L20 132 M150 262 L280 132"/>'
            '<circle class="mound" cx="150" cy="205" r="9"/>'
            '%s%s%s<path class="home" d="M145 258h10v4l-5 5-5-5z"/>%s</svg>') % (
        base(206.6, 205.4), base(150, 148.9), base(93.4, 205.4), pts)


def regole_card(p):
    """Paragrafo 'LA DIFESA – … <br/><em><strong>Voce;</strong></em> testo…' diviso in titolo, introduzione ed elenco: stesse parole."""
    parts = re.split(r'<br/>\s*(?=<em><strong>)', p.decode_contents())
    head = parts[0]
    m = re.match(r'\s*<em><strong>(?:<br/>)?\s*(.*?)\s*</strong></em>\s*(.*)', head, re.S)
    if not m:
        return None
    tit = m.group(1).strip()
    intro = m.group(2).strip()
    if tit.endswith('–'):
        tit = tit[:-1].strip()
    else:
        intro = re.sub(r'^–\s*', '', intro)
    items = []
    for x in parts[1:]:
        mm = re.match(r'\s*<em><strong>(.*?)</strong></em>\s*(.*)', x, re.S)
        items.append('<li><b>%s</b> %s</li>' % (mm.group(1), mm.group(2).strip()) if mm else '<li>%s</li>' % x)
    return '<div class="rule reveal"><h3>%s</h3><p>%s</p>%s</div>' % (tit, intro, '<ul>%s</ul>' % ''.join(items) if items else '')



def spezza_a_capo(html, path=''):
    """Paragrafi lunghi con molti 'a capo' diventano paragrafi separati: stesse parole, lettura più ariosa."""
    if path == 'baseball-2/al-cinema/':
        return html
    sq = BeautifulSoup(html, 'html.parser')
    for p in sq.find_all('p'):
        if p.find_parent(['li', 'td', 'form']) or not p.find('br') or len(p.get_text()) < 250 or re.search(r'<br/>\s*<em><strong>', str(p)):
            continue
        parti = [x for x in re.split(r'<br/?>', p.decode_contents()) if BeautifulSoup(x, 'html.parser').get_text(strip=True)]
        if len(parti) < 2:
            continue
        cls = (' class="%s"' % ' '.join(p['class'])) if p.get('class') else ''
        p.replace_with(BeautifulSoup(''.join('<p%s>%s</p>' % (cls if i == 0 else '', x.strip()) for i, x in enumerate(parti)), 'html.parser'))
    return str(sq)


def ritocchi_extra(path, content, root):
    """Ritocchi grafici per Lancers Field, Open Field, Il Baseball, Le regole, Al cinema, Amatori. I testi restano identici."""
    nav = sez_nav(path, root)
    if path == 'ballpark/':
        sq = BeautifulSoup(content, 'html.parser')
        ps = sq.find_all('p', recursive=False)
        emb = sq.find('div', class_='embed')
        gal = sq.find('div', class_='gallery-x')
        h2 = sq.find('h2')
        if len(ps) >= 3 and emb:
            addr = ps[0].decode_contents()
            steps = ''.join('<li>%s</li>' % x.decode_contents() for x in ps[1:])
            out = (str(h2) if h2 else '') + (
                '<div class="place"><div class="place-t reveal"><div class="addr"><i>%s</i><p>%s</p></div>'
                '<h3>Come arrivare</h3><ol class="steps">%s</ol>'
                '<a class="btn r" href="https://www.google.com/maps/dir/?api=1&amp;destination=Campo+da+baseball+Lancers+Field+Porto+di+Mezzo" target="_blank" rel="noopener">Indicazioni stradali</a></div>'
                '<div class="place-m reveal">%s</div></div>') % (ICO['pin'], addr, steps, emb.decode_contents())
            if gal:
                out += '<h2 class="has-text-align-center">Il campo in foto</h2>' + str(gal)
            return nav + out
    if path == 'ballpark/open-field-diamanti-inclusivi/':
        sq = BeautifulSoup(content, 'html.parser')
        ps = sq.find_all('p', recursive=False)
        emb = sq.find('div', class_='embed')
        if emb and len(ps) >= 2:
            q = ps[-1].get_text().strip()
            q = q.strip('“”"')
            return nav + ('<div class="of"><div class="of-v reveal">%s</div><div class="of-t reveal"><span class="kick">Fondazione CR Firenze · volontari Lancers</span>%s</div></div>'
                          '<blockquote class="bigq reveal"><p>“%s”</p></blockquote>') % (
                str(emb), ''.join(str(x) for x in ps[:-1]), e(q)) + hub(root, [
                ('pin', 'Lancers Field', 'Dove si trova il campo', 'ballpark/'),
                ('clock', 'Orari allenamenti', 'Vieni a provare', 'ballpark/orari-allenamenti/' if 'ballpark/orari-allenamenti/' in PAGES else None),
                ('ball', 'Gioca con noi', 'Il baseball è per tutti', 'gioca-anche-tu/' if 'gioca-anche-tu/' in PAGES else None),
            ])
    if path == 'ballpark/orari-allenamenti/':
        return nav + content
    if path == 'squadre-senior/amatoriale/':
        sq = BeautifulSoup(content, 'html.parser')
        sl = sq.find('div', class_='slider')
        ps = sq.find_all('p', recursive=False)
        form = sq.find('form', class_='contact')
        if sl and ps:
            h2 = sq.find('h2')
            txt = []
            for p in ps:
                h = p.decode_contents()
                h = re.sub(r'(\+39 [\d ]{9,13}\d)', lambda m: '<a class="tel" href="tel:%s">%s</a>' % (m.group(1).replace(' ', ''), m.group(1)), h)
                cls = ' class="callout"' if p.get_text().startswith('Cerchiamo te') else ''
                txt.append('<p%s>%s</p>' % (cls, h))
            out = (str(h2) if h2 else '') + '<div class="am"><div class="am-s reveal">%s</div><div class="am-t reveal">%s</div></div>' % (str(sl), ''.join(txt))
            if form:
                out += '<h2 class="has-text-align-center">Scrivici per provare</h2>' + str(form)
            return out
    if path == 'baseball-2/':
        sq = BeautifulSoup(content, 'html.parser')
        ps = sq.find_all('p', recursive=False)
        if ps:
            ps[0]['class'] = ['dropcap']
            ps[-1]['class'] = ['closing']
        for f in sq.find_all('figure'):
            f['class'] = f.get('class', []) + ['pic']
        return nav + '<article class="essay">%s</article>' % str(sq)
    if path == 'baseball-2/baseball/':
        sq = BeautifulSoup(content, 'html.parser')
        for p in sq.find_all('p', recursive=False):
            t = p.get_text()
            if t.startswith('Lanciatore (1)'):
                nomi = [x.strip() for x in t.split(',')]
                leg = ''.join('<li><b>%s</b>%s</li>' % (re.search(r'\((\d)\)', x).group(1), e(x)) if re.search(r'\((\d)\)', x) else '<li>%s</li>' % e(x) for x in nomi)
                p.replace_with(BeautifulSoup('<div class="field reveal">%s<ol class="pos">%s</ol></div>' % (diamante(), leg), 'html.parser'))
            elif p.find('em') and p.find('strong') and re.match(r'\s*(LA DIFESA|L’ATTACCO|L\'ATTACCO)', t):
                card = regole_card(p)
                if card:
                    prev = p.find_previous_sibling()
                    nb = BeautifulSoup(card, 'html.parser')
                    if prev is not None and prev.name == 'div' and prev.find('figure') and not prev.get_text(strip=True):
                        f = prev.find('figure').extract()
                        f['class'] = ['rule-pic']
                        prev.decompose()
                        nb.find('h3').insert_before(f)
                    p.replace_with(nb)
            elif p.find('a') and 'fibs.it' in str(p) and len(t) < 80:
                a = p.find('a')
                a['class'] = ['btn', 'r']
                p['class'] = ['has-text-align-center']
        for f in sq.find_all('figure'):
            f['class'] = f.get('class', []) + ['pic']
        return nav + '<article class="essay rules">%s</article>' % str(sq)
    if path == 'baseball-2/al-cinema/':
        sq = BeautifulSoup(content, 'html.parser')
        kids = [k for k in sq.children if getattr(k, 'name', None)]
        out, films, i = [], [], 0
        while i < len(kids):
            k = kids[i]
            if k.name == 'div' and k.find('figure') and i + 1 < len(kids) and kids[i + 1].name == 'p':
                p = kids[i + 1]
                h = re.sub(r'<br/>\s*_{5,}\s*$', '', p.decode_contents().strip())
                h = re.sub(r'^<strong><strong>(.*?)</strong></strong>', r'<strong>\1</strong>', h)
                h = h.replace('</strong><strong>', '')
                m = re.match(r'\s*<strong>(.*?)</strong>\s*(?:–\s*)?(.*)', h, re.S)
                tit, txt = (m.group(1), m.group(2)) if m else ('', h)
                ym = re.search(r'(\d{4})\)?\s*$', re.sub(r'<.*?>', '', tit))
                a = k.find('a')
                img = k.find('img')
                poster = '<a class="poster" href="%s" target="_blank" rel="noopener"><img src="%s" alt="%s" loading="lazy"></a>' % (
                    a['href'] if a else '#', img['src'], e(re.sub(r'<.*?>', '', tit))) if img else ''
                films.append('<div class="film reveal">%s<div class="film-b">%s<h3>%s</h3><p>%s</p></div></div>' % (
                    poster, '<span class="yr">%s</span>' % ym.group(1) if ym else '', tit, txt))
                i += 2
                continue
            if films:
                out.append('<div class="films">%s</div>' % ''.join(films))
                films = []
            if k.name == 'p' and not out[1:]:
                k['class'] = ['lead-box']
            out.append(str(k))
            i += 1
        if films:
            out.append('<div class="films">%s</div>' % ''.join(films))
        return nav + ''.join(out)
    return nav + content if nav else content


def piazzamenti(content, root):
    """Elenco dei piazzamenti: stessi testi, una riga per anno con il collegamento alla scheda della stagione."""
    s = BeautifulSoup(content, 'html.parser')
    ul = s.find('ul')
    if not ul:
        return content
    rows = []
    for li in ul.find_all('li'):
        m = re.match(r'\s*(\d{4})\s*:\s*', li.get_text())
        if not m:
            rows.append('<div class="pz-row"><div class="pz-t">%s</div></div>' % li.decode_contents())
            continue
        y = m.group(1)
        hl = bool(li.find('strong'))
        for a in li.find_all('a'):
            a.unwrap()
        inner = re.sub(r'^((?:\s*<[^>]+>)*)\s*%s\s*:\s*' % y, r'\1', li.decode_contents(), count=1)
        PZ_TXT[y] = re.sub(r'^\s*\d{4}\s*:\s*', '', li.get_text()).strip()
        has = y in SEAS['stagioni']
        btn = ('<a class="pz-b" href="%s">Scheda stagione<span>rosa, classifica, statistiche</span></a>' % link(root, '%s%s/' % (PZ, y))
               if has and SEAS['stagioni'][y].get('rosa') else
               '<a class="pz-b" href="%s">Scheda stagione<span>classifica e risultati</span></a>' % link(root, '%s%s/' % (PZ, y))
               if has else '')
        rows.append('<div class="pz-row reveal%s" id="a%s"><div class="pz-y"><span class="sr">%s: </span><b aria-hidden="true">%s</b></div><div class="pz-t">%s</div>%s</div>' % (
            ' hl' if hl else '', y, y, y, inner, btn))
    ul.replace_with(BeautifulSoup('<div class="pz">%s</div><p class="src">Le schede delle stagioni usano i dati del sito FIBS, che pubblica le classifiche dal 2016 e rose e statistiche dal 2020. Per gli anni precedenti non ci sono dati ufficiali online.</p>' % ''.join(rows), 'html.parser'))
    return str(s)


def _tab(head, rows, cls=''):
    return '<div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
        ''.join(head), ''.join(rows))


def sea_out(st, root, y, lead, cols_all, ragazzi=False, rosa_club=''):
    """Contenuto di una scheda stagione: riepilogo, classifica, rosa, statistiche, partite."""
    fatte = [g for g in st['partite'] if 'puntiCasa' in g]
    v = sum(1 for g in fatte if (g['puntiCasa'] > g['puntiOspiti']) == noi(g['casa']))
    pf = sum(g['puntiCasa'] if noi(g['casa']) else g['puntiOspiti'] for g in fatte)
    ps = sum(g['puntiOspiti'] if noi(g['casa']) else g['puntiCasa'] for g in fatte)
    pos = next((r['pos'] for c in st['classifiche'][:1] for r in c['righe'] if r['noi']), '')
    box = ['<div><b>%s</b><span>%s</span></div>' % (a, b) for a, b in (
        (pos + 'º' if pos else '', 'posto nel girone'), (v, 'vittorie'), (len(fatte) - v, 'sconfitte'),
        (pf, 'punti segnati'), (ps, 'punti subiti')) if a != '']
    out = ['<div class="season-h">%s</div>' % ''.join(box)]
    if lead:
        out.append('<p class="sea-lead">%s</p>' % e(lead))
    sez = [('classifica', 'Classifica', bool(st['classifiche'])), ('rosa', 'Rosa', bool(st.get('rosa')) or bool(rosa_club)),
           ('statistiche', 'Statistiche', bool(st.get('statistiche'))), ('partite', 'Partite', bool(st['partite']))]
    out.append('<div class="tabs sea-nav">%s</div>' % ''.join(
        '<a class="chip" href="#%s">%s</a>' % (i, l) for i, l, ok in sez if ok))

    # classifica
    if st['classifiche']:
        out.append('<h2 id="classifica" class="has-text-align-center">Classifica</h2>')
        for i, c in enumerate(st['classifiche']):
            tit = re.sub(r'\s*-\s*NAZIONALE\s*$', '', c['titolo']).strip()
            m = re.match(r'(.*?)\s*-\s*TOSCANA$', tit)
            if m:
                tit = ('%s · Toscana' % m.group(1).replace('Toscana - ', '')).strip(' ·') if m.group(1) else 'Toscana'
                tit = re.sub(r'^([A-Z]) · ', r'Girone \1 · ', tit)
            elif ragazzi and re.match(r'Girone \d+$', tit):
                tit = 'Finali nazionali, %s' % tit.lower()
            lab = tit if (i == 0 or ragazzi) else ('Fase finale' if len(c['righe']) <= 2 else tit)
            rows = []
            for r in c['righe']:
                tot = r['v'] + r['p']
                rows.append('<tr%s><td class="n">%s</td><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%s</td></tr>' % (
                    ' class="me"' if r['noi'] else '', e(r['pos']), e(squadra(r['nome'] or r['sigla'])), r['v'], r['p'], tot,
                    ('%.3f' % (r['v'] / tot)).lstrip('0') if tot and r['v'] != tot else ('1.000' if tot else '–')))
            out.append('<div class="stand sea-stand"><h3>%s</h3>%s</div>' % (e(lab), _tab(
                ['<th class="n">#</th><th>Squadra</th><th class="n">V</th><th class="n">P</th><th class="n">G</th><th class="n">%</th>'], rows)))

    # rosa
    if ragazzi and st.get('rosa'):
        rows = ['<tr><td class="n">%s</td><td>%s</td><td>%s</td><td class="n">%s</td></tr>' % (
            e(g['n']), e(squadra(g['nome'])), e(g['ruolo']), e(g['bt'])) for g in st['rosa']]
        out.append('<h2 id="rosa" class="has-text-align-center">Rosa %s</h2><div class="pstats sea-t">%s' % (y, _tab(
            ['<th class="n">#</th><th>Giocatore</th><th>Ruolo</th><th class="n"><abbr title="Batte / Tira">B/T</abbr></th>'], rows)))
        if st.get('staff'):
            rows = ['<tr><td class="n">%s</td><td>%s</td><td>%s</td></tr>' % (e(g['n']), e(squadra(g['nome'])), e(g['ruolo'])) for g in st['staff']]
            out.append('<h3 class="has-text-align-center">Staff tecnico</h3>%s' % _tab(['<th class="n">#</th><th>Nome</th><th>Ruolo</th>'], rows))
        out.append('<p class="pstats-leg has-text-align-center">%d giocatori registrati sul sito FIBS.%s</p></div>' % (
            len(st['rosa']), (' ' + rosa_club) if rosa_club else ''))
    elif st.get('rosa'):
        rows = ['<tr><td class="n">%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td></tr>' % (
            e(g['n']), giocatore_link(root, g['nome']), e(g['ruolo']), e(g['bt']), e(g['anno'])) for g in st['rosa']]
        out.append('<h2 id="rosa" class="has-text-align-center">Rosa %s</h2><div class="pstats sea-t">%s' % (y, _tab(
            ['<th class="n">#</th><th>Giocatore</th><th>Ruolo</th><th class="n"><abbr title="Batte / Tira">B/T</abbr></th><th class="n">Anno di nascita</th>'], rows)))
        if st.get('staff'):
            rows = ['<tr><td class="n">%s</td><td>%s</td><td>%s</td></tr>' % (e(g['n']), e(g['nome']), e(g['ruolo'])) for g in st['staff']]
            out.append('<h3 class="has-text-align-center">Staff tecnico</h3>%s' % _tab(
                ['<th class="n">#</th><th>Nome</th><th>Ruolo</th>'], rows))
        out.append('<p class="pstats-leg has-text-align-center">%d giocatori registrati sul sito FIBS per questa stagione.%s</p></div>' % (
            len(st['rosa']), (' ' + rosa_club) if rosa_club else ''))
    elif ragazzi and rosa_club:
        out.append('<h2 id="rosa" class="has-text-align-center">Rosa %s</h2><p class="sea-no">La FIBS non pubblica la rosa di questa squadra. %s</p>' % (y, rosa_club))
    elif ragazzi:
        out.append('<h2 id="rosa" class="has-text-align-center">Rosa e statistiche</h2><p class="sea-no">Per i campionati regionali la FIBS non pubblica online né la rosa né le statistiche dei giocatori: ci sono solo classifica e risultati.</p>')
    else:
        out.append('<h2 id="rosa" class="has-text-align-center">Rosa e statistiche</h2><p class="sea-no">Per il %s la FIBS non pubblica online né la rosa né le statistiche dei giocatori: sul sito federale ci sono solo classifica e risultati.</p>' % y)

    # statistiche
    if st.get('statistiche'):
        tipi = [(k, l) for k, l in (('batting', 'Battuta'), ('pitching', 'Lancio'), ('fielding', 'Difesa')) if st['statistiche'].get(k)]
        out.append('<h2 id="statistiche" class="has-text-align-center">Statistiche %s</h2><div class="pstats sea-t"><div class="tabs" role="tablist">%s</div>' % (
            y, ''.join('<button class="chip%s" data-tab="%s">%s</button>' % ('' if i else ' on', k, l) for i, (k, l) in enumerate(tipi))))
        for i, (k, l) in enumerate(tipi):
            cols = cols_all[k]
            rows = ['<tr><td>%s</td>%s</tr>' % (e(squadra(r['nome'])) if ragazzi else giocatore_link(root, r['nome']), ''.join('<td class="n">%s</td>' % e(str(x)) for x in r['v']))
                    for r in st['statistiche'][k]]
            out.append('<div data-tabp="%s"%s>%s<p class="pstats-leg">%s</p></div>' % (k, ' hidden' if i else '', _tab(
                ['<th>Giocatore</th>'] + ['<th class="n"><abbr title="%s">%s</abbr></th>' % (e(d), e(c)) for c, d in cols], rows),
                ' · '.join('<b>%s</b> %s' % (e(c), e(d)) for c, d in cols)))
        out.append('</div>')

    # partite
    if st['partite']:
        out.append('<h2 id="partite" class="has-text-align-center">Partite</h2><div class="cal sea-cal">%s</div>' % partite_rows(st))
    return out


def partite_rows(st):
    if True:
        rows = []
        for g in st['partite']:
            d = g['data'].split('-')
            casa = noi(g['casa'])
            avv = squadra(g['ospiti'] if casa else g['casa'])
            t = '<div class="t">%s %s<small>%s%s</small></div>' % ('vs' if casa else '@', e(avv), 'In casa' if casa else 'In trasferta',
                                                                 (' · ' + e(g['campo'])) if g.get('campo') else '')
            dd = '<div class="d">%d %s<br>%s</div>' % (int(d[2]), MESI[int(d[1]) - 1][:3], e(g.get('ora') or ''))
            if 'puntiCasa' in g:
                a, b = (g['puntiCasa'], g['puntiOspiti']) if casa else (g['puntiOspiti'], g['puntiCasa'])
                w = a > b
                sc = '<div class="s">%d–%d<i>%s</i></div>' % (a, b, 'V' if w else 'P')
                if g.get('boxscore'):
                    rows.append('<a class="g-row %s" href="https://www.fibs.it/it/events/%s/schedule-and-results/box-score/%s" target="_blank" rel="noopener" title="Tabellino sul sito FIBS">%s%s%s</a>' % (
                        'w' if w else 'l', st['slug'], g['boxscore'], dd, t, sc))
                else:
                    rows.append('<div class="g-row %s">%s%s%s</div>' % ('w' if w else 'l', dd, t, sc))
            else:
                rows.append('<div class="g-row">%s%s<div class="s"><i>%s</i></div></div>' % (dd, t, e(g.get('nota') or 'non disputata')))
        return ''.join(rows)


def build_stagione(y, prima, dopo):
    st = SEAS['stagioni'][y]
    path = '%s%s/' % (PZ, y)
    root = '../' * path.count('/')
    out = sea_out(st, root, y, PZ_TXT.get(y), SEAS['colonne'])
    agg = st.get('aggiornato', '').split('-')
    out.append('<p class="src">%sFonte: <a href="%s" target="_blank" rel="noopener">sito FIBS, %s %s</a></p>' % (
        'Dati letti il %d/%d/%s. ' % (int(agg[2]), int(agg[1]), agg[0]) if len(agg) == 3 else '', e(st['fibs']), e(st['campionato']), y))
    nav = '<nav class="pn">%s%s</nav>' % (
        '<a class="prev" href="%s"><span>← Stagione precedente</span>%s</a>' % (link(root, '%s%s/' % (PZ, prima)), prima) if prima else '<span></span>',
        '<a class="next" href="%s"><span>Stagione successiva →</span>%s</a>' % (link(root, '%s%s/' % (PZ, dopo)), dopo) if dopo else '')
    news = [p for p in POSTS if p['date'][:4] == y][:6]
    extra = ''
    if news:
        extra = '<section class="alt"><div class="wrap"><div class="sh"><h2>Le notizie del %s</h2></div><div class="news-grid">%s</div></div></section>' % (
            y, ''.join(post_card(root, p) for p in news))
    title = 'Stagione %s' % y
    body = band(root, path, title, st['campionato']) + '<section class="body"><div class="wrap"><div class="content reveal">%s</div>%s<p class="back"><a class="btn n" href="%s">Tutti i piazzamenti</a></p></div></section>%s%s' % (
        ''.join(out), nav, link(root, PZ), extra, cta(root))
    shell(path, title + ' – ' + st['campionato'], body, desc='Lancers Baseball Club, stagione %s in %s: classifica, rosa, statistiche e risultati.' % (y, st['campionato']), cls='page wide')


_GV = os.path.join(ROOT, 'tools', 'giovanili.json')
GIOV = json.load(open(_GV, encoding='utf-8')) if os.path.exists(_GV) else {'stagioni': {}, 'colonne': {}}
GV = 'giovanili/stagioni/'


def rosa_club(root, cat, y):
    """Collegamento al roster pubblicato dalla società (pagine giovanili/under-12/ e under-15/), se è di quell'anno."""
    pth = {'u12': 'giovanili/under-12/', 'u15': 'giovanili/under-15/'}.get(cat)
    pg = PAGES.get(pth)
    if pg and re.search(r'\b%s\b' % y, BeautifulSoup(pg['html'], 'html.parser').get_text()):
        return 'La società ha pubblicato la <a href="%s">foto del roster %s %s</a>.' % (link(root, pth), CAT_NOMI[cat], y)
    return ''


CAT_NOMI = {'u12': 'Under 12', 'u15': 'Under 15', 'u18': 'Under 18'}


def build_giovanile(key, st, prima, dopo):
    path = '%s%s/' % (GV, key)
    root = '../' * path.count('/')
    y = str(st['anno'])
    if len(st.get('rosa', [])) < 9:      # rosa parziale sul sito FIBS (pochi nomi): meglio non mostrarla
        st = dict(st, rosa=[], staff=[])
    out = sea_out(st, root, y, '', GIOV['colonne'], ragazzi=True, rosa_club=rosa_club(root, st['categoria'], y))
    agg = st.get('aggiornato', '').split('-')
    out.append('<p class="src">%sFonte: <a href="%s" target="_blank" rel="noopener">sito FIBS, %s %s</a></p>' % (
        'Dati letti il %d/%d/%s. ' % (int(agg[2]), int(agg[1]), agg[0]) if len(agg) == 3 else '', e(st['fibs']), e(st['nome']), y))
    nm = lambda k: '%s %s' % (CAT_NOMI[GIOV['stagioni'][k]['categoria']], GIOV['stagioni'][k]['anno'])
    nav = '<nav class="pn">%s%s</nav>' % (
        '<a class="prev" href="%s"><span>← Stagione precedente</span>%s</a>' % (link(root, '%s%s/' % (GV, prima)), nm(prima)) if prima else '<span></span>',
        '<a class="next" href="%s"><span>Stagione successiva →</span>%s</a>' % (link(root, '%s%s/' % (GV, dopo)), nm(dopo)) if dopo else '')
    title = '%s %s' % (st['nome'], y)
    body = band(root, path, title, 'Settore giovanile') + '<section class="body"><div class="wrap"><div class="content reveal">%s</div>%s<p class="back"><a class="btn n" href="%s">Tutte le stagioni giovanili</a></p></div></section>%s' % (
        ''.join(out), nav, link(root, GV), cta(root))
    shell(path, title, body, desc='Lancers Baseball Club, %s stagione %s: classifica, partite e risultati.' % (st['nome'], y), cls='page wide')


def giov_elenco(root):
    """Riquadri di tutte le stagioni giovanili, per categoria."""
    out = []
    for cat in ('u12', 'u15', 'u18'):
        ks = sorted((k for k, v in GIOV['stagioni'].items() if v['categoria'] == cat), reverse=True)
        if not ks:
            continue
        cards = []
        for k in ks:
            st = GIOV['stagioni'][k]
            pos = next((r['pos'] for c in st['classifiche'][:1] for r in c['righe'] if r['noi']), '')
            naz = any('NAZIONALE' in c['titolo'] for c in st['classifiche'])
            fatte = [g for g in st['partite'] if 'puntiCasa' in g]
            v = sum(1 for g in fatte if (g['puntiCasa'] > g['puntiOspiti']) == noi(g['casa']))
            cards.append('<a class="gv-c reveal%s" href="%s"><b>%s</b><span>%s</span><em>%s</em></a>' % (
                ' hl' if naz else '', link(root, '%s%s/' % (GV, k)), st['anno'],
                ('%sº posto in Toscana' % pos) if pos else 'Campionato regionale',
                ('%d vittorie, %d sconfitte' % (v, len(fatte) - v) if fatte else '') + (' · finali nazionali' if naz else '')))
        out.append('<h2 class="has-text-align-center">%s</h2><div class="gv-g">%s</div>' % (CAT_NOMI[cat], ''.join(cards)))
    return ''.join(out)


def build_giovanili():
    ks = sorted(GIOV['stagioni'], key=lambda k: (k.split('-')[0], k.split('-')[1]))
    for i, k in enumerate(ks):
        c = k.split('-')[0]
        stessa = [x for x in ks if x.split('-')[0] == c]
        j = stessa.index(k)
        build_giovanile(k, GIOV['stagioni'][k], stessa[j - 1] if j else None, stessa[j + 1] if j + 1 < len(stessa) else None)
    if not ks:
        return
    path = GV
    root = '../' * path.count('/')
    content = ('<p class="sea-lead">Le stagioni delle squadre giovanili dei Lancers registrate sul sito FIBS: classifica, calendario e risultati di ogni anno.</p>'
               '<p class="has-text-align-center">Sul sito federale le squadre giovanili dei Lancers compaiono dal 2022. La rosa c\'è solo per le squadre arrivate alle finali nazionali; '
               'per i campionati regionali la FIBS pubblica classifica e risultati. In rosso le stagioni con le finali nazionali.</p>' + giov_elenco(root))
    body = band(root, path, 'Stagioni giovanili', 'Settore giovanile') + \
        '<section class="body"><div class="wrap"><div class="content reveal">%s</div><p class="back"><a class="btn n" href="%s">Settore giovanile</a></p></div></section>%s' % (
            content, link(root, 'giovanili/'), cta(root))
    shell(path, 'Stagioni giovanili', body, desc='Le stagioni delle squadre giovanili dei Lancers: Under 12, Under 15 e Under 18, con classifica e risultati.', cls='page wide')


def build_stagioni():
    anni = sorted(SEAS['stagioni'])
    for i, y in enumerate(anni):
        build_stagione(y, anni[i - 1] if i else None, anni[i + 1] if i + 1 < len(anni) else None)


def cta(root):
    return '''<a class="strip" href="%s"><img src="%simages/banner-prova-il-baseball.jpg" alt="Prova il baseball: corsi a partire da 6 anni. Scrivici!" loading="lazy"></a>''' % (
        link(root, 'gioca-anche-tu/'), root)


def build_post(i, p):
    path = p['path']
    root = '../' * path.count('/')
    cat = ' · '.join(c[0] for c in p['cats'])
    newer = POSTS[i - 1] if i > 0 else None
    older = POSTS[i + 1] if i + 1 < len(POSTS) else None
    nav = '<nav class="pn">%s%s</nav>' % (
        '<a class="prev" href="%s"><span>← Notizia precedente</span>%s</a>' % (link(root, older['path']), e(older['title'])) if older else '<span></span>',
        '<a class="next" href="%s"><span>Notizia successiva →</span>%s</a>' % (link(root, newer['path']), e(newer['title'])) if newer else '')
    body = '''<section class="band post-band"><div class="wrap narrow">%s<div class="kick">%s%s</div><h1>%s</h1></div></section>
<section class="body"><div class="wrap narrow"><article class="content reveal">%s</article>%s
<p class="back"><a class="btn n" href="%s">Tutte le notizie</a></p></div></section>%s''' % (
        crumbs(root, path), fdate(p['date']), ' · ' + e(cat) if cat else '', e(p['title']), resolve(p['html'], root),
        nav, link(root, 'notizie/'), cta(root))
    shell(path, p['title'], body, desc=p['excerpt'][:155], cls='page')


def build_news():
    path = 'notizie/'
    root = '../'
    cats = []
    for p in POSTS:
        for c in p['cats']:
            if tuple(c) not in cats:
                cats.append(tuple(c))
    count = {c[1]: sum(1 for p in POSTS if c[1] in [x[1] for x in p['cats']]) for c in cats}
    cats.sort(key=lambda c: -count[c[1]])
    chips = '<button class="chip on" data-cat="">Tutte</button>' + ''.join(
        '<button class="chip" data-cat="%s">%s</button>' % (c[1], e(c[0])) for c in cats)
    cards = ''.join(post_card(root, p, hidden=i >= 12) for i, p in enumerate(POSTS))
    body = band(root, path, 'Notizie') + '''<section class="body"><div class="wrap">
<div class="news-tools"><div class="chips" role="group" aria-label="Filtra per categoria">%s</div>
<input type="search" id="news-q" placeholder="Cerca nelle notizie…" aria-label="Cerca nelle notizie"></div>
<div class="news-grid" id="news">%s</div>
<p class="empty" hidden>Nessuna notizia trovata.</p>
<p class="more-w"><button class="btn n" id="news-more">Carica altre notizie</button></p>
</div></section>%s''' % (chips, cards, cta(root))
    shell(path, 'Notizie', body, cls='page')


CONTOUR = ('<svg class="contour" viewBox="0 0 1200 600" preserveAspectRatio="none" aria-hidden="true">%s</svg>' % ''.join(
    '<path d="M-50 %d C 200 %d, 380 %d, 600 %d S 1000 %d, 1250 %d"/>' % (y, y - 70 + i * 9, y + 60 - i * 7, y - 10, y + 50 - i * 5, y - 30)
    for i, y in enumerate(range(60, 600, 34))))


def ticker(txt, n=14):
    t = ''.join('<span>%s</span>' % txt for _ in range(n))
    return '<div class="ticker" aria-hidden="true"><div>%s%s</div></div>' % (t, t)


def final_card(root):
    """Ultima partita giocata in stile tabellone 'FINAL'."""
    L, games, table = _stagione()
    played = [g for g in games if g['played']]
    if not played:
        return ''
    g = played[-1]
    sig = lambda k: 'LAN' if k == 'LAN' else k
    righe = [(g['ospiti'], g['puntiOspiti']), (g['casa'], g['puntiCasa'])]
    rows = ''.join('<div class="fs-r%s"><span class="fs-k">%s</span><span class="fs-n">%s</span><b>%d</b></div>' % (
        ' me' if k == 'LAN' else '', e(sig(k)), e(L['squadre'].get(k, k)), p) for k, p in righe)
    d = g['when']
    href = (L['stagione']['boxscore'] + str(g['boxscore'])) if g.get('boxscore') else link(root, 'squadre-senior/risultati/')
    return ('<a class="poster final reveal" href="%s"%s><div class="pk">Ultima partita</div><div class="echo" aria-hidden="true"><i>Final</i><i>Final</i></div>'
            '<h3>Final</h3><div class="fs">%s</div><p class="fs-d">%s %d %s %d · %s%s</p><span class="more">%s →</span></a>') % (
        href, ' target="_blank" rel="noopener"' if g.get('boxscore') else '', rows, GIORNI[d.weekday()], d.day, MESI[d.month - 1], d.year,
        e(g['campo']), (' · ' + e(g['nota'])) if g.get('nota') else '', 'Tabellino FIBS' if g.get('boxscore') else 'Tutti i risultati')


def spotlight(root):
    """Due protagonisti della stagione: miglior battitore (media, almeno 40 turni) e lanciatore con più strikeout."""
    try:
        t = open(_D + 'data/statistiche.js', encoding='utf-8').read()
        S = json.loads(t[t.index('{'):t.rindex('}') + 1])
    except Exception:
        return ''
    col = {k: [c[0] for c in v] for k, v in S['colonne'].items()}
    anno = max((r['anno'] for p in S['giocatori'].values() for r in p.get('batting', []) if r.get('sq') == 'LAN'), default=None)
    if not anno:
        return ''

    def riga(p, k):
        return next((r['v'] for r in p.get(k, []) if r['anno'] == anno and r.get('sq') == 'LAN'), None)

    def foto(slug):
        m = GIOC.get(slug, {})
        pg = PAGES.get(m.get('pagina') or '')
        if pg and pg.get('thumb') and media_ok(pg['thumb']):
            return pg, root + 'media/t/' + pg['thumb'], m.get('nome', pg['title'])
        return None, '', ''
    cand_b, cand_p = [], []
    for slug, p in S['giocatori'].items():
        pg, im, nome = foto(slug)
        if not pg:
            continue
        b = riga(p, 'batting')
        if b and b[col['batting'].index('AB')] >= 40:
            cand_b.append((float(b[col['batting'].index('AVG')]), slug, pg, im, nome, b))
        q = riga(p, 'pitching')
        if q and q[col['pitching'].index('SO')]:
            cand_p.append((q[col['pitching'].index('SO')], slug, pg, im, nome, q))
    out = []
    if cand_b:
        avg, slug, pg, im, nome, b = max(cand_b)
        c = col['batting']
        out.append((pg, im, nome, 'Miglior media battuta', [(b[c.index('AVG')], 'Media'), (b[c.index('H')], 'Valide'), (b[c.index('RBI')], 'Punti battuti')]))
    if cand_p:
        so, slug, pg, im, nome, q = max(cand_p)
        c = col['pitching']
        if not out or out[0][0] is not pg:
            out.append((pg, im, nome, 'Più strikeout', [(q[c.index('SO')], 'Strikeout'), (q[c.index('IP')], 'Inning'), (q[c.index('ERA')], 'ERA')]))
    cards = []
    for pg, im, nome, lab, st in out:
        cog = nome.split()[0]
        cards.append(('<a class="spot reveal" href="%s"><span class="spot-im" style="background-image:url(%s)"></span>'
                      '<span class="spot-b"><span class="pk">%s · %s</span><span class="echo" aria-hidden="true"><i>%s</i><i>%s</i></span>'
                      '<strong>%s</strong><span class="spot-s">%s</span></span></a>') % (
            link(root, pg['path']), im, anno, e(lab), e(cog), e(cog), e(nome),
            ''.join('<span><b>%s</b><em>%s</em></span>' % (e(str(v)), e(k)) for v, k in st)))
    if not cards:
        return ''
    return ('<section class="h-sec"><div class="wrap"><div class="h-sh reveal"><span class="pk">Serie B %s</span><h2>I protagonisti</h2></div>'
            '<div class="spots">%s</div><p class="h-more"><a class="btn o" href="%s">Tutta la rosa</a></p></div></section>') % (
        anno, ''.join(cards), link(root, 'squadre-senior/serie-a2/'))


def build_home():
    root = ''
    news = ''.join(post_card(root, p, big=i == 0) for i, p in enumerate(POSTS[:3]))
    teams = [('Senior', 'Serie B', 'squadre-senior/', 'squadra-serie-b.jpg'),
             ('Giovanili', 'Under 15', 'giovanili/under-15/', 'squadra-under-15.jpg'),
             ('Giovanili', 'Under 12', 'giovanili/under-12/', 'squadra-under-12.jpg'),
             ('Senior', 'Amatori', 'squadre-senior/amatoriale/', 'squadra-amatori.jpg')]
    tm = ''.join('<a class="team reveal" href="%s" style="background-image:url(images/%s)"><div><span>%s</span><h3>%s</h3></div></a>'
                 % (link(root, p), im, k, t) for k, t, p, im in teams)
    quick = [('Prova il baseball', 'Corsi a partire da 6 anni', 'gioca-anche-tu/'),
             ('Orari allenamenti', 'Tutte le squadre, dalle giovanili alla Serie B', 'ballpark/orari-allenamenti/'),
             ('Dove siamo', 'Lancers Field, Porto di Mezzo, Lastra a Signa', 'ballpark/'),
             ('Dirette YouTube', 'Le partite in streaming sul nostro canale', LIVE)]
    ql = ''.join('<a href="%s"%s><b>%s</b><span>%s</span></a>' % (
        p if p.startswith('http') else link(root, p), ' target="_blank" rel="noopener"' if p.startswith('http') else '', t, d) for t, d, p in quick)
    years = 2026 - 1982
    seen, ph = set(), []
    for p in POSTS:
        for n in re.findall(r'(?:MEDIA|THUMB):([^"]+)', p['html']):
            if n not in seen and media_ok(n) and len(ph) < 10:
                seen.add(n)
                ph.append('<a href="media/%s" data-lb="%s"><img src="media/t/%s" alt="%s" loading="lazy"></a>' % (n, e(p['title']), n, e(p['title'])))
                break
    photos = ''.join(ph)
    L, games, table = _stagione()
    body = ("""<section class="h-hero">%(contour)s%(tick)s
<div class="wrap h-hero-in">
<div class="h-pre reveal">Benvenuti ai</div>
<h1 class="h-title reveal"><span class="sr">Lancers Baseball Club</span><span aria-hidden="true">Lancers</span></h1>
<div class="h-photo reveal"><img src="images/hero-squadra.jpg" alt="La prima squadra dei Lancers" fetchpriority="high"></div>
<p class="h-tag reveal">Baseball Club · Lastra a Signa · dal 1982</p>
<p class="h-lead reveal">Il sito ufficiale dei Lancieri di Lastra a Signa: prima squadra in Serie B, settore giovanile e un campo aperto a tutti.</p>
<p class="h-cta reveal"><a class="btn r" href="%(gioca)s">Gioca con noi</a><a class="btn o" href="%(ris)s">Calendario e classifica</a></p>
</div>%(tick)s</section>
<section class="h-sec h-game"><div class="wrap">
<div class="h-sh reveal"><span class="pk">%(stag)s · %(gir)s</span><h2>Gameday</h2><a class="more" href="%(ris)s">Calendario completo →</a></div>
<div class="h-grid">
<div class="poster season-p reveal"><div class="echo" aria-hidden="true"><i>Stagione</i><i>Stagione</i></div><div data-next-game></div></div>
%(final)s
<nav class="h-list reveal" aria-label="Collegamenti rapidi">%(ql)s</nav>
</div>
<div class="h-two">
<div class="reveal"><h3 class="mini-t">Ultimi risultati</h3><div data-results></div></div>
<div class="reveal"><h3 class="mini-t">Classifica</h3><div data-standings="mini"></div></div>
</div></div></section>
%(spot)s
<section class="h-sec h-alt"><div class="wrap">
<div class="h-sh reveal"><span class="pk">Dal club</span><h2>Ultime notizie</h2><a class="more" href="%(not)s">Tutte le notizie →</a></div>
<div class="news">%(news)s</div></div></section>
<section class="stats"><div class="wrap"><div class="st reveal"><b data-count="%(years)d">%(years)d</b><span>anni di storia</span></div>
<div class="st reveal"><b data-count="4">4</b><span>squadre in campo</span></div>
<div class="st reveal"><b data-count="6">6</b><span>anni: l’età per iniziare</span></div>
<div class="st reveal"><b data-count="%(np)d">%(np)d</b><span>notizie in archivio</span></div></div></section>
<section class="h-sec"><div class="wrap">
<div class="h-sh reveal"><span class="pk">Una famiglia, quattro squadre</span><h2>Le nostre squadre</h2></div>
<div class="teams">%(tm)s</div>
<div class="h-ban">
<a class="ban reveal" href="%(gioca)s"><span class="ban-k">Corsi da 6 anni in su</span><b>Prova<br>il baseball</b><span class="more">Vieni al campo →</span></a>
<a class="ban yt reveal" href="%(live)s" target="_blank" rel="noopener"><span class="ban-k">Sul nostro canale YouTube</span><b>Le partite<br>in diretta</b><span class="more">Guarda le dirette →</span></a>
</div></div></section>
<section class="h-sec h-alt"><div class="wrap">
<div class="h-sh reveal"><span class="pk">Foto e video</span><h2>Dal campo</h2><div class="social big" data-social="label"></div></div>
<div class="gallery-x strip-g">%(photos)s</div></div></section>
<div class="spons"><div class="wrap"><h2>I nostri sponsor</h2>
<a href="%(spons)s"><img src="images/banner-sponsor-cso.jpg" alt="CSO Costruzione Strumenti Oftalmici sostiene i Lancers" loading="lazy">
<img src="images/banner-sponsor-edilpoggianti.jpg" alt="Edilpoggianti sostiene i Lancers" loading="lazy">
<img src="images/banner-sponsor-panamed.jpg" alt="Panamed sostiene i Lancers" loading="lazy"></a>
<p><a class="btn o" href="%(diventa)s">Diventa nostro sponsor</a></p></div></div>""") % dict(
        contour=CONTOUR, tick=ticker('Lancers Baseball Club'), gioca=link(root, 'gioca-anche-tu/'), ris=link(root, 'squadre-senior/risultati/'),
        stag=e(L['stagione']['nome']), gir=e(L['stagione']['girone']), final=final_card(root), ql=ql, spot=spotlight(root),
        news=news, years=years, np=len(POSTS), tm=tm, live=LIVE, photos=photos, spons=link(root, 'societa/sponsor/'),
        diventa=link(root, 'societa/diventa-nostro-sponsor/'), **{'not': link(root, 'notizie/')})
    shell('', '', body, cls='home')


def build_404():
    body = band('', '', 'Pagina non trovata') + '<section class="body"><div class="wrap narrow"><p>La pagina che cerchi non esiste o è stata spostata.</p><p><a class="btn r" href="/sito-lancers-quello-nuovo/">Torna alla home</a></p></div></section>'
    shell('', 'Pagina non trovata', body, cls='page')
    os.replace(os.path.join(ROOT, 'index.html'), os.path.join(ROOT, '404.html'))
    s = open(os.path.join(ROOT, '404.html')).read()
    base = '/sito-lancers-quello-nuovo/'
    s = re.sub(r'(href|src)="(?!https?:|mailto:|tel:|#|/)', r'\1="' + base, s)
    open(os.path.join(ROOT, '404.html'), 'w').write(s)


build_404()
for p in D['pages']:
    build_page(p)
for i, p in enumerate(POSTS):
    build_post(i, p)
build_stagioni()
build_giovanili()
build_giocatori()
build_news()
build_home()
print('ok', len(D['pages']), 'pagine,', len(POSTS), 'notizie')
