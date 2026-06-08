# A8 Damage Effect Chain Dispatch Queue

Status: `2026-06-08` active implementation dispatch queue for
[README.md](README.md). This queue starts A8 from the already accepted planning
boundary and tracks the bounded implementation waves through `A8-DEC-E`.

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
| `A8-DEC-E Consumer Integration` | partial | W7 landed the propulsion tuning consumer; one wing/control aero response remains. |

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

## Third Dispatch Acceptance 2026-06-08

| Packet | State | Notes |
| --- | --- | --- |
| `A8-W7 Propulsion Tuning Consumer` | pass | Explicit engine tuning now consumes propulsion damage before current thrust is computed. |
| `A8-DEC-E Consumer Integration` | partial | Propulsion tuning bypass is closed; wing/control aero response remains active. |

Accepted validation:

```bash
git diff --check -- src/systems/physics/propulsion_system.h tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py docs/task/air_combat/a8_damage_effect_chain
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_a8_engine_damage_scales_actual_thrust_with_explicit_engine_tuning
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_tuning_runtime.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_realism_guards.py
```

Outcomes: diff check pass, build pass, focused A8 propulsion consumer test
`1 passed`, weapon guidance realism guards `166 passed, 239 subtests passed`,
flight dynamics tuning runtime `3 passed`, 1v1 fire-missile tests `11 passed,
2 subtests passed`, and flight dynamics realism guards `4 passed`.

## Fourth Dispatch Wave 2026-06-08

Status: reviewed and accepted on 2026-06-08. No new conversation threads were
created.

This wave keeps one implementation writer and two non-overlapping support
workers. The implementation packet owns the code cut; scouts must not edit the
same production or test files.

| Packet | Cluster | Owner | Model / reasoning | Write set | Goal | Non-goals | Validation | Return packet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A8-W8 Wing/Control Aero Consumer` | `A8-DEC-E` | Popper | inherited / high | `src/systems/physics/aerodynamics_system.h`; optional new focused test module under `tests/runtime/air_combat/weapon_guidance_realism/` and collector import if needed | Make one narrow wing/control damage response visible through maintained aerodynamic forces, moments, or axis authority. Consume existing `AircraftDamageState` fields such as structural integrity, roll/pitch/yaw control integrity, hydraulic pressure, and control asymmetry. | No direct crash/disappearance rule, no independent can-fly verdict, no MQ-9 special rule, no real-world lethality or Pk claim, no broad flight-model rewrite. | `cmake --build build-workshop --target ef_py -j2`; focused new/changed test; `python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`; `python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_realism_guards.py` | Required worker packet with touched files, commands/outcomes, risks, residuals. |
| `A8-W9 MQ-9/AIM-120C Consumer Validation Scout` | `A8-DEC-F` | McClintock | inherited / high | Read-only | Identify the smallest deterministic MQ-9/AIM-120C validation checks that should prove W8's downstream response after integration. Prefer existing A8 fixture helpers and avoid live-only flaky acceptance. | No production edits, no test edits, no direct kill expectation, no real-world lethality claim. | File/line evidence and proposed exact pytest selectors. | Required worker packet with touched files `none`, commands/outcomes, risks, residuals. |
| `A8-W10 Integration Guard Scout` | `A8-DEC-G` | Plato | inherited / high | Read-only | Review A8 docs/status/test surfaces for what must change after W8 returns, and identify any architecture or CI gates likely to fail. | No acceptance marking, no archive move, no code/test edits. | File/line evidence and proposed integration checklist. | Required worker packet with touched files `none`, commands/outcomes, risks, residuals. |

Fourth-wave integration rules:

- `A8-W8` is the only writer in this wave.
- `A8-W9` and `A8-W10` are read-only and must not patch files.
- The main thread owns final merge, verification, and status synchronization.
- If W8 cannot make a narrow maintained-system response without a direct
  crash/can-fly shortcut, it must return `blocked` with the smallest safe
  replacement path.

## Fourth Dispatch Acceptance 2026-06-08

| Packet | State | Notes |
| --- | --- | --- |
| `A8-W8 Wing/Control Aero Consumer` | pass | Structural, hydraulic, axis-control, and control-asymmetry damage now affect maintained aerodynamic coefficients and moments. Main-thread integration added the fixed MQ-9/AIM-120C right-aileron response check proposed by W9 plus a 300 s stabilized long-run response check. |
| `A8-W9 MQ-9/AIM-120C Consumer Validation Scout` | pass | Read-only scout identified the smallest deterministic fixed MQ-9 right-aileron response selector and warned against live-only acceptance. |
| `A8-W10 Integration Guard Scout` | pass | Read-only scout identified the collection/docs/CI gates; main-thread integration collected the new mixin, formatted the changed C++ file, and synchronized status docs. |
| `A8-DEC-E Consumer Integration` | partial | Propulsion tuning and one wing/control aero response are landed. Broader fuel/fire, sensor/data-link, and aircraft-specific control-law fidelity remain held. |

Accepted validation:

```bash
clang-format --dry-run -Werror src/systems/physics/aerodynamics_system.h
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_aero_consumer.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'a8_mq9_aim120_right_aileron_damage_changes_roll_response_through_aero_path or wing_control_damage_reaches_neutral_aero_response'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'right_aileron_damage_long_run_reaches_ground_response or right_aileron_damage_changes_roll_response_through_aero_path'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_tuning_runtime.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

Outcomes: clang-format pass, focused Python lint pass, build pass, focused W8
aero/MQ-9 short response checks `2 passed, 166 deselected`, focused W8 long-run
MQ-9 response checks `2 passed, 167 deselected`, weapon guidance realism guards
`169 passed`, flight dynamics realism guards `4 passed`, flight dynamics tuning
runtime `3 passed`, and 1v1 fire-missile tests `11 passed`.

## Fourth-Wave Residuals

- Public failure-mode rows are now mergeable, but they remain synthetic and
  non-authoritative.
- `A8-DEC-E` now has propulsion tuning and one narrow control/aero response.
  Fuel/mass leakage already has a maintained runtime path and remains covered
  by existing A8 guards, but broader downstream fuel/fire and sensor/data-link
  response tests remain held.
- Long-run right-aileron damage reaches the near-ground response under stable
  throttle, but ground impact/crash-state propagation is not yet a maintained
  outcome.
- No consumer packet may add direct crash, direct disappearance, MQ-9 special
  handling, probability-of-kill claims, or an independent can-fly verdict.

## Fifth Dispatch Wave 2026-06-08

Status: reviewed and accepted on 2026-06-08. No new conversation threads were
created.

This wave keeps one bounded test/implementation worker and one read-only
lifecycle scout. The writer owns fuel/fire/mass downstream evidence only. The
scout owns the next crash/ground-impact lifecycle design evidence and must not
patch files.

| Packet | Cluster | Owner | Model / reasoning | Write set | Goal | Non-goals | Validation | Return packet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A8-W11 Fuel/Fire/Mass Consumer Evidence` | `A8-DEC-E/F` | Popper | inherited / high | Prefer tests under `tests/runtime/air_combat/weapon_guidance_realism/` and collector import only; production edits only if an existing maintained fuel/fire/mass path is proven unreachable and the blocker is described first. | Add the smallest deterministic MQ-9/AIM-120C-like profiled-hit evidence that fuel-system, leak, mass, fire-risk, or propulsion/fuel effects continue through maintained runtime paths after the immediate shot record. Prefer existing helpers and fixed local-hit cases over live-only acceptance. | No direct crash/disappearance rule, no ground-impact lifecycle implementation, no MQ-9 special kill rule, no real-world lethality or Pk claim, no broad fuel-system rewrite. | `cmake --build build-workshop --target ef_py -j2`; focused new/changed pytest selector; `python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py` if collector or shared guards change. | Required worker packet with status, touched files, commands/outcomes, remaining paths, behavior risks, integration notes. |
| `A8-W12 Ground-Impact Lifecycle Scout` | `A8-DEC-E/G` | McClintock | inherited / high | Read-only. | Identify the smallest maintained path for a damaged aircraft that reaches ground contact to become one of: still-observable landed airframe, crashed wreck, or debris/fragment residue. Inspect current ground-contact, health/loss-state, engagement report, runtime facade, and entity lifecycle surfaces. Return exact file/line evidence and a recommended follow-up writer packet. | No code edits, no docs edits, no direct touch-kill proposal, no independent can-fly verdict, no one-size-fits-all deletion rule, no real-world lethality claim. | File/line evidence; proposed exact tests and acceptance gates for the next implementation packet. | Required worker packet with touched files `none`, commands/outcomes, remaining paths, behavior risks, integration notes. |

Fifth-wave integration rules:

- `A8-W11` is the only writer in this wave.
- `A8-W12` is read-only and must not patch files.
- The main thread owns final review, verification, and status synchronization.
- If W11 finds fuel/fire/mass effects already covered by existing tests, it
  should return the evidence and avoid adding duplicate tests.
- If W12 finds that crash/ground-impact lifecycle requires a new public object
  or event contract, it must return `partial` or `blocked` with the smallest
  replacement path rather than inventing a direct deletion rule.

## Fifth Dispatch Acceptance 2026-06-08

| Packet | State | Notes |
| --- | --- | --- |
| `A8-W11 Fuel/Fire/Mass Consumer Evidence` | pass | Added a fixed center-fuel-cell MQ-9/AIM-120C-like profiled-hit check. The immediate shot row exposes `fuel_leak` and `fire_source`, the damage report remains non-authoritative and does not claim destruction, and later runtime steps drain fuel and mass through maintained systems. |
| `A8-W12 Ground-Impact Lifecycle Scout` | partial | Accepted as read-only evidence only. The scout found ground-contact detection and existing loss/destruct paths, but no public landed-airframe, crashed-wreck, or debris/residue lifecycle surface. This does not unlock direct touch-kill or direct disappearance behavior. |
| `A8-DEC-E Consumer Integration` | partial | Propulsion tuning, one wing/control aero response, and one fixed fuel-leak/mass runtime response are landed. Broader fire behavior, sensor/data-link consequences, aircraft-specific control laws, and ground-impact lifecycle remain held. |
| `A8-DEC-F MQ-9 / AIM-120C Validation` | partial pass | Fixed MQ-9/AIM-120C validation now covers non-authoritative shot rows, right-aileron short/long response, and center-fuel-cell leak/mass response. It still does not prove real-world lethality or final crash behavior. |

Accepted validation:

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain/a8_damage_effect_chain_dispatch_queue_20260607.md tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'center_fuel_hit_continues_into_leak_and_mass_runtime_path'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

Outcomes: diff whitespace check pass, focused Python lint pass, fixed
center-fuel-cell leak/mass runtime check `1 passed, 169 deselected`, and weapon
guidance realism guards `170 passed`.

Current residuals after fifth-wave acceptance:

- The fuel case proves leakage, mass change, and fire-source marking through
  maintained runtime paths. It does not yet prove broader fire spread, fuel-feed
  interruption, or crash behavior.
- The ground-impact path needs a public lifecycle or residue contract before it
  can be accepted. The next writer packet should test safe runway contact,
  damaged-aircraft crash/wreck publication, and low-speed non-crash contact.
- No consumer packet may add direct crash, direct disappearance, MQ-9 special
  handling, probability-of-kill claims, or an independent can-fly verdict.

## Sixth Dispatch Wave 2026-06-08

Status: W13 accepted on 2026-06-08 after main-thread takeover. W14 remains
held; no new conversation threads were created.

This wave opens `A8-DEC-H Ground-Impact Lifecycle` instead of extending
`A8-DEC-E`. The main question is no longer whether a damaged aircraft can fly;
that remains for the flight/physics systems. The question is how a severe
ground impact becomes an observable post-impact object state without deleting
the aircraft as the only result.

| Packet | Cluster | Owner | Model / reasoning | Write set | Goal | Non-goals | Validation | Return packet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A8-W13 Ground-Impact Lifecycle Writer` | `A8-DEC-H` | McClintock | inherited / high | Narrow lifecycle/ground-impact write set only: `src/systems/physics/ground_contact_system.h`, lifecycle or damage-state component/contract files if needed, Python bindings if a new public field is needed, focused tests under `tests/runtime/air_combat/weapon_guidance_realism/` and collector imports. | Implement the smallest maintained public path that distinguishes safe ground contact from severe damaged-aircraft impact. A severe impact should become observable as one of: landed airframe, crashed wreck, or debris/residue. Tests must cover safe runway contact, damaged MQ-9 long-run or constructed severe-impact contact, and low-speed non-crash contact. | No direct touch-kill, no direct disappearance as the public outcome, no MQ-9 special case, no independent can-fly verdict, no real-world lethality claim, no broad terrain/landing rewrite. | `git diff --check` on touched files; clang-format for touched C++; `cmake --build build-workshop --target ef_py -j2` if bindings/C++ change; focused pytest selector; full `python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py` if collector/shared guards change. | Required worker packet with status, touched files, commands/outcomes, remaining paths, behavior risks, integration notes. |
| `A8-W14 Sensor/Data-Link/Fire Consequence Scout` | `A8-DEC-E/F` | Popper | inherited / high | Read-only. | Identify the smallest next non-overlapping checks for sensor/data-link degradation and broader fire behavior after the fuel-leak evidence. Return exact file/line entry points, proposed fixed MQ-9/AIM-120C-like hit cases, and tests that do not overlap W13's lifecycle write set. | No code edits, no docs edits, no ground-impact implementation, no direct crash/disappearance rule, no real-world lethality claim. | File/line evidence; proposed exact pytest selectors and acceptance gates for a later writer packet. | Required scout packet with touched files `none`, commands/outcomes, remaining paths, behavior risks, integration notes. |

Sixth-wave integration rules:

- `A8-W13` is the only writer in this wave.
- `A8-W14` is read-only and must not patch files.
- W13 owns only post-impact lifecycle observability. It must not modify the
  weapon-effect logic to make an aircraft crash sooner.
- W14 must avoid files W13 needs unless it is only citing them as read-only
  context.
- The main thread owns final review, verification, status synchronization, and
  any commit.

## Sixth Dispatch Acceptance 2026-06-08

| Packet | State | Notes |
| --- | --- | --- |
| `A8-W13 Ground-Impact Lifecycle Writer` | pass | Main thread implemented the narrow writer slice after the existing agent returned no usable new packet. `GroundState` now exposes no-contact, landed-airframe, and crashed-wreck lifecycle states through `debug_get_ground_contact_state`. Severe impact and gear collapse no longer use `Health=0` as the only public result. |
| `A8-W14 Sensor/Data-Link/Fire Consequence Scout` | held | No accepted scout packet has been integrated yet. Sensor/data-link and broader fire consequences remain the next non-overlapping scout/writer area. |
| `A8-DEC-H Ground-Impact Lifecycle` | partial pass | Safe runway contact stays active/observable, constructed severe impact records crashed-wreck state while the entity remains active, and low-speed contact does not create a crash. Debris/residue entities are still not implemented. |

Accepted validation:

```bash
git diff --check -- src/components/systems/logistics.h src/systems/physics/ground_contact_system.h src/core/engine/simulation_kernel.h src/core/engine/simulation_kernel_observation_api.cpp src/interfaces/python/bindings_core.cpp tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'ground_contact_lifecycle'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

Outcomes: diff whitespace check pass, focused Python lint pass, `ef_py` build
pass, ground-contact lifecycle checks `3 passed, 170 deselected`, and weapon
guidance realism guards `173 passed`.

Current residuals after sixth-wave W13 acceptance:

- `crashed_wreck` is a public lifecycle state on the original entity, not a
  separate debris cloud or residue entity.
- W13 does not modify weapon-effect logic and does not make AIM-120C impacts
  crash sooner.
- W14 remains held; sensor/data-link and broader fire runtime consequences are
  still the next non-overlapping area.

## Seventh Dispatch Wave 2026-06-08

Status: reviewed and accepted on 2026-06-08. No new conversation threads were
created.

This wave returns to the remaining `A8-DEC-E/F` consequence checks after W13
closed the first ground-contact lifecycle gap. It keeps one writer and one
read-only scout with disjoint scope.

| Packet | Cluster | Owner | Model / reasoning | Write set | Goal | Non-goals | Validation | Return packet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A8-W15 Sensor/Data-Link Consequence Writer` | `A8-DEC-E/F` | Popper | inherited / high | Prefer tests under `tests/runtime/air_combat/weapon_guidance_realism/` and collector imports. Production/binding edits only if an existing maintained sensor/data-link consequence surface is proven unreachable and the blocker is named first. | Add the smallest deterministic MQ-9/AIM-120C-like fixed-hit check showing data-link, avionics, power, or sensor damage continues beyond the immediate shot row into an observable maintained runtime consequence. Prefer existing `debug_get_data_link_state`, contact/message surfaces, `AircraftDamageState`, or mission/sensor capability readouts. | No ground-impact/lifecycle edits, no direct crash/disappearance rule, no MQ-9 special kill rule, no real-world lethality or probability claim, no broad data-link rewrite. | `git diff --check` on touched files; focused pytest selector; `python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`; `cmake --build build-workshop --target ef_py -j2` only if production/binding files change. | Required worker packet with status, touched files, commands/outcomes, remaining paths, behavior risks, integration notes. |
| `A8-W16 Broader Fire Consequence Scout` | `A8-DEC-E/F` | McClintock | inherited / high | Read-only. | Identify the smallest next writer path for broader fire behavior after W11's fuel-leak/fire-source evidence. Inspect aircraft damage fire fields, mass/fuel leak runtime, platform fire severity, fire suppression fields, and any exposed debug/test surfaces. Return exact file/line evidence and proposed fixed MQ-9/AIM-120C-like hit cases. | No code edits, no docs edits, no sensor/data-link writer changes, no ground-impact lifecycle changes, no direct crash/disappearance rule, no real-world lethality claim. | File/line evidence; proposed exact pytest selectors and acceptance gates for a later writer packet. | Required scout packet with touched files `none`, commands/outcomes, remaining paths, behavior risks, integration notes. |

Seventh-wave integration rules:

- `A8-W15` is the only writer in this wave.
- `A8-W16` is read-only and must not patch files.
- W15 must prove a maintained downstream consequence; it must not add a fake
  mission-failed flag just to satisfy the test.
- W16 must avoid W15's test write set except as read-only context.
- The main thread owns final review, verification, status synchronization, and
  any commit.

## Seventh Dispatch Acceptance 2026-06-08

| Packet | State | Notes |
| --- | --- | --- |
| `A8-W15 Sensor/Data-Link Consequence Writer` | pass | Added a fixed MQ-9/AIM-120C-like data-link transceiver hit check. The shot row exposes `data_loss`, remains non-authoritative, and later runtime steps show mission/sensor/survivability plus avionics/crew/navigation degradation through maintained platform state. |
| `A8-W16 Broader Fire Consequence Scout` | pass | Accepted as read-only evidence. It found a tests-only next writer path using MQ-9 left-wing fuel-cell fire growth and rear-engine fire-zone seeding, while warning not to assert fire growth for engine-only hits without flammable exposure. |
| `A8-DEC-E Consumer Integration` | partial | Propulsion, wing/control aero, fuel-leak/mass, sensor/data-link mission consequence, and ground-contact lifecycle evidence are now in place. Broader fire behavior and debris/residue entities remain held. |

Accepted validation:

```bash
git diff --check -- docs/task/air_combat tests/runtime/air_combat/weapon_guidance_realism/a8_sensor_datalink_consumer.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_sensor_datalink_consumer.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'data_link_hit_continues_into_platform_mission_sensor_runtime_path'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

Outcomes: docs/tests diff whitespace check pass, focused Python lint pass,
data-link runtime consequence check `1 passed, 173 deselected`, and weapon
guidance realism guards `174 passed`.

Residuals before eighth-wave dispatch:

- Data-link consequence is proven through maintained platform mission/sensor
  state, not through active MQ-9 data-link message traffic.
- Broader fire behavior has read-only evidence but no writer slice yet.
- Debris/residue entities remain outside the accepted W13 lifecycle surface.

## Eighth Dispatch Wave 2026-06-08

Status: dispatched to current-session subagents on 2026-06-08. No new
conversation threads were created.

This wave turns the W16 fire scout into one bounded writer and starts a
separate read-only decision on whether A8 needs first-class debris/residue
objects before final acceptance. The two packets have disjoint write scopes:
W17 may write tests and, only if blocked, narrow maintained fire-path code;
W18 is read-only.

| Packet | Cluster | Owner | Model / reasoning | Write set | Goal | Non-goals | Validation | Return packet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A8-W17 Broader Fire Consequence Writer` | `A8-DEC-E/F` | McClintock | inherited / high | Prefer tests under `tests/runtime/air_combat/weapon_guidance_realism/` plus collector import. Production edits only if existing maintained fire fields are proven unreachable and the blocker is named first. | Add the smallest deterministic MQ-9/AIM-120C-like fixed-hit checks for broader fire behavior: left-wing fuel-cell fire growth and secondary damage through the runtime path; rear-engine fire-zone seeding plus propulsion consequence without falsely requiring fire growth when there is no flammable exposure. Use W16 evidence as the starting point. | No ground-impact/lifecycle edits, no direct crash/disappearance rule, no MQ-9 special kill rule, no real-world lethality or probability claim, no broad fire model rewrite, no assertion that engine-only fire zones must grow without fuel/flame exposure. | `git diff --check` on touched files; focused pytest selector; `python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`; `./.venv/bin/python -m ruff check` for touched Python; `cmake --build build-workshop --target ef_py -j2` only if production/binding files change. | Required worker packet with status, touched files, commands/outcomes, remaining paths, behavior risks, integration notes. |
| `A8-W18 Debris/Residue Lifecycle Decision Scout` | `A8-DEC-H/G` | Harvey | inherited / high | Read-only. | Decide the smallest next A8 decision path for post-crash debris/residue after W13. Inspect landed-airframe/crashed-wreck state, entity active/inactive behavior, loss/destruction surfaces, engagement reports, runtime observation APIs, and object/entity lifecycle mechanisms. Return whether A8 should accept the current original-entity lifecycle state for this slice and defer debris/residue objects, or require a narrow next writer that exposes debris/residue as a separate object/state. | No code edits, no docs edits, no direct touch-kill, no direct disappearance, no independent can-fly verdict, no real-world lethality claim, no broad object-system rewrite. | File/line evidence and proposed acceptance wording or exact writer packet. | Required scout packet with touched files `none`, commands/outcomes, file/line evidence, recommended next step, behavior risks, integration notes. |

Eighth-wave integration rules:

- `A8-W17` is the only writer in this wave.
- `A8-W18` is read-only and must not patch files.
- W17 owns fire consequence tests only; if it needs production edits, it must
  prove the maintained fire path is unreachable first.
- W18 must not decide final A8 acceptance by itself; it returns evidence and a
  recommended accept/defer or writer path for main-thread review.
- The main thread owns final review, verification, status synchronization, and
  any commit.

## Eighth Dispatch Acceptance 2026-06-08

| Packet | State | Notes |
| --- | --- | --- |
| `A8-W17 Broader Fire Consequence Writer` | pass | Added fixed MQ-9/AIM-120C-like fire-consequence checks. A left-wing fuel-cell hit now proves fire growth, fuel loss, and secondary flight/avionics/crew damage through maintained runtime state. A rear-engine hit proves engine fire-zone seeding plus propulsion consequence without falsely requiring fire growth when there is no flammable exposure. |
| `A8-W18 Debris/Residue Lifecycle Decision Scout` | pass | Accepted as read-only evidence. For this A8 slice, the current original-entity `landed_airframe` / `crashed_wreck` lifecycle is sufficient post-impact observability; first-class debris/residue objects are explicitly deferred. |
| `A8-DEC-E/F Consumer And Validation Coverage` | partial pass | Propulsion, wing/control aero, fuel-leak/mass, data-link mission/sensor consequence, and broader fire consequence checks are now in place. |
| `A8-DEC-H Ground-Impact Lifecycle` | partial pass | Landed-airframe/crashed-wreck observability is accepted for this slice; debris/residue entity creation remains deferred rather than an A8 blocker. |

Accepted validation:

```bash
git diff --check -- tests/runtime/air_combat/weapon_guidance_realism/a8_fire_consequence.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_fire_consequence.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'left_wing_fuel_hit_grows_fire or rear_engine_hit_seeds_engine_fire_zone'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

Outcomes: test diff whitespace check pass, focused Python lint pass, broader
fire consequence checks `2 passed, 174 deselected`, and weapon guidance realism
guards `176 passed`.

Current residuals after eighth-wave acceptance:

- Broader fire behavior is now covered by deterministic fixed MQ-9/AIM-120C-like
  tests, but it remains engineering evidence rather than calibrated fire truth.
- Debris/residue entities are deferred; the accepted A8 lifecycle surface is
  original-entity observability via `landed_airframe` and `crashed_wreck`.
- The remaining A8 decision is whether the current maintained-consumer set is
  sufficient for final `P6` acceptance with calibration and object-model work
  explicitly deferred.

## Ninth Dispatch Wave 2026-06-08

Status: dispatched to current-session subagents on 2026-06-08. No new
conversation threads were created.

This wave is a `P6` readiness wave. It does not add new behavior. It asks one
agent to audit whether the accepted slices satisfy A8's stated acceptance gate,
and another agent to run the final validation/readiness checks. The main thread
keeps all acceptance wording, parent-index synchronization, archive decisions,
and commits serial.

| Packet | Cluster | Owner | Model / reasoning | Write set | Goal | Non-goals | Validation | Return packet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A8-W19 P6 Acceptance Readiness Audit` | `A8-DEC-G` | Harvey | inherited / high | Read-only. | Compare A8 README acceptance gates, current status, task clusters, and dispatch history against the actual landed tests and implementation evidence. Return whether A8 should be marked accepted now, marked held, or accepted with explicitly deferred calibration/object-model residuals. Identify any blocker that must be fixed before final acceptance. | No code edits, no docs edits, no new physics claim, no real-world lethality/Pk/fuze authority claim, no direct crash rule, no demand for first-class debris unless it is a true blocker in the stated A8 gate. | File/line evidence; optional read-only command results. | Required scout packet with status, touched files `none`, acceptance recommendation, blocker list, residual wording, behavior risks, integration notes. |
| `A8-W20 P6 Final Validation Runner` | `A8-DEC-G` | McClintock | inherited / high | Read-only; do not edit files. | Run the smallest final validation set needed before main-thread P6 acceptance sync. At minimum include A8 docs/tests diff check, Python lint for A8 test modules touched in recent waves, full weapon-guidance realism guards, and any focused command you believe is needed to catch regressions from W13-W18. Report exact commands and outcomes. | No code edits, no docs edits, no acceptance wording edits, no new tests, no broad unrelated suite expansion unless a focused failure suggests it. | Exact command outcomes. | Required validation packet with status, touched files `none`, commands/outcomes, failures or flakes, residual risks, integration notes. |

Ninth-wave integration rules:

- Both packets are read-only.
- Neither packet may mark A8 accepted on its own; they return evidence for
  main-thread P6 review.
- If W19 finds an acceptance blocker, it must name the exact gate and evidence
  gap rather than proposing a broad new model.
- If W20 finds a failing gate, it should stop at the smallest useful failure
  report instead of editing files.
- The main thread owns final P6 wording, parent README/status sync, archive
  decisions, validation reconciliation, and any commit.
