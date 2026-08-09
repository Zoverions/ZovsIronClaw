# Portfolio status and runtime boundary

Evidence snapshot: `1a6f351676e55b800368803fd9b72ad8ae2a535f` (2026-08-09 review)

## Current status

ZovsIronClaw is the canonical Zoverions runtime, gateway, channel, and agent-execution foundation. It is an experimental fork-derived codebase, not a validated ethical authority or production-qualified high-risk control system. The recorded default-branch baseline did not pass, 17 material claim candidates remain unverified, and one revoked GitHub OAuth credential artifact remains in public history pending a separately approved history rewrite.

The repository must not claim that a “moral,” “soul,” entropy, thermodynamic, or GCA score proves ethical correctness. Such components are optional policy experiments whose failure and bypass behavior must be tested.

## Product boundary

- ZovsIronClaw owns runtime execution, gateway behavior, device/runtime integration, and channel adapters.
- IronAgent owns product/control-plane orchestration, approval state, capability registry, and rollback coordination.
- Shared behavior must use versioned, least-privilege contracts rather than copied runtime trees.
- High-risk or externally consequential actions must fail closed when policy or authorization is unavailable.

See [`UPSTREAM_DIVERGENCE.md`](UPSTREAM_DIVERGENCE.md) and [`UPSTREAM_SYNC_POLICY.md`](UPSTREAM_SYNC_POLICY.md). Draft PR #142 separately removes only the orphan `.nvm` gitlink; it does not resolve the broader upstream, cache-artifact, claim, or history-remediation work.
