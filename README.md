# Generatore Tessere Club Napoli Romazzurra

Questo progetto genera automaticamente le tessere associative partendo dal file `tessera_master.png`.

## Obiettivo

Il programma modifica solo le aree variabili:

- foto del socio
- nome e cognome
- qualifica
- numero tessera
- data iscrizione
- validità

Resta invece invariata tutta la grafica fissa della tessera, inclusi logo destro, lettering superiore, anniversario, social e fascia inferiore.

## Come si usa

1. Carica le foto nella cartella `photos`.
2. Compila il file `soci.csv`.
3. Esegui:

```bash
pip install -r requirements.txt
python generate_cards.py --pdf
```

Le tessere vengono salvate nella cartella `output`.

## Esempio CSV

```csv
nome,cognome,numero_tessera,qualifica,foto,data_iscrizione,validita
Mario,Rossi,000001,Socio ordinario,mario_rossi.jpg,01/08/2026,ANNUALE
```

## GitHub Actions

Il workflow `Genera tessere` permette di generare le tessere anche da GitHub, dalla scheda Actions.
