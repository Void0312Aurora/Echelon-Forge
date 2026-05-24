# Naval N4 Threat / ROE Dispatch Queue

Status: active dispatch queue opened on `2026-05-24` after owner approval to
expand distribution work.

Language:

- English canonical: `naval_n4_threat_roe_dispatch_queue_20260524.md`
- Chinese companion:
  [naval_n4_threat_roe_dispatch_queue_20260524.zh.md](naval_n4_threat_roe_dispatch_queue_20260524.zh.md)

Inputs:

- [N4 threat / ROE bridge README](README.md)
- [N4 threat / ROE bridge task cluster](naval_n4_threat_roe_bridge_cluster_20260524.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Scope Boundary

This queue activates the finite cluster plan from the task-cluster document. It
does not broaden the N4 bridge into weapons engagement or damage.

First dispatch wave:

- `N4-B0 Threat / ROE Source Inventory`: read-only diagnostics under `N4-B`.
  It may inform later N4-B/N4-C write scopes, but it does not unlock closure.
- `N4-A1 Scenario / Contract Boundary`: first implementation worker. It owns
  the scenario and contract boundary for `ddg51_take1_screen_threat_roe_v1`.

Gated work:

- `N4-B1 Threat / ROE Semantics` waits for the N4-A boundary and B0 source
  inventory.
- `N4-C1 Runtime / Facade Evidence` waits for N4-A and narrowed write scopes.
- `N4-D1 RL Task Surface Preflight` waits for accepted N4-A/B semantics.
- `N4-E1 Integration / Acceptance` is serial after implementation packets.

## Queue

| Dispatch | Cluster | Status | Model / reasoning | Owner type | Write scope | Parallel-safe | Expected packet |
|----------|---------|--------|-------------------|------------|-------------|---------------|-----------------|
| `N4-B0 threat/ROE source inventory` | `N4-B Threat / ROE Semantics` | pass / read-only | inherited parent model, medium | diagnostics explorer | read-only source/test/docs inspection | yes; does not edit files and does not unlock closure | returned field inventory, source anchors, minimal write-scope recommendation, architecture risks |
| `N4-A1 scenario contract boundary` | `N4-A Scenario / Contract Boundary` | pass / accepted | `gpt-5.4`, high | implementation worker | `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json`; `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json`; `python/testing/contracts/unit/comm.py`; focused tests under `tests/runtime/naval/` only if required | no; first blocking implementation boundary | returned pass packet; main thread re-ran contracts and naval screen tests |
| `N4-B1 threat/ROE semantics` | `N4-B Threat / ROE Semantics` | pass / accepted | `gpt-5.4`, high | implementation worker | narrowed after `N4-A1` and `N4-B0`; expected families are command shared-core, naval profile, loader runtime-state fallback, command bindings, and focused mission/binding tests | no for this wave; blocks N4-C until maintained fields are accepted | returned pass packet; main thread re-ran build, focused tests, and N4/N3 contracts |
| `N4-C1 facade/world-batch evidence` | `N4-C Runtime / Facade Evidence` | pass / accepted | `gpt-5.4`, high | implementation worker | narrowed after `N4-A1`; expected families are world-batch command-chain cache, vec-env tests, facade guards | no for this wave | returned pass packet; main thread re-ran build, bindings/facade/world-batch tests, and N4 contract |
| `N4-D1 RL preflight surface` | `N4-D RL Task Surface Preflight` | paused / not dispatched | `gpt-5.4`, medium | docs / design worker | docs under this subproject or a later explicitly named RL task doc | yes after N4-A/B/C evidence is accepted | paused by owner direction; no next wave dispatched |
| `N4-E1 integration and acceptance` | `N4-E Integration / Acceptance` | paused / not dispatched | `gpt-5.4`, high | integration owner | named naval docs and acceptance/status files only | no | paused by owner direction after C1 acceptance |

## Active Worker Packets

### N4-B0 Threat / ROE Source Inventory

Status: pass / read-only diagnostics complete. No files were modified.

Packet:

```md
Cluster: N4-B Threat / ROE Semantics
Dispatch: N4-B0 threat/ROE source inventory
Model / reasoning: inherited parent model, medium
Round cap: 1 diagnostics round
Goal: inventory existing threat state, ROE / engagement authority, assigned
target, and track-provenance surfaces.
Write scope: none; read-only.
Non-goals: implementation, scenario edits, contract edits, facade changes.
Validation: source anchors and test/doc paths only.
Closure gate: return field inventory, minimal N4-B/N4-C write-scope
recommendation, and architecture risks. This does not unlock N4-E closure.
Parallel/dependency: parallel-safe with N4-A1 because it is read-only.
```

Returned inventory summary:

- Existing maintained ROE/authority/target fields are present in
  `MissionCommand` shared core, `LeaderIntentCore`, Python bindings, the naval
  profile, episode JSON roundtrip, and world-batch maintained contracts.
- No dedicated `threat_state` field exists yet. The closest inputs are track
  `classification`, `source`, `quality/confidence`, `source_time_s`,
  `update_age_s`, and `snapshot_version`.
- No dedicated assigned-target provenance field exists yet. The closest
  maintained evidence is `TrackPacket` source/timing/snapshot data plus facade
  packet provenance.
- N4-B should add explicit maintained semantics for threat state and
  assigned-target provenance rather than treating loose scenario JSON or raw
  whole-shell mission command as the owner.
- N4-C should prove those fields survive through maintained facade/world-batch
  projection.
- Known risk: `gym_envs/scenario_loader/runtime_state.py` fallback mission JSON
  can lose `roe_state` and `engagement_authority_*` when it does not have
  canonical mission-command JSON.

### N4-A1 Scenario / Contract Boundary

Status: pass / accepted. Main thread locally re-ran the validation commands.

Packet:

```md
Cluster: N4-A Scenario / Contract Boundary
Dispatch: N4-A1 scenario contract boundary
Model / reasoning: gpt-5.4, high
Round cap: 2 implementation rounds before re-scope
Goal: implement the first N4 bridge boundary for
ddg51_take1_screen_threat_roe_v1.
Write scope:
- scenarios/naval/ddg51_take1_screen_threat_roe_v1.json
- tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
- python/testing/contracts/unit/comm.py
- tests/runtime/naval/test_naval_screen_scenario.py only if focused runtime
  assertions are required
Non-goals:
- no weapon release as a required objective
- no hit/intercept/damage/kill assertions
- no broad mission-command or facade refactor
- no RL trainer/reward implementation
Validation:
- PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
- PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json
- PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json
- PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_screen_scenario.py
Closure gate:
- new scenario loads through ScenarioLoader;
- existing N3 screen/contact gates still pass;
- N4 contract asserts threat/ROE pre-fire state from valid shared/local track
  evidence or records a concrete blocker if the maintained surface is missing;
- docs and tests continue to forbid N5/N6 claims.
Parallel/dependency:
- depends on N4-0 planning surface;
- blocks N4-B1, N4-C1, and N4-D1 implementation;
- may run in parallel with N4-B0 diagnostics because N4-B0 is read-only.
```

Returned evidence:

- Added `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json`.
- Added `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json`.
- Extended `python/testing/contracts/unit/comm.py` with narrow
  `naval_screen_threat_roe` handling while preserving existing
  `naval_screen_contact_report` behavior.
- Proves pre-fire `MissionCommand` ROE/authority/assigned-target visibility and
  no weapon-inventory, health, or damage delta during the contract window.
- Does not prove independent `threat_state` or assigned-target provenance.

Main-thread verification:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_screen_scenario.py
# 8 passed
```

### N4-B1 Threat / ROE Maintained Semantics

Status: pass / accepted. Main thread locally re-ran build, focused tests, and
scenario contracts.

Packet:

```md
Cluster: N4-B Threat / ROE Semantics
Dispatch: N4-B1 threat/ROE maintained semantics
Model / reasoning: gpt-5.4, high
Round cap: 2 implementation rounds before re-scope
Goal: add the minimal maintained semantics for independent pre-fire threat
state and assigned-target provenance.
Write scope:
- command shared-core / mission-command / leader-intent core files, only for
  N4 threat/provenance fields
- mission-command episode JSON codec
- command Python bindings
- python/rl/profile/naval_profile.py
- gym_envs/scenario_loader/runtime_state.py
- focused mission/binding tests
Non-goals:
- no weapon-release, hit/intercept, damage, or kill semantics
- no facade/world-batch projection work
- no RL trainer/reward implementation
Validation:
- focused mission-command ROE tests
- command binding surface tests
- N4 scenario contract smoke
Closure gate:
- maintained state exposes threat state and assigned-target provenance fields;
- Python profile and runtime-state fallback do not silently drop those fields;
- N4-A contract still passes.
Parallel/dependency:
- depends on N4-A1 and N4-B0;
- blocks N4-C1 until accepted.
```

Returned evidence:

- Added maintained shared-core fields:
  `threat_state`, `assigned_target_track_id`, `assigned_target_source_id`, and
  `assigned_target_snapshot_time_s`.
- Propagated those fields through mission-command JSON roundtrip, command
  bindings, naval profile mission-command construction, and loader runtime-state
  fallback.
- Added focused mission/binding tests for binding exposure, naval profile
  mapping, episode JSON roundtrip, and runtime-state fallback preservation.
- Left facade/world-batch projection untouched for `N4-C1`.

Main-thread verification:

```bash
cmake --build build-workshop --target ef_py -j2
# passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/mission/test_mission_command_roe_fields.py tests/runtime/mission/test_naval_mission_command_mapping.py
# 10 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/bindings/test_bindings_command_surface.py
# 5 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json
# PASS / PASS
```

### N4-C1 Runtime / Facade Evidence

Status: pass / accepted. Main thread locally re-ran build, focused tests, and
the N4 scenario contract. No follow-on worker is dispatched after this point.

Returned evidence:

- Applied N4 shared-core fields back into the world-batch compatibility shell:
  `threat_state`, `assigned_target_track_id`, `assigned_target_source_id`, and
  `assigned_target_snapshot_time_s`.
- Exposed the N4 fields through the runtime binding for
  `MissionCommandSharedCoreDirective`.
- Added focused maintained batch roundtrip coverage and facade tasking packet
  export coverage for the N4 fields.
- Preserved existing facade tasking packet provenance status:
  `compatibility_adapter`.

Main-thread verification:

```bash
cmake --build build-workshop --target ef_py -j2
# passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py
# 33 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/facade/test_runtime_facade.py
# 30 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "naval or task_order or command_chain or mission_command"
# 7 passed, 22 deselected

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "naval_owner_slice or task_order_naval or command_chain or mission_command"
# 5 passed, 56 deselected

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS
```

Pause note:

- Work is paused after C1 acceptance.
- `N4-D1` and `N4-E1` remain un-dispatched until a later owner decision.

## Worker Return Packet

Every worker must return:

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Stop Rules

- Stop if the N4 contract cannot assert ROE/authority/assignment without
  inventing a raw compatibility path.
- Stop if the scenario requires a successful weapon release to pass.
- Stop if the worker needs to edit broad facade/world-batch surfaces outside
  its dispatch write scope.
- Stop after the round cap and re-scope instead of adding another follow-up.
