<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md. Review before treating this file as authoritative. -->

# Realization P1 Master Task List

Status: `2026-05-17` version consolidated after review.

Related documents:

- [Archived Realization Master Task List (P0)](../archive/program/realism_program_taskboard_20260516.md)
- [Archived Flight Dynamics Realization P1 Implementation Package](../archive/flight/flight_dynamics_realism_p1_implementation_package_20260517.md)
- [Archived Sensor/Situation Realization P1 Implementation Package](../archive/sensor_situation/sensor_situation_realism_p1_implementation_package_20260517.md)
- [Archived Weapon/Guidance Realization P1 Implementation Package](../archive/weapon_guidance/weapon_guidance_realism_p1_implementation_package_20260517.md)

Purpose:

- Collect all “formally unsigned-off items” exposed during the `P0` review under `P1`.
- Clarify which items belong to `P1 Pre-Integration Cleanup` and which belong to `P1 Deepened Realization`.
- Provide a unified entry point for subsequent main-thread scheduling, branch splitting, and test acceptance.

---

## 1. Why These Issues Are Moved to P1

The current `P0` has completed the minimum realism skeleton along three lines:

1. Flight dynamics already possesses minimal `aero / propulsion / stall` trends.
2. Sensor/situation already possesses minimal `SNR/Pd / M-of-N / alpha-beta / track-report` semantics.
3. Weapon/guidance has cut direct reading of target truth and possesses minimal `3DoF + PN accel surrogate`.

However, the review also revealed that these achievements have not yet become “formal system-level capabilities.”

The exposed issues mostly do not indicate “wrong direction,” but rather:

1. New fields and new states already exist at runtime, but have not been fully integrated into `loader / factory / database / binding / observation`.
2. Old tests and old interfaces still carry semantic assumptions from before `P0`.
3. Some implementations still retain transitional patterns like `default constant / lazy init / debug-only path`.

Therefore, these issues are better moved into `P1`, for the following reasons:

1. They already exceed the `P0 minimal skeleton` goal.
2. Yet they are clearly earlier than more heavyweight model depth extensions like `P2`.
3. If these integration debts are not cleared first, deeper realism work will continue to be built on half-connected interfaces.

It should be emphasized:

- Although these issues are moved into `P1`, they should not be mixed at the same priority as deeper realism modeling.
- `P1` must first do “Pre-Integration Cleanup” and then “Deepened Realization.”

---

## 2. Two Layers of P1

### 2.1 P1-A: Pre-Integration Cleanup

This layer handles:

1. Hookup between configuration and database
2. Alignment of shared runtime semantics
3. Exposure of observation / Python bindings
4. Migration of old test contracts
5. Stabilization of lifecycle, build, and test entry points

The criterion is not “model is more complex,” but “the P0 skeleton is truly integrated into the mainline.”

### 2.2 P1-B: Deepened Realization

This layer handles:

1. More complete `Mach / compressibility / engine transient / stall semantics` in flight dynamics
2. More complete `track quality / minimal clutter / minimal IFF / minimal fusion` in sensors
3. More complete `seeker type / midcourse / parameterized 3DoF / fuze-damage layering` in weapons

The criterion is not “interfaces are connected,” but “causal chains are closer to credible tactical simulation.”

---

## 3. P1-A Pre-Integration Cleanup

This is the first phase of `P1` and the recommended first work package to open.

### 3.1 Common Goals Across Three Lines

1. New fields no longer rely solely on struct defaults or code constants.
2. New runtime states are stably observable by higher layers, tests, and Python interfaces.
3. Old semantics no longer slip through the new system.
4. Build and test entry points are repeatable, handover-able, and explainable.

### 3.2 Focus of Pre-Integration Cleanup for Each Line

#### Flight Dynamics

1. `AeroTuning / EngineTuning / StallState` go through `unit_definition -> loader -> factory`
2. `Propulsion` becomes the single source of truth for `Force / Logistics / Instrument / Observation`
3. Clarify whether `propulsion_system` is officially registered as an independent system
4. Fix unstable lifecycle issues in runtime tests / `ef_py`

#### Sensor/Situation

1. New `Sensor` fields complete `loader / factory` default value and database wiring
2. Extended fields (`Track status / quality / Detection`) enter observation and Python bindings
3. Old tests migrate from “shared contact masquerading as local detection” to “shared track report” semantics
4. Tighten the standard path `build -> ef_py -> runtime tests`

#### Weapon/Guidance

1. `MissileTuning` officially extended into the shared API
2. Launch phase correctly initializes missile mass, propellant, and runtime states
3. Key states (seeker / energy / autopilot) become observable via Python/debug
4. Fix shared semantics of `missile heading / ground track / seeker reference`

### 3.3 Suggested Order for P1-A

Suggested order:

1. `schema + loader/factory`
2. `shared runtime semantics`
3. `observation + binding`
4. `test contract migration`
5. `runtime lifecycle stabilization`

Not recommended:

- Doing more complex formulas first, then coming back to fix configuration and interfaces

---

## 4. P1-B Deepened Realization

This layer unfolds after `P1-A` is stabilized.

### 4.1 Flight Dynamics

Priorities:

1. More complete `Mach / drag rise / compressibility` scheduling
2. More realistic engine transient, dry throttle/afterburner semantics
3. More realistic `stall / post-stall / hysteresis / recovery`
4. First batch of aircraft parameter tables with source classification

### 4.2 Sensor/Situation

Priorities:

1. Refinement of `track status / quality / coast-drop`
2. Minimal clutter / weather penalty
3. Minimal IFF state machine
4. Minimal `Radar + DataLink` fusion
5. First batch of traceable radar parameter tables

### 4.3 Weapon/Guidance

Priorities:

1. Seeker type differentiation
2. `ARH midcourse + activation + datalink`
3. Parameterized `3DoF boost/sustain/coast + drag + mass`
4. Fuze / damage layering
5. First version of countermeasure interaction

---

## 5. What Continues to Be Left for P2

To avoid `P1` losing control again, the following content remains in `P2`:

1. Full 2D/3D lookup tables for flight dynamics, full FBW, full post-stall/spin
2. Full `JPDA / MHT / full Link 16 / full Mode 4/5 / NCTR / high-fidelity propagation` for sensors
3. Full `6DoF missile / DRFM/HOJ high-level logic / full fragment geometry / model-grade high-precision replication` for weapons

---

## 6. Recommended Main-Thread Breakdown

It is suggested to split tasks in the following order, rather than each discipline going solo:

1. `P1-A1 schema/integration PR`
   - Close `loader / factory / shared init` for all three lines at once
2. `P1-A2 observation/binding PR`
   - Uniformly expose new states for all three lines
3. `P1-A3 test-contract PR`
   - Update old test semantics, fix runtime test entry points
4. `P1-B1 dynamics PR`
   - Advance flight dynamics deepening first
5. `P1-B2 tracking PR`
   - Then advance sensor/situation deepening
6. `P1-B3 missile PR`
   - Finally advance weapon/guidance deepening

Benefits of this breakdown:

1. Resolve the “interface not yet connected” problem shared by all directions first
2. Then move into heavier realism improvements
3. Each round has a clear acceptance surface, avoiding mixing compatibility debt with model depth changes

---

## 7. Overall Acceptance Criteria for P1

After `P1-A` is completed, at minimum the following should hold:

1. All `P0` new fields and states across the three lines can be consistently accessed from configuration, runtime, observation, and Python.
2. Old tests no longer rely on pre-`P0` semantics.
3. Runtime test entry points are stable, no longer dependent on workarounds.

After `P1-B` is completed, at minimum the following should hold:

1. The input-output relationships of the causal chains (platform, sensor, weapon) are closer to engineering semantics supported by public literature.
2. Realization parameters begin entering the database and reference tables instead of remaining scattered in code default constants.
3. It becomes possible to re-evaluate the credibility of deeper training and stronger scenario conclusions.

---

## 8. Current Recommendation

If work is to continue now, the recommendation is not to immediately modify more complex formulas, but to:

1. Open `P1-A` according to this master task list.
2. Digest all the unsigned-off items exposed during this review.
3. Then proceed to `P1-B` according to the three sub-packages.

The most valuable conclusion at this point is not that “P0 is insufficient,” but:

- `P0` has already set the right direction.
- The primary task of `P1` is to turn this direction into a mainline formal capability.
- Then continue pushing realism deeper.
