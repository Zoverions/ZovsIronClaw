#!/usr/bin/env python3
"""
ZovsIronClaw Unified Installer
Simplifies setup for Windows, macOS, and Linux.
"""

import os
import sys
import subprocess
import shutil
import platform

def print_step(msg):
    print(f"\n🔹 {msg}")

def check_command(cmd, name):
    try:
        subprocess.check_call([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    print("=========================================")
    print("   ZovsIronClaw Unified Installer v1.0   ")
    print("=========================================")

    # 1. Check Prerequisites
    print_step("Checking Prerequisites...")

    if not check_command("node", "Node.js"):
        print("❌ Node.js not found. Please install Node.js v20+.")
        sys.exit(1)

    if not check_command("python3", "Python 3"):
        # On Windows it might be 'python'
        if not check_command("python", "Python 3"):
            print("❌ Python 3 not found. Please install Python 3.11+.")
            sys.exit(1)

    print("✅ Prerequisites met.")

    # 2. Install Python Dependencies
    print_step("Installing Python Dependencies...")
    req_path = os.path.join("apps", "gca-service", "requirements.txt")
    if os.path.exists(req_path):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
    else:
        print(f"⚠️ Warning: {req_path} not found.")

    # 3. Install Node Dependencies
    print_step("Installing Node Dependencies...")
    subprocess.check_call(["npm", "install"], shell=(platform.system() == "Windows"))

    # 4. Environment Setup
    print_step("Configuring Environment...")
    env_example = ".env.ironclaw.example"
    env_target = ".env"

    if not os.path.exists(env_target):
        if os.path.exists(env_example):
            shutil.copy(env_example, env_target)
            print("✅ Created .env from example.")
        else:
            print("⚠️ Example .env not found.")
    else:
        print("ℹ️ .env already exists.")

    # 5. API Key Setup
    print_step("API Key Configuration (Optional)")
    print("To use external models (GPT-4, Grok), you need API keys.")
    setup_keys = input("Do you want to configure API keys now? (y/n): ").strip().lower()

    if setup_keys == 'y':
        openai_key = input("Enter OpenAI API Key (leave blank to skip): ").strip()
        grok_key = input("Enter Grok/X.AI API Key (leave blank to skip): ").strip()

        with open(env_target, "a") as f:
            if openai_key:
                f.write(f"\nOPENAI_API_KEY={openai_key}")
            if grok_key:
                f.write(f"\nGROK_API_KEY={grok_key}")
        print("✅ API keys appended to .env")

    # 6. Build Desktop App
    print_step("Desktop App Setup")
    build_desktop = input("Do you want to build the Desktop App (Tauri)? (y/n): ").strip().lower()

    if build_desktop == 'y':
        # Check Rust
        if not check_command("cargo", "Rust"):
            print("❌ Rust (cargo) not found. Required for Tauri build.")
            print("👉 Install Rust: https://rustup.rs/")
        else:
            print("Building Desktop App... (This may take a while)")
            try:
                # Build Python binary first
                cwd = os.getcwd()
                os.chdir("apps/gca-service")
                subprocess.check_call([sys.executable, "build_binary.py"])
                os.chdir(cwd)

                # Build Tauri
                os.chdir("apps/desktop")
                subprocess.check_call(["npm", "install"], shell=(platform.system() == "Windows"))
                subprocess.check_call(["npm", "run", "tauri", "build"], shell=(platform.system() == "Windows"))
                os.chdir("../..")
                print("✅ Desktop App Built Successfully!")
            except Exception as e:
                print(f"❌ Build failed: {e}")

    print("\n=========================================")
    print("   Installation Complete! 🚀")
    print("   Run: npm run start:local")
    print("=========================================")

if __name__ == "__main__":
    main()
