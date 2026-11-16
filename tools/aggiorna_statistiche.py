#!/usr/bin/env python3
"""Scarica dal sito FIBS le statistiche di carriera dei giocatori e scrive data/statistiche.js.

Uso: python3 tools/aggiorna_statistiche.py
Per ogni giocatore con una pagina in squadre-senior/serie-a2/ usa il link "Statistiche FIBS.IT"
della sua scheda, ricava il codice giocatore e chiede alla FIBS le statistiche di ogni anno e campionato.
Se un giocatore non risponde restano i dati precedenti.
"""
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'statistiche.js')
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


def leggi(url):
    page = get(url)
    m = re.search(r'data-filters="([^"]*)"\s+data-route="([^"]*)"', page)
    if not m:
        raise ValueError('pagina giocatore senza dati')
    filtri = json.loads(html.unescape(m.group(1)))
    route = html.unescape(m.group(2))
    pid = re.search(r'pId=(\d+)', route).group(1)
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
    return res


def main():
    old = {}
    if os.path.exists(OUT):
        m = re.search(r'window\.LANCERS_STATS\s*=\s*(\{.*\})\s*;?\s*$', open(OUT, encoding='utf-8').read(), re.S)
        old = json.loads(m.group(1)) if m else {}
    players, errori = dict(old.get('giocatori', {})), 0
    for slug, nome, url in giocatori():
        try:
            players[slug] = leggi(url)
            p = players[slug]
            print('%-28s battuta %2d  lancio %2d  difesa %2d' % (nome, len(p['batting']), len(p['pitching']), len(p['fielding'])))
        except Exception as ex:
            errori += 1
            print('%-28s ERRORE: %s' % (nome, ex))
    if not players:
        print('Nessuna statistica letta: dati non modificati.')
        return 1
    new = {'aggiornato': old.get('aggiornato', ''),
           'colonne': {t: [[l, d] for _, l, d in c] for t, c in COLONNE.items()}, 'giocatori': players}
    if new == old:
        print('Nessuna novità.')
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
