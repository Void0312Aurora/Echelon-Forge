# A8 Damage Effect Chain Current Status

Status: `2026-06-07` second implementation checkpoint. A8 has a bounded work
surface, current-session read-only structure findings are integrated, and the
first two worker waves have been accepted as limited runtime/test slices.

## What Changed

- Created A8 as the follow-on for concrete damage effects after the sealed A2
  research/candidate record.
- Fixed the initial boundary: A8 will not add direct crash rules, special MQ-9
  kill rules, or a separate "can fly" verdict.
- Split the work into finite clusters: structure evidence, shot effect record,
  part damage vocabulary, consumer integration, MQ-9/AIM-120C validation, and
  acceptance.
- Integrated current-session read-only explorer checks for three areas:
  fuze/effects code, damage-to-flight consumers, and MQ-9/AIM-120C validation
  fixtures.
- Added the first implementation dispatch queue:
  [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md).
- Accepted the first worker wave:
  - `A8-W1 Shot Record`: pass. It froze the linked
    `EffectsEvent -> DamageReport -> DiagnosticsTrace` record without adding
    new public fields.
  - `A8-W2 Part Failure Vocabulary`: partial. It maps mechanism loads into
    internal part-failure modes and routes those modes through existing
    aircraft-damage entries; public per-component mode fields remain held for
    integration.
  - `A8-W3 Validation Fixtures`: partial pass. It adds fixed MQ-9/AIM-120C
    checks and non-authority guards, while leaving later flight-consumer checks
    for `A8-DEC-E`.
- Accepted the second worker wave:
  - `A8-W4 Public Failure Mode Rows`: pass. It exposes concrete simulated
    failure modes on public component shot rows and Python bindings while
    keeping `component_failure_mode_authority=false`.
  - `A8-W5 Propulsion Fuel Mass Consumer Scout`: pass as read-only evidence. It
    identifies the narrow propulsion/fuel/mass consumer path and the engine
    tuning bypass risk.
  - `A8-W6 Aero Control Consumer Scout`: pass as read-only evidence. It
    identifies the narrow control/aero response path and confirms that actual
    force/moment behavior still needs `A8-DEC-E` implementation.

## Acceptance Check 2026-06-07

Commands run:

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain src/components/combat/damage.h src/content/unit_definition_loader.cpp src/models/weapons/detail/default_effects_component_damage_detail.inc src/models/weapons/detail/default_effects_system_effect_detail.inc tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py tests/runtime/air_combat/weapon_guidance_realism
cmake --build build-workshop -j 8
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

Outcomes:

- Diff whitespace check: pass.
- Build: pass.
- Weapon guidance realism guards: `164 passed, 1 skipped`.
- 1v1 fire missile tests: `11 passed`.
- The skipped guard is intentional: it waits for public shot-effect record
  fields and public concrete damage-mode vocabulary.

## Second Acceptance Check 2026-06-07

Commands run:

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain src/runtime/contracts/engagement_contracts.h src/interfaces/python/bindings_runtime.cpp src/models/weapons/detail/default_effects_component_damage_detail.inc src/models/weapons/detail/default_effects_system_effect_detail.inc tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py tests/runtime/air_combat/weapon_guidance_realism/component_damage.py
cmake --build build-workshop -j 8
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
python -m pytest -q tests/runtime/engagement/test_engagement_contract_shape.py
```

Outcomes:

- Diff whitespace check: pass.
- Build: pass.
- Weapon guidance realism guards: `165 passed`.
- 1v1 fire missile tests: `11 passed`.
- Engagement contract shape tests: `4 passed`.

## Maturity Matrix

| Area | Accepted | Active | Held | Deferred |
| --- | --- | --- | --- | --- |
| Fuze and detonation event path | Proximity-fuze disappearance was recently repaired and guarded by runtime tests. | A8 must use the recorded event as the first stage of the chain. | Deterministic fuze truth is not accepted. | Real fuze calibration. |
| Structured parts and aircraft damage state | Named hitboxes, components, groups, aircraft state fields, and public component failure-mode rows exist. | A8 must keep the explanation non-authoritative and tied to shot rows. | Current integrity/capability numbers are still not enough by themselves. | Broad target-family data calibration. |
| Warhead action to part damage | Default effects code estimates fragment/blast/rod-like loads and now exposes simulated part-failure modes. | A8 must keep the synthetic vocabulary auditable through tests. | Current values are not AIM-120C truth. | Release-grade warhead modeling. |
| Part damage to aircraft behavior | Propulsion, fuel, sensor, and broad flight limits consume some damage state; W5/W6 identified the next narrow hooks. | A8 must implement maintained consumers in `A8-DEC-E`. | Aerodynamic/control consequences are still too indirect in forces and moments. | Full aircraft-specific flight-control law calibration. |
| MQ-9 / AIM-120C validation | Test fixtures and configs exist. | A8 should make fixed rear, wing/control, fuel/fire, and sensor/data-link cases. | A live smoke result is not enough for acceptance. | Probability of kill or real-world lethality claims. |

## Read-Only Findings Integrated

Fuze and effects structure:

- The current detonation path already records fuze geometry and then calls the
  effects model. The best first implementation cut is inside the default effects
  path, where direct hit or proximity projection has selected a hit box or part
  and mechanism loads are available.
- The immediate code area is the mechanism-load to component result layer:
  `sample_default_effects_component_failure`, `apply_component_damage_state`,
  and `apply_component_failure_impulse` should grow a concrete part-failure
  result before the chain widens into physics consumers.
- Current effects already estimate fragment energy, fragment density,
  penetration margin, blast pressure/impulse, and rod-cut margin. The gap is not
  "no mechanism input"; the gap is that those values mostly collapse into a
  failure probability and integrity number.

Damage-to-flight structure:

- The current bridge is not a single flight verdict. Damage flows into
  `AircraftDamageState`, then into `FlightModel`, `Propulsion`, `Mass`,
  `Sensor`, and `PlatformDamageState` each frame.
- Propulsion is the strongest existing consumer, because degraded propulsion can
  reduce thrust and then forces. There is a potential tuning-bypass risk when an
  active engine tuning overrides damaged propulsion values.
- Aerodynamics and the default control model are the main weak points. They do
  not yet fully consume damaged structure, damaged control surfaces, left/right
  asymmetry, or reduced axis authority as forces and moments.
- Existing `flight_control_kill`, `propulsion_kill`, and forced-landing fields
  should stay report/status outputs, not become a new shortcut around flight
  simulation.

MQ-9 / AIM-120C validation structure:

- The preferred validation pair is F-16C launching AIM-120C-7 against MQ-9 as an
  unarmed structured target. MQ-9 has useful engine, propeller, fuel, data-link,
  avionics, aileron/flap, and wing-spar parts, but its vulnerability profile is
  synthetic and non-authoritative.
- Existing tests cover the launch chain and many effect details separately, but
  there is no single fixed live AIM-120C-to-MQ-9 test that verifies launch,
  effects, component damage, downstream response, and outcome together.
- Fixed validation cases should include: near-range full chain, longer-range
  auditable chain, right aileron/flap control damage, data-link or power
  distribution mission damage, and an explicit non-authority check.

## Initial Chain Design

```text
1. Fuze result and detonation geometry
2. Warhead action at the detonation point
3. Aircraft part exposure
4. Concrete part damage type
5. Functional change
6. Existing aircraft systems consume that change
7. Later aircraft behavior is observed
```

Plain expected examples:

- Rear hit: engine, fuel-control, or propeller damage reduces thrust through
  propulsion and may add fire or fuel risk.
- Wing/control hit: spar, aileron, flap, or actuator damage changes control
  authority, asymmetry, drag, lift, or structural margin through the flight path.
- Fuel hit: storage damage leaks fuel, changes mass, increases fire risk, or
  disrupts supply if the feed path is damaged.
- Nose or fuselage electronics hit: sensor, avionics, or data-link damage can
  make the aircraft unable to complete its mission without requiring a crash.

## Evidence Links

- Fuze and combat damage update:
  [damage_system.h](../../../../src/systems/combat/damage_system.h)
- Damage component/state definitions:
  [damage.h](../../../../src/components/combat/damage.h)
- Default weapon effects:
  [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)
- Aerodynamic consumer:
  [aerodynamics_system.h](../../../../src/systems/physics/aerodynamics_system.h)
- Propulsion consumer:
  [propulsion_system.h](../../../../src/systems/physics/propulsion_system.h)
- MQ-9 structured damage config:
  [mq9_reaper.json](../../../../examples/config/database/aircraft/units/mq9_reaper.json)
- AIM-120C weapon config:
  [aim_120c.json](../../../../examples/config/database/weapons/air_to_air/aim_120c.json)
- Current regression entry:
  [test_weapon_guidance_realism_guards.py](../../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py)

## Residual Register

Immediate:

- Implement `A8-DEC-E` as maintained consumer work, not as a direct kill rule:
  propulsion tuning cap, fuel/mass leak behavior, and one wing/control
  aerodynamic or control response.
- Re-run fixed MQ-9/AIM-120C cases after consumer integration changes, because
  the current fixtures prove auditable damage and non-authority, not final
  flight-response fidelity.

Held:

- Direct crash or direct disappearance behavior for a structured aircraft.
- Special handling that makes MQ-9 easier to kill only because it is MQ-9.
- Any "can fly" verdict that bypasses existing flight and propulsion behavior.

Deferred:

- Calibrated fragment distribution, blast loads, and target vulnerability.
- Real-world probability of kill.
- Deterministic fuze truth.
- Full multi-platform aircraft damage datasets.

## Next Recommended Order

1. Connect the first narrow propulsion/fuel/mass consumer slice.
2. Connect one
   wing/control aerodynamic effect.
3. Run MQ-9/AIM-120C fixed validations and decide accepted or held.

## Forbidden Conclusions

- These are accepted slices, not full A8 completion.
- A8 does not prove real AIM-120C lethality.
- A8 does not release probability of kill or deterministic fuze authority.
- A8 does not replace the flight model with a direct kill rule.
