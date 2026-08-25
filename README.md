# Wohnungsradar

Fragt stündlich zwischen 8 und 22 Uhr deine Suchen auf Kleinanzeigen, ImmoScout24, WG-Gesucht und
Immowelt ab und baut daraus eine Übersichtsseite: neueste Anzeigen oben, mit Preis,
Zimmern, Fläche, €/m² und Alter. Läuft kostenlos über GitHub Actions, die Seite liegt
auf GitHub Pages. Kein Server, keine Installation auf deinem Rechner nötig.

---

## Einrichtung

### 1. Repository anlegen

Neues Repository auf GitHub erstellen, alle Dateien aus diesem Ordner hochladen
(inklusive des versteckten Ordners `.github/`).

**Nimm ein öffentliches Repository.** Bei privaten Repos zählen Actions-Minuten gegen
dein Kontingent (2000 Minuten/Monat frei). Beim eingestellten Takt – stündlich von 8 bis
22 Uhr, rund 450 Läufe im Monat zu je 1–2 Minuten – bleibst du zwar darunter, aber ohne
Reserve, falls du den Takt später erhöhst. Bei öffentlichen Repos sind die Läufe unbegrenzt. Das heißt aber: deine Such-URLs und die
gefundenen Anzeigen sind öffentlich lesbar. Nichts Privates in `config.json` schreiben.

### 2. Suchen eintragen

Das ist der wichtigste Schritt. Statt Filter im Code nachzubauen, benutzt der Agent
deine echten Suchergebnis-Seiten:

1. Geh auf die jeweilige Plattform und such normal – Stadt, Preis, Zimmer, alles.
2. Sortiere nach **neueste zuerst**.
3. Kopiere die URL aus der Adresszeile.
4. Trag sie in `config.json` ein.

```json
{
  "name": "Kleinanzeigen · Leipzig Süd bis 900 €",
  "plattform": "kleinanzeigen",
  "url": "https://www.kleinanzeigen.de/s-wohnung-mieten/leipzig/preis::900/c203l3607",
  "aktiv": true
}
```

Erlaubte Werte für `plattform`: `kleinanzeigen`, `immoscout24`, `wg-gesucht`, `immowelt`.
Mit `"aktiv": false` schaltest du eine Suche vorübergehend ab, ohne sie zu löschen.

### Mehrere Städte

Trag einfach weitere Einträge ein und gib jedem eine `"stadt"` mit. Alle laufen im selben
Durchgang, und im Dashboard erscheint dann automatisch ein Auswahlfeld, mit dem du zwischen
den Städten umschaltest. Die Stadt steht außerdem fett vor der Ortsangabe jeder Anzeige.

Braucht eine Stadt ein anderes Budget, hängst du ihr einen eigenen `filter`-Block an. Der
überschreibt nur die Werte, die drinstehen – alles andere gilt weiter aus dem globalen Filter:

```json
{
  "name": "Kleinanzeigen · Bochum",
  "stadt": "Bochum",
  "plattform": "kleinanzeigen",
  "url": "https://www.kleinanzeigen.de/...",
  "aktiv": true,
  "filter": { "max_miete": 950 }
}
```

Jede Suche kostet 3–8 Sekunden Laufzeit. Zwölf Suchen sind also gut eine Minute pro
Durchgang – unkritisch. Bei sehr vielen Suchen lohnt es, die Städte mit `"aktiv": false`
zu parken, die gerade nicht dringend sind.

### 3. Filter setzen

Greifen zusätzlich zu dem, was die Plattform schon gefiltert hat:

```json
"filter": {
  "max_miete": 1200,
  "min_zimmer": 2,
  "min_flaeche": 55,
  "ausschluss_woerter": ["tausch", "zwischenmiete", "möbliert"],
  "pflicht_woerter": []
}
```

Anzeigen ohne erkannte Angabe werden **nicht** aussortiert – eine passende Wohnung wegen
einer fehlenden Zahl zu verlieren wäre teurer als ein Fehltreffer in der Liste.
`pflicht_woerter` leer lassen heißt: keine Einschränkung. Steht dort etwas, muss mindestens
eines der Wörter im Titel oder Ort vorkommen (z. B. `["balkon", "terrasse"]`).

### 4. Pages aktivieren

Repository → **Settings** → **Pages** → Source: `Deploy from a branch`, Branch: `main`,
Ordner: `/docs`. Nach ein paar Minuten liegt dein Dashboard unter
`https://DEINNAME.github.io/DEINREPO/`. Lesezeichen auf dem Handy anlegen.

### 5. Ersten Lauf starten

Repository → **Actions** → einmal auf „I understand my workflows, enable them" klicken →
Workflow „Wohnungssuche" → **Run workflow**. Danach läuft er von selbst stündlich zwischen
8 und 22 Uhr.

---

## Was du wissen solltest

**ImmoScout24 wird sich wehren.** Die Seite hat starken Bot-Schutz und blockt Anfragen aus
Rechenzentren – GitHub-Actions-Server gehören dazu. Erwarte dort regelmäßig „Zugriff
blockiert (HTTP 403)". Das Dashboard zeigt das offen an, statt so zu tun, als gäbe es
keine Angebote. Zwei Auswege:

- ImmoScouts eigenen Suchagenten per Mail abonnieren und die Mails separat lesen.
- Das Skript zusätzlich lokal auf deinem Rechner laufen lassen (siehe unten) – von einer
  privaten IP klappt es meist.

Kleinanzeigen, WG-Gesucht und Immowelt laufen aus Actions heraus in der Regel durch.

**Die Auswertung kann brechen.** Ändert eine Plattform ihr HTML, findet der Parser nichts
mehr. Im Dashboard steht dann „Seite geladen, aber keine Anzeigen erkannt". Dann brauchen
die Selektoren in `sources.py` eine Anpassung – mit `python main.py --debug` legt das
Skript das rohe HTML unter `data/debug/` ab, damit man nachschauen kann.

**Abrufe bleiben höflich.** Zwischen den Suchen liegen 2–6 Sekunden Pause. Bitte den Takt
nicht auf jede Minute stellen: das bringt keine besseren Wohnungen, nur Sperren.

**Der Zeitstempel ist der Fundzeitpunkt**, nicht der Zeitpunkt der Veröffentlichung. Beim
allerersten Lauf ist deshalb alles gleichzeitig „neu". Ab dem zweiten Lauf stimmt es.

---

## Lokal laufen lassen

```bash
pip install -r requirements.txt
python main.py
```

Öffnet danach `docs/index.html` im Browser. `data/anzeigen.json` merkt sich, was schon
gesehen wurde – die Datei nicht löschen, sonst ist wieder alles „neu".

---

## Dateien

| Datei | Zweck |
|---|---|
| `config.json` | deine Suchen und Filter – das Einzige, was du normalerweise anfasst |
| `main.py` | Ablauf: abrufen, filtern, speichern, Seite bauen |
| `sources.py` | Abruf und Auswertung pro Plattform |
| `render.py` | erzeugt `docs/index.html` |
| `data/anzeigen.json` | Gedächtnis, welche Anzeigen schon bekannt sind |
| `.github/workflows/suche.yml` | Zeitplan für GitHub Actions |

## Takt ändern

Der Zeitplan steht an **zwei Stellen**, die einander nicht kennen – beide anpassen:

1. `.github/workflows/suche.yml`, Zeile `cron:` – das ist die echte Steuerung.
2. `config.json`, `takt_minuten` – nur der Hinweistext unten im Dashboard.

Cron läuft immer in **UTC**, nicht in deutscher Zeit. Aktuell eingestellt ist
`0 6-20 * * *`, also stündlich zur vollen Stunde von 6 bis 20 Uhr UTC = **8 bis 22 Uhr
MESZ**. Von Ende Oktober bis Ende März verschiebt sich das um eine Stunde nach vorn; wenn
dich das stört, dann auf `0 7-21 * * *` umstellen.

Andere Beispiele:

| Cron | Bedeutung |
|---|---|
| `0 6-20 * * *` | stündlich, 8–22 Uhr *(aktuell)* |
| `0,30 6-20 * * *` | halbstündlich, 8–22 Uhr |
| `*/20 * * * *` | alle 20 Minuten, rund um die Uhr |
| `0 * * * *` | stündlich, rund um die Uhr |

Geplante Läufe startet GitHub bei hoher Auslastung mit Verzögerung, gelegentlich 10–20
Minuten. Der Takt ist also eher „ungefähr stündlich". Sofort suchen kannst du jederzeit
über **Actions** → „Wohnungssuche" → **Run workflow**.

`behalten_tage` in `config.json` legt fest, wie lange alte Anzeigen im Dashboard bleiben.
