#!/usr/bin/env python3
"""Aggiorna data/stagione.js leggendo calendario, risultati e classifica dal sito FIBS.

Uso: pip install beautifulsoup4 && python3 tools/aggiorna_fibs.py
Nota: il sito FIBS rifiuta le richieste che arrivano dai server di GitHub Actions (errore 403),
quindi lo script va lanciato da un computer o da un'attività programmata esterna a GitHub.

Cerca da solo il campionato dell'anno in corso (poi quello precedente) in cui gioca la squadra.
Se il sito FIBS non risponde o cambia struttura, il file dei dati NON viene toccato.
"""
import datetime
import json
import os
import re
import sys
import urllib.request

from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'stagione.js')
BASE = 'https://www.fibs.it/it/events/'
CLUB = 'LANCERS'            # testo cercato nel nome della squadra sul sito FIBS
# campionati provati in ordine per ogni anno; {y} = anno
EVENTI = ['{y}-serie-b-baseball-{y}', '{y}-serie-a-baseball-{y}', '{y}-serie-c-baseball-{y}']
NOMI = {'serie-a': 'Serie A', 'serie-b': 'Serie B', 'serie-c': 'Serie C'}
BREVI = {'LAN': 'Lancers', 'LON': 'Longbridge Bologna', 'PAU': 'Padule Sesto F.no', 'PCR': 'Cali Roma',
         'HLP': 'Etruscan Fighters', 'COL': 'Colorno', 'LIV': 'Livorno 1948', 'BSA': 'Arezzo'}

HEAD = '''/* DATI DELLA STAGIONE
   Calendario, risultati e classifica sono aggiornati IN AUTOMATICO dal sito FIBS (tools/aggiorna_fibs.py):
   le modifiche fatte a mano a "partite" e "classifica" vengono sovrascritte.
   Si modificano a mano solo:
   - social: incolla qui i link di Facebook e Instagram (lascia "" per nasconderli);
   - squadre: il nome breve mostrato sul sito per ogni sigla. */
window.LANCERS = '''


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'LancersSite/1.0 (+https://lscarpul.github.io/sito-lancers-quello-nuovo/)',
                                               'Accept-Language': 'it'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return BeautifulSoup(r.read().decode('utf-8', 'replace'), 'html.parser')


def txt(e):
    return re.sub(r'\s+', ' ', e.get_text(' ', strip=True)) if e else ''


def citta(s):
    s = s.strip().rstrip(':').title()
    return re.sub(r"\b(A|Di|Della|Del|Dei|In|Sul|Al|Da|De)\b", lambda m: m.group(1).lower(), s) if ' ' in s else s


def breve(code, nome, old):
    if code in old:
        return old[code]
    if code in BREVI:
        return BREVI[code]
    n = re.sub(r'\b(A\.?S\.?D\.?|B\.?C\.?|S\.?C\.?|BASEBALL|SOFTBALL|CLUB|POLISPORTIVA|\*+)\b', ' ', nome, flags=re.I)
    n = re.sub(r'[*.]', ' ', n)
    return re.sub(r'\s+', ' ', n).strip().title() or code


def partite(slug, team):
    s = get('%s%s/calendars?team=%s' % (BASE, slug, team))
    out, nomi = [], {}
    for it in s.select('.schedule-item'):
        teams = it.select('.team-info')
        if len(teams) != 2:
            continue
        side = {}
        for t in teams:
            code = txt(t.select_one('.code'))
            ps = [txt(p) for p in t.find_all('p') if not p.get('class')]
            nomi[code] = ps[0] if ps else code
            side['casa' if 'local' in txt(t.select_one('.dugout')).lower() else 'ospiti'] = code
        if set(side) != {'casa', 'ospiti'}:
            continue
        m = re.search(r'(\d\d)/(\d\d)/(\d{4})(?:,?\s+(\d\d:\d\d|--:--))?', txt(it))
        if not m:
            continue
        g = {'data': '%s-%s-%s' % (m.group(3), m.group(2), m.group(1)),
             'ora': m.group(4) if m.group(4) and m.group(4)[0] != '-' else 'gara 2',
             'casa': side['casa'], 'ospiti': side['ospiti']}
        i = it.find('i')
        g['campo'] = citta(txt(i)) if i else ''
        lab = txt(it.select_one('.game-label'))
        sc = re.search(r'(\d+)\s*:\s*(\d+)', txt(it.select_one('.baseball-score-bug > div:not(.team-info)')))
        fin = re.match(r'(Finale|Final|F/(\d+))', lab)
        if fin and sc:
            g['puntiCasa'], g['puntiOspiti'] = int(sc.group(2)), int(sc.group(1))   # FIBS scrive ospiti : locali
            if fin.group(2):
                g['nota'] = fin.group(2) + ' inning'
            a = it.select_one('a.box-score-link[href*="box-score/"]')
            if a:
                g['boxscore'] = int(a['href'].rstrip('/').split('/')[-1])
        elif re.search(r'postpon|rinvia|sospes', lab, re.I):
            g['nota'] = 'rinviata'
        elif re.search(r'cancel|annull', lab, re.I):
            g['nota'] = 'annullata'
        out.append(g)
    out.sort(key=lambda g: (g['data'], g['ora'] == 'gara 2', g['ora']))
    return out, nomi


def classifica(slug, team):
    s = get('%s%s/standings' % (BASE, slug))
    for tab in s.find_all('table'):
        if not tab.find('a', href=re.compile(r'/teams/%s$' % team)):
            continue
        rows, nomi = [], {}
        for tr in tab.find_all('tr'):
            name = tr.select_one('.team-name')
            nums = [txt(td) for td in tr.find_all('td', class_='text-center')]
            if not name or len(nums) < 3:
                continue
            small = name.find('small')
            full = txt(small)
            if small:
                small.extract()
            code = txt(name)
            nomi[code] = full
            rows.append({'squadra': code, 'v': int(nums[1]), 'p': int(nums[2])})
        girone = ''
        h = tab.find_previous(['h2', 'h3', 'h4', 'h5'])
        if h:
            m = re.search(r'Girone\s+\w+', txt(h), re.I)
            girone = m.group(0).title() if m else ''
        return rows, nomi, girone
    return [], {}, ''


def trova():
    y = datetime.date.today().year
    for anno in (y, y - 1):
        for tpl in EVENTI:
            slug = tpl.format(y=anno)
            try:
                s = get('%s%s/calendars' % (BASE, slug))
            except Exception as ex:     # campionato inesistente o non ancora pubblicato
                print('  %s: %s' % (slug, ex))
                continue
            opt = [o for o in s.select('select option') if CLUB in txt(o).upper() and o.get('value', '').isdigit()]
            if not opt:
                continue
            team = opt[0]['value']
            games, nomi = partite(slug, team)
            if games:
                return slug, team, games, nomi
    return None


def main():
    old = {}
    if os.path.exists(OUT):
        m = re.search(r'window\.LANCERS\s*=\s*(\{.*\})\s*;?\s*$', open(OUT, encoding='utf-8').read(), re.S)
        old = json.loads(m.group(1)) if m else {}
    found = trova()
    if not found:
        print('Nessun calendario trovato sul sito FIBS: dati non modificati.')
        return 1
    slug, team, games, nomi = found
    rows, nomi2, girone = classifica(slug, team)
    nomi.update(nomi2)
    if not girone:
        girone = old.get('stagione', {}).get('girone', '')
    key = next((k for k in NOMI if k in slug), '')
    stag = {'nome': '%s %s' % (NOMI.get(key, 'Campionato'), slug[:4]), 'girone': girone,
            'aggiornato': old.get('stagione', {}).get('aggiornato', ''),
            'fonte': '%s%s/standings' % (BASE, slug),
            'calendarioFibs': '%s%s/calendars?team=%s' % (BASE, slug, team),
            'boxscore': '%s%s/schedule-and-results/box-score/' % (BASE, slug)}
    vecchi = old.get('squadre', {})
    codes = []
    for c in [r['squadra'] for r in rows] + [g[k] for g in games for k in ('casa', 'ospiti')]:
        if c not in codes:
            codes.append(c)
    new = {'social': old.get('social', {'facebook': '', 'instagram': '', 'youtube': ''}), 'stagione': stag,
           'squadre': {c: breve(c, nomi.get(c, c), vecchi) for c in codes},
           'classifica': rows or old.get('classifica', []), 'partite': games}
    if new == old and open(OUT, encoding='utf-8').read().startswith(HEAD):
        print('Nessuna novità: %d partite, %d squadre in classifica.' % (len(games), len(rows)))
        return 0
    if new != old:
        new['stagione']['aggiornato'] = datetime.date.today().isoformat()
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(HEAD + json.dumps(new, ensure_ascii=False, indent=2) + ';\n')
    print('Aggiornato: %s, %d partite, %d squadre in classifica.' % (slug, len(games), len(rows)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
