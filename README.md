# 🔎 Safe Mac Cleaner (SMC) v3.8 – The GUI Edition

**Safe Mac Cleaner (SMC) v3.8** is een lichte, voorspelbare macOS-app voor veilige schijfopruiming. De kern bestaat uit eenvoudige, betrouwbare Python-logica, verpakt in een overzichtelijke **PySide6 GUI**. Geen automatische deletes, geen cloud, geen verborgen acties — volledige controle blijft altijd bij de gebruiker.

Met deze app kun je:

* In één oogopslag zien hoeveel schijfruimte vrij is (GB en %)
* Oude en grote bestanden vinden met aanpasbare filters
* Bestanden selecteren via checkboxes en veilig naar de Prullenbak verplaatsen
* De Prullenbak direct vanuit de app legen

---

## 🔑 Kernprincipes & Veiligheid

* **Beperkte scanzones**
  Alleen gebruikersmappen worden gescand: `Downloads`, `Desktop`, `Documents`, `Movies`.
  Systeem- en kritieke mappen zijn expliciet uitgesloten.

* **Altijd omkeerbaar**
  Bestanden worden nooit permanent verwijderd. Alles verloopt via de macOS Prullenbak.

* **Gebruiker aan het stuur**
  Grootte-, ouderdom- en limietfilters zijn volledig instelbaar via de GUI.

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

Dit is de snelste en meest betrouwbare manier tijdens gebruik en ontwikkeling.

1. Zorg dat het bestand **`.vscode/tasks.json`** aanwezig is in de projectmap
2. Open het project in VS Code
3. Ga naar **Terminal → Run Task…**
4. Kies **Start Safe Mac Cleaner GUI**

Optioneel kun je de app ook starten met de sneltoets **⇧⌘B** (Shift + Command + B).

### 2. Handmatig starten via Terminal

Gebruik deze methode als je VS Code niet gebruikt.

1. Open Terminal
2. Navigeer naar de projectmap `safe-mac-cleaner`
3. Start de applicatie met:

```
/usr/bin/python3 smc_gui.py
```

Het gebruik van het absolute Python-pad voorkomt problemen met virtuele omgevingen of verkeerde Python-versies.

---

## ⚙️ Applicatie-overzicht

### 🔧 Instellingenmenu

Via **Instellingen → Pas Filters Aan…** stel je in wat een relevant bestand is voor de volgende scan:

| Instelling                | Standaard | Betekenis                                     |
| ------------------------- | --------- | --------------------------------------------- |
| Max. aantal resultaten    | 100       | Beperkt het aantal getoonde bestanden         |
| Minimale ouderdom (dagen) | 7         | Bestanden jonger dan dit worden genegeerd     |
| Minimale grootte (MB)     | 1         | Neemt alleen bestanden boven deze grootte mee |

---

### 🖼️ Resultatentabel

Bestanden worden gesorteerd op grootte voor snelle besluitvorming.

* Checkbox per bestand voor selectie
* Volgnummer voor overzicht
* Grootte en ouderdom als primaire beslisinformatie

---

### ⬇️ Actieknoppen (onderzijde)

| Knop                      | Functie                                     |
| ------------------------- | ------------------------------------------- |
| Start nieuwe scan         | Draait een nieuwe scan met huidige filters  |
| Selecteer alles           | Selecteert of deselecteert alle items       |
| Toon in Finder            | Opent het geselecteerde bestand in Finder   |
| Verplaats naar Prullenbak | Verplaatst geselecteerde bestanden          |
| Leeg Prullenbak           | Leegt de macOS Prullenbak (met bevestiging) |

---

## ❌ Bewuste beperkingen

Safe Mac Cleaner is bewust **beperkt in scope**. Alles wat extra risico, complexiteit of onduidelijk gedrag introduceert, is expliciet weggelaten.

De applicatie doet **niet** het volgende:

* ❌ Geen automatische of geplande scans op de achtergrond
* ❌ Geen permanente verwijdering van bestanden (altijd via Prullenbak)
* ❌ Geen toegang tot systeemmappen of verborgen OS-paden
* ❌ Geen cloud-sync, upload of externe communicatie
* ❌ Geen slimme heuristieken of "AI-beslissingen" over wat weg mag

Elke actie vereist expliciete gebruikersinput en bevestiging.

---

## 🎯 Doel van dit project

Safe Mac Cleaner is gebouwd als **persoonlijke utility**: klein, voorspelbaar en veilig.
Geen commerciële intentie, geen tracking, geen cloud-integratie.

De app doet precies één ding goed: je helpen bewust en gecontroleerd schijfruimte vrij te maken — zonder risico op dataverlies.
