# Upstream sync policy

## Cadence

- Check OpenClaw security advisories and releases at least weekly.
- Record the exact upstream ref reviewed, affected surfaces, and decision.
- Batch ordinary upstream review on a monthly cadence; handle material security fixes separately and promptly.

## Patch classification

Every Zoverions-specific change must be assigned one class before an upstream sync:

1. **core fork:** unavoidable modification to upstream-owned behavior;
2. **plugin:** independently loadable feature using a supported extension boundary;
3. **adapter:** versioned integration translating between external and upstream contracts;
4. **documentation/configuration:** no runtime behavior;
5. **non-product artifact:** cache, host state, credential, generated output, or local environment content that must not be propagated.

## Sync sequence

1. Preserve complete mirrors and exact source/upstream refs.
2. Review upstream security changes first.
3. Compare trees and identify shared-path collisions without automatic overwrite.
4. Port the smallest logical patch to a clean branch; prefer plugins/adapters over core edits.
5. Run upstream tests plus fork-specific gateway, channel, authorization, and GCA failure-mode tests.
6. Verify upgrade, rollback, configuration migration, and external-side-effect controls.
7. Open a draft PR with exact refs, claims affected, tests, and known incompatibilities.
8. Merge only after itemized approval and never combine upstream sync with credential-history rewriting.

## Security monitoring

Dependabot and GitHub vulnerability alerts remain enabled. Code scanning, dependency updates, and advisories are signals, not proof of a secure release. The revoked credential artifact remains a separate preservation-aware history-remediation decision.
