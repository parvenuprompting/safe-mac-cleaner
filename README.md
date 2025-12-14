````markdown
# 🔎 Safe Mac Cleaner (SMC) v3.8 - The GUI Edition

**SMC v3.8** is een lichtgewicht, console-gebaseerde logica, verpakt in een krachtige **PySide6 Graphical User Interface (GUI)** voor veilige en doelgerichte schijfopruiming op macOS.

Dit project stelt de gebruiker in staat om:
* De actuele schijfstatus (GB Vrij / % Vrij) te zien.
* Oude, grote bestanden te identificeren via aanpasbare filters.
* Geselecteerde bestanden veilig naar de Prullenbak te verplaatsen met behulp van checkboxes.
* De Prullenbak direct vanuit de app te legen.

## 🔑 Kernprincipes & Veiligheid

* **Veilige Zones:** Scant uitsluitend de gebruikersmappen (`Downloads`, `Desktop`, `Documents`, `Movies`). Kritieke systeemmappen worden geblokkeerd.
* **Omkeerbare Actie:** Bestanden worden **nooit permanent verwijderd** (alleen verplaatst naar de macOS Prullenbak).
* **Dynamische Controle:** Alle filters (grootte, ouderdom, aantal getoonde items) zijn aanpasbaar via het Instellingenmenu in de GUI.

## 🛠️ Installatie & Voorbereiding

Dit project vereist Python 3 en de volgende externe modules: `PySide6` (voor de GUI), `psutil` (voor schijfstatistieken) en `send2trash`.

### 1. Modules Installeren

Open uw Terminal in de projectmap (`safe-mac-cleaner`) en installeer de vereiste modules:

```bash
pip3 install PySide6 psutil send2trash
````

### 2. Snel starten via VS Code (Aanbevolen)

Om de applicatie direct met één klik te starten vanuit VS Code, moet u een Task instellen.

**Stappen:**

1. Ga in VS Code naar het menu **Terminal** > **Configure Tasks...**
2. Kies "Create tasks.json file from template" en selecteer dan "Others".
3. Vervang de inhoud van het nieuwe bestand `.vscode/tasks.json` door de volgende code:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start Safe Mac Cleaner GUI",
            "type": "shell",
            "command": "/usr/bin/python3",
            "args": [
                "${workspaceFolder}/smc_gui.py"
            ],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        }
    ]
}
```

Nadat u dit bestand heeft opgeslagen, kunt u de app starten via **Terminal > Run Task... > Start Safe Mac Cleaner GUI** (of met de sneltoets **⇧⌘B**).

### 3. Handmatig Starten

Voer het script direct uit in de Terminal:

```bash
/usr/bin/python3 smc_gui.py
```

## ⚙️ Applicatie Functies

De GUI bevat de volgende primaire elementen en controles:

### 🔧 Instellingenmenu

Via **Instellingen > Pas Filters Aan...** in de menubalk kunt u de scanfilters voor de volgende scan aanpassen:

| Instelling                    | Standaardwaarde | Functie                                                 |
| :---------------------------- | :-------------- | :------------------------------------------------------ |
| **Max. Aantal Resultaten**    | `100`           | Beperkt de weergave van de grootste items.              |
| **Minimale Ouderdom (Dagen)** | `7`             | Hoe oud moet een bestand zijn om getoond te worden.     |
| **Minimale Grootte (MB)**     | `1`             | Minimale grootte (in MB) van bestanden om mee te nemen. |

### 🖼️ Tabel & Selectie

De tabel toont de gevonden bestanden (gesorteerd op grootte):

* **Selecteer:** Gebruik de checkboxen om losse bestanden te selecteren voor verwijdering.
* **#:** Sequentiële nummering voor overzicht.
* **Grootte & Ouderdom:** De kritieke data voor besluitvorming.

### ⬇️ Actie Knoppen (Onderkant)

| Knop                                            | Actie                                                                               |
| :---------------------------------------------- | :---------------------------------------------------------------------------------- |
| **🚀 Start Nieuwe Scan**                        | Herstart de scan met de laatst ingestelde filters.                                  |
| **✅ Selecteer Alles**                           | Vinkt alle getoonde items aan of uit.                                               |
| **🔍 Toon Selectie in Finder**                  | Opent de locatie van het eerst aangevinkte bestand in Finder voor context.          |
| **🗑️ Verplaats Geselecteerde naar Prullenbak** | Verplaatst alle aangevinkte items naar de macOS Prullenbak.                         |
| **🗑️ Leeg Prullenbak**                         | Start het macOS-proces om de Prullenbak permanent te legen (vraagt om bevestiging). |

```