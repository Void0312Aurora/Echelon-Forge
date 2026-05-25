# TM01 Architecture Closure Task Clusters

Status: active task-cluster packet opened on `2026-05-24`.

This document is the finite dispatch and integration surface for
[TM01 Architecture Closure Remediation](README.md). It follows the
[Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)
and intentionally combines the task clusters, dispatch queue, and closure gates
in one file to avoid planning sprawl.

## 1. Scope Boundary

TM01 exists to close the implementation-level audit findings that are already
inside declared maintained or accepted surfaces. It is not a new architecture
expansion WP.

Hard inclusion rules:

- Include a task only if it repairs a focused current failure, records a narrow
  source-backed architecture residual, or closes a concrete WP24 documentation /
  governance mismatch.
- Keep each cluster finite and stop after the round cap instead of adding an
  ad-hoc follow-up wave.
- Treat `partial` evidence as useful context only; it never unlocks closure.

Hard exclusions:

- Full ground runtime behavior beyond the current tasking shell.
- Broad P7 launch/fire-control redesign.
- Public raw-runtime escape hatch deletion.
- Whole-repository compatibility API retirement.
- Full historical documentation rewrite.

## 2. Cluster Plan

| Cluster | Status | Goal | Write scope | Non-goals | Validation | Dependency / round cap |
|---------|--------|------|-------------|-----------|------------|------------------------|
| `TM01-A Ground Tasking Shell Repair` | pass / validated | Make the accepted ground MVP tasking shell load and preserve `TaskOrder -> LeaderIntent -> PilotReport` semantics. | `python/rl/tasking/leader_tasking.py`; focused tests under `tests/runtime/ground/` and `tests/leader/` only if assertions need tightening. | No ground movement, sensing, fire, damage, observation export, or schema expansion. | `python -m py_compile python/rl/tasking/leader_tasking.py`; focused ground/leader set passed with `27 passed` using the local `build-local-win` `ef_py` artifact and explicit Windows DLL directories. | First serial implementation cluster; closed by validation, no further repair round needed. |
| `TM01-B Launch Bridge Boundary Ledger` | pass / ledgered | Record the exact `systems -> SimulationKernel` weapon-release bridge residual and classify it as a source-backed architecture residual, not an implementation task. | Read-only by default; if edited, only `docs/task/simulation_architecture/tm01_architecture_closure_remediation/**`. | No P7 redesign, no launch request/event contract implementation, no movement of weapon APIs. | `rg -n "SimulationKernel&|core/engine/simulation_kernel.h|fire_.*weapon" src/systems src/core/engine`; source anchors for `pilot_weapon_release_system.h`, `naval_mission_weapon_release_system.h`, and `simulation_kernel_systems.cpp`. | Parallel-safe with `TM01-A` if read-only; one diagnostics round. |
| `TM01-C WP24 Provenance And Acceptance Sync` | pass / synced | Reconcile WP24-L wording with current maintained `agent_shim.py` defaults and record that canonical WP24 acceptance review is not part of this lane. | WP24 docs under `docs/task/simulation_architecture/wp24_taskorder_maintained_business_migration/`; acceptance docs are out of this lane. | No broad WP24 rewrite; no code changes unless validation proves the implementation contradicts the intended maintained default. | `rg -n "compatibility defaults|single_agent_role|roster_slot_role|MAINTAINED" docs/task/simulation_architecture/wp24_taskorder_maintained_business_migration python/rl/runtime/agent_shim.py tests`; `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP24 --summary` still reports `acceptance reviews (canonical): 0`. | Gated after `TM01-A` status is known; at most one doc-sync round. |
| `TM01-D Focused Closure Verification` | pass / integrated | Publish focused validation, residual ownership, and the audited-slice close/block recommendation for TM01 without claiming broader architecture closure. | TM01 docs only; no acceptance record in this lane. | No full-suite CI mandate, no new implementation work, no reopening `TM01-A` or `TM01-B` without re-scope. | `git diff --check`; `python -m py_compile python/rl/tasking/leader_tasking.py`; focused ground/leader set passed with `27 passed` using the local `build-local-win` `ef_py` artifact and explicit Windows DLL directories; `python tools/maintenance/wp_doc_closure_audit.py --wp WP24 --summary` still reports `acceptance reviews (canonical): 0`. | Serial final cluster after `TM01-A` through `TM01-C`; one integration round, then audited-slice close recommendation only. |

## 3. Dispatch Queue

No worker may be dispatched outside the named clusters below. Workers are not
alone in the codebase and must not revert unrelated edits.

| Dispatch | Cluster | Model / reasoning | Owner type | Write scope | Parallel-safe | Expected packet |
|----------|---------|-------------------|------------|-------------|---------------|-----------------|
| `TM01-A1 ground enum repair` | `TM01-A` | `gpt-5.4`, high | implementation worker or main thread | `python/rl/tasking/leader_tasking.py`; focused tests only if required | No, this is the first blocking implementation step. Prefer main-thread ownership if immediate execution is required. | `status`, touched files, commands/outcomes, remaining paths, behavior risks, integration notes. |
| `TM01-B1 launch bridge fact ledger` | `TM01-B` | `gpt-5.4-mini`, xhigh | diagnostics worker | Read-only source inspection; TM01 docs only if asked to record findings directly | Yes, if it stays read-only and does not touch implementation files. | Exact source anchors, classification, deferred-or-blocked recommendation. |
| `TM01-C1 WP24 doc sync preflight` | `TM01-C` | `gpt-5.4-mini`, xhigh | diagnostics/docs worker | WP24 docs; acceptance docs only after green validation | Gated after `TM01-A` status is known for acceptance wording. | Stale wording list, proposed replacement scope, audit command result. |
| `TM01-D1 integration and closure` | `TM01-D` | `gpt-5.4`, high | integration owner | TM01 docs and optional acceptance record | No. Closure stays serial. | Final validation matrix, residual register, close/block recommendation. |

## 4. Worker Packet Requirements

Every delegated result must return:

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Acceptance meanings:

- `pass` applies only to the assigned cluster.
- `partial` records evidence but does not unlock downstream closure.
- `blocked` must name the blocker, owner, failing or missing guard, and the next
  forced review trigger.
- The main thread must verify important worker claims locally before accepting
  them as TM01 evidence.

## 5. Initial Evidence

Audit evidence captured before TM01 opened:

- Facade/runtime focused tests passed.
- Air, naval, link, mission, and architecture guard focused tests passed.
- Ground MVP tasking shell validation failed in
  `tests/runtime/ground/test_ground_mvp_scenario.py` because
  `python/rl/tasking/leader_tasking.py` assigned an incompatible value to
  `TaskOrder.recovery_approach_type`.
- `src/systems/combat/pilot_weapon_release_system.h` and
  `src/systems/naval/naval_mission_weapon_release_system.h` include
  `core/engine/simulation_kernel.h` and capture `SimulationKernel&` for weapon
  release.
- WP24 documentation originally said `agent_shim.py` may keep compatibility
  defaults, while current implementation defaults are maintained.

Post-validation state:

- `TM01-A` is fixed and validated by focused ground/leader checks.
- `TM01-B` is pass/ledgered as a source-backed residual, not an implementation
  task.
- `TM01-C` is synced to maintained defaults; no canonical WP24 acceptance review
  was created.
- `TM01-D` is complete as the final integration pass and records the audited
  slice close recommendation.

## 5.1 Post-Opening Progress

`2026-05-25` integration update:

- `TM01-A` status: `pass / validated`. `leader_tasking.py` now coerces inferred
  recovery-approach values through the binding enum before assigning them to
  `TaskOrder` or `LeaderIntent`. A regression test covers an invalid raw ground
  recovery value falling back to `RecoveryApproachType.None`.
- `TM01-A` validation: `python -m py_compile python/rl/tasking/leader_tasking.py`
  passed; the focused ground/leader test set passed with `27 passed` using the
  local `build-local-win` `ef_py` artifact and explicit Windows DLL directories.
- `TM01-B` status: `pass / ledgered`. The residual remains source-backed at
  `src/systems/combat/pilot_weapon_release_system.h` and
  `src/systems/naval/naval_mission_weapon_release_system.h`, both of which
  include `core/engine/simulation_kernel.h` and capture `SimulationKernel&`.
  This is a residual ownership ledger entry, not a TM01 implementation task.
- `TM01-C` status: `pass / synced`. WP24-L wording now matches the maintained
  `agent_shim.py` defaults. No canonical WP24 acceptance review was created;
  `python tools/maintenance/wp_doc_closure_audit.py --wp WP24 --summary` still
  reports `acceptance reviews (canonical): 0`.
- `TM01-D` is complete as the final integration pass and records the audited
  slice close recommendation.

## 5.2 Final Residual Register

- `TM01-B` launch bridge residual: `src/systems/combat/pilot_weapon_release_system.h`
  and `src/systems/naval/naval_mission_weapon_release_system.h` still include
  `core/engine/simulation_kernel.h` and capture `SimulationKernel&`; this is a
  source-backed boundary residual for later architecture work.
- Raw-runtime and compatibility residuals: controlled diagnostics, tests, and
  compatibility surfaces remain in place and are not retired by TM01.
- WP24 canonical acceptance: no acceptance review was created in this lane;
  `acceptance reviews (canonical): 0`.

## 6. Close-Out Wording

If all clusters pass, TM01 may say:

> Focused maintained-path remediation is closed for the audited slice. Ground
> tasking shell validation is restored, WP24 provenance wording is synchronized,
> and the launch-bridge boundary residual is owned as a later architecture slice.

TM01 must not say:

> Ground runtime is complete; P7 launch contracts are redesigned; raw runtime
> escape hatches are retired; WP24 canonical acceptance is complete; or all
> follow-on architecture work is fully closed.
