# G4 Selected Runtime Slice Cluster

Status: `2026-05-22` implemented and validated for the selected tasking-only
lifecycle-proof slice through normalized ground `TaskOrder -> LeaderIntent ->
PilotReport` status shell.

Inputs:

- [G4 README](README.md)
- [G3 execution surface preflight cluster](../g3_execution_surface_design/g3_execution_surface_preflight_cluster_20260521.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Define the released G4 cluster boundaries, worker packets, and acceptance
criteria for the one approved ground runtime slice.

## Task Clusters

### `G4-A` Selected lifecycle shell

- Normalize the ground tasking path from `TaskOrder` to `LeaderIntent` to
  `PilotReport`.
- Keep the slice to a status shell only.
- Do not add command-delivery, sensing, movement, terrain, fires, or effects
  semantics.

Acceptance:

- The released path is exactly the normalized
  `TaskOrder -> LeaderIntent -> PilotReport` lifecycle shell.
- The implementation stays within the G3-approved write scope only.

### `G4-B` Worker packet and validation focus

- Keep the worker packet concise and serializable for dispatch.
- Name the validation commands that prove the released slice without widening
  behavior.
- Preserve shared entry points for air/naval compatibility checks.

Acceptance:

- The worker packet spells out scope, exclusions, validation, and residuals.
- Validation commands are explicit and runnable from the repo root.

### `G4-C` No-private-path proof

- Prove the slice uses maintained shared entry points.
- Show that no ground-only runtime path, private import shortcut, or
  air-only fallback was introduced.

Acceptance:

- The proof references the maintained `tasking_profile` bridge.
- The proof does not depend on route refs, recovery base/runway fields,
  landing/takeoff semantics, world-truth observation surfaces, or deferred
  terrain/LOS/radio runtime.

### `G4-D` Residual map and handoff

- Record the deferred surfaces that remain outside this slice.
- Hand off the remaining work as a residual map, not as implied acceptance.

Acceptance:

- The residual map explicitly keeps `CommandPacket`, `ObservationPacket`,
  `TrackPacket`, `P3`, `P10`, movement, sensing, terrain, fires, and broad
  `MissionCommand` work deferred.
- The doc set names the touched files, commands run, compatibility results, and
  residuals.

## Write Scope

Released by G3 with a bounded file-family rule. The eventual worker should stay
within the narrowest set needed to prove shared entry-point lifecycle behavior:

- shared tasking-profile/runtime call sites that carry the normalized
  `TaskOrder -> LeaderIntent -> PilotReport` shell
- focused ground lifecycle tests
- narrow compatibility guards on common-core / naval mission-profile behavior

Do not edit until released:

- movement/physics systems
- sensor/track systems
- fire-control, weapon, or damage runtime
- broad facade API surfaces
- C++ DTOs or binding surfaces unless a later accepted plan explicitly releases
  them

## Suggested Validation

Accepted baseline expectation:

```bash
git diff --check
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/runtime/mission/test_leader_tasking_runtime.py
python -m pytest -q tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/ground/task_order_ground_profile_defaults.json tests/contracts/unit/ground/task_order_ground_minimal_structures.json tests/contracts/unit/ground/task_order_ground_support_relationships.json
```

## Handoff

Return:

- touched files
- commands run
- evidence for maintained entry points
- compatibility results
- residual map

No-private-path proof expectations:

- ground runtime selection must go through the maintained `tasking_profile`
  bridge, not a ground-only loop or an air-only import shortcut
- the first slice must not depend on route refs, recovery base/runway fields,
  landing/takeoff semantics, world-truth observation surfaces, or deferred
  terrain/LOS/radio runtime

## Main-Thread Validation Result

Touched implementation files:

- `python/rl/runtime/world_batch_vec_env.py`
- `python/rl/runtime/cooperative_world_batch_vec_env.py`
- `tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py`

Accepted evidence:

- Both batch envs import `build_kernel_mission_command` from
  `python.rl.tasking.bridge`, not from the air-first `leader_tasking` module.
- `tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py` proves
  explicit ground `tasking_profile` dispatch, Army `service_profile` inference,
  source-level no-private-path import checks, and air/naval compatibility
  resolution.
- The first G4 slice still exports only the shared command-chain status shell:
  `TaskOrder`, `LeaderIntent`, and `PilotReport`.

Validation passed:

```bash
git diff --check -- docs\task\ground python\rl\runtime tests\runtime\mission\test_ground_runtime_lifecycle_bridge.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\mission\test_ground_runtime_lifecycle_bridge.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\leader\test_tasking_profile_contracts.py tests\runtime\mission\test_leader_tasking_runtime.py
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_scenario_contract.py --spec tests\contracts\unit\ground\task_order_ground_profile_defaults.json tests\contracts\unit\ground\task_order_ground_minimal_structures.json tests\contracts\unit\ground\task_order_ground_support_relationships.json
```

Still deferred:

- `CommandPacket`, `ObservationPacket`, `TrackPacket`, formal `P3`, formal
  `P10`, movement, sensing, terrain, fires, effects, DTO/binding expansion, and
  broad `MissionCommand` growth.
