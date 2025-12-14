# 🔎 Safe Mac Cleaner (SMC) v3.2

**SMC v3.2** is een lichtgewicht, console-gebaseerde **Beslis-hulpmiddel** (`Decision Helper`) ontworpen in Python om gebruikers te helpen bij het **veilig** en **doelgericht** opschonen van grote, ongebruikte bestanden op macOS.

Dit programma is geen automatische "Cleaner", maar een transparante tool die de gebruiker volledige controle geeft over welke bestanden naar de prullenbak worden verplaatst.

## 🔑 Kernprincipes & Veiligheid

* **Veilige Zones:** Scant uitsluitend de mappen `/Downloads`, `/Desktop`, `/Documents`, en `/Movies`. Kritieke systeemmappen zoals `/System` en `~/Library` worden geblokkeerd.
* **Omkeerbare Actie:** Bestanden worden **nooit permanent verwijderd** (`os.remove`), maar veilig verplaatst naar de macOS Prullenbak met behulp van de `send2trash` module.
* **Nauwkeurige Context:** Filtert op **Grootte** (vanaf 10 MB) én **Laatst Benaderde Tijd** (vanaf 7 dagen) om bestanden te identificeren die daadwerkelijk al lange tijd niet geopend zijn.
* **Batch Controle:** Ondersteunt interactieve groepsacties om snel grote hoeveelheden ruimte vrij te maken.

## 🛠️ Installatie & Voorbereiding

Dit project vereist Python 3 en één externe module.

### 1. Module Installeren

Open uw Terminal in de projectmap (`safe-mac-cleaner`) en installeer de vereiste module:

```bash
pip3 install send2trash