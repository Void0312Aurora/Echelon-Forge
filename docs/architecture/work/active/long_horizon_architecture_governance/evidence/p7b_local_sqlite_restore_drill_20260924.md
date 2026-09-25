# P7-B Local SQLite Restore Drill Evidence

Status: `2026-09-25` — local supported-topology restore drill completed;
external provider restore and production rollback-window operation remain open.

## Scope

This packet records the bounded local restore proof required by the P7-A
retention authority's minimum scope. The drill uses the maintained
`SQLiteArtifactLedger` provider in a temporary test root and covers one
release/rollout decision chain, its bound `RunReceipt`, and a persisted state
checkpoint.

The drill performs the following sequence:

1. Advance the durable rollout authority through `production-canary` and verify
   the release, decision, RunReceipt, and rollout-evidence retention classes.
2. Persist a checkpoint through its own fenced checkpoint stream.
3. Create a SQLite backup, restore it into a distinct root, and re-read both
   the retention projection and checkpoint identity from the restored ledger.

## Verification

Executed in the isolated
`codex/long-horizon-governance-architecture` worktree:

```powershell
$env:CMO_BUILD_DIR='artifacts/p5c-venv-final-20260922/Lib/site-packages'
python -m pytest -q tests/architecture/runtime_host/test_sqlite_rollout_admission.py
```

Initial drill result: **7 passed**. The restore case itself passed, including retention
classes and restored checkpoint release/decision identity.

The same SQLite admission/restore file was rerun in the current checkout on
`2026-09-25` and passed **8 tests**; the additional cases cover the current
durable admission and rollback-window bindings. The P7-A governance checks
also build and validate an in-memory provider-neutral evidence-manifest
projection over the resulting local stable projection and revalidate its
digest after a distinct-root restore. That manifest is not yet persisted as a
separate retained `ArtifactLedger` blob. This remains local provider evidence
only.

## Boundary

This is local SQLite provider evidence for the supported Windows single-process
row. It does not establish an external object-store/provider restore, a
quarterly operator drill, production rollback-window observation, production
cutover, or P8 acceptance.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p7b_local_sqlite_restore_drill_20260924.md`
Owner: `release/runtime integration`
Last verified: `2026-09-25`
