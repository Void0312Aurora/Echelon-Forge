# P5-D Real Process And Package Rollback Evidence

Status: `2026-09-25` — local supported-row rollback and rollback-window
recheck drill; production canary publication and P5-D acceptance remain open.

This packet records the first executable process and package rollback drill
behind the durable SQLite rollout controller. It uses two existing Windows
CPython 3.12 `ef_py` build outputs in the worktree, starts each in a separate
OS process, and observes the native `RuntimeFacade` construction. The current
process now reads the SQLite rollout snapshot in the child and constructs a
`RuntimeFacadeAdapter` only after validating the signed decision, release
manifest, and RunReceipt binding.

## Drill sequence

1. Build an admitted release manifest containing the measured package
   identities for the current and rollback build outputs.
2. Commit `prepared → shadow → canary-ready → production-canary` through
   `SQLiteArtifactLedger.commit_rollout_admission`, with every RunReceipt
   bound to the measured current package and native binding digest.
   The read-only retention projection confirms the four authority blobs are
   present with `active-release`, `rollback-window`, `run-retained`, and
   `rollback-window` classes respectively.
3. Start the current build through
   `tools/maintenance/p5d_process_rollback_drill.py`; the child process opens
   the durable ledger, verifies the production-canary snapshot and its
   release/RunReceipt binding, then constructs one `RuntimeFacade` through the
   maintained adapter. Readiness records the admitted release, plan, decision
   digest, production authorization, and evidence-binding result.
4. Trip the durable kill switch, stop the child process, and commit the typed
   `backed-out` decision with the N-1 plan/package evidence and a new writer
   generation. Re-reading the retention projection confirms the decision
   remains retained for the rollback window after backout.
5. Start the rollback build in a new child process with a new epoch and verify
   the new boot identity, build path, native binding digest, and facade type.
   The child now also checks that the imported `ef_py` module is the selected
   build's binding and that the RunReceipt package and wheel digests match the
   selected rollback build. Starting the current build against the backout
   receipt is rejected before readiness; the backout process is admitted only
   as a non-authoritative, evidence-bound process.
6. Run the package restart drill contract with closed admission, finalized
   journals, source stop, caller resynchronization, and finalized receipt
   prerequisites.

## Long-lived rollback-window recheck

The durable snapshot reader was also exercised while a maintained adapter
remained alive. The release controller advanced the same signed release
through `adoption-expanding → rollback-window → stable`; after each commit the
adapter reloaded the snapshot and remained production-authorized. A subsequent
kill switch caused the same adapter to reject its next admission refresh before
any facade mutation. This is a local single-process rollback-window operation,
not a production cutover or an external-provider drill.

## Verification

Executed in the isolated
`codex/long-horizon-governance-architecture` worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python -m pytest -q tests/architecture/runtime_host/test_p5d_real_process_package_rollback.py
python -m pytest -q tests/architecture/runtime_host/test_sqlite_rollout_admission.py tests/architecture/runtime_host/test_production_rollout_gate.py tests/architecture/runtime_host/test_rollout_evidence_binding.py tests/architecture/runtime_host/test_p5d_rollout_operations.py
python -m pytest -q tests/architecture/runtime_host/test_p5d_supported_row_measurement.py
python -m ruff check tools/maintenance/p5d_process_rollback_drill.py tests/architecture/runtime_host/test_p5d_real_process_package_rollback.py
git diff --check
```

Results: the real process/package drill passed **1 test**; the durable SQLite
admission file now passes **8 tests**, including the long-lived rollback-window
recheck; the combined P5-D durable admission, binding, gate, operations,
rollback, and supported-row group passes **27 tests**; Ruff and the diff check
pass.

The child process reports the actual `RuntimeFacade` type and SHA-256 of the
loaded `ef_py` binding, plus the production-canary/backout state, release/plan
identities, decision digest, package digest, wheel digest, and evidence-binding
result. The parent asserts a new boot identity and epoch after the rollback
process starts and rejects a mismatched current build. The same child
readiness record carries Windows working-set and handle observations for the
process lifetime; these are operational samples, not an approved resource
budget. No test-only facade stub is used for this drill.

## Boundary

The drill proves the supported local Windows row, its durable backout chain,
and the in-process rollback-window recheck. It does not admit remote or
multi-process execution, and it does not claim the sole production-canary
decision has been published. Representative release cadence, complete
maintained caller parity, production rollback-window operation, and rebuild
retirement remain P5-D work.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_real_process_package_rollback_20260923.md`
Owner: `release/runtime integration`
Last verified: `2026-09-25`
