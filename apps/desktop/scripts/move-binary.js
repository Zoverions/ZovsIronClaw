const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Determine the current OS target triple (Rust naming convention)
// This script assumes it's running on the build machine
function getTargetTriple() {
    const arch = process.arch === 'x64' ? 'x86_64' : 'aarch64';
    let platform = '';

    switch (process.platform) {
        case 'win32':
            platform = 'pc-windows-msvc';
            break;
        case 'darwin':
            platform = 'apple-darwin';
            break;
        case 'linux':
            platform = 'unknown-linux-gnu';
            break;
        default:
            throw new Error(`Unsupported platform: ${process.platform}`);
    }

    return `${arch}-${platform}`;
}

const targetTriple = getTargetTriple();
console.log(`Building for target: ${targetTriple}`);

// Paths
const rootDir = path.resolve(__dirname, '../../..');
const desktopDir = path.resolve(__dirname, '..');
const gcaServiceDir = path.join(rootDir, 'apps', 'gca-service');
const tauriBinDir = path.join(desktopDir, 'src-tauri', 'binaries');

// Source binary (built by PyInstaller)
const srcBinaryName = process.platform === 'win32' ? 'gca-brain.exe' : 'gca-brain';
const srcBinaryPath = path.join(gcaServiceDir, 'dist', srcBinaryName);

// Target binary (Tauri sidecar naming convention: name-target-triple.extension)
const destBinaryName = process.platform === 'win32'
    ? `gca-brain-${targetTriple}.exe`
    : `gca-brain-${targetTriple}`;
const destBinaryPath = path.join(tauriBinDir, destBinaryName);

// Ensure binaries directory exists
if (!fs.existsSync(tauriBinDir)) {
    fs.mkdirSync(tauriBinDir, { recursive: true });
}

// Check if source exists
if (fs.existsSync(srcBinaryPath)) {
    console.log(`Moving binary from ${srcBinaryPath} to ${destBinaryPath}`);
    fs.copyFileSync(srcBinaryPath, destBinaryPath);
    // Make executable on unix
    if (process.platform !== 'win32') {
        fs.chmodSync(destBinaryPath, '755');
    }
} else {
    console.warn(`Warning: Source binary not found at ${srcBinaryPath}.`);
    console.warn("Ensure you have run the PyInstaller build step first (e.g., 'python gca-service/build_binary.py').");
    console.warn("For development/CI without the binary, creating a dummy placeholder.");

    // Create a dummy placeholder to allow Tauri build to succeed in CI/incomplete environments
    if (!fs.existsSync(destBinaryPath)) {
        fs.writeFileSync(destBinaryPath, '');
        if (process.platform !== 'win32') {
            fs.chmodSync(destBinaryPath, '755');
        }
    }
}
