# Safe Mac Cleaner v3

[![CI](https://github.com/parvenuprompting/safe-mac-cleaner/actions/workflows/ci.yml/badge.svg)](https://github.com/parvenuprompting/safe-mac-cleaner/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-3.0.0--alpha.2-orange)](https://github.com/parvenuprompting/safe-mac-cleaner/tree/main/v3)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=111111)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8%2B-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2-24C8DB?logo=tauri&logoColor=111111)](https://tauri.app/)
[![Rust](https://img.shields.io/badge/Rust-desktop%20layer-000000?logo=rust&logoColor=white)](https://www.rust-lang.org/)

This is the separate React + Tauri v3 line. The existing Python/PySide6 application remains the stable v2.x line in the repository root.

## Requirements

- macOS on Apple Silicon for the current target
- Node.js 22 or newer
- Rust and Cargo

## Development

```bash
npm install
npm run dev
```

Run the desktop shell with:

```bash
npm run tauri:dev
```

## Checks

```bash
npm run build
npm run test
npm run test:e2e
```

The first v3 milestone contains the frontend shell, Tauri 2 commands, local clipboard/store plugins and test foundations. The Rust scanner is available through `scan_files`, with progress events and cancellation through `cancel_scan`. The React results view is connected to the scanner and selected files can be moved to the macOS Trash after stale-file validation.

The **Aangepaste scan** profile exposes editable filters for minimum file size, minimum age and maximum result count. Preset profiles remain available for faster scans.

Results can be selected for safe Trash deletion or revealed in Finder. The main panels reserve their space during progress and profile changes to keep the desktop layout stable.

## v3 Alpha Release

Create a v3 alpha release from the repository root with:

```bash
git tag v3.0.0-alpha.2
git push origin v3.0.0-alpha.2
```

The `v3.*` GitHub Actions workflow builds an Apple Silicon `Safe Mac Cleaner v3.app` with the v3 logo and native macOS icon, then publishes it as a prerelease. Signing and notarization are not configured for the alpha yet.
