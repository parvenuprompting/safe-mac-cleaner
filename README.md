🔎 Safe Mac Cleaner - Verbeterde Versie

Safe Mac Cleaner is een lichte, voorspelbare macOS-app voor veilige schijfopruiming. De kern bestaat uit eenvoudige, betrouwbare Python-logica, verpakt in een overzichtelijke PySide6 GUI. Geen automatische deletes, geen cloud, geen verborgen acties — volledige controle blijft altijd bij de gebruiker.

Met deze app kun je:
In één oogopslag zien hoeveel schijfruimte vrij is (GB en %)
Oude en grote bestanden vinden met aanpasbare en persistente filters.
Bestanden permanent uitsluiten van toekomstige scans via een simpele rechtermuisklik.
Bestanden selecteren via checkboxes en veilig naar de Prullenbak verplaatsen, met directe feedback over de totale grootte van de selectie.
De Prullenbak direct vanuit de app legen.

🔑 Kernprincipes & Veiligheid
Veilige Zoekgebieden
Alleen gebruikersmappen worden gescand: Downloads, Desktop, Documents, Movies. Systeem- en kritieke mappen zijn expliciet uitgesloten.
Altijd Omkeerbaar
Bestanden worden nooit permanent verwijderd door de app zelf. Alles verloopt via de macOS Prullenbak.
Gebruiker aan het Stuur
Grootte-, ouderdom- en limietfilters zijn volledig instelbaar via de GUI en worden onthouden voor de volgende keer. De gebruikersnaam wordt automatisch gedetecterd.

🛠️ Installatie & Voorbereiding
Vereisten
macOS
Python 3
Externe Python-modules:
PySide6 (GUI)
psutil (schijfstatistieken)
send2trash (veilige bestandsverplaatsing)

Modules installeren
Open Terminal in de projectmap (safe-mac-cleaner) en installeer de vereiste modules:
pip3 install PySide6 psutil send2trash

🚀 Opstartinstructies
Zodra de vereiste modules zijn geïnstalleerd, kun je Safe Mac Cleaner op twee manieren starten: via VS Code (aanbevolen) of handmatig via de Terminal.

1. Starten via VS Code Task (aanbevolen)
Zorg dat het bestand .vscode/tasks.json aanwezig is in de projectmap
Open het project in VS Code
Ga naar Terminal → Run Task…
Kies Start Safe Mac Cleaner GUI
Optioneel kun je de app ook starten met de sneltoets ⇧⌘B (Shift + Command + B).

2. Handmatig starten via Terminal
Open Terminal
Navigeer naar de projectmap safe-mac-cleaner
Start de applicatie met:
/usr/bin/python3 smc_gui.py

⚙️ Applicatie-overzicht

🔧 Instellingenmenu (Persistent)
Via Instellingen → Pas Filters Aan… stel je in wat een relevant bestand is voor de volgende scan. Deze instellingen worden nu permanent opgeslagen via QSettings.
Instelling
Standaard
Betekenis
Max. aantal resultaten
100
Beperkt het aantal getoonde bestanden
Minimale ouderdom (dagen)
7
Bestanden jonger dan dit worden genegeerd
Minimale grootte (MB)
1
Neemt alleen bestanden boven deze grootte mee
Tijdscriterium
Last Used
Keuze tussen 'Laatst Benaderd (Gebruikt)' en 'Laatst Gewijzigd (Modified)'.


🖼️ Resultatentabel (Verbeterd)
De tabel toont nu het volledige bestandspad en de numerieke kolommen zijn rechts-uitgelijnd voor betere leesbaarheid.
Context Menu (Rechtermuisklik):
🔍 Toon in Finder
❌ Sluit dit Bestand uit van Scan: Voegt het bestandspad toe aan een persistente uitsluitingslijst (~/.smc_exclusions.json).
🗑️ Verplaats naar Prullenbak
⬇️ Actieknoppen (onderzijde)
Knop
Functie
Start nieuwe scan
Draait een nieuwe scan met huidige filters
Selecteer alles
Selecteert of deselecteert alle items
Toon in Finder
Opent het EERSTE geselecteerde bestand
Verplaats naar Prullenbak
Dynamisch: Toont de totale MB van de selectie op de knop. Verplaatst geselecteerde bestanden.
Leeg Prullenbak
PERMANENT: Leegt de volledige macOS Prullenbak. Dit is een onomkeerbare, permanente actie.


❌ Bewuste beperkingen
Safe Mac Cleaner is bewust beperkt in scope. Alles wat extra risico, complexiteit of onduidelijk gedrag introduceert, is expliciet weggelaten.
De applicatie doet niet het volgende:
❌ Geen automatische of geplande scans op de achtergrond
❌ Geen permanente verwijdering van bestanden (altijd via Prullenbak)
❌ Geen toegang tot systeemmappen of verborgen OS-paden
❌ Geen cloud-sync, upload of externe communicatie
❌ Geen slimme heuristieken of "AI-beslissingen" over wat weg mag
Elke actie vereist expliciete gebruikersinput en bevestiging.

🎯 Doel van dit project
Safe Mac Cleaner is gebouwd als een persoonlijke utility: klein, voorspelbaar en veilig. Het biedt een bewuste en gecontroleerde manier om schijfruimte vrij te maken, zonder de complexiteit of risico's van commerciële cleaners.

