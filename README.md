# Lancers Baseball Club 1982 – nuovo sito

Proposta di restyling del sito ufficiale (lancersbaseballclub.com), sito statico senza dipendenze.

Anteprima: https://lscarpul.github.io/sito-lancers-quello-nuovo/

- `index.html` e le cartelle delle sezioni (`societa/`, `squadre-senior/`, `giovanili/`, `ballpark/`, `gallery/`, `notizie/` ...): pagine generate
- `css/style.css`, `js/main.js`: stile e interazioni (menu mobile, lightbox, slider, filtri notizie)
- `images/`: grafica del sito, `media/`: foto dei contenuti, `files/`: PDF scaricabili
- `tools/`: `extract.py` estrae i contenuti dal sito WordPress in `content.json`; `build.py` rigenera tutte le pagine

Per cambiare menu, footer o layout: modificare `tools/build.py` e lanciare `python3 tools/build.py`.
