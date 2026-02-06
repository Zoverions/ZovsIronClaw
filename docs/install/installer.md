---
summary: "Information about the legacy OpenClaw installer scripts"
read_when:
  - You want to understand `openclaw.ai/install.sh`
  - You want to automate installs (CI / headless)
title: "Installer Internals"
---

# Installer internals

<Warning>
**ZovsIronClaw Note**: The standard OpenClaw installer scripts (`openclaw.ai/install.sh`, etc.) install the *original* OpenClaw package. To install ZovsIronClaw with GCA support, please follow the **From Source** instructions in [Install](/install).
</Warning>

This page documents the behavior of the upstream OpenClaw installer scripts for reference.

| Script                              | Platform             | What it does                                                                                 |
| ----------------------------------- | -------------------- | -------------------------------------------------------------------------------------------- |
| [`install.sh`](#install-sh)         | macOS / Linux / WSL  | Installs Node if needed, installs OpenClaw via npm (default) or git, and can run onboarding. |
| [`install-cli.sh`](#install-cli-sh) | macOS / Linux / WSL  | Installs Node + OpenClaw into a local prefix (`~/.openclaw`). No root required.              |
| [`install.ps1`](#install-ps1)       | Windows (PowerShell) | Installs Node if needed, installs OpenClaw via npm (default) or git, and can run onboarding. |

*(Remainder of document refers to standard OpenClaw installation behavior)*
