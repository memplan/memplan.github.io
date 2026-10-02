# MEM Plan – Lernziele der MEM-Berufe

Interaktive Übersicht über die Bildungspläne der MEM-Berufe. Die Lernziele werden aus den offiziellen Daten von [skills.futuremem.swiss](https://skills.futuremem.swiss/) aufbereitet und in einer durchsuchbaren, filterbaren Hierarchie dargestellt.

👉 **Live:** https://memplan.ch/ ([github.com/memplan/memplan.github.io](https://github.com/memplan/memplan.github.io))

Abgedeckt sind alle Berufe des FutureMEM-Portals:

| Kürzel | Beruf |
| --- | --- |
| AA | Anlagen- und Apparatebauer/in EFZ |
| KR | Konstrukteur/in EFZ |
| MP | Mechanikpraktiker/in EBA |
| PR | Produktionsmechaniker/in EFZ |
| PM | Polymechaniker/in EFZ |
| AM | Automatikmonteur/in EFZ |
| AU | Automatiker/in EFZ |
| ET | Elektroniker/in EFZ |

Dieses Tool richtet sich an Lernende, Berufsbildnerinnen, Lehrpersonen und alle, die sich einen schnellen, strukturierten Überblick über die Lerninhalte der MEM-Grundbildung verschaffen wollen.

## Hierarchie

**HKB** (Handlungskompetenzbereich) → **HK** (Handlungskompetenz) → **LK** (Leistungskriterium) → **LZ** (Lernziel)

Die Gliederung folgt dem kompetenzorientierten Bildungsplan (BPL) der jeweiligen beruflichen Grundbildung. Jeder Beruf hat seine eigene Farbe, die sich durch die Seite und die PDF-Zielblätter zieht.

## Datenquellen

- **skills.futuremem.swiss** – offizielle Lernzielplattform von Swissmem
- **Bildungsplan** – becc.admin.ch (BECC)
- **Berufsverordnung** – SBFI

## Features

- **Berufsseiten** für alle acht MEM-Berufe, erreichbar über die Startseite
- **Suche** über alle LZ, LK, HK und HKB (Fuzzy-Suche via Fuse.js)
- **Filter** nach Bereich, Typ (Pflicht/Wahl), Lernort (BFS/üK/BE) und Semester
- **Querverweise** – Lernziele, die in mehreren LKs vorkommen, werden verlinkt
- **Highlight** – `?highlight=lk-MEM_08_02` in der URL springt direkt zu einem bestimmten LK
- **Alle einklappen/ausklappen** für schnelle Navigation
- **PDF-Zielblätter** pro Beruf und Lernort (Betrieb, Berufsschule, überbetriebliche Kurse)

## Deployment

Die Seite wird via **GitHub Pages** gehostet. Einfach den `main`-Branch pushen. Der Workflow `.github/workflows/deploy.yml` baut die statische Seite mit `site/build_site.py` nach `_site/` und veröffentlicht sie.

Die Startseite `/` listet alle Berufe; jeder Beruf ist unter seinem Kürzel erreichbar (`/AA/`, `/AM/`, `/AU/`, `/ET/`, `/KR/`, `/MP/`, `/PM/`, `/PR/`). Alle Berufsseiten teilen sich `style.css` und `script.js`; der jeweilige Beruf wird über `window.JOB` gesetzt. Die Metadaten (Name, SBFI-, Bildungsplan- und Verordnungs-Links) stehen in `data/jobs.json`, die Templates unter `site/templates/`.

Lokal bauen:

```bash
pip install jinja2
python3 site/build_site.py   # schreibt _site/
```

## Datenaktualisierung

Die Skripte in `data/` laden die aktuellen Excel-Daten von skills.futuremem.swiss und bereiten sie auf. Die Excel-Dateien enthalten alle acht Berufe des futuremem-Portals (`AA`, `KR`, `MP`, `PR`, `PM`, `AM`, `AU`, `ET`). Für jeden Beruf entsteht eine eigene, hierarchisch gegliederte Datei `data/lehrplan_<BPL>.json` (z. B. `data/lehrplan_ET.json`). Die Webseite und die PDF-Zielblätter erzeugen daraus je eine Berufsseite bzw. drei Dokumente pro Beruf.

```bash
# 1. Excel-Dateien herunterladen
python3 data/download_excel.py

# 2. Daten aller Berufe aus allen drei Lernorten (BFS, üK, BE) zusammenführen
python3 data/merge_lehrplan.py

# 3. Beschreibungen von HKB, HK, LK von der Website scrapen
python3 data/scrape_hkb.py
python3 data/scrape_hk.py
python3 data/scrape_lk.py

# 4. Hierarchische JSON-Dateien erstellen (eine pro Beruf)
python3 data/csv_to_json.py

# 5. Doppelte Lernziele pro Beruf zusammenführen
for f in data/lehrplan_*.json; do python3 data/deduplicate_lernziele.py "$f"; done
```

Mit `python3 data/merge_lehrplan.py --bpl ET` lässt sich die Zusammenführung auf einen einzelnen Beruf einschränken.

## Druckbare Zielblätter (Typst/PDF)

Für **jeden Beruf** lassen sich druckbare Zielblätter erzeugen, auf denen Lernende erreichte Ziele abhaken und signieren können.

```bash
# Zielblätter für alle Berufe generieren und zu PDF kompilieren
./pdf/generate.sh
```

Das Skript liest die Berufsliste aus `data/jobs.json` und erzeugt pro Beruf drei Dokumente in `pdf/output/`:

| Datei | Inhalt |
| --- | --- |
| `pdf/output/Lernziele_<Beruf>_Betrieb.typ` / `.pdf` | Alle Leistungskriterien für den Lernort **Betrieb (BE)** |
| `pdf/output/Lernziele_<Beruf>_Berufsschule.typ` / `.pdf` | Alle Ziele für die **Berufsschule (BFS)**, sortiert nach Semestern |
| `pdf/output/Lernziele_<Beruf>_Ueberbetriebliche_Kurse.typ` / `.pdf` | Alle Ziele für die **überbetrieblichen Kurse (üK)**, sortiert nach Semestern |

`<Beruf>` ist der Wert `short` aus `data/jobs.json` (z. B. `Polymechaniker`, `Automatiker`, `Anlagen_Apparatebauer`).

Jedes Dokument beginnt mit einer **Titelseite** (Name, Startjahr, Firma), einem
**Inhaltsverzeichnis** und einem Kapitel **«Hinweise und Überblick»**, das die Begriffe
HKB, HK, LK und LZ erklärt und eine Übersicht über alle Handlungskompetenzbereiche mit
deren Pflicht-/Wahl-Status zeigt. Ab dem Inhaltsverzeichnis tragen alle Seiten einen
**Kopf** (Titel links, Untertitel rechts) und eine **Fusszeile** (Bildungsplan-Notiz
links, Seitenzahl rechts). Die Ziele sind hierarchisch nach HKB → HK → LK (→ LZ)
gegliedert. Jede Handlungskompetenz ist mit einem **Pflicht/Wahl-Badge** markiert
(Pflicht in der Berufsfarbe, Wahl grau), und die **Tabellenköpfe sind entsprechend eingefärbt**:
Berufsfarbe für Pflicht-HKs, grau für Wahl-HKs. Leistungskriterien stehen als
**hervorgehobene Gruppenzeilen** (leicht eingefärbt, mit Akzent-Trennlinie) in einer
Tabelle mit Signaturspalte, Lernziele darunter **eingerückt**, kleiner und ausgegraut –
so ist die Hierarchie LK → LZ auf einen Blick erkennbar.

Jeder Beruf hat seine **eigene Farbe** (passend zur Webseite). Die Werte stehen in
`data/jobs.json` unter `accent` / `accentSoft` und werden in den DESIGN-Block injiziert.

### Layout anpassen

Das Layout ist in **Jinja2-Templates** unter `pdf/templates/` ausgelagert – Farbschema,
Schriften, Abstände und Tabellenoptik lassen sich dort ändern, ohne den Python-Code
anzufassen:

| Template | Inhalt |
| --- | --- |
| `pdf/templates/base.typ.j2` | Einstieg + **DESIGN-Block** (Farben, Schriften, Heading-Styles) |
| `pdf/templates/title_page.typ.j2` | Titelseite mit Feldkarte (Name, Startjahr, Firma) |
| `pdf/templates/toc.typ.j2` | Inhaltsverzeichnis + Start von Seitennummerierung, Kopf und Fusszeile |
| `pdf/templates/overview.typ.j2` | Kapitel «Hinweise und Überblick» (Struktur + HKB/HK-Übersicht) |
| `pdf/templates/table.typ.j2` | Tabellen-Makros `lk_row`, `lz_row`, `lk_table` |

Zum Anpassen des Layouts genügt der DESIGN-Block in `base.typ.j2`. Die Farben selbst
werden pro Beruf aus `data/jobs.json` eingesetzt:

```typst
#let accent = rgb("{{ accent }}")        // Berufsfarbe (Titel, Tabellenkopf)
#let accent-soft = rgb("{{ accent_soft }}")  // helle Flächen (Lernziel-Zeilen, Karte)
#let muted = rgb("#5b6474")         // Nebentexte
#let faint = rgb("#8a93a6")         // IDs, Fusszeilen
#let border-color = rgb("#d3d9e4")  // Tabellenrahmen
```

Danach reicht `./pdf/generate.sh`, um die Dokumente aller Berufe neu zu erzeugen und zu kompilieren.

### Skript direkt verwenden

```bash
# Einzelnes Dokument mit Optionen erzeugen (Beruf wird aus dem Dateinamen erkannt)
python3 pdf/generate_lehrplan_typ.py ../data/lehrplan_ET.json \
    --lernort BE --no-descriptions --signature both \
    -o output/Lernziele_Elektroniker_Betrieb.typ

# Zu PDF kompilieren (Typst muss installiert sein)
typst compile pdf/output/Lernziele_Elektroniker_Betrieb.typ
```

Optionen:

| Option | Bedeutung |
| --- | --- |
| `--lernort BE\|BFS\|üK` | Nur Ziele dieses Lernorts (mehrfach angeben möglich) |
| `--by-semester` | Ziele nach Semestern gruppieren, pro Semester ein Kapitel |
| `--show-descriptions` / `--no-descriptions` | Lange HK-Beschreibungen anzeigen/ausblenden |
| `--signature both\|lk\|lz\|none` | Signaturspalte pro LK+LZ, nur LK, nur LZ oder keine |
| `--name`, `--start-year`, `--company` | Kopfzeile vorausfüllen (sonst Leerzeilen) |
| `-o DATEI` | Ausgabedatei (Standard: `output/Lernziele_<Beruf>_<Lernort>.typ`) |

Als Eingabe kann neben einer vollständigen `lehrplan_<BPL>.json` auch **jede Teilmenge**
verwendet werden, solange sie das gleiche Schema hat
(`{"ET": {"handlungskompetenzbereiche": [...]}}` oder direkt
`{"handlungskompetenzbereiche": [...]}`).

> Hinweis: `generate.sh` erwartet eine installierte Typst-Binärdatei (`typst`).
