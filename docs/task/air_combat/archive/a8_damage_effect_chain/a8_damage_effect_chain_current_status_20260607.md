# A8 Damage Effect Chain Current Status

Status: `2026-06-08` accepted with deferred residuals. A8 has a bounded work
surface, current-session structure findings are integrated, and the accepted
slice covers limited propulsion, wing/control aerodynamic, fixed fuel-leak/mass
consumer evidence, fixed broader-fire consequence evidence, fixed data-link
mission/sensor consequence evidence, and a narrow ground-contact lifecycle
surface.

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
- Accepted the first `A8-DEC-E` implementation slice:
  - `A8-W7 Propulsion Tuning Consumer`: pass. It makes explicit engine tuning
    consume `AircraftDamageState.propulsion_integrity` before runtime thrust is
    computed, closing the tuning-bypass risk without adding a direct kill rule.
    Evidence note:
    [a8_w7_propulsion_tuning_consumer_20260608.md](a8_w7_propulsion_tuning_consumer_20260608.md).
- Accepted the second `A8-DEC-E` implementation slice:
  - `A8-W8 Wing/Control Aero Consumer`: pass. It makes structural, hydraulic,
    roll/pitch/yaw control, and control-asymmetry damage affect maintained
    aerodynamic coefficients and moments, without adding a direct crash or
    independent flight verdict. Main-thread validation also added a fixed
    MQ-9/AIM-120C right-aileron response check following `A8-W9` scout
    guidance. Evidence note:
    [a8_w8_aero_consumer_20260608.md](a8_w8_aero_consumer_20260608.md).
- Accepted the fifth-wave work:
  - `A8-W11 Fuel/Fire/Mass Consumer Evidence`: pass. It adds a fixed
    center-fuel-cell MQ-9/AIM-120C-like hit that records fuel-leak and
    fire-source modes, keeps the immediate damage report non-authoritative, and
    then proves fuel and mass drain through maintained runtime systems.
  - `A8-W12 Ground-Impact Lifecycle Scout`: partial, accepted as read-only
    evidence only. It confirms the current ground-contact path can detect
    ground contact, but the observable crash/wreck/debris lifecycle is not yet
    a maintained public surface and must not be replaced by direct deletion.
- Accepted the first `A8-DEC-H` implementation slice:
  - `A8-W13 Ground-Impact Lifecycle Writer`: pass. Existing subagent return
    did not provide a usable new packet, so the main thread implemented the
    narrow writer slice. Ground contact now exposes a public debug state that
    distinguishes no contact, landed airframe, and crashed wreck. Severe impact
    no longer relies on `Health.current_hp = 0.0` as the only visible result,
    and tests keep safe/low-speed contact out of the crashed-wreck state.
  - `A8-W14 Sensor/Data-Link/Fire Consequence Scout`: no accepted sixth-wave
    scout packet was integrated; the seventh-wave W15/W16 packets below replace
    that open sensor/data-link and fire-consequence gap.
- Accepted the seventh-wave work:
  - `A8-W15 Sensor/Data-Link Consequence Writer`: pass. It adds a fixed
    MQ-9/AIM-120C-like data-link transceiver hit that records `data_loss`,
    keeps the immediate damage report non-authoritative, and then proves later
    mission/sensor/survivability plus avionics/crew/navigation degradation
    through maintained platform state.
  - `A8-W16 Broader Fire Consequence Scout`: pass as read-only evidence. It
    identifies the next tests-only writer path for left-wing fuel-cell fire
    growth and rear-engine fire-zone seeding, while warning that an engine-only
    fire zone should not be asserted to grow without flammable exposure.
- Accepted the eighth-wave work:
  - `A8-W17 Broader Fire Consequence Writer`: pass. It adds fixed
    MQ-9/AIM-120C-like checks for left-wing fuel-cell fire growth plus
    secondary damage, and rear-engine fire-zone seeding plus propulsion
    consequence. It makes no production edits and does not require engine-only
    fire growth without flammable exposure.
  - `A8-W18 Debris/Residue Lifecycle Decision Scout`: pass as read-only
    evidence. For this A8 slice, original-entity `landed_airframe` /
    `crashed_wreck` lifecycle observability is sufficient; first-class
    debris/residue objects are deferred rather than an A8 blocker.
- Accepted the ninth-wave P6 readiness work:
  - `A8-W19 P6 Acceptance Readiness Audit`: pass as read-only evidence. It
    found no blocker against the stated A8 acceptance gate and recommended
    accepting the bounded slice with explicit deferred residuals.
  - `A8-W20 P6 Final Validation Runner`: pass as read-only validation. A8
    docs/test diff hygiene, Python lint, the full weapon-guidance realism guard
    collector, and a focused W13-W18 selector all passed.
- Main-thread P6 decision: A8 is accepted for the bounded damage-effect-chain
  slice. Deferred residuals remain calibration-grade warhead/fire/target truth,
  aircraft-specific control-law fidelity, platform-family expansion, real-world
  Pk/fuze/stock lethality authority, and first-class debris/residue objects.

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

## Third Acceptance Check 2026-06-08

Commands run:

```bash
git diff --check -- src/systems/physics/propulsion_system.h tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py docs/task/air_combat/a8_damage_effect_chain
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_a8_engine_damage_scales_actual_thrust_with_explicit_engine_tuning
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_tuning_runtime.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_realism_guards.py
```

Outcomes:

- Diff whitespace check: pass.
- Build: pass.
- Focused A8 tuned-engine propulsion consumer test: `1 passed`.
- Weapon guidance realism guards: `166 passed, 239 subtests passed`.
- Flight dynamics tuning runtime: `3 passed`.
- 1v1 fire-missile tests: `11 passed, 2 subtests passed`.
- Flight dynamics realism guards: `4 passed`.

## Fourth Acceptance Check 2026-06-08

Commands run:

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

Outcomes:

- Changed C++ file clang-format gate: pass.
- Focused Python lint: pass.
- Build: pass.
- Focused W8 aero/MQ-9 short response checks: `2 passed, 166 deselected`.
- Focused W8 long-run MQ-9 response checks: `2 passed, 167 deselected`.
- Weapon guidance realism guards: `169 passed`.
- Flight dynamics realism guards: `4 passed`.
- Flight dynamics tuning runtime: `3 passed`.
- 1v1 fire-missile tests: `11 passed`.

## Fifth Acceptance Check 2026-06-08

Commands run:

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain/a8_damage_effect_chain_dispatch_queue_20260607.md tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'center_fuel_hit_continues_into_leak_and_mass_runtime_path'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

Outcomes:

- Diff whitespace check: pass.
- Focused Python lint: pass.
- Fixed center-fuel-cell leak/mass runtime check: `1 passed, 169 deselected`.
- Weapon guidance realism guards: `170 passed`.
- `A8-W12` was read-only and made no file changes; its acceptance is evidence
  for the next writer packet, not implementation acceptance.

## Sixth Acceptance Check 2026-06-08

Commands run:

```bash
git diff --check -- src/components/systems/logistics.h src/systems/physics/ground_contact_system.h src/core/engine/simulation_kernel.h src/core/engine/simulation_kernel_observation_api.cpp src/interfaces/python/bindings_core.cpp tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'ground_contact_lifecycle'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

Outcomes:

- Diff whitespace check: pass.
- Focused Python lint: pass.
- `ef_py` build: pass.
- Ground-contact lifecycle focused checks: `3 passed, 170 deselected`.
- Weapon guidance realism guards: `173 passed`.

## Seventh Acceptance Check 2026-06-08

Commands run:

```bash
git diff --check -- docs/task/air_combat tests/runtime/air_combat/weapon_guidance_realism/a8_sensor_datalink_consumer.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_sensor_datalink_consumer.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'data_link_hit_continues_into_platform_mission_sensor_runtime_path'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

Outcomes:

- Docs/tests diff whitespace check: pass.
- Focused Python lint: pass.
- Data-link mission/sensor consequence check: `1 passed, 173 deselected`.
- Weapon guidance realism guards: `174 passed`.

## Eighth Acceptance Check 2026-06-08

Commands run:

```bash
git diff --check -- tests/runtime/air_combat/weapon_guidance_realism/a8_fire_consequence.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_fire_consequence.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'left_wing_fuel_hit_grows_fire or rear_engine_hit_seeds_engine_fire_zone'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

Outcomes:

- Test diff whitespace check: pass.
- Focused Python lint: pass.
- Broader fire consequence checks: `2 passed, 174 deselected`.
- Weapon guidance realism guards: `176 passed`.

## Ninth P6 Acceptance Check 2026-06-08

Commands run:

```bash
git diff --check -- docs/task/air_combat tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py tests/runtime/air_combat/weapon_guidance_realism/a8_aero_consumer.py tests/runtime/air_combat/weapon_guidance_realism/a8_sensor_datalink_consumer.py tests/runtime/air_combat/weapon_guidance_realism/a8_fire_consequence.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py tests/runtime/air_combat/weapon_guidance_realism/a8_aero_consumer.py tests/runtime/air_combat/weapon_guidance_realism/a8_sensor_datalink_consumer.py tests/runtime/air_combat/weapon_guidance_realism/a8_fire_consequence.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'ground_contact_lifecycle or engine_damage_scales_actual_thrust or data_link_hit_continues or left_wing_fuel_hit_grows_fire or rear_engine_hit_seeds_engine_fire_zone or right_aileron_damage_long_run_reaches_ground_response'
```

Outcomes:

- A8 docs/tests diff whitespace check: pass.
- A8 Python lint: pass.
- Weapon guidance realism guards: `176 passed`.
- Focused W13-W18 regression selector: `8 passed, 168 deselected`.

## Maturity Matrix

| Area | Accepted | Active | Held | Deferred |
| --- | --- | --- | --- | --- |
| Fuze and detonation event path | Proximity-fuze disappearance was recently repaired and guarded by runtime tests. | A8 must use the recorded event as the first stage of the chain. | Deterministic fuze truth is not accepted. | Real fuze calibration. |
| Structured parts and aircraft damage state | Named hitboxes, components, groups, aircraft state fields, and public component failure-mode rows exist. | A8 must keep the explanation non-authoritative and tied to shot rows. | Current integrity/capability numbers are still not enough by themselves. | Broad target-family data calibration. |
| Warhead action to part damage | Default effects code estimates fragment/blast/rod-like loads and now exposes simulated part-failure modes. | A8 must keep the synthetic vocabulary auditable through tests. | Current values are not AIM-120C truth. | Release-grade warhead modeling. |
| Part damage to aircraft behavior | Propulsion damage reaches runtime thrust even when explicit engine tuning is active; wing/control damage now reaches limited aerodynamic coefficients, moments, and axis authority; fixed fuel-cell damage reaches leak/mass runtime response; fixed fire cases reach fire growth, secondary damage, fire-zone seeding, and propulsion consequence; fixed data-link damage reaches mission/sensor runtime response. | Accepted for the bounded A8 slice. | Current aero response is synthetic and scalar; fire checks are deterministic engineering evidence, not calibrated fire truth; the data-link case proves platform-state consequences, not active message traffic; left/right sign fidelity and aircraft-specific control laws are not accepted. | Full aircraft-specific flight-control law calibration and release-grade fire lifecycle calibration. |
| Ground-contact lifecycle | Safe contact and severe contact now have a public debug lifecycle state; severe constructed impact can be observed as `crashed_wreck` while the entity remains active. | A8 accepts original-entity observability for this slice. | The lifecycle does not make weapon hits crash sooner and does not generate physical fragments. | Full wreck/residue object model. |
| MQ-9 / AIM-120C validation | Test fixtures, fixed component cases, non-authority checks, a fixed right-aileron aero-response check, a 300 s right-aileron long-run check, a fixed center-fuel-cell leak/mass check, fixed broader-fire checks, a fixed data-link mission/sensor consequence check, and ground-contact lifecycle checks exist. | Accepted for fixed MQ-9/AIM-120C-like engineering checks. | A live smoke result is not enough for acceptance; fuel/fire/data-link consequences or crashed-wreck lifecycle tests are not real-world kill proof. | Probability of kill or real-world lethality claims. |

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
  reduce thrust and then forces. `A8-W7` closes the narrow tuning-bypass risk:
  explicit engine tuning now receives the same propulsion-damage scale before
  runtime thrust is computed.
- Aerodynamics now consumes a limited set of damaged structure, damaged control
  path, and asymmetry fields as lift/drag scaling and roll/pitch/yaw moments.
  This is an engineering response path, not calibrated aircraft-specific
  control law behavior.
- Existing `flight_control_kill`, `propulsion_kill`, and forced-landing fields
  should stay report/status outputs, not become a new shortcut around flight
  simulation.
- The current ground-contact system records terrain height and contact state.
  `A8-W13` changed the off-runway/severe-impact path so gear collapse and severe
  impact publish a ground-contact lifecycle state instead of making `Health=0`
  the only observable path.
- There is not yet a public airframe lifecycle or residue object type for
  debris fragments. Reusing weapon damage reports for ground impact would blur
  "weapon effect" and "later crash" into one event.

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
  propulsion and can seed engine fire-zone state without requiring fire growth
  when no flammable exposure exists.
- Wing/control hit: spar, aileron, flap, or actuator damage changes control
  authority, asymmetry, drag, lift, or structural margin through the flight path.
- Fuel hit: storage damage leaks fuel, changes mass, marks a fire source, and
  can grow fire plus secondary damage through the maintained runtime path.
- Nose or fuselage electronics hit: sensor, avionics, or data-link damage can
  make the aircraft less able to complete its mission without requiring a
  crash. The fixed W15 case now proves this through platform mission/sensor
  state, not through active message traffic.

## Evidence Links

- Fuze and combat damage update:
  [damage_system.h](../../../../../src/systems/combat/damage_system.h)
- Damage component/state definitions:
  [damage.h](../../../../../src/components/combat/damage.h)
- Default weapon effects:
  [default_effects_model.cpp](../../../../../src/models/weapons/default_effects_model.cpp)
- Aerodynamic consumer:
  [aerodynamics_system.h](../../../../../src/systems/physics/aerodynamics_system.h)
- Propulsion consumer:
  [propulsion_system.h](../../../../../src/systems/physics/propulsion_system.h)
- MQ-9 structured damage config:
  [mq9_reaper.json](../../../../../examples/config/database/aircraft/units/mq9_reaper.json)
- AIM-120C weapon config:
  [aim_120c.json](../../../../../examples/config/database/weapons/air_to_air/aim_120c.json)
- Current regression entry:
  [test_weapon_guidance_realism_guards.py](../../../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py)

## Residual Register

Immediate:

- A8 `P6` is accepted for the bounded damage-effect-chain slice:
  propulsion tuning, one wing/control aerodynamic response, one fixed
  fuel-leak/mass response, one fixed broader-fire response pair, one fixed
  data-link mission/sensor response, and original-entity ground-contact
  lifecycle observability are landed.
- Keep the new ground-contact lifecycle path narrow: it covers landed airframe
  and crashed wreck observability; debris fragments or a full wreck object
  model are deferred.

Held:

- Direct crash or direct disappearance behavior for a structured aircraft.
- Special handling that makes MQ-9 easier to kill only because it is MQ-9.
- Any "can fly" verdict that bypasses existing flight and propulsion behavior.
- Direct ground-contact kill logic that bypasses a maintained crash/impact path.

Deferred:

- Calibrated fragment distribution, blast loads, and target vulnerability.
- Real-world probability of kill.
- Deterministic fuze truth.
- Full multi-platform aircraft damage datasets.
- Aircraft-specific control-law fidelity and release-grade fire lifecycle
  calibration.
- First-class debris/residue object modeling.

## Follow-On Order

1. Keep A8 closed unless a new task explicitly reopens calibrated warhead/fire
   truth, platform-family expansion, or first-class residue objects.
2. Treat real-world lethality/Pk/fuze authority as a separate data-admission
   problem, not as an A8 acceptance follow-up.

## Forbidden Conclusions

- These are accepted slices, not full A8 completion.
- A8 does not prove real AIM-120C lethality.
- A8 does not release probability of kill or deterministic fuze authority.
- A8 does not replace the flight model with a direct kill rule.
