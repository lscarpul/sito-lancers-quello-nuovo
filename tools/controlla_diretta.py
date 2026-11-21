"""Controlla se il canale YouTube dei Lancers è in diretta e scrive data/diretta.json.

Lo lancia ogni 5 minuti il workflow .github/workflows/diretta.yml (sui server di GitHub,
che possono raggiungere YouTube). Il file cambia solo quando la diretta inizia o finisce,
così il sito si ripubblica solo in quei momenti. Il sito mostra il pulsante "Guarda la diretta"
solo se data/diretta.json dice live: true.
"""
import json, os, re, sys, urllib.request, datetime as DT, html

CANALE = 'https://www.youtube.com/@LancersBC-nh4wu'
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'diretta.json')


def scarica(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
        'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
        'Cookie': 'CONSENT=YES+1; SOCS=CAI',
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')


def controlla():
    h = scarica(CANALE + '/live')
    can = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    vid = re.search(r'watch\?v=([\w-]{11})', can.group(1)) if can else None
    live = bool(vid) and '"isLiveNow":true' in h
    titolo = re.search(r'<meta name="title" content="([^"]*)"', h)
    return {
        'live': live,
        'url': 'https://www.youtube.com/watch?v=' + vid.group(1) if live else CANALE + '/live',
        'titolo': html.unescape(titolo.group(1)) if live and titolo else '',
    }


def main():
    try:
        vecchio = json.load(open(FILE))
    except Exception:
        vecchio = {}
    try:
        nuovo = controlla()
    except Exception as ex:
        print('controllo non riuscito:', ex)
        return 0  # al prossimo giro si riprova; il file resta com'è
    if nuovo['live'] == vecchio.get('live') and nuovo['url'] == vecchio.get('url'):
        print('nessun cambiamento:', 'in diretta' if nuovo['live'] else 'non in diretta')
        return 0
    nuovo['dal'] = DT.datetime.now(DT.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    json.dump(nuovo, open(FILE, 'w'), ensure_ascii=False, indent=2)
    print('aggiornato:', nuovo)
    return 0


if __name__ == '__main__':
    sys.exit(main())
