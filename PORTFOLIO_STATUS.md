# Portfolio status and runtime boundary

Status date: 2026-08-10

## Current status

ZovsIronClaw is the canonical Zoverions runtime, gateway, channel, and agent-execution foundation. It is a large OpenClaw-derived codebase with a fork-specific experimental GCA layer. It is **not** a validated ethical authority or a production-qualified high-risk control system.

The recorded full/default-application baseline remains failed and 17 material claim candidates from the earlier audit remain unverified. A revoked GitHub OAuth credential artifact also remains in public history pending a separately justified history-remediation decision; no history rewrite is part of this branch.

The repository must not claim that a “moral,” “soul,” entropy, thermodynamic, causal-emergence, or GCA score proves ethical correctness, trust, authorization, or production safety. Those outputs are research/policy heuristics only.

## GCA authority boundary implemented on this branch

The fork-specific GCA service/provider is now default-deny at the authority boundary:

- every `/v1/*` GCA control route requires the configured `GCA_API_KEY`;
- if no API key is configured, the control API fails closed with service unavailable rather than inventing a fallback credential;
- invalid/missing credentials are rejected before the control endpoint executes;
- `/health` remains outside the control API and reports whether the experimental runtime is enabled;
- the Pulse background loop is disabled unless `GCA_ENABLE_EXPERIMENTAL_RUNTIME=1`;
- mesh listener startup and network-visible device registration/broadcast are disabled unless that same explicit experimental-runtime flag is enabled;
- governance proposal/vote/mining, remote swarm tasks, and memory-sync mutation are rejected while the experimental runtime is disabled;
- reasoning-generated memory propagation is disabled unless the experimental runtime is explicitly enabled;
- the OpenClaw GCA provider requires `GCA_API_KEY` and sends `X-GCA-API-Key` to the service;
- provider transport defaults to loopback HTTP; plaintext HTTP is rejected for non-loopback destinations and non-local transport must use HTTPS;
- the former `_gca_token` moral-signature authority stamp has been removed from the provider;
- GCA-generated tool calls are not forwarded by the provider unless `GCA_ENABLE_EXPERIMENTAL_TOOL_CALLS=1`;
- the GCA service itself also suppresses tool-call output from both `/v1/reason` and `/v1/chat/completions` unless that explicit tool-call flag is enabled;
- when tool-call output is suppressed, the service returns advisory text/metadata rather than a standard executable tool-call object or moral-signature authorization artifact.

Explicit experimental opt-in does **not** convert GCA moral/entropy/thermodynamic scores or signatures into capability grants. Any forwarded tool suggestion remains subject to the normal OpenClaw approval, sandbox, authorization, and tool-policy boundaries.

## Verification boundary

A dependency-free helper in `apps/gca-service/runtime_boundary.py` defines the API-key and default-off side-effect rules without importing model, mesh, blockchain, or FastAPI runtime components.

The permanent read-only workflow `.github/workflows/gca-runtime-boundary.yml` binds the fork-specific security contract. It uses immutable action SHAs, `ubuntu-24.04`, compiles the boundary/service/test sources, and runs eight offline contract tests covering:

1. explicit opt-in semantics for experimental flags;
2. fail-closed API-key status behavior;
3. no invented credential fallback;
4. default-off network/governance mutation paths;
5. authenticated provider calls and removal of `_gca_token` authority minting;
6. global `/v1/*` control authentication plus default-off runtime markers;
7. guarded reasoning-memory propagation;
8. service-level default suppression of tool-call output.

Two bounded feature-branch patch workflows were used only to modify the large GCA service after exact preimage checks. Their successful commits deleted those write-capable workflows and their temporary patch scripts from the branch. They are not part of the durable runtime.

The first large patch attempt also exposed a repository-structure problem: clean Actions checkout failed because `.nvm` was a tracked gitlink without a matching `.gitmodules` URL. PR #142 removed only that orphan gitlink and added `.nvm/` to `.gitignore`; it was squash-merged to `main` as `885450d9cf00e331b946966ff6a09eb5b477cf1a`. No history was rewritten.

Promotion of this branch still requires a final ordinary owner-authored run of the permanent GCA boundary workflow on the exact current head. That narrow workflow result must not be misrepresented as a clean full-application baseline.

## Product boundary

- ZovsIronClaw owns runtime execution, gateway behavior, device/runtime integration, and channel adapters.
- IronAgent owns product/control-plane orchestration, approval state, capability registry, and rollback coordination.
- Shared behavior must use versioned, least-privilege contracts rather than copied runtime trees.
- GCA outputs may be advisory policy/research signals only; they must not substitute for capability, authorization, or execution policy.
- High-risk or externally consequential actions must fail closed when policy or authorization is unavailable.

See [`UPSTREAM_DIVERGENCE.md`](UPSTREAM_DIVERGENCE.md) and [`UPSTREAM_SYNC_POLICY.md`](UPSTREAM_SYNC_POLICY.md).

## Remaining gates / non-claims

This branch does not establish that ZovsIronClaw or GCA is production-ready, ethically correct, safe for high-risk autonomous action, or synchronized with upstream OpenClaw.

Remaining work includes:

- restore/establish a clean full application baseline independently of the narrow GCA boundary tests;
- review the 17 previously unverified material claims against executable evidence;
- continue path-by-path upstream divergence classification rather than bulk merging;
- review the revoked credential history and committed host/cache artifacts under a separately justified preservation/remediation plan;
- test real authenticated GCA service integration without granting GCA heuristics execution authority;
- independently review high-risk tool, channel, gateway, file, model-loading, and desktop surfaces before production promotion;
- keep fork-specific experimental GCA/swarm/governance behavior isolated from AXIOM capability and policy authority unless a versioned, independently verified adapter is later designed.
