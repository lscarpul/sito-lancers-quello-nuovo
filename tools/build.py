#!/usr/bin/env python3
"""Genera il sito statico a partire da tools/content.json.  Uso: python3 tools/build.py"""
import os, re, json, html as H
from bs4 import BeautifulSoup

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
    ('Giovanili', 'giovanili/', [('Settore giovanile', 'giovanili/'), ('Under 15', 'giovanili/under-15/'),
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
<a class="logo" href="%sindex.html"><img src="%simages/logo-lancers.jpg" alt="Lancers Baseball Club 1982" width="122" height="76"></a>
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
<script src="%sdata/stagione.js"></script><script src="%sjs/main.js" defer></script>''' % (
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


def shell(path, title, body, desc='', cls=''):
    depth = path.count('/')
    root = '../' * depth
    full = (title + ' | Lancers Baseball Club 1982') if title else 'Lancers Baseball Club 1982 | Lastra a Signa'
    doc = '''<!doctype html>
<html lang="it" class="no-js"><head><script>document.documentElement.classList.remove("no-js")</script><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><meta name="description" content="%s">
<link rel="icon" href="%simages/logo-lancers.jpg"><link rel="stylesheet" href="%scss/style.css">
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
    open(out, 'w', encoding='utf-8').write(doc)
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
    if path == 'societa/piazzamenti/':
        content = piazzamenti(content, root)
        cls += ' wide'
    if 'gallery-x' in content or path.startswith('gallery') or path == 'shop/':
        cls += ' wide'
    if path == 'squadre-senior/risultati/':
        title = 'Calendario e classifica Serie B'
        content = re.sub(r'<p>\s*in costruzione\s*</p>', '', content)
        content = re.sub(r'<h2.*?</h2>', '', content, count=1, flags=re.S)
        content = ('<div data-season-head></div><div class="tabs" role="tablist"><button class="chip on" data-tab="cal">Calendario e risultati</button>'
                   '<button class="chip" data-tab="cls">Classifica</button></div>'
                   '<div data-tabp="cal"><div data-calendar></div></div>'
                   '<div data-tabp="cls" id="classifica" hidden><div data-standings></div></div>'
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


def build_stagione(y, prima, dopo):
    st = SEAS['stagioni'][y]
    path = '%s%s/' % (PZ, y)
    root = '../' * path.count('/')
    fatte = [g for g in st['partite'] if 'puntiCasa' in g]
    v = sum(1 for g in fatte if (g['puntiCasa'] > g['puntiOspiti']) == noi(g['casa']))
    pf = sum(g['puntiCasa'] if noi(g['casa']) else g['puntiOspiti'] for g in fatte)
    ps = sum(g['puntiOspiti'] if noi(g['casa']) else g['puntiCasa'] for g in fatte)
    pos = next((r['pos'] for c in st['classifiche'][:1] for r in c['righe'] if r['noi']), '')
    box = ['<div><b>%s</b><span>%s</span></div>' % (a, b) for a, b in (
        (pos + 'º' if pos else '', 'posto nel girone'), (v, 'vittorie'), (len(fatte) - v, 'sconfitte'),
        (pf, 'punti segnati'), (ps, 'punti subiti')) if a != '']
    out = ['<div class="season-h">%s</div>' % ''.join(box)]
    if PZ_TXT.get(y):
        out.append('<p class="sea-lead">%s</p>' % e(PZ_TXT[y]))
    sez = [('classifica', 'Classifica', bool(st['classifiche'])), ('rosa', 'Rosa', bool(st.get('rosa'))),
           ('statistiche', 'Statistiche', bool(st.get('statistiche'))), ('partite', 'Partite', bool(st['partite']))]
    out.append('<div class="tabs sea-nav">%s</div>' % ''.join(
        '<a class="chip" href="#%s">%s</a>' % (i, l) for i, l, ok in sez if ok))

    # classifica
    if st['classifiche']:
        out.append('<h2 id="classifica" class="has-text-align-center">Classifica</h2>')
        for i, c in enumerate(st['classifiche']):
            tit = re.sub(r'\s*-\s*NAZIONALE\s*$', '', c['titolo']).strip()
            lab = ('%s' % tit) if i == 0 else ('Fase finale' if len(c['righe']) <= 2 else tit)
            rows = []
            for r in c['righe']:
                tot = r['v'] + r['p']
                rows.append('<tr%s><td class="n">%s</td><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%s</td></tr>' % (
                    ' class="me"' if r['noi'] else '', e(r['pos']), e(squadra(r['nome'] or r['sigla'])), r['v'], r['p'], tot,
                    ('%.3f' % (r['v'] / tot)).lstrip('0') if tot and r['v'] != tot else ('1.000' if tot else '–')))
            out.append('<div class="stand sea-stand"><h3>%s</h3>%s</div>' % (e(lab), _tab(
                ['<th class="n">#</th><th>Squadra</th><th class="n">V</th><th class="n">P</th><th class="n">G</th><th class="n">%</th>'], rows)))

    # rosa
    if st.get('rosa'):
        rows = ['<tr><td class="n">%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td></tr>' % (
            e(g['n']), giocatore_link(root, g['nome']), e(g['ruolo']), e(g['bt']), e(g['anno'])) for g in st['rosa']]
        out.append('<h2 id="rosa" class="has-text-align-center">Rosa %s</h2><div class="pstats sea-t">%s' % (y, _tab(
            ['<th class="n">#</th><th>Giocatore</th><th>Ruolo</th><th class="n"><abbr title="Batte / Tira">B/T</abbr></th><th class="n">Anno di nascita</th>'], rows)))
        if st.get('staff'):
            rows = ['<tr><td class="n">%s</td><td>%s</td><td>%s</td></tr>' % (e(g['n']), e(g['nome']), e(g['ruolo'])) for g in st['staff']]
            out.append('<h3 class="has-text-align-center">Staff tecnico</h3>%s' % _tab(
                ['<th class="n">#</th><th>Nome</th><th>Ruolo</th>'], rows))
        out.append('<p class="pstats-leg has-text-align-center">%d giocatori registrati sul sito FIBS per questa stagione.</p></div>' % len(st['rosa']))
    else:
        out.append('<h2 id="rosa" class="has-text-align-center">Rosa e statistiche</h2><p class="sea-no">Per il %s la FIBS non pubblica online né la rosa né le statistiche dei giocatori: sul sito federale ci sono solo classifica e risultati.</p>' % y)

    # statistiche
    if st.get('statistiche'):
        tipi = [(k, l) for k, l in (('batting', 'Battuta'), ('pitching', 'Lancio'), ('fielding', 'Difesa')) if st['statistiche'].get(k)]
        out.append('<h2 id="statistiche" class="has-text-align-center">Statistiche %s</h2><div class="pstats sea-t"><div class="tabs" role="tablist">%s</div>' % (
            y, ''.join('<button class="chip%s" data-tab="%s">%s</button>' % ('' if i else ' on', k, l) for i, (k, l) in enumerate(tipi))))
        for i, (k, l) in enumerate(tipi):
            cols = SEAS['colonne'][k]
            rows = ['<tr><td>%s</td>%s</tr>' % (giocatore_link(root, r['nome']), ''.join('<td class="n">%s</td>' % e(str(x)) for x in r['v']))
                    for r in st['statistiche'][k]]
            out.append('<div data-tabp="%s"%s>%s<p class="pstats-leg">%s</p></div>' % (k, ' hidden' if i else '', _tab(
                ['<th>Giocatore</th>'] + ['<th class="n"><abbr title="%s">%s</abbr></th>' % (e(d), e(c)) for c, d in cols], rows),
                ' · '.join('<b>%s</b> %s' % (e(c), e(d)) for c, d in cols)))
        out.append('</div>')

    # partite
    if st['partite']:
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
        out.append('<h2 id="partite" class="has-text-align-center">Partite</h2><div class="cal sea-cal">%s</div>' % ''.join(rows))

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


def build_home():
    root = ''
    news = ''.join(post_card(root, p, big=i == 0) for i, p in enumerate(POSTS[:3]))
    teams = [('Senior', 'Serie B', 'squadre-senior/', 'squadra-serie-b.jpg'),
             ('Giovanili', 'Under 15', 'giovanili/under-15/', 'squadra-under-15.jpg'),
             ('Giovanili', 'Under 12', 'giovanili/under-12/', 'squadra-under-12.jpg'),
             ('Senior', 'Amatori', 'squadre-senior/amatoriale/', 'squadra-amatori.jpg')]
    tm = ''.join('<a class="team reveal" href="%s" style="background-image:url(images/%s)"><div><span>%s</span><h3>%s</h3></div></a>'
                 % (link(root, p), im, k, t) for k, t, p, im in teams)
    quick = [('Prova il baseball', 'Corsi a partire da 6 anni. Vieni al campo per un allenamento di prova.', 'Scopri come', 'gioca-anche-tu/'),
             ('Orari allenamenti', 'Giorni e orari di tutte le squadre, dalle giovanili alla Serie B.', 'Vedi gli orari', 'ballpark/orari-allenamenti/'),
             ('Dove siamo', 'Lancers Field, Porto di Mezzo, Lastra a Signa. Contatti e indicazioni.', 'Contatti', 'societa/contatti/')]
    qc = ''.join('<a class="card reveal" href="%s"><h3>%s</h3><p>%s</p><span class="more">%s →</span></a>' % (link(root, p), t, d, m)
                 for t, d, m, p in quick)
    years = 2026 - 1982
    seen, ph = set(), []
    for p in POSTS:
        for n in re.findall(r'(?:MEDIA|THUMB):([^"]+)', p['html']):
            if n not in seen and media_ok(n) and len(ph) < 10:
                seen.add(n)
                ph.append('<a href="media/%s" data-lb="%s"><img src="media/t/%s" alt="%s" loading="lazy"></a>' % (n, e(p['title']), n, e(p['title'])))
                break
    photos = ''.join(ph)
    body = '''<div class="hero"><div class="wrap">
<div class="kick">Lastra a Signa · dal 1982</div>
<h1>Lancers <span>Baseball</span> Club</h1>
<p>Il sito ufficiale dei Lancieri di Lastra a Signa: prima squadra in Serie B, settore giovanile e un campo aperto a tutti.</p>
<a class="btn r" href="%s">Gioca con noi</a><a class="btn o" href="%s">Calendario e classifica</a>
</div></div>
<div class="wrap"><div class="quick">%s</div></div>
<section><div class="wrap">
<div class="sh"><h2>Ultime notizie</h2><a class="more" href="%s">Tutte le notizie →</a></div>
<div class="news">%s</div></div></section>
<section class="season alt"><div class="wrap">
<div class="sh"><h2>La stagione</h2><a class="more" href="%s">Calendario completo →</a></div>
<div class="season-g"><div class="reveal" data-next-game></div><div class="reveal"><h3 class="mini-t">Ultimi risultati</h3><div data-results></div></div>
<div class="reveal"><h3 class="mini-t">Classifica</h3><div data-standings="mini"></div></div></div></div></section>
<section class="stats"><div class="wrap"><div class="st reveal"><b data-count="%d">%d</b><span>anni di storia</span></div>
<div class="st reveal"><b data-count="4">4</b><span>squadre in campo</span></div>
<div class="st reveal"><b data-count="6">6</b><span>anni: l’età per iniziare</span></div>
<div class="st reveal"><b data-count="%d">%d</b><span>notizie in archivio</span></div></div></section>
%s
<section><div class="wrap">
<div class="sh"><h2>Le nostre squadre</h2></div>
<div class="teams">%s</div></div></section>
<section class="alt"><div class="wrap">
<div class="sh"><h2>Dal campo</h2><div class="social big" data-social="label"></div></div>
<div class="gallery-x strip-g">%s</div></div></section>
<div class="spons"><div class="wrap"><h2>I nostri sponsor</h2>
<a href="%s"><img src="images/banner-sponsor-cso.jpg" alt="CSO Costruzione Strumenti Oftalmici sostiene i Lancers" loading="lazy">
<img src="images/banner-sponsor-edilpoggianti.jpg" alt="Edilpoggianti sostiene i Lancers" loading="lazy">
<img src="images/banner-sponsor-panamed.jpg" alt="Panamed sostiene i Lancers" loading="lazy"></a>
<p><a class="btn o" href="%s">Diventa nostro sponsor</a></p></div></div>''' % (
        link(root, 'gioca-anche-tu/'), link(root, 'squadre-senior/risultati/'), qc, link(root, 'notizie/'), news,
        link(root, 'squadre-senior/risultati/'),
        years, years, len(POSTS), len(POSTS), cta(root), tm, photos, link(root, 'societa/sponsor/'),
        link(root, 'societa/diventa-nostro-sponsor/'))
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
build_giocatori()
build_news()
build_home()
print('ok', len(D['pages']), 'pagine,', len(POSTS), 'notizie')
