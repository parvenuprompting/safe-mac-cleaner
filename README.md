# Safe Mac Cleaner

[![CI](https://github.com/parvenuprompting/safe-mac-cleaner/actions/workflows/ci.yml/badge.svg)](https://github.com/parvenuprompting/safe-mac-cleaner/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS-000000?logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![License](https://img.shields.io/badge/license-not%20specified-lightgrey)](https://github.com/parvenuprompting/safe-mac-cleaner)

Safe Mac Cleaner is een lichte, voorspelbare macOS-app voor veilige schijfopruiming. De kern bestaat uit Python-logica, verpakt in een overzichtelijke **PySide6 GUI**. Geen automatische deletes, geen cloud, geen verborgen acties: volledige controle blijft bij de gebruiker.

De applicatie is momenteel een persoonlijke utility in actieve v2-ontwikkeling. De nadruk ligt op transparantie, veilige defaults en acties die de gebruiker kan controleren.

Met deze app kun je:

* In één oogopslag zien hoeveel schijfruimte vrij is (GB en %)
* Oude en grote bestanden vinden met **aanpasbare en persistente filters**
* Bestanden **permanent uitsluiten** van toekomstige scans via een simpele rechtermuisklik
* Bestanden selecteren via checkboxes en veilig naar de Prullenbak verplaatsen, met **directe feedback over de totale grootte van de selectie**
* De Prullenbak direct vanuit de app legen

---

## 🔑 Kernprincipes & Veiligheid

### Veilige zoekgebieden

Alleen bestaande submappen van de huidige gebruikers-home-directory kunnen worden gescand:

* `Downloads`
* `Desktop`
* `Documents`
* `Movies`
* `Pictures`
* `Music`

Systeem- en kritieke mappen, de home-directory zelf en paden buiten de home-directory worden geweigerd. Overlappende scanmappen worden automatisch samengevoegd.

### Altijd omkeerbaar

Bestanden worden nooit permanent verwijderd door de app zelf. Alles verloopt via de macOS Prullenbak.

### Gebruiker aan het stuur

* Grootte-, ouderdom- en limietfilters zijn volledig instelbaar via de GUI
* Instellingen worden **onthouden** voor volgende sessies
* De actieve gebruikersnaam wordt automatisch gedetecteerd

---

## Installatie & Voorbereiding

### Vereisten

* macOS
* Python 3.10 of nieuwer
* macOS voor de GUI en Finder-integratie

### Modules installeren

Maak vanuit de projectmap (`safe-mac-cleaner`) een virtuele omgeving en installeer de applicatie inclusief ontwikkeltools:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

De runtime-dependencies zijn `PySide6`, `psutil` en `send2trash`. De extra ontwikkeltools bevatten `pytest` en `ruff`.

---

## Opstartinstructies

Zodra de vereiste modules zijn geïnstalleerd, kun je Safe Mac Cleaner op twee manieren starten: via VS Code (aanbevolen) of handmatig via de Terminal.

### 1. Starten via VS Code Task (aanbevolen)

1. Zorg dat het bestand **`.vscode/tasks.json`** aanwezig is in de projectmap
2. Open het project in VS Code
3. Ga naar **Terminal → Run Task…**
4. Kies **Start Safe Mac Cleaner GUI**

Optioneel kun je de app ook starten met **⇧⌘B** (Shift + Command + B).

### 2. Handmatig starten via Terminal

1. Open Terminal
2. Navigeer naar de projectmap `safe-mac-cleaner`
3. Start de applicatie met:

```bash
.venv/bin/python smc_gui.py
```

De VS Code-task gebruikt het systeem-Python-pad en vereist daarom dat de dependencies daar beschikbaar zijn. Gebruik de virtuele omgeving voor een reproduceerbare lokale setup.

### Tests en linting

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check smc_cleaner.py smc_gui.py tests
```

Deze checks draaien ook automatisch via GitHub Actions bij iedere push en pull request.

---

## ⚙️ Applicatie-overzicht

### 🔧 Instellingenmenu (persistent)

Via **Instellingen → Pas Filters Aan…** stel je in wat een relevant bestand is voor de volgende scan. Deze instellingen worden permanent opgeslagen via **QSettings**.

| Instelling                | Standaard | Betekenis                                            |
| ------------------------- | --------- | ---------------------------------------------------- |
| Max. aantal resultaten    | 100        | Beperkt het aantal getoonde bestanden                |
| Minimale ouderdom (dagen) | 30         | Bestanden jonger dan dit worden genegeerd            |
| Minimale grootte (MB)     | 100        | Neemt alleen bestanden boven deze grootte mee        |
| Tijdscriterium            | Last Used  | Keuze tussen *Laatst gebruikt* en *Laatst gewijzigd* |

---

### 🖼️ Resultatentabel (verbeterd)

* Volledig bestandspad zichtbaar
* Numerieke kolommen rechts-uitgelijnd voor betere leesbaarheid
* Verwijderacties controleren of een bestand sinds de scan niet is gewijzigd
* Mislukte verwijderacties worden afzonderlijk aan de gebruiker gemeld

#### Contextmenu (rechtermuisklik)

* 🔍 **Toon in Finder**
* ❌ **Sluit dit bestand uit van scan**
  Voegt het bestandspad toe aan een persistente uitsluitingslijst (`~/.smc_exclusions.json`)
* 🗑️ **Verplaats naar Prullenbak**

---

### ⬇️ Actieknoppen (onderzijde)

| Knop                      | Functie                                                            |
| ------------------------- | ------------------------------------------------------------------ |
| Start nieuwe scan         | Draait een nieuwe scan met huidige filters                         |
| Selecteer alles           | Selecteert of deselecteert alle items                              |
| Toon in Finder            | Opent het **eerste** geselecteerde bestand                         |
| Verplaats naar Prullenbak | Dynamisch: toont totale MB van de selectie en verplaatst bestanden |
| Leeg Prullenbak           | **PERMANENT**: leegt de volledige macOS Prullenbak (onomkeerbaar)  |

---

## ❌ Bewuste beperkingen

Safe Mac Cleaner is bewust beperkt in scope. Alles wat extra risico, complexiteit of onduidelijk gedrag introduceert, is expliciet weggelaten.

De applicatie doet **niet** het volgende:

* ❌ Geen automatische of geplande scans op de achtergrond
* ❌ Geen permanente verwijdering van bestanden door de app zelf
* ❌ Geen toegang tot systeemmappen, de home-directory zelf of paden buiten de home-directory
* ❌ Geen cloud-sync, upload of externe communicatie
* ❌ Geen slimme heuristieken of "AI-beslissingen" over wat weg mag

Elke actie vereist expliciete gebruikersinput en bevestiging.

---

## Doel van dit project

Safe Mac Cleaner is gebouwd als een **persoonlijke utility**: klein, voorspelbaar en veilig.

Het biedt een bewuste en gecontroleerde manier om schijfruimte vrij te maken, zonder de complexiteit, agressieve strategieën of risico’s van commerciële cleaners.

## Projectstructuur

* `smc_cleaner.py`: scan-, safety- en Prullenbaklogica
* `smc_gui.py`: PySide6-interface en achtergrondworkers
* `models.py`: gedeelde, gevalideerde applicatiestatus zoals scaninstellingen
* `workers.py`: achtergrondworkers voor scans en Prullenbakacties
* `platform_macos.py`: macOS-specifieke Finder- en Prullenbakintegratie
* `tests/`: tests voor scanvalidatie en veilige verwijdering
* `Safe Mac Cleaner.spec`: PyInstaller-configuratie voor een macOS-build
* `.github/workflows/ci.yml`: automatische tests en linting

De resultatenlijst ondersteunt zoeken op bestandsnaam of pad, sorteren per kolom en een detailweergave van het geselecteerde bestand. Via **Uitsluitingen** kunnen eerder uitgesloten bestanden ook weer worden beheerd en verwijderd uit de uitsluitingslijst.

Er zijn ook scanprofielen beschikbaar:

* **Aangepaste scan**: gebruikt je huidige filters
* **Grote bestanden**: bestanden vanaf 1.000 MB
* **Oude bestanden**: bestanden ouder dan 180 dagen en vanaf 100 MB
* **Oude downloads**: bestanden ouder dan 30 dagen en vanaf 100 MB

De lokale scanhistorie bewaart maximaal 20 samenvattingen met datum, aantal resultaten, totale grootte en eventuele scanwaarschuwingen. Er wordt geen bestandsinhoud of data naar buiten de computer gestuurd.

## Status

De applicatie is bedoeld voor macOS. De engine-tests en statische checks draaien automatisch in CI; een volledige GUI- en PyInstaller-test hoort op macOS te gebeuren.
