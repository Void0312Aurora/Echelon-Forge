# G1 Profile And DTO Preflight

Status: `2026-05-21` preflight complete for G1 implementation release review.

Inputs:

- [Ground subagent dispatch queue](../ground_subagent_dispatch_queue_20260521.md)
- [G1 README](README.md)
- [G1 profile and DTO contract cluster](g1_profile_dto_contract_cluster_20260521.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [US Army profile](../../../standards/services/army.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Recommendation

- Recommendation: `implementation-ready`
- DTO-shell recommendation: `not needed in G1`
- Scope recommendation: keep G1 `Python-profile-only`

No blocking source gap was found for a narrow G1 that only adds alias
resolution, a ground profile shell, and common-core starter defaults. G1 should
stop immediately if anyone tries to widen the slice into ground
`MissionCommand`, runtime execution behavior, scenario-loader behavior, Python
bindings, or new C++ DTO field ownership.

## Source Inventory

### Python resolver and profile-selection surface

| File | Anchor | Preflight finding |
|------|--------|-------------------|
| `python/rl/tasking/bridge.py` | `_normalized_profile_name` at lines 11-32 | Only `air` and `naval` are recognized today. `Army`, `army`, `ground`, and `land` are currently unknown. |
| `python/rl/tasking/bridge.py` | `resolve_tasking_profile` at lines 43-53 | Resolver returns `_air` or `_naval` only. Future G1 ground alias work belongs here. |
| `python/rl/tasking/bridge.py` | `tasking_profile_for_loader` at lines 56-80 | Existing precedence is already correct for G1: explicit `tasking_profile` wins, then `service_profile` inference. Ground implementation should preserve this precedence exactly. |
| `python/rl/tasking/common_core_profile.py` | `_profile_name_from_context` at lines 23-59 | Common-core defaults also only infer `naval`, otherwise they fall back to `air`. Ground support must be added here too, not just in `bridge.py`. |
| `python/rl/tasking/common_core_profile.py` | `_profile_module_for_context` at lines 62-66 | Only `_naval_profile` or `_air_profile` can be selected today. Ground profile selection must be wired here. |
| `python/rl/tasking/common_core_profile.py` | `normalize_task_order_spec` at lines 187-188 | Dispatches to the selected profile module. Ground normalization can slot into this existing pattern. |
| `python/rl/tasking/common_core_profile.py` | `infer_coordination_mode` at lines 195-210 | Already delegates to the selected profile module, so ground-specific `Support` handling can stay Python-local. |
| `python/rl/tasking/common_core_profile.py` | `apply_task_order_common_core_defaults` at lines 359-436 | Shared backfill path already exists for `service_profile`, `task_family`, `tactical_unit_type`, `command_relationship`, `authority_scope`, `coordination_mode`, and support IDs. |
| `python/rl/tasking/common_core_profile.py` | `apply_leader_intent_common_core_defaults` at lines 439-545 | Existing propagation path can carry ground defaults from `TaskOrder` into `LeaderIntent` without DTO changes. |
| `python/rl/tasking/common_core_profile.py` | `apply_pilot_report_common_core_defaults` at lines 548-630 | Existing propagation path can carry ground defaults from `TaskOrder` into `PilotReport` without DTO changes. |

### Existing adapter/profile pattern to mirror

| File | Anchor | Preflight finding |
|------|--------|-------------------|
| `python/rl/tasking/air_adapter.py` | module exports at lines 3-48 | Adapter modules are thin export surfaces over common-core helpers plus one profile module. |
| `python/rl/tasking/naval_adapter.py` | module exports at lines 3-45 | Ground can follow the same thin-adapter pattern without changing the bridge contract shape. |
| `python/rl/profile/naval_profile.py` | `infer_naval_task_family` at lines 97-120 | Domain-specific task-family fallback is kept in Python profile code today. |
| `python/rl/profile/naval_profile.py` | `infer_coordination_mode` at lines 123-159 | Domain-specific coordination defaults are also Python-local today. |
| `python/rl/profile/naval_profile.py` | `normalize_task_order_spec` at lines 196-260 | Per-profile normalization pattern already exists. Ground should reuse this structure. |
| `python/rl/profile/air_profile.py` | `infer_coordination_mode` at lines 153-178 | Air uses generic coordination fallbacks over the shared enum surface; ground can do the same. |

### DTO and binding surface relevant to the G1 DTO decision

| File | Anchor | Preflight finding |
|------|--------|-------------------|
| `src/components/tasking/common/core_tasking_enums.h` | lines 3-66 | Shared enums already expose `ServiceProfile::Army`, generic `TacticalUnitType`, `CommandRelationship::Support`, and `CoordinationMode::Support`. No ground-specific enum is required for G1 defaults. |
| `src/components/tasking/common/task_order_core.h` | lines 7-28 | `TaskOrderCore` already owns all first-wave ground fields needed by G0: service, task family, tactical unit type, parent/support IDs, command relationship, authority scope, coordination mode. |
| `src/components/tasking/common/leader_intent_core.h` | lines 7-27 | `LeaderIntentCore` already carries the common fields needed for default propagation. |
| `src/components/tasking/common/pilot_report_core.h` | lines 8-25 | `PilotReportCore` already carries the common fields needed for default propagation. |
| `src/components/tasking/task_order.h` | lines 3-11 | Aggregate shape is still `common + air + naval`; no ground slice exists yet. |
| `src/components/tasking/leader_intent.h` | lines 3-11 | Same aggregate layering pattern as `TaskOrder`. |
| `src/components/tasking/pilot_report.h` | lines 3-7 | Same aggregate layering pattern as `TaskOrder`. |
| `src/components/tasking/naval/task_order_naval.h` | lines 7-10 | Naval-only headers exist only because naval owns extra DTO fields. G1 ground does not yet own any equivalent extra field. |
| `src/interfaces/python/bindings_command.cpp` | `ServiceProfile` at lines 100-105 | Python bindings already expose `ServiceProfile.Army`. |
| `src/interfaces/python/bindings_command.cpp` | `TaskOrder` bindings at lines 319-379 | Common-core tasking fields needed for G1 are already bound. |
| `src/interfaces/python/bindings_command.cpp` | `LeaderIntent` bindings at lines 381-429 | Common-core leader-intent fields needed for G1 are already bound. |

### Existing test anchors to preserve

| File | Anchor | Preflight finding |
|------|--------|-------------------|
| `tests/leader/test_tasking_profile_contracts.py` | `test_normalize_task_order_spec_backfills_common_core` at lines 77-95 | Existing shared-default behavior must stay intact for air. |
| `tests/leader/test_tasking_profile_contracts.py` | `test_bridge_resolves_naval_profile` at lines 22-24 | Ground alias work must not regress naval resolution. |
| `tests/leader/test_tasking_profile_contracts.py` | `test_normalize_task_order_spec_uses_naval_defaults` at lines 26-41 | Ground work must not leak into naval default mapping. |
| `tests/runtime/mission/test_naval_mission_command_mapping.py` | `test_tasking_profile_for_loader_prefers_explicit_profile_over_service_profile` at lines 32-44 | Explicit `tasking_profile` precedence must remain unchanged after adding ground aliases. |
| `tests/runtime/mission/test_naval_mission_command_mapping.py` | `test_tasking_profile_for_loader_infers_naval_from_service_profile_when_tasking_profile_missing` at lines 45-56 | Service-profile inference pattern must still work for naval after adding Army inference. |
| `tests/leader/test_command_field_projection_contracts.py` | lines 13-93 | Domain-specific DTO additions currently require binding and kernel roundtrip coverage. This is evidence against adding empty ground DTO shells without owned fields. |

## Proposed Future Implementation Write Scope

### Files to edit

- `python/rl/tasking/bridge.py`
- `python/rl/tasking/common_core_profile.py`
- `python/rl/tasking/ground_adapter.py` new
- `python/rl/profile/ground_profile.py` new
- focused tests under `tests/leader/`

### Files to leave untouched in G1

- `src/components/tasking/**`
- `src/components/command/**`
- `src/interfaces/python/bindings_command.cpp`
- `tests/runtime/mission/**` except existing read-only regressions used for validation
- runtime, movement, sensor, weapon, damage, facade, and scenario-loader code

### Narrow implementation objective

Future G1 should only:

1. Teach the Python resolver and common-core helper layer to recognize
   `army`, `ground`, and `land`.
2. Add a thin `ground_adapter` module that exposes the same callable names as
   the existing air/naval adapters.
3. Add a `ground_profile` module that normalizes starter task orders and
   provides ground-specific default inference over the existing common-core DTO
   fields.
4. Add focused ground semantics tests.

Future G1 should not:

- invent new ground DTO fields
- add ground-specific C++ headers
- add Python bindings
- define a maintained ground `MissionCommand` execution vocabulary
- modify scenario ingestion or runtime behavior

## Alias Normalization Plan

### Accepted inputs

Resolver-level accepted inputs should be:

- string `army`
- string `ground`
- string `land`
- stringified enum `ServiceProfile.Army`
- enum value `ef_py.ServiceProfile.Army`

### Normalized result

All accepted inputs above should normalize to maintained tasking profile name
`ground`.

### Resolver rules

1. Extend `python/rl/tasking/bridge.py::_normalized_profile_name` so
   `Army`/`army`/`ground`/`land` return `ground`.
2. Extend `python/rl/tasking/common_core_profile.py::_profile_name_from_context`
   with the same recognition set.
3. Preserve existing precedence in `tasking_profile_for_loader`:
   explicit `tasking_profile` still wins over any `service_profile`.
4. Infer `ground` from `service_profile = Army` only when no explicit
   `tasking_profile` was found.
5. Keep `army` and `land` as accepted input aliases only. Future normalized
   output and profile-module naming should remain `ground`.

## Starter Task Default Mapping Table

The current shared `TaskFamily` enum has no `Maneuver` or generic `Support`
entry, so G1 should use the nearest existing generic family and keep the exact
ground meaning in `task_name`, the ground profile module, and the accepted
alias `ground`.

| Task name | `service_profile` | `task_family` fallback | `tactical_unit_type` | `command_relationship` | `authority_scope` | `coordination_mode` | ID rules |
|-----------|-------------------|------------------------|----------------------|------------------------|-------------------|---------------------|----------|
| `TASK_MOVE` | `Army` | `Transit` | `TacticalUnit` | `TACON` | `Tactical` | `Independent` | `parent_node_id` is the command-owner fallback; `supported_node_id` and `supporting_node_id` stay optional |
| `TASK_OCCUPY` | `Army` | `Defend` | `TacticalUnit` | `TACON` | `Tactical` | `Independent` | `parent_node_id` is the command-owner fallback; support IDs stay optional |
| `TASK_SUPPORT` | `Army` | `Defend` | `TacticalUnit` | `Support` | `Tactical` | `Support` | `supporting_node_id` and `supported_node_id` carry the relationship when known; `parent_node_id` remains the fallback owner |

Notes:

- `TacticalUnit` is the nearest maintained common-core unit category for the
  frozen platoon-centered first slice.
- `TASK_SUPPORT` should use the existing shared support relationship fields, not
  naval-only DTO extensions.
- If main thread wants a different `task_family` fallback than `Defend` for
  `TASK_OCCUPY` or `TASK_SUPPORT`, that is a policy choice, not a code blocker.
  The current source surface can support either choice without new DTOs.

## DTO-Shell Recommendation

Recommendation: `not needed in G1`

Evidence:

- The G0 ground baseline only needs common-core ownership fields already
  present in `TaskOrderCore`, `LeaderIntentCore`, and `PilotReportCore`.
- `ServiceProfile::Army` is already present and bound.
- The only existing domain-specific tasking DTO slice is naval, and its extra
  fields are backed by dedicated headers, bindings, and kernel roundtrip tests.
  Ground does not yet own any equivalent field set.
- Adding empty `src/components/tasking/ground/**` or
  `src/components/command/ground/**` headers now would widen the C++ and binding
  boundary without adding behavior, coverage value, or frozen field ownership.

Escalation trigger for later work:

- If a later phase introduces a ground-owned DTO field that cannot live in the
  current common core, that later phase should add C++ shells, bindings, and
  roundtrip tests together. That is not justified in G1.

## Focused Validation Plan

### Read-only validation to run during implementation

```bash
git diff --check
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/runtime/mission/test_naval_mission_command_mapping.py
```

### Focused tests to add in future G1 implementation

Add one new focused file, preferably `tests/leader/test_tasking_profile_contracts.py`,
covering:

1. `resolve_tasking_profile("army" | "ground" | "land")` returns the ground
   adapter.
2. `resolve_tasking_profile(ef_py.ServiceProfile.Army)` returns the ground
   adapter.
3. `tasking_profile_for_loader` still prefers explicit `tasking_profile` over
   `service_profile = Army`.
4. `tasking_profile_for_loader` infers ground from `service_profile = Army`
   when `tasking_profile` is absent.
5. `normalize_task_order_spec` maps `TASK_MOVE`, `TASK_OCCUPY`, and
   `TASK_SUPPORT` to the table above.
6. `apply_task_order_common_core_defaults`,
   `apply_leader_intent_common_core_defaults`, and
   `apply_pilot_report_common_core_defaults` preserve ground semantics and IDs.

Tests intentionally not required in G1:

- mission-runtime execution behavior
- scenario-loader fixture coverage
- kernel roundtrip tests for new DTO fields

Those belong to later G2/G3/G4 slices unless scope is explicitly widened.

## Compatibility Risks For Air/Naval Behavior

1. `bridge.py` and `common_core_profile.py` each have their own profile-name
   inference. Ground support must land in both places or resolver and default
   propagation will disagree.
2. Existing explicit-profile precedence must remain unchanged. Ground inference
   must not override an explicit `air` or `naval` tasking profile.
3. `service_profile_default()` still returns `AirForce`, so ground defaults must
   be injected from the ground profile path rather than by changing the global
   shared default for everyone.
4. G1 should avoid any new `MissionCommand` semantics for ground. That surface
   is not yet frozen and widening it would risk air/naval regressions outside
   G1 scope.

## Residuals And Release Decision

### Residuals for G2/G3

- G2 still needs the first fixture path and task-spec examples after G1 lands.
- G3 still owns the first accepted ground execution surface and any real ground
  `MissionCommand` behavior.
- The exact `task_family` fallback labels can be revisited later if the common
  enum surface grows, without forcing a G1 DTO change now.

### Blocker check

No blocker was found for a narrow G1 release.

Release should be stopped only if the requested implementation scope expands
beyond:

- Python resolver/profile work
- common-core default mapping
- focused leader/profile tests

## Worker Return Packet

Stream: `G1-A`

Status: `preflight-only`

Touched files:

- `docs/task/ground/g1_contract_skeleton/g1_profile_dto_preflight_20260521.md`

Commands run:

- `sed -n '1,220p' docs/standards/governance/subagent_usage_policy.md`
- `sed -n '1,240p' docs/task/ground/ground_subagent_dispatch_queue_20260521.md`
- `sed -n '1,220p' docs/task/ground/g1_contract_skeleton/README.md`
- `sed -n '1,260p' docs/task/ground/g1_contract_skeleton/g1_profile_dto_contract_cluster_20260521.md`
- `sed -n '1,260p' docs/standards/ground/README.md`
- `sed -n '1,260p' docs/standards/ground/minimal_task_structure.md`
- `sed -n '1,260p' docs/standards/services/army.md`
- `rg -n "tasking_profile|common_core_profile|naval_profile|ground_profile|adapter|TASK_MOVE|TASK_OCCUPY|TASK_SUPPORT|specialization|army|ground|land" python src tests`
- `nl -ba python/rl/tasking/bridge.py | sed -n '1,240p'`
- `nl -ba python/rl/tasking/common_core_profile.py | sed -n '1,220p'`
- `nl -ba python/rl/tasking/common_core_profile.py | sed -n '220,660p'`
- `nl -ba python/rl/tasking/air_adapter.py | sed -n '1,220p'`
- `nl -ba python/rl/tasking/naval_adapter.py | sed -n '1,220p'`
- `nl -ba python/rl/profile/naval_profile.py | sed -n '1,260p'`
- `nl -ba python/rl/profile/air_profile.py | sed -n '100,260p'`
- `nl -ba python/rl/profile/air_profile.py | sed -n '520,620p'`
- `nl -ba tests/leader/test_tasking_profile_contracts.py | sed -n '1,220p'`
- `nl -ba tests/leader/test_tasking_profile_contracts.py | sed -n '1,220p'`
- `rg -n "struct TaskOrder|struct LeaderIntent|struct PilotReport|class TaskOrder|TaskOrder\\b|LeaderIntent\\b|PilotReport\\b|ServiceProfile|TaskFamily|TacticalUnitType|CoordinationMode" src/interfaces src/components src/core`
- `nl -ba src/components/tasking/README.md | sed -n '1,220p'`
- `find src/components -maxdepth 3 \\( -path '*/tasking/*' -o -path '*/command/*' \\) | sort`
- `nl -ba src/interfaces/python/bindings_command.cpp | sed -n '300,520p'`
- `nl -ba src/components/tasking/common/core_tasking_enums.h | sed -n '1,220p'`
- `nl -ba python/rl/profile/common_core_defaults.py | sed -n '1,260p'`
- `nl -ba src/components/tasking/task_order.h | sed -n '1,120p'`
- `nl -ba src/components/tasking/leader_intent.h | sed -n '1,120p'`
- `nl -ba src/components/tasking/pilot_report.h | sed -n '1,120p'`
- `nl -ba src/components/tasking/naval/task_order_naval.h | sed -n '1,160p'`
- `nl -ba src/components/tasking/naval/leader_intent_naval.h | sed -n '1,160p'`
- `nl -ba src/components/tasking/naval/pilot_report_naval.h | sed -n '1,160p'`
- `nl -ba tests/runtime/mission/test_naval_mission_command_mapping.py | sed -n '1,240p'`
- `nl -ba python/rl/tasking/__init__.py | sed -n '1,220p'`
- `nl -ba python/rl/profile/__init__.py | sed -n '1,200p'`
- `find docs/task/ground/g1_contract_skeleton -maxdepth 1 -type f | sort`
- `git status --short`
- `nl -ba tests/leader/test_command_field_projection_contracts.py | sed -n '1,220p'`
- `nl -ba src/components/tasking/common/task_order_core.h | sed -n '1,220p'`
- `nl -ba src/components/tasking/common/leader_intent_core.h | sed -n '1,220p'`
- `nl -ba src/components/tasking/common/pilot_report_core.h | sed -n '1,220p'`
- `rg -n "TaskFamily\\.(Transit|Patrol|Escort|Intercept|Attack|Defend|Recover|Withdraw)|task_family.*(Transit|Patrol|Escort|Intercept|Attack|Defend|Recover|Withdraw)" python tests src`
- `rg -n "TASK_MOVE|TASK_OCCUPY|TASK_SUPPORT|Maneuver|Support" docs python tests src`
- `nl -ba docs/task/ground/g2_content_test_seed/g2_content_fixture_test_cluster_20260521.md | sed -n '1,200p'`

Evidence:

- Ground alias resolution is currently absent from both Python resolver
  pathways.
- Existing common-core DTO fields are sufficient for first-wave ground starter
  defaults.
- Current C++ tasking layering justifies domain-specific headers only when a
  domain owns extra fields.
- Existing naval tests provide the key compatibility guardrails G1 must retain.

Residuals:

- G2 fixtures and tests wait on the accepted G1 implementation.
- G3 still owns the first real ground execution surface.

Integration notes:

- Main-thread integration should treat this note as the authoritative G1
  preflight recommendation for implementation release review.

Closure impact:

- This preflight unblocks a narrow G1 implementation request.

G1 implementation recommendation:

- `implementation-ready`

G1 blockers:

- none for the narrow Python-profile-only slice
- block if scope expands into runtime semantics, scenario-loader changes,
  Python bindings, or C++ ground DTO ownership
