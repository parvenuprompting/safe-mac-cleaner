# Safe Mac Cleaner

[![CI](https://github.com/parvenuprompting/safe-mac-cleaner/actions/workflows/ci.yml/badge.svg)](https://github.com/parvenuprompting/safe-mac-cleaner/actions/workflows/ci.yml)
[![v3 alpha](https://img.shields.io/badge/v3-3.0.0--alpha.3-orange)](https://github.com/parvenuprompting/safe-mac-cleaner/releases/tag/v3.0.0-alpha.3)
[![Latest v2 release](https://img.shields.io/github/v/release/parvenuprompting/safe-mac-cleaner?filter=v2.*&label=v2%20stable&color=2ea44f)](https://github.com/parvenuprompting/safe-mac-cleaner/releases)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=111111)](v3/README.md)
[![Tauri](https://img.shields.io/badge/Tauri-2-24C8DB?logo=tauri&logoColor=111111)](v3/README.md)
[![Rust](https://img.shields.io/badge/Rust-1.94%2B-000000?logo=rust&logoColor=white)](v3/README.md)
[![macOS](https://img.shields.io/badge/platform-macOS-000000?logo=apple&logoColor=white)](https://www.apple.com/macos/)

Safe Mac Cleaner is een lokale macOS-app om oude en grote persoonlijke bestanden gecontroleerd op te ruimen. De **v3-lijn** is de actieve ontwikkelversie: een React 19 + TypeScript-interface bovenop een kleine Rust/Tauri 2 desktoplaag.

Geen cloud, geen verborgen verwijderacties en geen AI-runtime. De gebruiker bepaalt wat er gebeurt; bestanden worden alleen naar de macOS-Prullenbak verplaatst.

## V3 Status

De huidige v3-alpha is `3.0.0-alpha.3` en ondersteunt:

- Scannen van veilige gebruikersmappen op macOS Apple Silicon
- Grootte-, ouderdoms- en limietfilters
- Vooraf ingestelde scanprofielen en aangepaste filters
- Live scanprogress en scanannulering
- Bescherming van Photos Libraries en andere macOS-pakketten
- Zoekbare resultaten met selectie en totale bestandsgrootte
- Stale-file controle vóór verwijderen
- Verplaatsen naar de Prullenbak met foutresultaten per bestand
- Een bestand onthullen in Finder
- Eigen v3-logo en native macOS icon-set
- Lokale clipboard- en store-pluginbasis voor volgende features

De v3-resultatenweergave en Rust-scanengine zijn gekoppeld. De app is nog een alpha: instellingenpersistentie, uitsluitingenbeheer en scanhistorie worden nog verder gemigreerd vanuit v2.x.

## Veiligheidsmodel

De Rust-engine valideert scan- en delete-acties onafhankelijk van de frontend:

- Alleen bestaande submappen van de gebruikers-home-directory zijn toegestaan.
- De home-directory zelf en paden buiten de home-directory worden geweigerd.
- Systeemmappen, verborgen bestanden en macOS-pakketten worden overgeslagen.
- Photos Libraries worden niet geopend.
- Symlinks worden niet gevolgd.
- Voor verwijderen worden pad, bestandstype, grootte en wijzigingsdatum opnieuw gecontroleerd.
- Verwijderen gaat via de macOS-Prullenbak, niet via permanente filesystem-delete.

## V3 Installeren

### Vereisten

- macOS op Apple Silicon
- Node.js 22 of nieuwer
- Rust en Cargo

### Development starten

```bash
cd v3
npm install
npm run tauri:dev
```

Alleen de frontend starten:

```bash
npm run dev
```

### V3 testen

```bash
npm run build
npm run test
npm run test:e2e
cd src-tauri
cargo check
cargo test
```

De GitHub Actions CI voert deze frontend-, Rust- en E2E-checks automatisch uit.

## V3 Structuur

```text
v3/
├── src/                    React-interface en frontendlogica
├── src-tauri/src/scanner.rs   Veilige Rust-scanengine
├── src-tauri/src/deletion.rs  Stale-file controle en Trash-acties
├── src-tauri/src/lib.rs       Tauri commands en events
├── src-tauri/icons/           Eigen native macOS icon-set
└── tests/e2e/                 Playwright desktop-preview tests
```

Belangrijke Tauri commands:

- `scan_files`: scan veilige gebruikersmappen
- `cancel_scan`: annuleer de actieve scan
- `move_to_trash`: verplaats geselecteerde bestanden na metadata-check
- `reveal_in_finder`: toon een bestand in Finder

## V3 Releases

Een v3-alpha wordt gepubliceerd met een `v3.*`-tag:

```bash
git tag v3.0.0-alpha.3
git push origin v3.0.0-alpha.3
```

De workflow `.github/workflows/release-v3.yml` bouwt een Apple Silicon `Safe Mac Cleaner v3.app`, verpakt de app als zip en publiceert een GitHub prerelease.

De laatste v3-release staat op:

https://github.com/parvenuprompting/safe-mac-cleaner/releases/tag/v3.0.0-alpha.3

Signing en notarization zijn nog niet geconfigureerd voor de alpha-builds.

## V2.x Stable

De bestaande Python/PySide6-app blijft als stabiele v2.x-lijn beschikbaar in de repositoryroot. Deze versie bevat onder andere:

- Persistente instellingen, uitsluitingen en scanhistorie
- Finder-integratie en macOS-Prullenbakacties
- Python-tests en PyInstaller-releasebuilds

Start v2.x lokaal vanuit de root:

```bash
.venv/bin/python smc_gui.py
```

De nieuwste stabiele v2-release is `v2.1.0`. Nieuwe desktopfunctionaliteit wordt primair in `v3/` ontwikkeld; v2.x blijft beschikbaar voor bestaande gebruikers en regressievergelijking.

## Projectprincipes

Safe Mac Cleaner blijft bewust klein, lokaal en voorspelbaar. De app maakt geen claims over “magische” performancewinst en gebruikt geen cloud of modelgebaseerde beslissingen om bestanden te verwijderen.
