# Naval Warfare Follow-up Delegation Execution Sheet

Status: `2026-05-17` Execution Preparation Version.

Related documents:

- [Naval Warfare Realism Analysis](../flight_dynamics/naval/naval_realism_analysis_20260516.zh.md)
- [Naval Warfare Realism Hierarchical Checklist and Next Steps for Current Scenario](./naval_realism_layering_and_next_step_plan_20260516.md)

Document positioning:

- This document converts completed verification conclusions into executable tasks that can be directly delegated to subagents / workers.
- This document does not re-argue "whether a problem exists", only answers "what to do next, who does it, and what to verify".
- This document defaults to continuing the current minimal naval warfare MVP mindset, not jumping directly into full fleet-level high-fidelity naval warfare.

## I. Current Recommendations

Next steps are not recommended to be done by me personally on a large-scale main track, but directly to distribute tasks by domain using existing subagents.

Recommended execution order:

1. First open three parallel lines for `P0/P1`:
   - `Maritime Situational Awareness MVP`
   - `Ship Motion / Sea State MVP`
   - `Red Force Replacement + Data Link / C2 Convergence`
2. Second wave:
   - `Shipboard Weapon Chain MVP`
   - `Warship Damage State Machine MVP`
3. Third wave:
   - `Sonar / ASW MVP`
   - `Shipboard Aircraft Coordination MVP`
   - `UNREP / Logistics MVP`

Reason:

- The first wave can all be incrementally advanced on the existing structure, with relatively separable file sets.
- The second wave depends on the first wave for more credible targets, situational awareness, and mission chains.
- The third wave has high value but involves more new systems and cross-module coupling; it is safer to place after the first two waves.

## II. Delegation Mapping

### 2.1 Wegener

Responsible for: `Ship Motion / Sea State`

Suggested tasks:

1. `N-MOTION-01` Low-speed rudder effectiveness & no rudder speed threshold completion
2. `N-MOTION-02` Minimum sea state input entry
3. `N-MOTION-03` Wave attitude proxy
4. `N-MOTION-04` Wave-added resistance minimal coupling

Primary files:

- [src/systems/naval/ship_motion_system.h](../../../src/systems/naval/ship_motion_system.h)
- [src/components/naval/ship_platform.h](../../../src/components/naval/ship_platform.h)
- [src/content/unit_definition_loader.cpp](../../../src/content/unit_definition_loader.cpp)
- [examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json](../../../examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json)
- [examples/config/database/ships/units/take1_usns_lewis_and_clark.json](../../../examples/config/database/ships/units/take1_usns_lewis_and_clark.json)
- [tests/runtime/naval/test_naval_ship_database.py](../../../tests/runtime/naval/test_naval_ship_database.py)

Acceptance criteria:

- Near-zero speed, a pure heading change command should not cause significant turning.
- Behavior at `sea_state=0` should be identical to current behavior.
- At `sea_state > 0`, `roll/pitch` should no longer be permanently zero and should be bounded.
- Steady-state speed in high sea states should be lower than in calm water.

### 2.2 Hilbert

Responsible for: `Shipboard Radar / ESM, Sonar / ASW, Shipboard Aircraft Coordination`

Suggested tasks:

1. `N-SENS-01` Multi-sensor mounting
2. `N-SENS-02` Maritime radar specialization fields and detection loss
3. `N-SENS-03` Shipboard ESM MVP
4. `N-ASW-01` `Submarine + Sonar` base type and loading
5. `N-ASW-02` Underwater acoustics MVP runtime
6. `N-HELO-01` Shipboard aircraft coordination token MVP

Primary files:

- [src/content/unit_definition.h](../../../src/content/unit_definition.h)
- [src/content/unit_definition_loader.cpp](../../../src/content/unit_definition_loader.cpp)
- [src/models/core/default_unit_factory.h](../../../src/models/core/default_unit_factory.h)
- [src/components/systems/sensor.h](../../../src/components/systems/sensor.h)
- [src/models/systems/default_sensor_model.cpp](../../../src/models/systems/default_sensor_model.cpp)
- [src/components/systems/ew.h](../../../src/components/systems/ew.h)
- [src/core/engine/simulation_kernel_observation_api.cpp](../../../src/core/engine/simulation_kernel_observation_api.cpp)
- New suggestions:
  - [src/components/systems/sonar.h](../../../src/components/systems/sonar.h)
  - [src/core/interfaces/acoustic_model.h](../../../src/core/interfaces/acoustic_model.h)
  - [src/models/systems/default_acoustic_model.cpp](../../../src/models/systems/default_acoustic_model.cpp)
  - [src/systems/systems/sonar_system.h](../../../src/systems/systems/sonar_system.h)
  - [src/components/naval/embarked_air_ops.h](../../../src/components/naval/embarked_air_ops.h)

Acceptance criteria:

- DDG can simultaneously mount multiple sensors and passive reconnaissance components.
- Sea state / horizon / optional ducting can change surface radar detection results.
- Enemy emitters can trigger bearing-only ESM alerts.
- Submarine and sonar JSON can be loaded; acoustic contacts can enter observation.
- `LaunchHelo / RecoverHelo / RelayOTHTargeting` have at least token-level closure.

### 2.3 Galileo

Responsible for: `Shipboard Weapon Chain, Warship Damage`

Suggested tasks:

1. `N-WEAPON-01` Shipboard weapon runtime structure persistence
2. `N-WEAPON-02` `VLS-SAM` minimum launch chain
3. `N-WEAPON-03` Main gun & `CIWS` simplified engagement
4. `N-DAMAGE-01` Warship damage state machine
5. `N-DAMAGE-02` Persistent damage propagation

Primary files:

- [src/components/combat/weapon.h](../../../src/components/combat/weapon.h)
- [src/content/unit_definition.h](../../../src/content/unit_definition.h)
- [src/content/unit_definition_loader.cpp](../../../src/content/unit_definition_loader.cpp)
- [src/models/core/default_unit_factory.h](../../../src/models/core/default_unit_factory.h)
- [src/core/engine/simulation_kernel_weapon_api.cpp](../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [src/components/combat/damage.h](../../../src/components/combat/damage.h)
- [src/components/combat/health.h](../../../src/components/combat/health.h)
- [src/models/weapons/default_effects_model.cpp](../../../src/models/weapons/default_effects_model.cpp)
- [src/systems/combat/damage_system.h](../../../src/systems/combat/damage_system.h)

Acceptance criteria:

- DDG's `VLS / gun / CIWS` can be loaded as structured data.
- `VLS-SAM` can only be fired when a track exists; magazine and cooldown are active.
- After a ship is hit, intermediate states such as `mission kill / mobility kill / sensor kill` can appear.
- Light damage does not immediately sink; heavy damage can transition to a loss state after persistent propagation.

### 2.4 Nietzsche

Responsible for: `Red Force Replacement, Screening / Formation Control, Data Link / C2, Logistics`

Suggested tasks:

1. `N-RED-01` Replace red force placeholder ships with a minimal enemy surface combatant template
2. `N-C2-01` Screening / formation minimum closed-loop stabilization
3. `N-C2-02` Data link de-flooding and task group level sharing
4. `N-LOG-01` UNREP / logistics abstract inventory version

Primary files:

- New suggestion: [examples/config/database/ships/units/red_surface_combatant_minimal.json](../../../examples/config/database/ships/units/red_surface_combatant_minimal.json)
- [scenarios/naval/ddg51_take1_screen_contact_report_v1.json](../../../scenarios/naval/ddg51_take1_screen_contact_report_v1.json)
- [scenarios/naval/ddg51_take1_screen_closing_contact_v1.json](../../../scenarios/naval/ddg51_take1_screen_closing_contact_v1.json)
- [gym_envs/scenario_loader/behavior_runtime/naval_screen.py](../../../gym_envs/scenario_loader/behavior_runtime/naval_screen.py)
- [gym_envs/scenario_loader/behavior_runtime/command_chain.py](../../../gym_envs/scenario_loader/behavior_runtime/command_chain.py)
- [src/systems/systems/data_link_system.h](../../../src/systems/systems/data_link_system.h)
- [src/systems/systems/track_manager_system.h](../../../src/systems/systems/track_manager_system.h)
- [src/components/command/common/comm_message.h](../../../src/components/command/common/comm_message.h)
- [src/components/systems/logistics.h](../../../src/components/systems/logistics.h)
- [src/systems/systems/logistics_system.h](../../../src/systems/systems/logistics_system.h)

Acceptance criteria:

- Red force no longer reuses `T-AKE-1`.
- `TASK_SCREEN` can stabilize and recover to target station after disturbance.
- Track sharing messages no longer flood every step.
- `T-AKE` and `DDG` have at least abstract inventory and replenishment window state machine.

## III. Recommended Parallel Waves

### 3.1 First Wave

Recommend to immediately start three parallel lines:

1. `Hilbert`: `N-SENS-01 / N-SENS-02 / N-SENS-03`
2. `Wegener`: `N-MOTION-01 / N-MOTION-02 / N-MOTION-03`
3. `Nietzsche`: `N-RED-01 / N-C2-02`

Reason:

- The file sets are largely separable.
- These three lines directly improve the most obvious gaps: "can see, moves like a ship, target is no longer a wrong ship type".

### 3.2 Second Wave

After the first wave is merged, start:

1. `Galileo`: `N-WEAPON-01 / N-WEAPON-02 / N-DAMAGE-01`
2. `Nietzsche`: `N-C2-01`

Reason:

- Weapon chain and damage chain need to be built on more credible targets, situational awareness, and station control.
- The screening closed-loop stabilization should use the new targets and shared semantics from the first wave to correct behavior.

### 3.3 Third Wave

After the second wave is stable, start:

1. `Hilbert`: `N-ASW-01 / N-ASW-02`
2. `Hilbert` or new worker: `N-HELO-01`
3. `Nietzsche`: `N-LOG-01`
4. `Galileo`: `N-WEAPON-03 / N-DAMAGE-02`

Reason:

- ASW, shipboard aircraft, and logistics all cross systems more deeply.
- At this point, the basic platform, targets, weapons, and message semantics are more stable, reducing rework risk.

## IV. Data Usage Guidelines

All subsequent tasks uniformly adopt the following annotation rules:

1. `Official / semi-official public facts`
   - Can be used for: ship types, equipment families, system purposes, task division, platform boundaries.
   - Example: DDG-51 equipment family, existence and purpose of `SQQ-89`/`SLQ-32`/`MH-60R`.

2. `Professional public materials`
   - Can be used for: sea clutter, waveguides, convergence zones, underwater acoustics propagation, wave-added resistance, fire control chain mechanisms.
