# A8 Damage Effect Chain Dispatch Queue

Status: `2026-06-07` first implementation dispatch queue for
[README.md](README.md). This queue starts A8 from the already accepted planning
boundary and read-only structure evidence.

## Dispatch Boundary

The first A8 implementation wave must start with explainability and tests before
touching flight behavior. Workers may change their assigned files only. They
must not revert unrelated local edits, especially the existing dirty A2 retained
artifact manifests and RL/HMoE files in the parent worktree.

This dispatch starts these clusters:

- `A8-DEC-C Shot Effect Record`
- `A8-DEC-D Part Effect Vocabulary`
- `A8-DEC-F MQ-9 / AIM-120C Validation`

`A8-DEC-E Consumer Integration` remains held until C and D have a stable record
and vocabulary. It should not be implemented in this wave.

## Worker Packets

| Packet | Cluster | Owner | Model / reasoning | Write set | Goal | Non-goals | Validation | Return packet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A8-W1 Shot Record` | `A8-DEC-C` | current-session worker | inherited / high | `src/core/interfaces/**`, `src/core/engine/*damage*`, `src/models/weapons/detail/default_effects_result_detail.inc`, `tests/runtime/air_combat/weapon_guidance_realism/**`; optional A8 contract note if needed | Freeze the smallest shot-effect record that can explain fuze result, detonation geometry, warhead action, affected part, concrete damage mode, and downstream consequence hooks. Prefer tests that expose the contract before broad implementation. | No aerodynamic/control changes, no direct kill rule, no Pk/fuze authority claim, no MQ-9 special rule. | Focused pytest under `tests/runtime/air_combat/weapon_guidance_realism` and any existing contract/header guard touched by the worker. | Required worker packet with touched files, commands/outcomes, risks, residuals. |
| `A8-W2 Part Failure Vocabulary` | `A8-DEC-D` | current-session worker | inherited / high | `src/components/combat/damage.h`, `src/content/unit_definition_loader.cpp`, `src/models/weapons/detail/default_effects_component_damage_detail.inc`, `src/models/weapons/detail/default_effects_system_effect_detail.inc`, focused component-damage tests; optional A8 vocabulary note if needed | Map existing fragment/blast/penetration/rod-load evidence into named part failure modes such as puncture, cut, deformation, leak, pressure loss, data loss, fire source, and structural weakening. | No flight/aerodynamic consumer edits, no broad aircraft data rewrite, no calibrated vulnerability claim. | Component-damage and loader tests selected by the worker; run `test_weapon_guidance_realism_guards.py` if public behavior changes. | Required worker packet with touched files, commands/outcomes, risks, residuals. |
| `A8-W3 Validation Fixtures` | `A8-DEC-F` | current-session worker | inherited / medium/high | `tests/runtime/air_combat/**`, test-only helpers/fixtures if needed, no production code unless blocked and approved by integration | Build or stage fixed MQ-9 / AIM-120C checks for near-range full chain, longer-range auditable chain, right aileron/flap control damage, data-link or power-distribution mission damage, and non-authority guard. | No production physics implementation, no real-world lethality or probability claim, no flaky live-only acceptance. | `test_air_combat_1v1_fire_missile.py`, `test_weapon_guidance_realism_guards.py`, and new focused tests if added. | Required worker packet with touched files, commands/outcomes, risks, residuals. |

## Integration Rules

- The main thread owns final merge/integration into the parent worktree.
- Workers must treat existing dirty files outside their write set as user or
  unrelated work and must not revert them.
- `A8-W1` owns public shot-record shape. `A8-W2` may not add public fields that
  conflict with W1; it may return a blocked packet if it needs W1's record shape.
- `A8-W3` may prepare tests against existing fields, but tests requiring new
  shot-record fields should be marked expected integration follow-up until W1
  lands.
- No worker may implement `A8-DEC-E` in this dispatch.
- No new conversation threads may be created; use current-session subagents
  only.

## Validation Before Integration

Minimum integration checks after worker results are merged:

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain src tests
cmake --build build-workshop -j 8
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

Add narrower tests named by each worker packet before acceptance.

## Current Dispatch State

| Packet | State | Notes |
| --- | --- | --- |
| `A8-W1 Shot Record` | pass | Accepted existing linked shot record shape through focused guard tests; no new public fields added. |
| `A8-W2 Part Failure Vocabulary` | partial | Accepted internal failure-mode vocabulary and existing-aircraft-state routing; public per-row fields remain held. |
| `A8-W3 Validation Fixtures` | partial pass | Accepted fixed MQ-9/AIM-120C fixtures and non-authority guards; A8-DEC-E flight-consumer checks remain held. |
| `A8-DEC-E Consumer Integration` | held | Starts only after record and vocabulary are stable. |

## Integration Acceptance 2026-06-07

Accepted validation:

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain src/components/combat/damage.h src/content/unit_definition_loader.cpp src/models/weapons/detail/default_effects_component_damage_detail.inc src/models/weapons/detail/default_effects_system_effect_detail.inc tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py tests/runtime/air_combat/weapon_guidance_realism
cmake --build build-workshop -j 8
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

Outcomes: diff check pass, build pass, `164 passed, 1 skipped` for the realism
guards, and `11 passed` for the 1v1 fire-missile tests.

## Residuals

- If W1 and W2 both need the same public field shape, stop and merge W1 first.
- If W3 can only produce flaky live-missile checks, keep them as diagnostic
  probes, not acceptance tests.
- If any worker needs to edit physics consumers, re-scope into `A8-DEC-E`.
