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
| `A8-W2 Part Failure Vocabulary` | partial | Accepted internal failure-mode vocabulary and existing-aircraft-state routing. W4 later exposed the public row fields. |
| `A8-W3 Validation Fixtures` | partial pass | Accepted fixed MQ-9/AIM-120C fixtures and non-authority guards; A8-DEC-E flight-consumer checks remain held. |
| `A8-DEC-E Consumer Integration` | held | Starts after W5/W6 scout evidence is integrated into a narrow implementation packet. |

## Second Dispatch Wave

Status: `2026-06-07` dispatched to current-session subagents only. No new
conversation threads are allowed.

This wave keeps one implementation task and two read-only consumer scouts so
public record work does not conflict with flight-consumer planning.

| Packet | Cluster | Owner | Model / reasoning | Write set | Goal | Non-goals | Validation | Return packet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A8-W4 Public Failure Mode Rows` | `A8-DEC-C/D` | Popper | inherited / high | `src/runtime/contracts/engagement_contracts.h`, `src/interfaces/python/bindings_runtime.cpp`, `src/models/weapons/detail/default_effects_component_damage_detail.inc`, `src/models/weapons/detail/default_effects_system_effect_detail.inc`, focused A8 row tests; optional `a8_w4_public_failure_mode_rows_20260607.md` | Expose the concrete part-failure modes from the internal W2 assessment on public component shot rows and Python bindings. | No flight/aero/propulsion consumer edits, no direct kill rule, no MQ-9 special rule, no Pk or deterministic fuze claim. | `cmake --build build-workshop -j 8`; `python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`; `python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py` | Required worker packet with touched files, commands/outcomes, risks, residuals. |
| `A8-W5 Propulsion Fuel Mass Consumer Scout` | `A8-DEC-E` | McClintock | inherited / high | Read-only; optional `a8_w5_propulsion_fuel_mass_consumer_evidence_20260607.md` | Identify the smallest safe path for engine, propeller, fuel leak, and mass effects through existing maintained systems. | No production code changes, no direct crash/disappear behavior, no MQ-9 special rule, no real-world lethality claim. | File/line evidence; optional focused greps or existing tests. | Required worker packet with touched files, commands/outcomes, risks, residuals. |
| `A8-W6 Aero Control Consumer Scout` | `A8-DEC-E` | Plato | inherited / high | Read-only; optional `a8_w6_aero_control_consumer_evidence_20260607.md` | Identify the smallest safe path for wing, control-surface, structure, authority, and asymmetry damage to affect maintained flight/aero/control systems. | No production code changes, no independent "can fly" verdict, no direct crash rule, no real-world lethality claim. | File/line evidence; optional focused greps or existing tests. | Required worker packet with touched files, commands/outcomes, risks, residuals. |

Second-wave integration rules:

- `A8-W4` is the only writer allowed to touch public shot-row fields in this
  wave.
- `A8-W5` and `A8-W6` are read-only preparation packets for `A8-DEC-E`.
- No worker may widen consumer integration until W4's public row fields are
  mergeable or explicitly blocked.
- The main thread owns final merge and status synchronization.

## Second Dispatch Acceptance 2026-06-07

| Packet | State | Notes |
| --- | --- | --- |
| `A8-W4 Public Failure Mode Rows` | pass | Public component rows now expose simulated failure-mode names, severities, source, and non-authority flag. |
| `A8-W5 Propulsion Fuel Mass Consumer Scout` | pass | Read-only evidence identifies the propulsion/fuel/mass path and engine-tuning bypass risk. |
| `A8-W6 Aero Control Consumer Scout` | pass | Read-only evidence identifies the control/aero hook and confirms force/moment response still needs implementation. |
| `A8-DEC-E Consumer Integration` | held | No production consumer changes landed in this wave. |

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

Second-wave accepted validation:

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain src/runtime/contracts/engagement_contracts.h src/interfaces/python/bindings_runtime.cpp src/models/weapons/detail/default_effects_component_damage_detail.inc src/models/weapons/detail/default_effects_system_effect_detail.inc tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py tests/runtime/air_combat/weapon_guidance_realism/component_damage.py
cmake --build build-workshop -j 8
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
python -m pytest -q tests/runtime/engagement/test_engagement_contract_shape.py
```

Outcomes: diff check pass, build pass, `165 passed` for the realism guards,
`11 passed` for 1v1 fire-missile tests, and `4 passed` for engagement contract
shape tests.

## Residuals

- Public failure-mode rows are now mergeable, but they remain synthetic and
  non-authoritative.
- `A8-DEC-E` should split into narrow implementation packets: propulsion/fuel
  first, then one control/aero response.
- No consumer packet may add direct crash, direct disappearance, MQ-9 special
  handling, probability-of-kill claims, or an independent can-fly verdict.
