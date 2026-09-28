# P8 Post-Acceptance Governance Monitor

Status: `2026-09-28` — governance mechanisms registered after bounded P8
acceptance.

## Purpose

P8 acceptance is limited to the executable Windows CPU in-process lane,
short-cycle repeatability, local SQLite backup/restore, and fail-closed
unsupported-topology checks. The controls below preserve visibility into
longer-term or externally dependent risks without making those risks implicit
acceptance blockers.

## Controls

| Control | Trigger | Owner | Evidence | Escalation |
| --- | --- | --- | --- | --- |
| local cadence/package-pair probe | each release batch or material package change | release/runtime integration | P2-B/P5-D measurement packet | failed SLO, digest drift, or missing package identity opens a repair task |
| resource trend probe | each local repeat batch | release engineering | working-set/handle observation | missing samples or monotonic growth opens a leak/resource investigation |
| SQLite restore probe | each acceptance refresh or retention-schema change | documentation governance | distinct-root restore and manifest digest check | restore mismatch blocks that retention change, not the already accepted runtime scope |
| CI lane drift probe | workflow, runner, label, or timeout change | release engineering | P6-B lane audit output | owner/selector drift is repaired before the changed lane is reused |
| Linux qualification probe | when a maintained Linux checkout and matching build artifact exist | release/runtime integration | [Linux qualification packet](p8_linux_qualification_probe_20260928.md) | current probe builds/imports but leaves the row partial after two native fixture assertions; resolve before expanding support |
| external provider readiness probe | only after explicit provider admission | documentation governance | provider-specific restore/migration packet | provider cannot become an authority until restore and retrieval are proven |
| production rollback probe | only after an authorized production environment exists | release/runtime integration | rollback telemetry and owner decision | never infer production behavior from local fixtures |

## Operating Rules

1. Every triggered probe produces a dated packet or an explicit `not-run`
   record.
2. A failed probe creates a bounded repair task with an owner and due trigger;
   it does not silently change the accepted local scope.
3. Unsupported multi-process, external-host, and CUDA-canonical rows remain
   fail-closed until a separate admission decision supplies executable gates.
4. The monitor is a governance surface, not a second runtime authority or a
   replacement for the P8 acceptance matrix.

## Current Records

- Windows local governance suite: **79 passed**.
- Windows P8 matrix/manifest subset: **17 passed**.
- HEI Linux temporary-clone P8/P7-A subset: **15 passed** after full history
  was fetched; this is short-cycle governance/import evidence, not Linux
  package qualification.
- HEI current-branch Linux configure/build/import: **passed**; native
  `ef_test`: **150 passed, 2 failed** because two CPU-reference tests assert a
  CUDA fixed-air ID against a platform-specific Flecs ID. Linux remains
  `partial` and is not promoted into the accepted matrix.
- External provider, hosted branch protection, long-running cadence, and
  production rollback probes: `not-run` by design and non-blocking.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p8_post_acceptance_governance_20260928.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-28`
