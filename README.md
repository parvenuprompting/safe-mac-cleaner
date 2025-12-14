# 🔎 Safe Mac Cleaner 

Safe Mac Cleaner is een lichte, voorspelbare macOS-app voor veilige schijfopruiming. De kern bestaat uit eenvoudige, betrouwbare Python-logica, verpakt in een overzichtelijke **PySide6 GUI**. Geen automatische deletes, geen cloud, geen verborgen acties — volledige controle blijft altijd bij de gebruiker.

Met deze app kun je:

* In één oogopslag zien hoeveel schijfruimte vrij is (GB en %)
* Oude en grote bestanden vinden met **aanpasbare en persistente filters**
* Bestanden **permanent uitsluiten** van toekomstige scans via een simpele rechtermuisklik
* Bestanden selecteren via checkboxes en veilig naar de Prullenbak verplaatsen, met **directe feedback over de totale grootte van de selectie**
* De Prullenbak direct vanuit de app legen

---

## 🔑 Kernprincipes & Veiligheid

### Veilige zoekgebieden

Alleen gebruikersmappen worden gescand:

* `Downloads`
* `Desktop`
* `Documents`
* `Movies`

Systeem- en kritieke mappen zijn expliciet uitgesloten.

### Altijd omkeerbaar

Bestanden worden nooit permanent verwijderd door de app zelf. Alles verloopt via de macOS Prullenbak.

### Gebruiker aan het stuur

* Grootte-, ouderdom- en limietfilters zijn volledig instelbaar via de GUI
* Instellingen worden **onthouden** voor volgende sessies
* De actieve gebruikersnaam wordt automatisch gedetecteerd

---

## 🛠️ Installatie & Voorbereiding

### Vereisten

* macOS
* Python 3
* Externe Python-modules:

  * `PySide6` (GUI)
  * `psutil` (schijfstatistieken)
  * `send2trash` (veilige bestandsverplaatsing)

### Modules installeren

Open Terminal in de projectmap (`safe-mac-cleaner`) en installeer de vereiste modules:

```
pip3 install PySide6 psutil send2trash
```

---

## 🚀 Opstartinstructies

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

```
/usr/bin/python3 smc_gui.py
```

Het gebruik van het absolute Python-pad voorkomt problemen met virtuele omgevingen of verkeerde Python-versies.

---

## ⚙️ Applicatie-overzicht

### 🔧 Instellingenmenu (persistent)

Via **Instellingen → Pas Filters Aan…** stel je in wat een relevant bestand is voor de volgende scan. Deze instellingen worden permanent opgeslagen via **QSettings**.

| Instelling                | Standaard | Betekenis                                            |
| ------------------------- | --------- | ---------------------------------------------------- |
| Max. aantal resultaten    | 100       | Beperkt het aantal getoonde bestanden                |
| Minimale ouderdom (dagen) | 7         | Bestanden jonger dan dit worden genegeerd            |
| Minimale grootte (MB)     | 1         | Neemt alleen bestanden boven deze grootte mee        |
| Tijdscriterium            | Last Used | Keuze tussen *Laatst gebruikt* en *Laatst gewijzigd* |

---

### 🖼️ Resultatentabel (verbeterd)

* Volledig bestandspad zichtbaar
* Numerieke kolommen rechts-uitgelijnd voor betere leesbaarheid

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
* ❌ Geen toegang tot systeemmappen of verborgen OS-paden
* ❌ Geen cloud-sync, upload of externe communicatie
* ❌ Geen slimme heuristieken of "AI-beslissingen" over wat weg mag

Elke actie vereist expliciete gebruikersinput en bevestiging.

---

## 🎯 Doel van dit project

Safe Mac Cleaner is gebouwd als een **persoonlijke utility**: klein, voorspelbaar en veilig.

Het biedt een bewuste en gecontroleerde manier om schijfruimte vrij te maken, zonder de complexiteit, agressieve strategieën of risico’s van commerciële cleaners.
