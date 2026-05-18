<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/program/realism_program_convergence_plan_20260517.zh.md. Review before treating this file as authoritative. -->

# Next Convergence Plan Based on Analysis Documents

Status: `2026-05-17` Rewritten based on the closure markers of five `*realism_analysis*` documents.

Related documents:

- [Realism Analysis of Flight Dynamics](../flight/flight_dynamics_realism_analysis_20260516.zh.md)
- [Realism Analysis of Sensors and Situational Awareness](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [Realism Analysis of Weapon Systems and Guidance Loops](../weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md)
- [Realism Analysis of Naval Warfare Simulation](../naval/naval_realism_analysis_20260516.zh.md)
- [Realism Analysis of Command Chain and C2 Communications](../c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)
- [Current Status of Realistic Main Line and Related Sub-projects](realism_program_current_status_20260517.zh.md)
- [Naval Warfare Advancement Checkpoint](../../naval/naval_progress_checkpoint_20260517.zh.md)

Document purpose:

- Derive next steps only from entries still marked as `unresolved / partially resolved` in the analysis documents.
- Do not continue treating directions marked as `minimum closure achieved / resolved` as the default main thread entry points.
- The goal is to converge the current work scope and avoid spreading out again by discipline.

## 1. Items Removed from Main Blockage

The following issues should no longer be treated as "starting from scratch" or "completely missing":

1. `flight`
   - Propulsion transients, basic `Mach` scheduling, stall guard, and runtime/debug skeleton are already connected.
2. `weapon`
   - `launch gate / seeker-only runtime / minimum 3DoF + PN-autopilot surrogate / midcourse minimal semantics` are already connected.
3. `sensor`
   - `track/report` and `DataLink / track` guard surfaces turned green in this review round; should now be handled as maintenance state.
4. `naval`
   - `screen-hold / sea_state / Sonar / embarked helo token / UNREP` are no longer the main blockages; the naval weapon command chain has also been moved to maintenance acceptance surface.
5. `C2`
   - `MissionCommand roundtrip / DataLink budget / deadband override / minimum ROE gate` are already integrated into the main line.

The implication is not that these directions are "completely done," but that:
In the next steps, they should no longer be treated as new default entry points for repeated expansion.

## 2. Only Three Execution Main Lines Retained

### 2.1 Closure of Naval Weapon Command Chain

Source entries:

1. `naval 2.5 / 2.8 / 2.9`
2. `c2 2.1 / 2.3 / 2.4 / 2.11`

Why do this first:

1. This group of issues was previously the clearest set of red points, but the current sample review has turned green, making it better described as structural debt closure.
2. It simultaneously blocks a batch of "partially resolved" entries across the `naval / C2 / sensor` analysis documents.

This line only does:

1. Fix the main gun direct-fire link in `fire_naval_weapon()`, so that "has track -> can fire -> reduce inventory" holds again.
2. Fix the `MissionCommand -> CIWS` command-driven chain, so ships can trigger close-in defense without relying on a direct weapon API.
3. Align `MissionCommand / authority / track source / weapon selector` shared semantics on the ship path.

Acceptance lines:

1. `tests/runtime/test_naval_ship_database.py::NavalShipDatabaseTests::test_ddg_gun_can_fire_with_track_and_reduce_ammo`
2. `tests/runtime/test_naval_ship_database.py::NavalShipDatabaseTests::test_naval_mission_command_can_trigger_ciws_without_direct_weapon_api`
3. `tests/runtime/test_ship_mission_command_authority.py`
4. `tests/runtime/test_naval_mission_command_mapping.py`

This line explicitly does not expand:

1. More detailed differentiation of SAM missile types like `SM-2 / SM-6`
2. Complete naval fire-control AI
3. Full refinement of gun/`CIWS` ballistics, firing arcs, and tracking channels

### 2.2 Closure of Track Lifecycle / IFF / Fusion

Source entries:

1. `sensor 2.1 / 2.5 / 2.6 / 2.7 / 2.8 / 2.9 / 2.10`

Why do this first:

1. Currently, many behaviors that appear "connected at the upper level" are still built on overly simplified `track quality / identity / fusion` semantics.
2. Without tightening this layer first, `weapon / naval / C2` will continue to bypass it individually.

This line only does:

1. Clearly define `Tentative -> Confirmed -> Coasted -> Dropped` as runtime contracts.
2. Add minimal `quality / velocity / source_mask` to `track` to prevent `Radar + DataLink` from remaining a coverage illusion.
3. Implement a minimal `IFF` state machine, at least distinguishing the convergence path for `pending / friendly / unknown / hostile`.
4. Keep `DataLink = track/report` scope, do not revert to raw contact sharing, while tightening `sensor / DataLink` timing and reception-side boundaries.

Acceptance lines:

1. `tests/runtime/test_sensor_situation_realism_p0.py`
2. `tests/runtime/test_data_link_qos_runtime.py`
3. New or strengthened directed guard tests for `track lifecycle / IFF / fused track`

This line explicitly does not expand:

1. Complete `SNR/Pd` physical detection model
2. `PRF / waveform / micro-Doppler` refinement
3. `DRFM / cross-eye / full ECM` countermeasure system

### 2.3 Minimum Closure of Missile Terminal Realism

Source entries:

1. `weapon 2.3 / 2.4 / 4.4 / 5.1 / 5.2 / 5.3 / 6.1 / 6.2 / 6.4 / 8.2`

Why do this now:

1. The front-end of the weapon line ("can launch, can fly, can switch to seeker") is no longer the main problem.
2. The larger current structural risk is that truth shortcut, fuze shortcut, and damage shortcut coexist.

This line only does:

1. Tighten the usage boundary of truth-based `LOS/target state` to make seeker/track input more consistent with guidance contract.
2. Add a minimal seeker reject/decoy contract to avoid "any strongest signal can be tracked unconditionally."
3. First converge `fuze / hit / damage` into a consistent minimal contract to prevent the `HP` path and subsystem path from continuing to drift.
4. Clarify the minimal observable impact of launch altitude/speed on terminal behavior.

Acceptance lines:

1. Existing `tests/runtime/test_weapon_guidance_realism_guards.py`
2. Existing `tests/runtime/test_air_combat_1v1_fire_missile.py`
3. New directed guard tests for truth guidance dependency, fuze timing, damage contract

This line explicitly does not expand:

1. Complete seeker family differentiation
2. Complete warhead geometry
3. Complete `IRCCM / SARH / LOAL` system

## 3. All Other Directions are Either Maintenance or Deferred

1. `flight`
   - Currently only accepts boundary closures that do not break existing guards, and interface preparation for `compressibility / RSS / FBW`.
2. `naval`
   - Currently no new ship types, full buoyancy/compartment/ stability, or larger formation doctrine.
3. `C2`
   - Currently no full authority transfer state machine, nor full `multi-hop / retry / jamming` network.
4. `sensor`
   - Currently no full radar equation, full clutter chain, or complete electronic warfare countermeasure system.

The purpose is not conservatism, but to avoid "continuing to dig deep into each line before tightening shared semantics."

## 4. Suggested Parallel Distribution

1. Worker A
   - Maintenance closure and regression testing for `sensor / DataLink / track`
2. Worker B
   - Regression testing and structural debt reduction for the naval weapon command chain/authority
3. Worker C
   - Consistency closure for weapon terminal `fuze / damage / truth guidance`
4. Main thread
   - Responsible for shared schema, `MissionCommand`, `DataLink`, bindings, and acceptance test integration to avoid multiple workers cross-editing the same shared contract.

## 5. Completion Criteria

The next round of work is considered a real "step forward" only when the following conditions are met:

1. The guard surfaces of naval and `sensor/DataLink/track` remain green continuously, not reverting to behavioral red points.
2. `Track / IFF / Fused` forms independent guard tests, rather than continuing to rely on coincidental scenario validity.
3. The weapon terminal no longer simultaneously depends on conflicting truth shortcuts and damage shortcuts.
4. The entries currently marked as `unresolved` in the five analysis documents should at least decrease in number across the `naval / sensor / weapon` lines, rather than continuing to add new directions.

## 6. One-Sentence Conclusion

The next step is no longer to advance evenly across the five lines `flight / sensor / weapon / naval / C2`, but only to converge on three things:

1. Naval weapon command chain and naval acceptance surface
2. Track lifecycle / `IFF` / fusion contract
3. Consistency of `fuze / damage / truth guidance` in the weapon terminal
