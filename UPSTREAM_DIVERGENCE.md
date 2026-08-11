# Upstream divergence snapshot

Captured: 2026-08-09

- ZovsIronClaw ref: `1a6f351676e55b800368803fd9b72ad8ae2a535f`
- OpenClaw `main` ref: `b0b82291cada1588f461d09371c398adf0a8d611`
- GitHub relationship: ZovsIronClaw is not registered as a fork (`fork: false`); no GitHub parent/source relationship is present.
- Comparison method: direct tree comparison with rename detection disabled. This is not a merge-base or shared-ancestry claim.

## Tree result

| Relative to current OpenClaw tree | Paths |
|---|---:|
| Present only in ZovsIronClaw | 2,427 |
| Present only in current OpenClaw | 28,491 |
| Same path, different content | 2,627 |

The scale of the divergence makes an automatic upstream merge unsafe. Current OpenClaw has major source, extension, app, UI, documentation, script, test, package, and quality-assurance surfaces not present in this snapshot. ZovsIronClaw also contains fork-only product and host-state material.

## Fork-only classification candidates

| Class | Examples | Decision |
|---|---|---|
| Plugin/adapter candidate | `extensions/gca-brain/`, GCA providers, bounded hooks | Extract only after interface, license, test, and failure-mode review |
| Separate service candidate | `apps/gca-service/` | Keep outside upstream core; define authenticated API/schema and independent tests |
| Experimental policy | moral, soul, QPT, entropy, thermodynamic, swarm-ethics modules | Optional and disabled for high-risk authority until adversarially validated; never describe as objective ethics |
| Documentation/configuration | `AGENTS.md`, prompts, workflow instructions, fork README | Preserve as fork-specific documentation; remove guarantee language |
| Non-product host state | `.npm/`, `.cache/`, `.config/`, shell/home artifacts | Do not upstream or migrate; prepare removal and separate history review after complete backup |
| Shared-path core changes | modifications under upstream-owned `src/`, `apps/`, `extensions/`, `docs/`, and scripts | Require semantic patch-by-patch classification before sync |

## Safety conclusion

Do not bulk merge upstream or publish a compatibility claim. First remove non-product host state on an ordinary draft branch where possible, complete the separately approved credential-history plan if authorized, and classify fork patches as core fork, plugin, adapter, or documentation. Preserve exact refs and negative findings throughout.
