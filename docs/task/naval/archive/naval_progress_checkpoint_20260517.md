# Naval Warfare Development Checkpoint

Status: `2026-05-17` Third wave core completed, aligned with mainline review.

Update: `2026-05-18` workspace recheck note.
This addendum only updates the "current workspace spot-check" framing and does
not rewrite the main body of this `2026-05-17` checkpoint as a dated snapshot.

Related documents:

- [Naval Warfare Realism Analysis](../flight_dynamics/naval/naval_realism_analysis_20260516.zh.md)
- [Naval Warfare Realism Layered Checklist and Next Steps for Current Scenario](./naval_realism_layering_and_next_step_plan_20260516.md)
- [Naval Warfare Subsequent Task Execution Sheet](../naval_delegated_execution_backlog_20260517.md)

Purpose of this document:

- This document is used to collect the actual deliverables from completed subagent work.
- This document answers "what has been achieved, which risks remain, and what to assign next."
- This document defaults to the minimal naval warfare MVP path and does not overstate current progress as full-fidelity naval warfare.

## 1. Completed Items

### 1.1 Wegener: Ship Motion / Sea State

Completed:

1. `N-MOTION-01` Low-speed rudder effectiveness and no-rudder speed threshold
2. `N-MOTION-02` Minimum `sea_state` input entry
3. `N-MOTION-03` Wave attitude proxy
4. `N-MOTION-04` Minimum wave-added resistance coupling
5. Sea state environment-level elevation patch
6. Maritime state merge/fallback rule convergence

Current effect:

- At near-zero speed, pure heading change commands no longer cause significant turning.
- `sea_state=0` is compatible with legacy behavior.
- When `sea_state>0`, ship `roll/pitch` is no longer permanently zero.
- Under high sea states, steady-state speed is lower than calm sea.
- The scenario layer `environment.maritime` can now explicitly inject environment maritime state; when not configured, it clears the override and falls back to platform defaults.
- The current rules for maritime state are locked:
  - When `configured=false`, no environment override is provided, continuing with platform defaults.
  - When `configured=true`, it fully overwrites `sea_state / wave_heading_deg / wave_period_s`. Even `sea_state=0` is treated as an explicit calm override.
  - The current MVP does not support partial field merging.

Validation:

- `tests/runtime/naval/test_naval_ship_database.py`
- `tests/runtime/naval/test_naval_screen_scenario.py`
- `tests/scenario/test_scenario_compiler.py`
- Relevant results from receipts include:
  - `38 passed, 1 failed`
  - `5 passed, 17 deselected`
  - `3 passed, 17 deselected`

Residual risks:

- Maritime state rules are clear but remain "full coverage or no coverage"; fine-grained merge (e.g., only overwriting `wave_heading` or only `wave_period`) is not yet supported.
- `wave_heading / wave_period` have been locked through compilation/scenario injection and existing ship motion test cases, but there are no finer-grained runtime assertions for attitude phase/directionality.

### 1.2 Hilbert: Multi-Sensor / Maritime Radar / ESM / ASW / Shipborne Aircraft

Completed:

1. `N-SENS-01` Multi-sensor mounting
2. `N-SENS-02` Maritime radar specialization fields and ducting extension
3. `N-SENS-03` Shipborne ESM MVP
4. `N-ASW-01` `Submarine + Sonar` base type and loading
5. `N-ASW-02` Underwater acoustics MVP runtime
6. `N-HELO-01` Shipborne aircraft collaboration token MVP
7. Minimum sea surface LOS patching
8. Consistent consumption of maritime state in radar/sonar chain

Current effect:

- Ships are no longer limited by a single primary sensor assumption.
- Unit-level `esm` configuration can enter runtime `ESMReceiver`.
- Maritime radar can approximate the effects of horizon, sea state, and ducting on detection results via open mechanisms.
- Track management can retain `ESM / bearing-only` passive contact source markings.
- Submarines and sonar have minimum JSON loading and underwater contact closure.
- Shipborne helicopters can form a minimal token-level loop of `LaunchHelo / RecoverHelo / RelayOTHTargeting`.
- Surface units have a minimal sea surface LOS tolerance path when maritime state is configured, reducing false kills of near-sea-surface `z≈0` targets by general terrain checks.
- Both maritime radar and sonar prioritize consuming the global maritime state from `EnvironmentModel`, falling back to platform default sea state fields only when not configured.

Validation:

- `tests/runtime/naval/test_naval_ship_database.py`
- `tests/runtime/naval/test_naval_sensor_realism_runtime.py`
- `tests/runtime/naval/test_naval_asw_helo_runtime.py`
- `tests/runtime/bindings/test_bindings_command_surface.py`
- `tests/runtime/naval/test_naval_screen_scenario.py`
- Relevant results from receipts include:
  - `27 passed, 1 deselected`
  - `9 tests OK`

Residual risks:

- Sea surface LOS is still a minimal patch, not a full sea/terrain/refraction unified model.
- Current ESM remains an MVP, closer to passive bearing warning than a full electronic support and classification system.
- Acoustic model is still at the `engineering calibration / community-derived approximation` level, not high-fidelity sonar.
- `RecoverHelo` is currently a token-level "recover and return to ship," not a full flight deck operation.
- For stability, this round placed more consistency tests on raw detection / `snr_db` comparisons rather than strongly relying on "detection on/off" boundaries.

### 1.3 Nietzsche: Red Force Template / Data Link / C2 / Logistics Base

Completed:

1. `N-RED-01` Red force placeholder ship replacement
2. `N-C2-02` Data link de-flooding and task group-level convergence approximation
3. `N-C2-01` Small-scale screen-hold stabilization patch
4. `N-LOG-01` Minimum `UNREP` abstract inventory and closure

Current effect:

- Red force scenarios no longer use `T-AKE-1` as a stand-in for enemy surface combatants.
- Track sharing has converged from "full broadcast every step" to "confirmed/new-significant/refresh" triggers.
- `TASK_SCREEN` uses smoother capture and hold logic after approaching the target station, reducing terminal oscillation.
- `DDG-51` and `T-AKE-1` now have abstract inventory, replenishment window parameters, and minimal observation/debugging interfaces.
- `UNREP` can now complete the minimal chain: "approach window -> establish replenishment -> transfer abstract inventory -> complete/exit".
- The "active" observation semantics have been tightened to only count when inventory transfer actually begins, so being outside the window no longer misjudges as already replenishing.

Validation:

- `tests/runtime/naval/test_naval_screen_scenario.py`
- Directed test cases related to red force templates, abstract inventory, and replenishment windows in `tests/runtime/naval/test_naval_ship_database.py`
- Message semantics in naval contracts synchronized to `ReportTrack`
- Relevant results from receipts include:
  - `4 passed`
  - `10 passed, 2 failed`

Residual risks:

- Current data link is still an engineering approximation, not a full fleet C2 / Link management model.
- Current `UNREP` minimal closure is functional, but remains an abstract inventory state machine, not a full replenishment doctrine or detailed operational workflow.
- `screen-hold` is no longer retained as a stable red flag; current attention should be on maritime sensor/LOS and `sensor/naval` linkage closure.

### 1.4 Galileo: Shipborne Weapons / Damage

Completed:

1. `N-WEAPON-01` Shipborne weapon runtime structure landing
2. `N-WEAPON-02` `VLS-SAM` minimal launch chain
3. `N-DAMAGE-01` Ship damage intermediate states
4. `N-WEAPON-03` Main gun and `CIWS` simplified engagement modules
5. `N-DAMAGE-02` Continuous damage propagation
6. Minimum `MissionCommand` integration for the shipborne weapon chain

Current effect:

- `DDG-51`'s `VLS / gun / CIWS` can be structurally loaded.
- Ships can execute the minimal `VLS-SAM` launch chain based on existing tracks, reflecting inventory and cooldown.
- `5in gun / CIWS` have advanced from pure database items to runtime structural surfaces; under the `2026-05-18` workspace recheck, the main-gun direct-fire path and the `MissionCommand -> CIWS` minimal command path both pass their directed tests.
- Ships hit no longer only have "full health or sunk"; they can enter intermediate states like `mission kill / mobility kill / sensor kill`, with continuous capability degradation driven by fire, flooding, and breaches.
- The command-driven path `MissionCommand -> CIWS` has been integrated into the mainline code; the `2026-05-18` minimal directed regression is green, but this still should not be overstated as a complete automatic close-in-defense loop.

Validation:

- Directed test cases related to structured weapons, `VLS-SAM`, main gun, `CIWS`, intermediate damage states, and continuous damage propagation in `tests/runtime/naval/test_naval_ship_database.py`
- Current workspace spot-check results:
  - `tests/runtime/naval/test_naval_ship_database.py::NavalShipDatabaseTests::test_ddg_gun_can_fire_with_track_and_reduce_ammo`
  - `tests/runtime/naval/test_naval_ship_database.py::NavalShipDatabaseTests::test_naval_mission_command_can_trigger_ciws_without_direct_weapon_api`
  - `2026-05-17` receipt record: `2 failed`
  - `2026-05-18` workspace recheck: `2 passed in 0.10s`

Residual risks:

- `VLS-SAM` is still an abstract ship-to-air missile, not differentiated into finer types.
- `gun / CIWS` are currently engineering-approximate engagement modules, not full fire control/ballistics/field of fire/tracking channel simulations.
- The main-gun direct-fire and `MissionCommand -> CIWS` minimal command paths are now green, but they still lack broader stability coverage in more complex scenarios.
- Continuous damage propagation has formed a framework, but remains a scalar proxy, not a compartment/pump/stability/free surface high-fidelity model.
- The current integration is a minimal command-driven skeleton, not a full naval tasking/fire-control AI.

## 2. Current Capability Assessment

The naval warfare mainline has advanced from "minimum realistic maritime screening contact scenario" to a "tactical prototype with maritime motion, situational awareness, localized engagement chain, and support chain rudiments":

1. Platform layer:
   - Ship motion, low-speed maneuvering, sea state proxy, sea state environment entry, and maritime merge/fallback rules provide minimal dynamic differentiation.
2. Situational awareness layer:
   - Multi-sensor, maritime radar, ESM, sonar, track sharing, sea surface LOS patching, and screening closure form a continuous chain.
3. Support layer:
   - Shipborne aircraft token collaboration has established a minimal loop.
   - Abstract logistics inventory, replenishment window, and minimal `UNREP` transfer loop are established.
4. Engagement layer:
   - It has entered an operational skeleton of "minimal `VLS-SAM` + main gun/CIWS structured runtime + intermediate damage states + continuous damage propagation"; as of `2026-05-18`, the main-gun direct-fire and `MissionCommand -> CIWS` minimal directed regressions are green, while broader scenario stability still needs more coverage.

However, the current state cannot be called full realistic naval warfare. The main gaps remain:

1. Sea surface LOS is still a minimal patch, not a full sea/terrain/refraction unified model.
2. Shipborne aircraft are still token collaboration, not a complete aviation sortie system.
3. The weapon chain has entered the command path, but is not yet a full naval tasking/fire-control AI.
4. Continuous damage still lacks more realistic buoyancy, compartmentation, and stability evolution.
5. Current naval warfare is more suitable as a high-value acceptance surface for `sensor/C2/runtime` rather than an independent feature expansion mainline.

## 3. Unified Data Policy

Subsequent tasks continue to follow these rules:

1. Open facts:
   - Can be used for ship types, equipment families, responsibility boundaries, and platform existence.
2. Open professional sources:
   - Can be used for mechanism approximations such as sea clutter, ducting, underwater sound propagation, wave-added resistance, fire control chains, etc.
3. Community/unofficial sources:
   - Only used for `engineering calibration` or `community-derived approximation` level initial parameters.
4. Prohibited from being hardcoded as absolute facts:
   - Precise sonar detection range, fixed speed loss under specific sea state, actual limit performance of specific munitions, specific survivability compartment details, real replenishment doctrine and precise replenishment rates.

## 4. Next Round Suggestions

### 4.1 Current Suggestions

Priority should be given to:

1. Naval weapon command chain directed fixes and gate regression
2. Consistency supplementary tests for `DataLink / MissionCommand / naval` shared semantics
3. Maritime sensor / sea surface LOS / `sensor/naval` linkage gate regression

Rationale:
