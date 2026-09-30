# P5-D Process-Resync Admission Evidence

Status: 2026-09-23 — process-lifetime admission recheck slice; not a
production cutover or P5-D acceptance.

The local production adapter previously validated its signed RolloutDecision
only during construction. This slice retains the construction check and adds
an explicit refresh_rollout_admission() path. Production mutations now
re-read the durable slot before setup, command injection, launch, step, and
maintained runtime-window execution. A kill-switch or typed backout written
by another local controller therefore closes the existing process before it
accepts another truth-changing action. A newly started process continues to
perform the same check in its constructor.

## Verification

Executed in the isolated codex/long-horizon-governance-architecture worktree:

    $env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/maintenance/cmo_env.ps1 python -m pytest -q tests/architecture/runtime_host/test_production_rollout_gate.py
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/maintenance/cmo_env.ps1 python -m pytest -q tests/world_batch/test_world_batch_vec_env_command_chain.py -k "capability_snapshot or step_worlds or legacy_task_order_batch_writer_is_removed"
    python -m ruff check python/rl/runtime/world_batch/adapter.py tests/architecture/runtime_host/test_production_rollout_gate.py

Results:

- production rollout gate: **7 passed**;
- adapter capability/step guard subset: **4 passed, 19 deselected**;
- Ruff passed.

The new gate test exercises an admitted production-canary adapter, writes a
durable kill switch, verifies that an explicit refresh rejects the closed
slot, verifies that a subsequent pilot-action mutation is rejected before it
reaches the facade, and verifies that a newly constructed adapter also
rejects the closed slot.

## Remaining boundary

This is an admission-resynchronization safeguard, not the complete package
rollback drill. P5-D still needs to bind the slot to the actual release
manifest/package and durable RunReceipt/ArtifactLedger records, rehearse
same-release checkpoint recovery and stop/restart package rollback, collect
support-row telemetry/SLO evidence, and retire or explicitly quarantine the
in-kernel rebuild authority.
