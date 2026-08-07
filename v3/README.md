# Safe Mac Cleaner v3

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

The first v3 milestone contains the frontend shell, Tauri 2 commands, local clipboard/store plugins and test foundations. The Rust scanner is now available through the `scan_files` command; the React results table will be connected in the next step.
