#!/usr/bin/env python3
"""Estrae i contenuti dal sito WordPress (HTML salvato in RAW) e scarica immagini e file.

Uso: python3 tools/extract.py RAW_DIR URLS_TXT
Produce tools/content.json, media/ (immagini) e files/ (pdf).
"""
import sys, os, re, json, hashlib, io, subprocess, concurrent.futures as cf
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup, Comment, NavigableString
from PIL import Image

RAW, URLS = sys.argv[1], sys.argv[2]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = 'https://lancersbaseballclub.com'
HOSTS = ('lancersbaseballclub.com', 'lancersbc.wordpress.com', 'lancersbc.files.wordpress.com')
urls = [u.rstrip('/') + '/' for u in open(URLS).read().split()]
POST_RE = re.compile(r'\.com/(\d{4})/(\d\d)/(\d\d)/([^/]+)/$')


def load(u):
    p = os.path.join(RAW, hashlib.md5(u.rstrip('/').encode()).hexdigest() + '.html')
    if not os.path.exists(p):
        p = os.path.join(RAW, hashlib.md5(u.encode()).hexdigest() + '.html')
    return BeautifulSoup(open(p, encoding='utf-8', errors='replace').read(), 'html.parser')


# ---------- mappa URL -> percorso locale ----------
local = {}      # path WP ("/societa/") -> percorso locale ("societa/")
byslug = {}
byid = {}
posts_meta = {}
for u in urls:
    path = urlparse(u).path
    m = POST_RE.search(u)
    if m:
        local[path] = 'notizie/%s/' % m.group(4)
    elif path != '/':
        local[path] = path.strip('/') + '/'
    else:
        local['/'] = ''
        continue
    byslug.setdefault(path.strip('/').split('/')[-1], local[path])

media = {}   # url originale -> nome file locale
files = {}


def media_name(orig):
    p = unquote(urlparse(orig).path)
    m = re.search(r'/(\d{4})/(\d\d)/([^/]+)$', p)
    base = ('%s-%s-%s' % m.groups()) if m else os.path.basename(p)
    base = re.sub(r'[^A-Za-z0-9._-]+', '-', base).lower()
    stem = os.path.splitext(base)[0]
    return stem + '.jpg'


def reg_media(src):
    if not src or src.startswith('data:'):
        return None
    if src.startswith('//'):
        src = 'https:' + src
    if src.startswith('/'):
        src = B + src
    pu = urlparse(src)
    if 'wp-content/uploads' not in pu.path and 'files.wordpress.com' not in pu.netloc:
        return None
    path = pu.path
    if pu.netloc == 'i0.wp.com' or re.match(r'i\d\.wp\.com', pu.netloc):
        path = '/' + path.split('/', 2)[2] if path.count('/') > 1 else path
    if 'files.wordpress.com' in pu.netloc:
        path = '/wp-content/uploads' + path
    orig = B + path
    if not re.search(r'\.(jpe?g|png|gif|webp)$', path, re.I):
        return None
    media.setdefault(orig, media_name(orig))
    return media[orig]


def reg_file(href):
    pu = urlparse(href)
    orig = B + pu.path
    name = re.sub(r'[^A-Za-z0-9._-]+', '-', os.path.basename(unquote(pu.path))).lower()
    files.setdefault(orig, name)
    return files[orig]


def b62(s):
    al = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    n = 0
    for c in s:
        n = n * 62 + al.index(c)
    return n


def fix_href(h):
    """Ritorna (tipo, valore): 'local' percorso dal root, 'ext' url, 'img' media, 'file' nome file."""
    h = h.strip()
    if re.match(r'^[\w.+-]+@[\w-]+\.[\w.-]+$', h):
        return 'ext', 'mailto:' + h
    if h.startswith(('mailto:', 'tel:', '#')):
        return 'ext', h
    if h.startswith('/'):
        h = B + h
    pu = urlparse(h)
    if pu.netloc == 'wp.me':
        m = re.match(r'/[pP]\w+-(\w+)$', pu.path)
        if m and b62(m.group(1)) in byid:
            return 'local', byid[b62(m.group(1))]
        return 'ext', h
    if pu.netloc.replace('www.', '') in HOSTS or re.match(r'i\d\.wp\.com', pu.netloc):
        path = pu.path
        if re.search(r'\.(jpe?g|png|gif|webp)$', path, re.I):
            n = reg_media(h)
            if n:
                return 'img', n
        if re.search(r'\.(pdf|docx?|xlsx?|zip|pptx?)$', path, re.I):
            return 'file', reg_file(h)
        p = path if path.endswith('/') else path + '/'
        if p in local:
            return 'local', local[p]
        m = re.match(r'/category/([^/]+)/', p)
        if m:
            return 'local', 'notizie/?cat=' + m.group(1)
        if p.startswith(('/tag/', '/author/')):
            return 'local', 'notizie/'
        slug = p.strip('/').split('/')[-1]
        if slug in byslug:
            return 'local', byslug[slug]
        if p == '/':
            return 'local', ''
        return 'ext', B + path
    return 'ext', h


KEEP_CLASS = {'alignleft', 'alignright', 'aligncenter', 'has-text-align-center', 'has-text-align-right'}


def clean(pc):
    for c in pc.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    for x in pc.select('#jp-post-flair,.sharedaddy,#comments,#respond,.post-navigation,script,style,template,'
                       'noscript,svg,.wp-block-spacer,.clear,.post_cat,.post_name,.post_meta,meta,link,.filedunder,'
                       '.jp-relatedposts,.wpcnt,.wp-block-jetpack-slideshow_button-prev,'
                       '.wp-block-jetpack-slideshow_button-next,.wp-block-jetpack-slideshow_button-pause,'
                       '.wp-block-jetpack-slideshow_pagination'):
        x.decompose()
    soup = BeautifulSoup('', 'html.parser')
    # moduli di contatto -> segnaposto
    for f in pc.select('.jetpack-contact-form-container, form.contact-form, div.wpcf7, form'):
        if f.parent is None:
            continue
        ph = soup.new_tag('div')
        ph['data-contact-form'] = '1'
        f.replace_with(ph)
    # emoji come immagini
    for im in pc.select('img.emoji, img.wp-smiley'):
        im.replace_with(im.get('alt', ''))
    # iframe
    for fr in pc.find_all('iframe'):
        src = fr.get('src') or fr.get('data-src') or ''
        if not re.search(r'youtube|vimeo|google\.com/maps', src):
            fr.decompose()
            continue
        if src.startswith('//'):
            src = 'https:' + src
        src = re.sub(r'\?.*$', '', src) if 'youtube' in src else src
        nf = soup.new_tag('iframe', src=src, loading='lazy', allowfullscreen='')
        nf['title'] = 'Video'
        w = soup.new_tag('div')
        w['class'] = 'embed'
        w.append(nf)
        top = fr
        while top.parent is not pc and top.parent is not None and top.parent.name in ('span', 'p', 'div', 'figure') \
                and len(top.parent.get_text(strip=True)) == 0 and len(top.parent.find_all('iframe')) == 1:
            top = top.parent
        top.replace_with(w)
    # slideshow jetpack
    for sl in pc.select('.wp-block-jetpack-slideshow'):
        box = soup.new_tag('div')
        box['class'] = 'slider'
        for im in sl.find_all('img'):
            n = reg_media(im.get('data-orig-file') or im.get('src') or im.get('data-src'))
            if n:
                fig = soup.new_tag('div')
                fig['class'] = 'slide'
                a = soup.new_tag('a', href='MEDIA:' + n)
                a['data-lb'] = ''
                a.append(soup.new_tag('img', src='MEDIA:' + n, alt='', loading='lazy'))
                fig.append(a)
                box.append(fig)
        sl.replace_with(box)
    # gallerie
    gal_sel = '.wp-block-gallery, .coblocks-gallery, .tiled-gallery, div.gallery, .wp-block-jetpack-tiled-gallery'
    for g in pc.select(gal_sel):
        if g.parent is None or g.find_parent(class_='gallery-x'):
            continue
        box = soup.new_tag('div')
        box['class'] = 'gallery-x'
        for im in g.find_all('img'):
            n = reg_media(im.get('data-orig-file') or im.get('src') or im.get('data-src'))
            if not n:
                continue
            cap = ''
            fc = im.find_parent('figure')
            if fc and fc.find('figcaption'):
                cap = fc.find('figcaption').get_text(' ', strip=True)
            a = soup.new_tag('a', href='MEDIA:' + n)
            a['data-lb'] = cap
            a.append(soup.new_tag('img', src='THUMB:' + n, alt=cap, loading='lazy'))
            box.append(a)
        g.replace_with(box)
    # didascalie classiche
    for cap in pc.select('div.wp-caption'):
        fig = soup.new_tag('figure')
        cls = [c for c in cap.get('class', []) if c in KEEP_CLASS]
        if cls:
            fig['class'] = cls
        t = cap.select_one('.wp-caption-text')
        txt = t.get_text(' ', strip=True) if t else ''
        if t:
            t.decompose()
        for ch in list(cap.children):
            fig.append(ch.extract())
        if txt:
            fc = soup.new_tag('figcaption')
            fc.string = txt
            fig.append(fc)
        cap.replace_with(fig)
    # immagini singole
    for im in pc.find_all('img'):
        if im.find_parent(class_=['gallery-x', 'slider']):
            continue
        n = reg_media(im.get('data-orig-file') or im.get('src') or im.get('data-src'))
        if not n:
            im.decompose()
            continue
        alt = im.get('alt', '')
        cls = [c for c in im.get('class', []) if c in KEEP_CLASS]
        small = False
        try:
            small = int(im.get('width', 9999)) < 200
        except ValueError:
            pass
        im.attrs = {'src': 'MEDIA:' + n, 'alt': alt, 'loading': 'lazy'}
        if cls:
            im['class'] = cls
        if small:
            im['class'] = im.get('class', []) + ['small']
        a = im.find_parent('a')
        if a is None:
            a = soup.new_tag('a', href='MEDIA:' + n)
            a['data-lb'] = ''
            im.wrap(a)
        else:
            kind, val = fix_href(a.get('href', ''))
            if kind == 'img' or (kind == 'ext' and val.startswith(B)) or kind == 'local' and 'attachment' in a.get('rel', []):
                a.attrs = {'href': 'MEDIA:' + n, 'data-lb': ''}
    # link
    for a in pc.find_all('a'):
        if a.has_attr('data-lb'):
            continue
        h = a.get('href')
        cls = a.get('class', [])
        if not h:
            a.unwrap()
            continue
        kind, val = fix_href(h)
        a.attrs = {}
        if kind == 'local':
            a['href'] = 'ROOT:' + val
        elif kind == 'img':
            a['href'] = 'MEDIA:' + val
            a['data-lb'] = ''
        elif kind == 'file':
            a['href'] = 'FILE:' + val
            a['class'] = ['download']
        else:
            a['href'] = val
            if val.startswith('http'):
                a['target'] = '_blank'
                a['rel'] = 'noopener'
        if 'wp-block-button__link' in cls:
            a['class'] = ['btn', 'r']
    # tabelle
    for t in pc.find_all('table'):
        t.attrs = {}
        rows = t.find_all('tr')
        if rows:
            cells = rows[0].find_all(['td', 'th'])
            if len(cells) > 2 and all(c.find('strong') or c.name == 'th' for c in cells):
                t['class'] = ['has-head']
        w = soup.new_tag('div')
        w['class'] = 'table-wrap'
        fig = t.find_parent('figure')
        target = fig if fig and 'wp-block-table' in fig.get('class', []) else t
        target.wrap(w)
        if target is not t:
            target.unwrap()
    # attributi e tag superflui
    for e in pc.find_all(True):
        if e.attrs is None:
            continue
        if e.name in ('span', 'font', 'o:p', 'center'):
            e.unwrap()
            continue
        if e.name == 'h1':
            e.name = 'h2'
        style = e.get('style', '') or ''
        keep = {}
        raw_cls = e.get('class', [])
        if isinstance(raw_cls, str):
            raw_cls = raw_cls.split()
        cls = [c for c in raw_cls if c in KEEP_CLASS or c in (
            'slider', 'slide', 'gallery-x', 'embed', 'table-wrap', 'btn', 'r', 'download', 'has-head', 'small',
            'wp-block-buttons', 'wp-block-columns', 'wp-block-column')]
        if re.search(r'text-align:\s*center', style) and 'has-text-align-center' not in cls:
            cls.append('has-text-align-center')
        for k in ('href', 'src', 'alt', 'loading', 'target', 'rel', 'data-lb', 'data-contact-form', 'allowfullscreen',
                  'title', 'colspan', 'rowspan'):
            if e.has_attr(k):
                keep[k] = e[k]
        if cls:
            keep['class'] = cls
        e.attrs = keep
    # pulizia blocchi vuoti
    for _ in range(3):
        for e in pc.find_all(['p', 'div', 'figure', 'h2', 'h3', 'h4', 'h5', 'li', 'ul', 'strong', 'em']):
            if e.attrs is None or getattr(e, 'decomposed', False):
                continue
            if e.attrs.get('data-contact-form') or e.find(['img', 'iframe', 'table']) or \
                    any(c in e.get('class', []) for c in ('slider', 'gallery-x', 'embed')):
                continue
            if not e.get_text(strip=True) and not e.find(attrs={'data-contact-form': True}):
                e.decompose()
    h = pc.decode_contents()
    h = re.sub(r'(<br\s*/?>\s*){3,}', '<br/><br/>', h)
    h = re.sub(r'\n\s*\n+', '\n', h).strip()
    return h


# ---------- primo passaggio: id ----------
soups = {}
for u in urls:
    s = load(u)
    soups[u] = s
    path = urlparse(u).path
    cls = ' '.join(s.body.get('class', [])) if s.body else ''
    m = re.search(r'(?:page-id|postid)-(\d+)', cls)
    if m and path in local:
        byid[int(m.group(1))] = local[path]

pages, posts = [], []
for u in urls:
    path = urlparse(u).path
    if path == '/':
        continue
    s = soups[u]
    pc = s.select_one('#post_content .primary-content')
    title = re.sub(r'\s+[–-]\s+Lancers Baseball Club 1982\s*$', '', s.title.get_text()).strip()
    m = POST_RE.search(u)
    if m:
        t = pc.select_one('time')
        date = (t.get('datetime') if t else '%s-%s-%s' % m.groups()[:3])[:10]
        cats = [(a.get_text(strip=True), a['href'].rstrip('/').split('/')[-1]) for a in pc.select('.post_cat a')]
        h1 = pc.select_one('.post_name')
        if h1:
            title = h1.get_text(' ', strip=True)
        body = pc.select_one('.post_text') or pc
        html = clean(body)
        text = re.sub(r'\s+', ' ', BeautifulSoup(html, 'html.parser').get_text(' ')).strip()
        im = re.search(r'(?:MEDIA|THUMB):([^"]+)', html)
        posts.append(dict(slug=m.group(4), path=local[path], title=title or 'Senza titolo', date=date, cats=cats,
                          html=html, excerpt=text[:190], thumb=im.group(1) if im else None, src=u))
    else:
        html = clean(pc)
        im = re.search(r'(?:MEDIA|THUMB):([^"]+)', html)
        pages.append(dict(path=local[path], title=title, html=html, thumb=im.group(1) if im else None, src=u))

posts.sort(key=lambda p: p['date'], reverse=True)
json.dump(dict(pages=pages, posts=posts), open(os.path.join(ROOT, 'tools', 'content.json'), 'w'),
          ensure_ascii=False, indent=1)
print(len(pages), 'pagine', len(posts), 'notizie', len(media), 'immagini', len(files), 'file')

# ---------- download ----------
os.makedirs(os.path.join(ROOT, 'media', 't'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'files'), exist_ok=True)


def get(url):
    r = subprocess.run(['curl', '-sS', '-L', '-m', '60', '--retry', '2', url], capture_output=True)
    return r.stdout if r.returncode == 0 else b''


def dl_media(item):
    orig, name = item
    full = os.path.join(ROOT, 'media', name)
    th = os.path.join(ROOT, 'media', 't', name)
    if os.path.exists(full) and os.path.exists(th):
        return None
    data = get(orig + '?w=1280')
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:
        return orig
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        bg = Image.new('RGB', im.size, 'white')
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert('RGB')
    im.thumbnail((1280, 1280))
    im.save(full, 'JPEG', quality=78, optimize=True)
    im.thumbnail((560, 560))
    im.save(th, 'JPEG', quality=72, optimize=True)
    return None


def dl_file(item):
    orig, name = item
    p = os.path.join(ROOT, 'files', name)
    if os.path.exists(p):
        return None
    data = get(orig)
    if len(data) < 500:
        return orig
    open(p, 'wb').write(data)
    return None


with cf.ThreadPoolExecutor(8) as ex:
    bad = [b for b in ex.map(dl_media, media.items()) if b]
    bad += [b for b in ex.map(dl_file, files.items()) if b]
json.dump(bad, open(os.path.join(ROOT, 'tools', 'missing.json'), 'w'), indent=1)
print('non scaricati:', len(bad))
