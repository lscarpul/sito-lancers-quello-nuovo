#!/usr/bin/env python3
"""Scarica dal sito FIBS le statistiche di carriera dei giocatori e scrive data/statistiche.js.

Uso: python3 tools/aggiorna_statistiche.py
Per ogni giocatore con una pagina in squadre-senior/serie-a2/ (link "Statistiche FIBS.IT" della scheda) e per
tutti quelli comparsi nelle stagioni di tools/stagioni.json (elenco salvato in tools/giocatori.json) ricava il codice giocatore e chiede alla FIBS le statistiche di ogni anno e campionato.
Se un giocatore non risponde restano i dati precedenti.
"""
import datetime
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'statistiche.js')
META = os.path.join(ROOT, 'tools', 'giocatori.json')
UA = 'LancersSite/1.0 (+https://lscarpul.github.io/sito-lancers-quello-nuovo/)'
PREFIX = 'squadre-senior/serie-a2/'
# colonne mostrate sul sito: (chiave FIBS, etichetta, descrizione)
COLONNE = {
    'batting': [('g', 'G', 'Partite'), ('ab', 'AB', 'Turni alla battuta'), ('r', 'R', 'Punti segnati'),
                ('h', 'H', 'Valide'), ('double', '2B', 'Doppi'), ('triple', '3B', 'Tripli'),
                ('hr', 'HR', 'Fuoricampo'), ('rbi', 'RBI', 'Punti battuti a casa'), ('bb', 'BB', 'Basi su ball'),
                ('so', 'SO', 'Strikeout'), ('sb', 'SB', 'Basi rubate'), ('avg', 'AVG', 'Media battuta'),
                ('obp', 'OBP', 'Percentuale arrivi in base'), ('slg', 'SLG', 'Media bombardieri'),
                ('ops', 'OPS', 'OBP + SLG')],
    'pitching': [('pitch_win', 'V', 'Vittorie'), ('pitch_loss', 'P', 'Sconfitte'), ('era', 'ERA', 'Media PGL'),
                 ('pitch_appear', 'G', 'Presenze'), ('pitch_gs', 'GS', 'Partenze'), ('pitch_save', 'SV', 'Salvezze'),
                 ('pitch_cg', 'CG', 'Partite complete'), ('pitch_ip', 'IP', 'Inning lanciati'),
                 ('pitch_h', 'H', 'Valide concesse'), ('pitch_r', 'R', 'Punti concessi'),
                 ('pitch_er', 'ER', 'Punti guadagnati'), ('pitch_bb', 'BB', 'Basi su ball'),
                 ('pitch_so', 'SO', 'Strikeout'), ('pitch_whip', 'WHIP', 'Basi concesse per inning'),
                 ('bavg', 'AVG', 'Media battuta avversari')],
    'fielding': [('field_g', 'G', 'Partite'), ('field_c', 'TC', 'Occasioni totali'), ('field_po', 'PO', 'Eliminazioni'),
                 ('field_a', 'A', 'Assistenze'), ('field_e', 'E', 'Errori'), ('fldp', 'FLD%', 'Media difesa'),
                 ('field_dp', 'DP', 'Doppi giochi')],
}
ORDINE = ['ITA-SERIE-A1-M-BB', 'ITA-SERIE-A-M-BB', 'ITA-SERIE-B-M-BB', 'ITA-SERIE-C-M-BB']


def get(url, as_json=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'it',
                                               'X-Requested-With': 'XMLHttpRequest'})
    for attesa in (20, 60, 0):          # la FIBS limita le richieste ravvicinate (errore 429)
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read().decode('utf-8', 'replace')
            break
        except urllib.error.HTTPError as ex:
            if ex.code != 429 or not attesa:
                raise
            time.sleep(attesa)
    time.sleep(1)
    return json.loads(data) if as_json else data


def giocatori():
    d = json.load(open(os.path.join(ROOT, 'tools', 'content.json'), encoding='utf-8'))
    out = []
    for p in d['pages']:
        if p['path'].startswith(PREFIX) and p['path'] != PREFIX:
            m = re.search(r'href="(https://www\.fibs\.it/[^"]*?/players/\d+)"', p['html'])
            if m:
                out.append((p['path'][len(PREFIX):].strip('/'), p['title'], m.group(1).replace('/en/', '/it/')))
    return out


def breve(nome):
    nome = re.sub(r'\s+Baseball$', '', nome.strip())
    return nome.replace('Coppa Italia Serie A Gold', 'Coppa Italia A').replace('Serie A Gold', 'Serie A') \
        .replace('Internal Team Italy', 'Nazionale')


def leggi(url, cache=None):
    page = get(url)
    m = re.search(r'data-filters="([^"]*)"\s+data-route="([^"]*)"', page)
    if not m:
        raise ValueError('pagina giocatore senza dati')
    filtri = json.loads(html.unescape(m.group(1)))
    route = html.unescape(m.group(2))
    pid = re.search(r'pId=(\d+)', route).group(1)
    if cache is not None and pid in cache:
        return cache[pid]
    w = re.search(r'href="(https://www\.wbsc\.org/[^"]*/player/[^"]+)"', page)
    cats = filtri.get('elementRS', {}).get('categories', [])
    cats.sort(key=lambda c: ORDINE.index(c['value']) if c['value'] in ORDINE else 99)
    res = {'pid': int(pid), 'fibs': url, 'wbsc': w.group(1) if w else '', 'batting': [], 'pitching': [], 'fielding': []}
    for c in cats:
        q = urllib.parse.urlencode({'tab': 'career', 'fedId': c.get('fedId', 2), 'eventCategory': c['value']})
        d = get('%s&%s' % (route, q), as_json=True)
        if not isinstance(d, dict):
            continue
        for tipo, cols in COLONNE.items():
            rows = d.get(tipo) or []
            for r in rows:
                if not any(r.get(k) not in (None, 0, '0', '-', '', '.000', '0.0', '0.00') for k, _, _ in cols):
                    continue
                res[tipo].append({'anno': r.get('year'), 'camp': breve(c['text']), 'sq': r.get('teamcode', ''),
                                  'v': [r.get(k, '') for k, _, _ in cols]})
            tot = (d.get('totalsRow') or {}).get(tipo)
            if isinstance(tot, dict) and len([x for x in res[tipo] if x['camp'] == breve(c['text'])]) > 1:
                res[tipo].append({'anno': 'Totale', 'camp': breve(c['text']), 'sq': '', 'tot': True,
                                  'v': [tot.get(k, '') for k, _, _ in cols]})
    for tipo in COLONNE:
        res[tipo].sort(key=lambda r: (1 if r.get('tot') else 0, -(r['anno'] if isinstance(r['anno'], int) else 0)))
    if cache is not None:
        cache[pid] = res
    return res


def titolo(n):
    n = re.sub(r'\s+', ' ', n).strip()
    return n.title() if n.upper() == n else n


def slugify(n):
    n = unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', n).strip('-')


def persone():
    """Tutti i giocatori comparsi nelle rose o nelle statistiche delle stagioni in tools/stagioni.json."""
    f = os.path.join(ROOT, 'tools', 'stagioni.json')
    if not os.path.exists(f):
        return {}
    out = {}
    for y, st in sorted(json.load(open(f, encoding='utf-8'))['stagioni'].items()):
        base = 'https://www.fibs.it/it/events/%s/teams/%s/players/' % (st['slug'], st['team'])
        for g in st.get('rosa', []):
            if g.get('pid'):
                q = out.setdefault(g['nome'].lower(), {'nome': titolo(g['nome']), 'stagioni': {}})
                q['stagioni'][y] = {'n': g['n'], 'ruolo': g['ruolo'], 'bt': g['bt'], 'rosa': True}
                q['nascita'] = g['anno']
                q['url'] = base + str(g['pid'])
        for rows in st.get('statistiche', {}).values():
            for r in rows:
                if r.get('pid'):
                    q = out.setdefault(r['nome'].lower(), {'nome': titolo(r['nome']), 'stagioni': {}})
                    q['stagioni'].setdefault(y, {'rosa': False})
                    q['stagioni'][y]['campo'] = True
                    q['url'] = base + str(r['pid'])
    return out


def main():
    old = {}
    if os.path.exists(OUT):
        m = re.search(r'window\.LANCERS_STATS\s*=\s*(\{.*\})\s*;?\s*$', open(OUT, encoding='utf-8').read(), re.S)
        old = json.loads(m.group(1)) if m else {}
    oldmeta = json.load(open(META, encoding='utf-8')) if os.path.exists(META) else {}
    players, meta, errori = dict(old.get('giocatori', {})), dict(oldmeta), 0
    cache, bypid = {}, {}

    def prendi(nome, url):
        r = leggi(url, cache)
        print('%-34s battuta %2d  lancio %2d  difesa %2d' % (nome, len(r['batting']), len(r['pitching']), len(r['fielding'])))
        return r

    # 1) giocatori con una scheda scritta dalla società (pagine in squadre-senior/serie-a2/)
    for slug, nome, url in giocatori():
        try:
            players[slug] = prendi(nome, url)
            bypid[players[slug]['pid']] = slug
            meta[slug] = {'nome': nome, 'pagina': PREFIX + slug + '/', 'pid': players[slug]['pid'],
                          'stagioni': meta.get(slug, {}).get('stagioni', {})}
        except Exception as ex:
            errori += 1
            print('%-34s ERRORE: %s' % (nome, ex))
    # 2) tutti gli altri giocatori delle stagioni registrate sul sito FIBS
    usati = set(meta)
    for q in sorted(persone().values(), key=lambda x: x['nome']):
        try:
            r = prendi(q['nome'], q['url'])
        except Exception as ex:
            errori += 1
            print('%-34s ERRORE: %s' % (q['nome'], ex))
            continue
        slug = bypid.get(r['pid'])
        if not slug:
            slug = next((k for k, v in meta.items() if v.get('pid') == r['pid']), None) or slugify(q['nome'])
            while slug in usati and meta.get(slug, {}).get('pid') != r['pid']:
                slug += '-2'
            bypid[r['pid']] = slug
            players[slug] = r
            meta[slug] = {'nome': q['nome'], 'pagina': '', 'pid': r['pid']}
        usati.add(slug)
        st = dict(meta[slug].get('stagioni') or {}) if bypid.get(r['pid']) and meta[slug].get('_visto') else {}
        st.update(q['stagioni'])
        meta[slug].update(stagioni=st, nascita=q.get('nascita', meta[slug].get('nascita', '')), nomeFibs=q['nome'], _visto=True)
        meta[slug].setdefault('alias', [])
        if q['nome'].lower() not in meta[slug]['alias']:
            meta[slug]['alias'].append(q['nome'].lower())
    for v in meta.values():
        v.pop('_visto', None)
    if not players:
        print('Nessuna statistica letta: dati non modificati.')
        return 1
    if meta != oldmeta:
        json.dump(meta, open(META, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
        print('Salvato tools/giocatori.json: ora lancia python3 tools/build.py')
    new = {'aggiornato': old.get('aggiornato', ''),
           'colonne': {t: [[l, d] for _, l, d in c] for t, c in COLONNE.items()}, 'giocatori': players}
    if new == old:
        print('Nessuna novità nelle statistiche.')
        return 0
    new['aggiornato'] = datetime.date.today().isoformat()
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('/* STATISTICHE DEI GIOCATORI – file generato da tools/aggiorna_statistiche.py leggendo il sito FIBS.\n'
                '   Non modificare a mano: viene riscritto a ogni aggiornamento. */\nwindow.LANCERS_STATS = '
                + json.dumps(new, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('Aggiornate le statistiche di %d giocatori (%d errori).' % (len(players), errori))
    return 0


if __name__ == '__main__':
    sys.exit(main())
