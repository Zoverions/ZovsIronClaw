# ZovsIronClaw Desktop (Iron Shell)

This directory contains the Tauri v2 application that serves as the desktop installer and wrapper for ZovsIronClaw. It bundles the Python GCA service as a sidecar and wraps the existing Web UI.

## Architecture

- **Frontend**: Reuses the `ui` workspace (Vite + Lit).
- **Backend (Rust)**: Manages the system tray, file system, and spawns the Python sidecar.
- **Sidecar (Python)**: The `gca-service` compiled into a standalone executable.

## Development

### Prerequisites

1.  **Node.js** (v20+) & **pnpm**
2.  **Rust** (Stable)
3.  **Python 3.12+** & **PyInstaller** (to build the sidecar)

### Setup

1.  **Build the Sidecar**:
    The desktop app requires the compiled `gca-brain` binary.
    ```bash
    cd ../../gca-service
    pip install -r requirements.txt
    pip install pyinstaller
    python build_binary.py
    ```
    This will generate `gca-service/dist/gca-brain`.

2.  **Run Development Mode**:
    ```bash
    cd ../../apps/desktop
    pnpm install
    pnpm tauri dev
    ```
    This command will:
    - Run `scripts/move-binary.js` to place the sidecar in `src-tauri/binaries/`.
    - Start the `ui` dev server.
    - Launch the Tauri app window.

## Building for Production

To create an installer (`.msi`, `.dmg`, `.deb`):

```bash
pnpm tauri build
```

This automates the entire process:
1.  Invokes `scripts/move-binary.js` to rename and move the Python binary with the correct target triple (e.g., `gca-brain-x86_64-pc-windows-msvc.exe`).
2.  Builds the `ui` frontend.
3.  Compiles the Rust backend.
4.  Bundles everything into an installer.

## Project Structure

- `src-tauri/`: Rust backend code.
  - `src/lib.rs`: Main logic for sidecar orchestration and model downloading.
  - `tauri.conf.json`: Tauri configuration.
- `scripts/`: Helper scripts.
  - `move-binary.js`: Handles sidecar binary renaming and placement.

## Icons

The `src-tauri/icons/` directory currently contains placeholder files. Before releasing, replace these with real assets:
- `icon.ico`: Windows icon
- `icon.icns`: macOS icon
- `32x32.png`, `128x128.png`: Linux/Tray icons
