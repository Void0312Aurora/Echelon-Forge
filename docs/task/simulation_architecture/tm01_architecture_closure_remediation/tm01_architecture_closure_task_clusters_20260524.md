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
| `TM01-A Ground Tasking Shell Repair` | open | Make the accepted ground MVP tasking shell load and preserve `TaskOrder -> LeaderIntent -> PilotReport` semantics. | `python/rl/tasking/leader_tasking.py`; focused tests under `tests/runtime/ground/` and `tests/leader/` only if assertions need tightening. | No ground movement, sensing, fire, damage, observation export, or schema expansion. | `python -m py_compile python/rl/tasking/leader_tasking.py`; `PYTHONPATH=build-workshop python -m pytest -q tests/runtime/ground/test_ground_mvp_scenario.py tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py tests/leader/test_ground_profile_semantics.py tests/leader/test_common_core_semantics.py`. | First serial implementation cluster; at most one repair round before re-scope. |
| `TM01-B Launch Bridge Boundary Ledger` | open | Record the exact `systems -> SimulationKernel` weapon-release bridge residual and decide whether it is deferred, blocked, or eligible for a later contract slice. | Read-only by default; if edited, only `docs/task/simulation_architecture/tm01_architecture_closure_remediation/**`. | No P7 redesign, no launch request/event contract implementation, no movement of weapon APIs. | `rg -n "SimulationKernel&|core/engine/simulation_kernel.h|fire_.*weapon" src/systems src/core/engine`; source anchors for `pilot_weapon_release_system.h`, `naval_mission_weapon_release_system.h`, and `simulation_kernel_systems.cpp`. | Parallel-safe with `TM01-A` if read-only; one diagnostics round. |
| `TM01-C WP24 Provenance And Acceptance Sync` | open | Reconcile WP24-L wording with current maintained `agent_shim.py` defaults and record whether canonical WP24 acceptance review is part of this lane. | WP24 docs under `docs/task/simulation_architecture/wp24_taskorder_maintained_business_migration/`; acceptance docs under `docs/task/review/archive/wp-acceptance/` only if the implementation validation gate is green and an acceptance record is explicitly created. | No broad WP24 rewrite; no code changes unless validation proves the implementation contradicts the intended maintained default. | `rg -n "compatibility defaults|single_agent_role|roster_slot_role|MAINTAINED" docs/task/simulation_architecture/wp24_taskorder_maintained_business_migration python/rl/runtime/agent_shim.py tests`; `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP24 --summary`. | Gated after `TM01-A` status is known; at most one doc-sync round. |
| `TM01-D Focused Closure Verification` | open | Publish focused validation and residual ownership for TM01 without claiming broader architecture closure. | TM01 docs only, unless an acceptance record is explicitly created after green validation. | No full-suite CI mandate, no new implementation work, no reopening `TM01-A` or `TM01-B` without re-scope. | `git diff --check`; focused commands from `TM01-A`; existing domain smoke set from the audit if needed: facade, mission, air, naval, link, architecture guard tests. | Serial final cluster after `TM01-A` through `TM01-C`; one integration round. |

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
- WP24 documentation says `agent_shim.py` may keep compatibility defaults, while
  current implementation defaults are maintained.

## 6. Close-Out Wording

If all clusters pass, TM01 may say:

> Focused maintained-path remediation is closed for the audited slice. Ground
> tasking shell validation is restored, WP24 provenance wording is synchronized,
> and the launch-bridge boundary residual is owned as a later architecture slice.

TM01 must not say:

> Ground runtime is complete; P7 launch contracts are redesigned; raw runtime
> escape hatches are retired; WP24 and all follow-on architecture work are fully
> closed.
