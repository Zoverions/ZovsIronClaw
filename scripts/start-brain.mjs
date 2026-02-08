import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const serviceDir = path.join(rootDir, "apps", "gca-service");

// Detect Platform
const isWin = process.platform === "win32";

// Path to venv python
let pythonPath;
if (isWin) {
    pythonPath = path.join(serviceDir, ".venv", "Scripts", "python.exe");
} else {
    pythonPath = path.join(serviceDir, ".venv", "bin", "python");
}

// Fallback to system python if venv not found (but warn)
if (!fs.existsSync(pythonPath)) {
    console.warn(`[GCA-BRAIN] Virtual environment python not found at ${pythonPath}. Trying system python.`);
    pythonPath = isWin ? "python" : "python3";
}

console.log(`[GCA-BRAIN] Starting GCA Service using: ${pythonPath}`);

const args = ["-m", "uvicorn", "api_server:app", "--host", "127.0.0.1", "--port", "8000", "--reload"];

const child = spawn(pythonPath, args, {
    cwd: serviceDir,
    stdio: "inherit",
    env: { ...process.env, PYTHONUNBUFFERED: "1" }
});

child.on("error", (err) => {
    console.error(`[GCA-BRAIN] Failed to start process: ${err.message}`);
});

child.on("exit", (code) => {
    console.log(`[GCA-BRAIN] Process exited with code ${code}`);
    process.exit(code || 0);
});
