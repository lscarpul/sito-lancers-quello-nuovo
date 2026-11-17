#!/usr/bin/env python3
"""Scarica dal sito FIBS le stagioni delle squadre giovanili (U12, U15, U18): classifica, rosa, partite, statistiche.
Salva tutto in tools/giovanili.json, da cui tools/build.py genera le schede in giovanili/stagioni/<categoria>-<anno>/.

Uso: pip install beautifulsoup4 && python3 tools/aggiorna_giovanili.py [--tutte]
Senza argomenti riscarica solo l'anno in corso (e cerca da solo se i Lancers sono iscritti); con --tutte riscarica tutto.
Sul sito FIBS i Lancers compaiono nei campionati giovanili dal 2022: prima non ci sono dati.
"""
import datetime
import json
import os
import re
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aggiorna_stagioni as S  # noqa: E402

ROOT = S.ROOT
OUT = os.path.join(ROOT, 'tools', 'giovanili.json')
CATEGORIE = {'u12': 'Under 12', 'u15': 'Under 15', 'u18': 'Under 18'}
# campionato sul sito FIBS e id della squadra Lancers, trovati cercando "LANCERS" nelle classifiche di ogni edizione
NOTE = {
    ('u12', 2022): ('2022-fibs-u12-baseball-misti', 20669),
    ('u12', 2023): ('2023-u12-baseball-2023', 24346),
    ('u12', 2024): ('2024-u12-baseball-2024', 29297),
    ('u12', 2025): ('2025-u12-baseball-2025', 34721),
    ('u12', 2026): ('2026-u12-baseball-2026', 40273),
    ('u15', 2022): ('2022-fibs-u15-baseball-misti', 20619),
    ('u15', 2025): ('2025-u15-baseball-2025', 34719),
    ('u15', 2026): ('2026-u15-baseball-2026', 40275),
    ('u18', 2022): ('2022-fibs-u18-baseball-maschile', 20621),
    ('u18', 2023): ('2023-u18-baseball', 24348),
}
# come si chiamano i campionati degli anni nuovi
MODELLI = {'u12': '{y}-u12-baseball-{y}', 'u15': '{y}-u15-baseball-{y}', 'u18': '{y}-u18-baseball-{y}'}


def cerca(slug):
    """Id della squadra Lancers nelle classifiche di un campionato, o None."""
    try:
        s = BeautifulSoup(S.get('%s%s/standings' % (S.BASE, slug)), 'html.parser')
    except Exception:
        return None
    for tr in s.find_all('tr'):
        n = tr.select_one('.team-name')
        a = tr.find('a', href=re.compile(r'/teams/\d+$'))
        if n and a and 'LANCERS' in n.get_text().upper():
            return int(a['href'].rsplit('/', 1)[1])
    return None


def scarica(cat, anno, slug, team):
    s = {'categoria': cat, 'nome': CATEGORIE[cat], 'anno': anno, 'slug': slug, 'team': team,
         'fibs': '%s%s/teams/%s' % (S.BASE, slug, team), 'aggiornato': datetime.date.today().isoformat()}
    s['classifiche'] = S.classifiche(slug, team)
    # per le giovanili il calendario FIBS mostra le partite solo filtrando per comitato: Toscana (7) e nazionale (0)
    s['partite'], visti = [], set()
    for com in (7, 0):
        try:
            for g in S.partite(slug, team, '&committee=%d' % com):
                k = (g['data'], g['ora'], g['casa'], g['ospiti'])
                if k not in visti:
                    visti.add(k)
                    s['partite'].append(g)
        except Exception as ex:
            print('    partite: %s' % ex)
    s['partite'].sort(key=lambda g: (g['data'], g['ora']))
    try:
        s['rosa'], s['staff'] = S.rosa(slug, team)
    except Exception as ex:
        print('    rosa: %s' % ex)
        s['rosa'], s['staff'] = [], []
    for g in s['rosa']:          # sono ragazzi: niente anno di nascita né collegamenti alla scheda FIBS personale
        g.pop('anno', None)
        g.pop('pid', None)
    s['statistiche'] = S.statistiche(slug, team) if s['rosa'] else {}
    for rows in s['statistiche'].values():
        for r in rows:
            r.pop('pid', None)
    return s


def main():
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    dati = dict(old.get('stagioni', {}))
    y = datetime.date.today().year
    elenco = dict(NOTE)
    for k, v in old.get('trovate', {}).items():
        c, a = k.split('-')
        elenco[(c, int(a))] = tuple(v)
    for c, m in MODELLI.items():          # l'anno in corso: cerca da solo se i Lancers sono iscritti
        if (c, y) not in elenco:
            t = cerca(m.format(y=y))
            if t:
                elenco[(c, y)] = (m.format(y=y), t)
                print('Trovata nuova squadra: %s %d' % (CATEGORIE[c], y))
    tutte = '--tutte' in sys.argv
    for (c, a), (slug, team) in sorted(elenco.items()):
        key = '%s-%d' % (c, a)
        if not tutte and key in dati and a != y:
            continue
        try:
            s = scarica(c, a, slug, team)
        except Exception as ex:
            print('%s ERRORE: %s' % (key, ex))
            continue
        v = dati.get(key)
        if v and {k: x for k, x in v.items() if k != 'aggiornato'} == {k: x for k, x in s.items() if k != 'aggiornato'}:
            s['aggiornato'] = v['aggiornato']
        dati[key] = s
        print('%s  classifiche %d  partite %d  rosa %d  staff %d  statistiche %s' % (
            key, len(s['classifiche']), len(s['partite']), len(s['rosa']), len(s['staff']),
            {k: len(x) for k, x in s['statistiche'].items()}))
    new = {'colonne': {t: [[l, d] for _, l, d in col] for t, col in S.COLONNE.items()}, 'stagioni': dati,
           'trovate': {'%s-%d' % k: list(v) for k, v in elenco.items() if k not in NOTE}}
    if new != old:
        json.dump(new, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
        print('Salvato tools/giovanili.json: ora lancia python3 tools/build.py')
    else:
        print('Nessuna novità.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
