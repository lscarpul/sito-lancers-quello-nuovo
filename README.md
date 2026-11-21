# Lancers Baseball Club 1982 – nuovo sito

Proposta di restyling del sito ufficiale (lancersbaseballclub.com), sito statico senza dipendenze.

Anteprima: https://lscarpul.github.io/sito-lancers-quello-nuovo/

- `index.html` e le cartelle delle sezioni (`societa/`, `squadre-senior/`, `giovanili/`, `ballpark/`, `gallery/`, `notizie/` ...): pagine generate
- `css/style.css`, `js/main.js`: stile e interazioni (menu mobile, lightbox, slider, filtri notizie)
- `images/`: grafica del sito, `media/`: foto dei contenuti, `files/`: PDF scaricabili
- `tools/`: `extract.py` estrae i contenuti dal sito WordPress in `content.json`; `build.py` rigenera tutte le pagine

Per cambiare menu, footer o layout: modificare `tools/build.py` e lanciare `python3 tools/build.py`.

## Aggiornare calendario, risultati, classifica e social

Calendario, risultati e classifica si aggiornano da soli dal sito FIBS (`tools/aggiorna_fibs.py`, lanciato da un'attività programmata di Claude due volte a settimana; GitHub Actions non si può usare perché la FIBS ne blocca i server. In `data/stagione.js` si modificano a mano solo i link social e i nomi brevi delle squadre. `build.py` scrive calendario, risultati e classifica direttamente nell'HTML (homepage e Calendario e classifica Serie B), quindi dopo ogni cambio di `data/stagione.js` va rilanciato.
La prossima partita e il conto alla rovescia compaiono in homepage quando c'è una partita futura senza punteggio.

## Statistiche dei giocatori

`python3 tools/aggiorna_statistiche.py` legge dal sito FIBS le statistiche di carriera (battuta, lancio, difesa) di ogni giocatore che ha una scheda in `squadre-senior/serie-a2/` e riscrive `data/statistiche.js`. Le tabelle nelle schede sono disegnate da `js/main.js`.

## Schede delle stagioni (Piazzamenti)

`python3 tools/aggiorna_stagioni.py` legge dal sito FIBS classifica, rosa, statistiche e partite di ogni stagione dal 2016 (rose e statistiche esistono solo dal 2020) e le salva in `tools/stagioni.json`. Poi `python3 tools/build.py` genera le schede in `societa/piazzamenti/<anno>/` e i collegamenti nella pagina Piazzamenti. Senza argomenti lo script riscarica solo la stagione in corso; per una nuova stagione va aggiunta una riga a `STAGIONI` nello script.

## Giocatori passati

`tools/aggiorna_statistiche.py` scarica le statistiche di carriera di tutti i giocatori comparsi nelle stagioni di `tools/stagioni.json` (non solo di quelli con una scheda scritta dalla società) e salva l'elenco in `tools/giocatori.json`. `tools/build.py` genera una scheda in `squadre-senior/giocatori/<nome>/` per chi non ha una pagina propria e l'elenco `squadre-senior/giocatori-passati/` con chi non è nella rosa dell'ultima stagione. Va lanciato dopo `aggiorna_stagioni.py`.

## Stagioni giovanili

`python3 tools/aggiorna_giovanili.py` legge dal sito FIBS classifica, partite e (quando c'è) rosa delle squadre Under 12, Under 15 e Under 18 e le salva in `tools/giovanili.json`; `tools/build.py` genera le schede in `giovanili/stagioni/<categoria>-<anno>/`. Senza argomenti aggiorna solo l'anno in corso e cerca da solo se i Lancers sono iscritti; `--tutte` riscarica tutto. Per i ragazzi non vengono mostrati l'anno di nascita né collegamenti a schede personali.
