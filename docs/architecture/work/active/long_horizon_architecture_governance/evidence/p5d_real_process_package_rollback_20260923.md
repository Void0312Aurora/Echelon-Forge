# P5-D Real Process And Package Rollback Evidence

Status: `2026-09-23` — local supported-row rollback drill; production canary
publication and P5-D acceptance remain open.

This packet records the first executable process and package rollback drill
behind the durable SQLite rollout controller. It uses two existing Windows
CPython 3.12 `ef_py` build outputs in the worktree, starts each in a separate
OS process, and observes the native `RuntimeFacade` construction before the
process is stopped and restarted.

## Drill sequence

1. Build an admitted release manifest containing the measured package
   identities for the current and rollback build outputs.
2. Commit `prepared → shadow → canary-ready → production-canary` through
   `SQLiteArtifactLedger.commit_rollout_admission`, with every RunReceipt
   bound to the measured current package and native binding digest.
3. Start the current build through
   `tools/maintenance/p5d_process_rollback_drill.py`; the child process imports
   the selected local binding and constructs one `RuntimeFacade`.
4. Trip the durable kill switch, stop the child process, and commit the typed
   `backed-out` decision with the N-1 plan/package evidence and a new writer
   generation.
5. Start the rollback build in a new child process with a new epoch and verify
   the new boot identity, build path, native binding digest, and facade type.
6. Run the package restart drill contract with closed admission, finalized
   journals, source stop, caller resynchronization, and finalized receipt
   prerequisites.

## Verification

Executed in the isolated
`codex/long-horizon-governance-architecture` worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python -m pytest -q tests/architecture/runtime_host/test_p5d_real_process_package_rollback.py
python -m pytest -q tests/architecture/runtime_host/test_sqlite_rollout_admission.py tests/architecture/runtime_host/test_production_rollout_gate.py tests/architecture/runtime_host/test_rollout_evidence_binding.py tests/architecture/runtime_host/test_p5d_rollout_operations.py
python -m ruff check tools/maintenance/p5d_process_rollback_drill.py tests/architecture/runtime_host/test_p5d_real_process_package_rollback.py
git diff --check
```

Results: the real process/package drill passed **1 test**; the combined
P5-D durable admission, binding, gate, operations, and rollback group passed
**23 tests**; Ruff and the diff check passed.

The child process reports the actual `RuntimeFacade` type and SHA-256 of the
loaded `ef_py` binding. The parent asserts a new boot identity and epoch after
the rollback process starts. No test-only facade stub is used for this drill.

## Boundary

The drill proves the supported local Windows row and its durable backout
chain. It does not admit remote or multi-process execution, and it does not
claim the sole production-canary decision has been published. Measured
multi-run SLO/adoption data, complete maintained caller parity, rollback-window
retention, and rebuild retirement remain P5-D work.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_real_process_package_rollback_20260923.md`
Owner: `release/runtime integration`
Last verified: `2026-09-23`
