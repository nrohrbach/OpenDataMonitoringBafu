# OGD Monitoring BAFU

Interaktive Web-Applikation zur Überwachung der Open Government Data (OGD) Publikationen des Bundesamts für Umwelt (BAFU) auf [opendata.swiss](https://opendata.swiss).

## Live-App

👉 **https://nrohrbach.github.io/OpenDataMonitoringBafu**

## Funktionsweise

Das Projekt folgt dem Prinzip von [metaodi/gym-occupancy](https://github.com/metaodi/gym-occupancy):

- Die CSVs enthalten immer nur den **aktuellen Stand** — sie werden täglich vollständig überschrieben
- Die **Git-History ist die Zeitreihe** — jeder tägliche Commit ist ein Snapshot
- `extract_git_history.py` rekonstruiert daraus die vollständige History für die Charts

```
täglich 06:00 UTC
       │
       ▼
fetch_data.py          → ogd_packages.csv + ogd_resources.csv  (überschreiben)
       │
       ▼
git commit + push      → Git-History wächst täglich um einen Eintrag
       │
       ▼
extract_git_history.py → ogd_packages_history.csv + ogd_resources_history.csv
       │
       ▼
GitHub Pages Deploy    → index.html + beide History-CSVs
```

## Projektstruktur

```
├── fetch_data.py              # CKAN API → beide CSVs überschreiben
├── extract_git_history.py     # Git-History → beide History-CSVs
├── index.html                 # Interaktive Web-App (Plotly.js + PapaParse)
├── ogd_packages.csv           # Aktueller Stand Packages (versioniert)
├── ogd_resources.csv          # Aktueller Stand Ressourcen (versioniert)
├── ogd_packages_history.csv   # Rekonstruierte History (nicht versioniert, .gitignore)
├── ogd_resources_history.csv  # Rekonstruierte History (nicht versioniert, .gitignore)
├── requirements.txt
└── .github/workflows/
    └── update_data.yml        # Täglicher Cronjob + GitHub Pages Deploy
```

## Datenquellen

- **API**: [CKAN opendata.swiss](https://ckan.opendata.swiss/api/3/action/package_search?fq=organization:bundesamt-fur-umwelt-bafu)
- **Organisation**: `bundesamt-fur-umwelt-bafu`

### ogd_packages.csv

Eine Zeile pro Package (Datensatz).

| Spalte | Beschreibung |
|---|---|
| `package_name` | Technischer Name (Join-Key) |
| `title_de` | Deutscher Titel |
| `maintainer` | Abteilungsname |
| `maintainer_email` | E-Mail der Abteilung |
| `issued` | Erstveröffentlichung |
| `modified` | Letzte Aktualisierung |
| `license` | Lizenz-Kürzel |
| `keywords_de` | Keywords, kommagetrennt |

### ogd_resources.csv

Eine Zeile pro Ressource (ein Package kann mehrere Ressourcen haben).

| Spalte | Beschreibung |
|---|---|
| `package_name` | Fremdschlüssel → ogd_packages.csv |
| `resource_id` | Eindeutige Ressourcen-ID |
| `title_de` | Deutscher Titel |
| `format` | Datenformat (WMS, CSV, GeoJSON, …) |
| `url` | Download- oder Service-URL |
| `media_type` | MIME-Type |
| `issued` / `modified` | Datumsangaben |
| `license` | Lizenz |
| `has_stac` | URL enthält `data.geo.admin.ch/browser` |
| `is_service` | Format ist `SERVICE` |

## Ansichten der App

| Seite | Inhalt |
|---|---|
| **Dashboard** | KPI-Kacheln + Gesamtentwicklung über Zeit |
| **Abteilung** | Packages pro Maintainer-Abteilung |
| **Formate** | Verteilung der Ressourcen-Formate |
| **STAC** | Geodaten mit/ohne STAC-Browser-Link |
| **Lizenzen & Aktualität** | Lizenzverteilung + letzte Änderungsdaten |
| **Themen** | Keywords gematcht gegen BAFU-Themenbereiche |

## Lokale Entwicklung

```bash
pip install -r requirements.txt

# Aktuelle Daten abrufen
python fetch_data.py

# History rekonstruieren (benötigt mindestens einen Commit mit den CSVs)
python extract_git_history.py

# App lokal öffnen (einfacher HTTP-Server nötig wegen fetch())
python -m http.server 8000
# → http://localhost:8000
```

## Technologie

| Komponente | Technologie |
|---|---|
| Datenabfrage | Python / requests |
| Historienextraktion | Python / GitPython |
| Frontend | Statisches HTML + JavaScript |
| Visualisierungen | [Plotly.js](https://plotly.com/javascript/) |
| CSV-Parsing | [PapaParse](https://www.papaparse.com/) |
| Design | Oblique-inspiriertes CSS |
| Automatisierung | GitHub Actions |
| Hosting | GitHub Pages |
