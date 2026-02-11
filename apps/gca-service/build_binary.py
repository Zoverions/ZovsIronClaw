import PyInstaller.__main__
import os
import sys
import shutil

# ============================================================================
# GCA Brain Build Script (PyInstaller)
# ============================================================================
# This script bundles the GCA FastAPI service (`api_server.py`) into a single
# standalone executable named `gca-brain`.
#
# Requirements:
#   - Python 3.12+
#   - pyinstaller
#   - Installed dependencies from `requirements.txt`
#
# Usage:
#   1. Install dependencies:
#      pip install -r requirements.txt
#      pip install pyinstaller
#
#   2. Run script:
#      python build_binary.py
#
# Output:
#   - dist/gca-brain (Linux/macOS) OR dist/gca-brain.exe (Windows)
#
# This binary is then consumed by the Tauri Desktop App (`apps/desktop`).
# ============================================================================

# Ensure we are in the gca-service directory
script_dir = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != script_dir:
    os.chdir(script_dir)

cwd = os.getcwd()
print(f"Current working directory: {cwd}")

print("Starting GCA Brain build process...")

# Clean previous builds
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')

# Define paths
gca_core_path = os.path.join(cwd, 'gca_core')
config_path = os.path.join(cwd, 'config.yaml')

if not os.path.exists(gca_core_path):
    print(f"Error: gca_core not found at {gca_core_path}")
    sys.exit(1)

# PyInstaller arguments
args = [
    'api_server.py',
    '--name=gca-brain',
    '--onefile',
    f'--add-data={gca_core_path}{os.pathsep}gca_core',  # Include the core library
    f'--add-data={config_path}{os.pathsep}.',      # Default config
    '--clean',
    '--collect-all=uvicorn',
    '--collect-all=fastapi',
    '--collect-all=pydantic',
    # We will let the mocks be collected if present
]

# Check if heavy deps are installed
try:
    import torch
    args.append('--collect-all=torch')
except ImportError:
    pass

try:
    import transformers
    args.append('--collect-all=transformers')
except ImportError:
    pass

try:
    import sentence_transformers
    args.append('--collect-all=sentence_transformers')
except ImportError:
    pass

print(f"Running PyInstaller with args: {args}")

PyInstaller.__main__.run(args)

print("Build complete. Binary should be in gca-service/dist/gca-brain")
