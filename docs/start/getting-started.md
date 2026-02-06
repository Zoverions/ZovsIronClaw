---
summary: "Get ZovsIronClaw installed and run your first chat in minutes."
read_when:
  - First time setup from zero
  - You want the fastest path to a working chat
title: "Getting Started"
---

# Getting Started

Goal: go from zero to a first working chat with minimal setup.

<Info>
Fastest chat: open the Control UI (no channel setup needed). Run `zovsironclaw dashboard`
and chat in the browser, or open `http://127.0.0.1:18789/` on the
<Tooltip headline="Gateway host" tip="The machine running the ZovsIronClaw gateway service.">gateway host</Tooltip>.
Docs: [Dashboard](/web/dashboard) and [Control UI](/web/control-ui).
</Info>

## Prereqs

- Node 22 or newer
- Docker & Docker Compose (for the GCA service)

<Tip>
Check your Node version with `node --version` if you are unsure.
</Tip>

## Quick setup (CLI)

<Steps>
  <Step title="Install ZovsIronClaw">
    Since this is a custom fork, we recommend installing from source:

    ```bash
    git clone https://github.com/Zoverions/ZovsIronClaw.git
    cd ZovsIronClaw
    pnpm install
    pnpm build
    npm link
    ```

    This makes the `zovsironclaw` command available globally.
  </Step>
  <Step title="Start the GCA Service">
    ZovsIronClaw requires the Python GCA service to be running.

    ```bash
    docker-compose up -d gca-service
    ```
  </Step>
  <Step title="Run the onboarding wizard">
    ```bash
    zovsironclaw onboard --install-daemon
    ```

    The wizard configures auth, gateway settings, and optional channels.
    See [Onboarding Wizard](/start/wizard) for details.

  </Step>
  <Step title="Check the Gateway">
    If you installed the service, it should already be running:

    ```bash
    zovsironclaw gateway status
    ```

  </Step>
  <Step title="Open the Control UI">
    ```bash
    zovsironclaw dashboard
    ```
  </Step>
</Steps>

<Check>
If the Control UI loads, your Gateway is ready for use.
</Check>

## Optional checks and extras

<AccordionGroup>
  <Accordion title="Run the Gateway in the foreground">
    Useful for quick tests or troubleshooting.

    ```bash
    zovsironclaw gateway --port 18789
    ```

  </Accordion>
  <Accordion title="Send a test message">
    Requires a configured channel.

    ```bash
    zovsironclaw message send --target +15555550123 --message "Hello from ZovsIronClaw"
    ```

  </Accordion>
</AccordionGroup>

## Go deeper

<Columns>
  <Card title="GCA Integration" href="/docs/gca-integration">
    Learn about the ethical reasoning engine.
  </Card>
  <Card title="Onboarding Wizard (details)" href="/start/wizard">
    Full CLI wizard reference and advanced options.
  </Card>
</Columns>

## What you will have

- A running Gateway
- A running GCA Service (the Conscience)
- Auth configured
- Control UI access or a connected channel

## Next steps

- DM safety and approvals: [Pairing](/start/pairing)
- Connect more channels: [Channels](/channels)
- Advanced workflows and from source: [Setup](/start/setup)
