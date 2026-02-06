---
summary: "Install ZovsIronClaw — from source (recommended for this fork)"
read_when:
  - You need an install method other than the Getting Started quickstart
  - You want to deploy to a cloud platform
  - You need to update, migrate, or uninstall
title: "Install"
---

# Install

Already followed [Getting Started](/start/getting-started)? You're all set — this page is for alternative install methods, platform-specific instructions, and maintenance.

## System requirements

- **[Node 22+](/install/node)**
- macOS, Linux, or Windows
- `pnpm` (required for building from source)
- Docker & Docker Compose (for the GCA service)

<Note>
On Windows, we strongly recommend running ZovsIronClaw under [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).
</Note>

## Install methods

<Tip>
Since ZovsIronClaw is a specialized fork with the GCA service, installing from source is the primary supported method.
</Tip>

<AccordionGroup>
  <Accordion title="From source (Recommended)" icon="github" defaultOpen>
    For contributors or anyone who wants to run ZovsIronClaw.

    <Steps>
      <Step title="Clone and build">
        Clone the [ZovsIronClaw repo](https://github.com/Zoverions/ZovsIronClaw) and build:

        ```bash
        git clone https://github.com/Zoverions/ZovsIronClaw.git
        cd ZovsIronClaw
        pnpm install
        pnpm ui:build
        pnpm build
        ```
      </Step>
      <Step title="Link the CLI">
        Make the `zovsironclaw` command available globally:

        ```bash
        pnpm link --global
        ```

        Alternatively, skip the link and run commands via `./zovsironclaw.mjs ...` from inside the repo.
      </Step>
      <Step title="Start GCA Service">
        ```bash
        docker-compose up -d gca-service
        ```
      </Step>
      <Step title="Run onboarding">
        ```bash
        zovsironclaw onboard --install-daemon
        ```
      </Step>
    </Steps>

    For deeper development workflows, see [Setup](/start/setup).

  </Accordion>
</AccordionGroup>

## Other install methods

<CardGroup cols={2}>
  <Card title="Docker" href="/install/docker" icon="container">
    Containerized or headless deployments.
  </Card>
  <Card title="Nix" href="/install/nix" icon="snowflake">
    Declarative install via Nix.
  </Card>
  <Card title="Ansible" href="/install/ansible" icon="server">
    Automated fleet provisioning.
  </Card>
  <Card title="Bun" href="/install/bun" icon="zap">
    CLI-only usage via the Bun runtime.
  </Card>
</CardGroup>

## After install

Verify everything is working:

```bash
zovsironclaw doctor         # check for config issues
zovsironclaw status         # gateway status
zovsironclaw dashboard      # open the browser UI
```

## Troubleshooting: `zovsironclaw` not found

<Accordion title="PATH diagnosis and fix">
  Quick diagnosis:

```bash
node -v
npm -v
npm prefix -g
echo "$PATH"
```

If `$(npm prefix -g)/bin` (macOS/Linux) or `$(npm prefix -g)` (Windows) is **not** in your `$PATH`, your shell can't find global npm binaries (including `zovsironclaw`).

Fix — add it to your shell startup file (`~/.zshrc` or `~/.bashrc`):

```bash
export PATH="$(npm prefix -g)/bin:$PATH"
```

On Windows, add the output of `npm prefix -g` to your PATH.

Then open a new terminal (or `rehash` in zsh / `hash -r` in bash).
</Accordion>

## Update / uninstall

<CardGroup cols={3}>
  <Card title="Updating" href="/install/updating" icon="refresh-cw">
    Keep ZovsIronClaw up to date.
  </Card>
  <Card title="Migrating" href="/install/migrating" icon="arrow-right">
    Move to a new machine.
  </Card>
  <Card title="Uninstall" href="/install/uninstall" icon="trash-2">
    Remove ZovsIronClaw completely.
  </Card>
</CardGroup>
