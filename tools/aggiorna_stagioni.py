#!/usr/bin/env python3
"""Scarica dal sito FIBS i dati delle stagioni passate (classifica, rosa, statistiche, partite)
e li salva in tools/stagioni.json, da cui tools/build.py genera le schede in societa/piazzamenti/<anno>/.

Uso: pip install beautifulsoup4 && python3 tools/aggiorna_stagioni.py [anno ...]
Senza argomenti scarica solo le stagioni che mancano e quella in corso; con gli anni riscarica quelli indicati.
La FIBS pubblica le classifiche dal 2016 e rose e statistiche dal 2020: prima non c'è niente da leggere.
"""
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aggiorna_fibs as F  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tools', 'stagioni.json')
UA = 'LancersSite/1.0 (+https://lscarpul.github.io/sito-lancers-quello-nuovo/)'
BASE = 'https://www.fibs.it/it/events/'
API = 'https://www.fibs.it/api/v1/stats/events/%s/index?section=players&stats-section=%s&team=%s&round=&split=&language=it'
# anno: (campionato sul sito FIBS, id della squadra in quel campionato, nome del campionato)
STAGIONI = {
    2016: ('2016-fibs-serie-b-baseball-maschile', 3660, 'Serie B'),
    2017: ('2017-fibs-serie-b-baseball-maschile', 5360, 'Serie B'),
    2018: ('2018-fibs-serie-b-baseball-maschile', 13808, 'Serie B'),
    2019: ('2019-fibs-serie-b-baseball-maschile', 15450, 'Serie B'),
    2020: ('2020-fibs-serie-a2-baseball-maschile', 2306, 'Serie A2'),
    2021: ('2021-fibs-serie-a-baseball-maschile', 19360, 'Serie A'),
    2022: ('2022-fibs-serie-b-baseball-maschile', 19926, 'Serie B'),
    2023: ('2023-serie-b-baseball', 23657, 'Serie B'),
    2024: ('2024-serie-b-baseball-2024', 28785, 'Serie B'),
    2025: ('2025-serie-b-baseball-2025', 34083, 'Serie B'),
    2026: ('2026-serie-b-baseball-2026', 39604, 'Serie B'),
}
COLONNE = {
    'batting': [('g', 'G', 'Partite'), ('ab', 'AB', 'Turni alla battuta'), ('r', 'R', 'Punti segnati'),
                ('h', 'H', 'Valide'), ('double', '2B', 'Doppi'), ('triple', '3B', 'Tripli'),
                ('hr', 'HR', 'Fuoricampo'), ('rbi', 'RBI', 'Punti battuti a casa'), ('bb', 'BB', 'Basi su ball'),
                ('so', 'SO', 'Strikeout'), ('sb', 'SB', 'Basi rubate'), ('avg', 'AVG', 'Media battuta'),
                ('obp', 'OBP', 'Percentuale arrivi in base'), ('slg', 'SLG', 'Media bombardieri'),
                ('ops', 'OPS', 'OBP + SLG')],
    'pitching': [('pitch_win', 'V', 'Vittorie'), ('pitch_loss', 'P', 'Sconfitte'), ('era', 'ERA', 'Media PGL'),
                 ('pitch_appear', 'G', 'Presenze'), ('pitch_gs', 'GS', 'Partenze'), ('pitch_save', 'SV', 'Salvezze'),
                 ('pitch_ip', 'IP', 'Inning lanciati'), ('pitch_h', 'H', 'Valide concesse'),
                 ('pitch_r', 'R', 'Punti concessi'), ('pitch_er', 'ER', 'Punti guadagnati'),
                 ('pitch_bb', 'BB', 'Basi su ball'), ('pitch_so', 'SO', 'Strikeout'),
                 ('pitch_whip', 'WHIP', 'Basi concesse per inning')],
    'fielding': [('field_g', 'G', 'Partite'), ('field_c', 'TC', 'Occasioni totali'), ('field_po', 'PO', 'Eliminazioni'),
                 ('field_a', 'A', 'Assistenze'), ('field_e', 'E', 'Errori'), ('fldp', 'FLD%', 'Media difesa'),
                 ('field_dp', 'DP', 'Doppi giochi')],
}


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'it',
                                               'X-Requested-With': 'XMLHttpRequest'})
    for attesa in (20, 60, 0):          # la FIBS limita le richieste ravvicinate (errore 429)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read().decode('utf-8', 'replace')
            break
        except urllib.error.HTTPError as ex:
            if ex.code != 429 or not attesa:
                raise
            time.sleep(attesa)
    time.sleep(1.5)
    return data


def txt(e):
    return re.sub(r'\s+', ' ', e.get_text(' ', strip=True)) if e else ''


def classifiche(slug, team):
    """Tutte le tabelle (girone, eventuali playoff) in cui compare la squadra."""
    s = BeautifulSoup(get('%s%s/standings' % (BASE, slug)), 'html.parser')
    out = []
    for tab in s.find_all('table'):
        if 'LANCERS' not in txt(tab).upper():
            continue
        rows = []
        for tr in tab.find_all('tr'):
            name = tr.select_one('.team-name')
            nums = [txt(td) for td in tr.find_all('td', class_='text-center')]
            if not name or len(nums) < 3:
                continue
            small = name.find('small')
            full = txt(small)
            if small:
                small.extract()
            rows.append({'pos': nums[0], 'sigla': txt(name), 'nome': full, 'v': int(nums[1]), 'p': int(nums[2]),
                         'noi': 'LANCERS' in full.upper()})
        tit = [txt(h) for h in (tab.find_previous(['h4', 'h5']), tab.find_previous(['h2', 'h3'])) if h]
        out.append({'titolo': tit[0] if tit else '', 'fase': tit[1] if len(tit) > 1 else '', 'righe': rows})
    return out


def partite(slug, team, extra=''):
    """Come aggiorna_fibs.partite, ma con i nomi interi (negli anni vecchi la FIBS non ha le sigle) e la fase."""
    s = BeautifulSoup(get('%s%s/calendars?team=%s%s' % (BASE, slug, team, extra)), 'html.parser')
    out = []
    for it in s.select('.schedule-item'):
        teams = it.select('.team-info')
        if len(teams) != 2:
            continue
        side = {}
        for t in teams:
            ps = [txt(x) for x in t.find_all('p') if not x.get('class')]
            side['casa' if 'local' in txt(t.select_one('.dugout')).lower() else 'ospiti'] = ps[0] if ps else txt(t.select_one('.code'))
        m = re.search(r'(\d\d)/(\d\d)/(\d{4})(?:,?\s+(\d\d:\d\d))?', txt(it))
        if set(side) != {'casa', 'ospiti'} or not m:
            continue
        g = {'data': '%s-%s-%s' % (m.group(3), m.group(2), m.group(1)), 'ora': m.group(4) or '',
             'casa': side['casa'], 'ospiti': side['ospiti']}
        f = re.search(r'#\S+\s+-\s+(.+)', txt(it.find('p')))
        g['fase'] = f.group(1).strip() if f else ''
        i = it.find('i')
        g['campo'] = F.citta(txt(i)) if i else ''
        lab = txt(it.select_one('.game-label'))
        sc = re.search(r'(\d+)\s*:\s*(\d+)', txt(it.select_one('.baseball-score-bug > div:not(.team-info)')))
        fin = re.match(r'(Finale|Final|F/(\d+))', lab)
        if fin and sc:
            g['puntiCasa'], g['puntiOspiti'] = int(sc.group(2)), int(sc.group(1))   # FIBS scrive ospiti : locali
            if fin.group(2):
                g['nota'] = fin.group(2) + ' inning'
            b = it.select_one('a.box-score-link[href*="box-score/"]')
            if b:
                g['boxscore'] = int(b['href'].rstrip('/').split('/')[-1])
        elif re.search(r'postpon|rinvia|sospes', lab, re.I):
            g['nota'] = 'rinviata'
        elif re.search(r'cancel|annull', lab, re.I):
            g['nota'] = 'annullata'
        out.append(g)
    out.sort(key=lambda g: (g['data'], g['ora']))
    return out


def rosa(slug, team):
    s = BeautifulSoup(get('%s%s/teams/%s' % (BASE, slug, team)), 'html.parser')
    gioc, staff = [], []
    for tab in s.find_all('table'):
        head = [txt(th) for th in tab.find_all('th')]
        for tr in tab.find_all('tr'):
            td = [txt(x) for x in tr.find_all('td')]
            if len(td) >= 5 and 'YOB' in head:
                gioc.append({'n': td[0], 'nome': td[1], 'ruolo': td[2], 'bt': td[3], 'anno': td[4]})
                a = tr.find('a', href=re.compile(r'/players/\d+$'))
                if a:
                    gioc[-1]['pid'] = int(a['href'].rsplit('/', 1)[-1])
            elif len(td) == 3 and 'YOB' not in head:
                staff.append({'n': td[0], 'nome': td[1], 'ruolo': td[2]})
    return gioc, staff


def nome(h):
    s = BeautifulSoup(h, 'html.parser')
    last, first = txt(s.select_one('.lastname')), txt(s.select_one('.firstname'))
    return ('%s %s' % (last.title(), first)).strip() if last else txt(s)


def fmt(k, v):
    if k in ('avg', 'slg', 'obp', 'ops', 'fldp') and isinstance(v, int):
        return ('%.3f' % (v / 1000.0)).replace('0.', '.', 1) if v < 1000 else '%.3f' % (v / 1000.0)
    if k in ('era', 'pitch_whip') and isinstance(v, (int, float)):
        return '%.2f' % v
    return v


def statistiche(slug, team):
    out = {}
    for tipo, cols in COLONNE.items():
        try:
            d = json.loads(get(API % (slug, tipo, team)))
        except Exception as ex:
            print('    statistiche %s: %s' % (tipo, ex))
            continue
        rows = [r for r in d.get('data', []) if str(r.get('teamid')) == str(team)]
        chiave = {'batting': 'ab', 'pitching': 'pitch_appear', 'fielding': 'field_g'}[tipo]
        rows = [r for r in rows if r.get(chiave) or (tipo == 'batting' and r.get('g'))]
        rows.sort(key=lambda r: nome(r.get('name', '')))
        if rows:
            out[tipo] = [{'nome': nome(r.get('name', '')), 'pid': int(str(r.get('link', '0')).rsplit('/', 1)[-1] or 0),
                          'v': [fmt(k, r.get(k, '')) for k, _, _ in cols]} for r in rows]
    return out


def stagione(anno):
    slug, team, camp = STAGIONI[anno]
    s = {'anno': anno, 'campionato': camp, 'slug': slug, 'team': team, 'fibs': '%s%s/calendars?team=%s' % (BASE, slug, team),
         'aggiornato': datetime.date.today().isoformat()}
    s['classifiche'] = classifiche(slug, team)
    try:
        s['partite'] = partite(slug, team)
    except Exception as ex:
        print('    partite: %s' % ex)
        s['partite'] = []
    try:
        s['rosa'], s['staff'] = rosa(slug, team)
    except Exception as ex:
        print('    rosa: %s' % ex)
        s['rosa'], s['staff'] = [], []
    s['statistiche'] = statistiche(slug, team) if s['rosa'] else {}
    return s


def main():
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    dati = dict(old.get('stagioni', {}))
    chiesti = [int(a) for a in sys.argv[1:]]
    oggi = datetime.date.today().year
    for anno in sorted(STAGIONI):
        if chiesti and anno not in chiesti:
            continue
        if not chiesti and str(anno) in dati and anno != oggi:
            continue
        try:
            s = stagione(anno)
        except Exception as ex:
            print('%d ERRORE: %s' % (anno, ex))
            continue
        v = dati.get(str(anno))
        if v and {k: x for k, x in v.items() if k != 'aggiornato'} == {k: x for k, x in s.items() if k != 'aggiornato'}:
            s['aggiornato'] = v['aggiornato']
        dati[str(anno)] = s
        print('%d  classifiche %d  partite %d  rosa %d  staff %d  statistiche %s' % (
            anno, len(s['classifiche']), len(s['partite']), len(s['rosa']), len(s['staff']),
            {k: len(x) for k, x in s['statistiche'].items()}))
    new = {'colonne': {t: [[l, d] for _, l, d in c] for t, c in COLONNE.items()}, 'stagioni': dati}
    if new != old:
        json.dump(new, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Salvato tools/stagioni.json: ora lancia python3 tools/build.py')
    else:
        print('Nessuna novità.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
