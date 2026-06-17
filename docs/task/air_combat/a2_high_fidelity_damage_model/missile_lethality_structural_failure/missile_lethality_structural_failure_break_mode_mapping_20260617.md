# MLF-6 P2 Break-Mode Mapping

Status: `2026-06-17` v1 design — component-to-break-mode classification with
explicit integrity thresholds. Consumes P1 inventory. Feeds P3 state machine
implementation.

## Purpose

Define the exact mapping from F-16C component integrity values (read from ECS
`ComponentDamageState`) to MLF-6 break modes and breakup states. Every F-16C
component is classified into exactly one structural group or `none`. Each
group has an explicit integrity threshold and trigger rule.

All thresholds are **engineering assumptions** (`evidence_level =
engineering_assumption`), not real F-16 structural data. They are designed to:
1. Never trigger from undamaged flight (no false positives).
2. Trigger reliably when components receive significant structural damage from
   missile effects.
3. Be monotonic: once a break mode activates, it stays active (per D4).

## 1. Tentative Classification Resolution

Five P1 tentative classifications are resolved here:

| Component | P1 tentative | P2 decision | Rationale |
| --- | --- | --- | --- |
| `afterburner_nozzle` | `engine_right` or `fuselage` | `engine_right` | Aft engine assembly. Nozzle damage in isolation (without core damage) does NOT trigger `engine_detach`; it requires core-engine co-failure. |
| `dedicated_intake_lip_or_duct_component` | `fuselage` | `fuselage` | Intake duct is forward fuselage structure. System tag `engine` reflects propulsion function, not structural location. |
| `tail_hydraulic_pump` | `none` or `fuselage`/`tail_left` | `none` | Hydraulic component, not a structural member. Pump failure affects hydraulics (MLF-7 concern), not airframe integrity. |
| `engine_fuel_control_unit` | `none` | `none` | Engine accessory. Failure affects engine operation (MLF-7), not structural integrity. |
| `wing_spar_center_carrythrough_segment` (S5) | `fuselage` | `fuselage` | Center carrythrough crosses the fuselage; structurally it is a fuselage member, not a wing member. |

## 2. Structural Group Definitions

### 2.1 Group: `wing_left`

| Role | Component(s) | Default DB | TG-P7 DB |
| --- | --- | --- | --- |
| Primary | `wing_spar_center` (shared, default) / `wing_spar_center_left_root_segment` (S4) + `wing_spar_center_left_inner_wing_segment` (S3) (TG-P7) | 1 shared | 2 dedicated |
| Contributing | `left_aileron_actuator` | ✓ | ✓ |
| Contributing | `left_leading_edge_flap_actuator` | ✓ | ✓ |
| Contributing | `left_wing_fuel_cell` | ✓ | ✓ |
| **Total members** | | **4** | **5** |

**Threshold**: component integrity ≤ **0.25** → "structurally failed" for this group.

**Trigger rule**:
- Default DB: `wing_spar_center` failed → `wing_loss` immediately (primary member).
  OR 2+ contributing members failed → `wing_loss`.
- TG-P7 DB: either S3 or S4 failed → `wing_loss` immediately (primary).
  OR 2+ contributing members failed → `wing_loss`.

**Break mode**: `wing_loss`. `detached_part_ref` = `"left_wing"`.

### 2.2 Group: `wing_right`

| Role | Component(s) | Default DB | TG-P7 DB |
| --- | --- | --- | --- |
| Primary | `wing_spar_center` (shared, default) / `wing_spar_center_right_root_segment` (S6) + `wing_spar_center_right_inner_wing_segment` (S7) (TG-P7) | 1 shared | 2 dedicated |
| Contributing | `right_aileron_actuator` | ✓ | ✓ |
| Contributing | `right_leading_edge_flap_actuator` | ✓ | ✓ |
| Contributing | `right_wing_fuel_cell` | ✓ | ✓ |
| **Total members** | | **4** | **5** |

**Threshold**: same as wing_left (0.25).

**Trigger rule**: same structure as wing_left.

**Break mode**: `wing_loss`. `detached_part_ref` = `"right_wing"`.

**Shared-spar note (default DB only)**: `wing_spar_center` is a single
monolithic component shared between `wing_left` and `wing_right` groups. When
it fails (integrity ≤ 0.25), BOTH `wing_loss` break modes activate
simultaneously. This accurately reflects that a center wing spar fracture
compromises both wings. TG-P7 split resolves this by assigning left segments
to `wing_left`, right segments to `wing_right`, and the carrythrough to
`fuselage`.

### 2.3 Group: `tail_left`

| Role | Component(s) |
| --- | --- |
| Primary | `left_horizontal_tail_actuator_or_surface_component` |
| **Total members** | **1** |

**Threshold**: component integrity ≤ **0.20**.

**Trigger rule**: single member failed → `tail_loss`.

**Break mode**: `tail_loss`. `detached_part_ref` = `"left_stabilator"`.

Single-component group. The stricter threshold (0.20 vs 0.25) reflects that
there is no redundancy — a single actuator/surface failure means complete loss
of the left stabilator.

### 2.4 Group: `tail_right`

Identical structure to `tail_left`.

| Role | Component(s) |
| --- | --- |
| Primary | `right_horizontal_tail_actuator_or_surface_component` |
| **Total members** | **1** |

**Threshold**: 0.20. **Break mode**: `tail_loss`.
`detached_part_ref` = `"right_stabilator"`.

### 2.5 Group: `vertical_tail`

| Role | Component(s) |
| --- | --- |
| Primary | `rudder_actuator` |
| **Total members** | **1** |

**Threshold**: component integrity ≤ **0.25**.

**Trigger rule**: single member failed → `tail_loss`.

**Break mode**: `tail_loss`. `detached_part_ref` = `"vertical_stabilizer"`.

Note: `tail_left`, `tail_right`, and `vertical_tail` all produce the same
`break_mode = tail_loss`. They are separate groups so that left-stabilator
loss, right-stabilator loss, and rudder loss can occur independently. If any
one triggers, `tail_loss` is asserted. If two or three trigger, `tail_loss`
remains asserted (idempotent).

### 2.6 Group: `engine_right`

F-16C has a single engine. `engine_left` is empty.

| Role | Component(s) | Default DB | TG-P7 DB |
| --- | --- | --- | --- |
| Primary | `engine_core` (default) / S0+S1+S2 (TG-P7) | 1 | 3 segments |
| Contributing | `afterburner_nozzle` | ✓ | ✓ |
| **Total members** | | **2** | **4** |

**Threshold**: component integrity ≤ **0.15** for primary, ≤ **0.25** for contributing.

**Trigger rule**:
- Default DB: `engine_core` failed → `engine_detach` immediately.
  `afterburner_nozzle` alone does NOT trigger; it requires `engine_core ≤ 0.40`
  as a co-condition.
- TG-P7 DB: 2+ engine segments failed → `engine_detach`.
  `afterburner_nozzle` alone does NOT trigger; same co-condition.

The strict threshold (0.15) reflects that engine detachment requires severe
structural degradation of the engine mount/core. Superficial engine damage
below this threshold does not cause the engine to fall off the airframe.

**Break mode**: `engine_detach`. `detached_part_ref` = `"engine_core"`.

### 2.7 Group: `fuselage`

| Role | Component(s) | Default DB | TG-P7 DB |
| --- | --- | --- | --- |
| Primary | `center_fuselage_fuel_cell` | ✓ | ✓ |
| Primary | `dedicated_intake_lip_or_duct_component` | ✓ | ✓ |
| Primary | — | — | `wing_spar_center_carrythrough_segment` (S5) |
| **Total members** | | **2** | **3** |

**Threshold**: primary member integrity ≤ **0.30** for fuel cell; ≤ **0.20**
for intake duct and carrythrough.

**Trigger rule**: ANY single primary member failed → `fuselage_rupture`.

**Break mode**: `fuselage_rupture`. `detached_part_ref` =
`"center_fuselage"`.

The differentiated thresholds reflect structural significance: a fuel cell
rupture (0.30) is a structural breach of the fuselage at a lower threshold
than duct/carrythrough failure (0.20) because fuel cells are thinner structures.

### 2.8 Group: `none`

All other components. Their integrity values are read but never trigger a
break mode. This includes all avionics, sensors, cockpit, crew station,
hydraulic pump, fuel control unit, flight computer, and electrical bus.

| Component | Raw `system` | Why `none` |
| --- | --- | --- |
| `apg68_radar_array` | `radar` | Nose avionics; not structural |
| `cockpit_crew_station` | `cockpit` | Crew station; not structural |
| `data_link_terminal` | `data_link` | Data link avionics |
| `dedicated_canopy_surface_component` | `cockpit` | Canopy surface |
| `electrical_power_bus` | `avionics` | Electrical bus |
| `engine_fuel_control_unit` | `engine` | Engine accessory (P2 resolved) |
| `flight_control_computer` | `flight_control` | Flight computer avionics |
| `iff_interrogator` | `avionics` | IFF avionics |
| `inertial_navigation_unit` | `navigation` | INS avionics |
| `mission_computer` | `avionics` | Mission computer |
| `nose_avionics_bay` | `avionics` | Nose avionics bay |
| `tail_hydraulic_pump` | `hydraulic` | Hydraulic component (P2 resolved) |

## 3. Break Mode Summary

| Break mode | Trigger groups | `detached_part_ref` | Minimum failed members (default) |
| --- | --- | --- | --- |
| `wing_loss` | `wing_left` | `"left_wing"` | 1 primary OR 2 contributing |
| `wing_loss` | `wing_right` | `"right_wing"` | 1 primary OR 2 contributing |
| `tail_loss` | `tail_left` | `"left_stabilator"` | 1 (sole member) |
| `tail_loss` | `tail_right` | `"right_stabilator"` | 1 (sole member) |
| `tail_loss` | `vertical_tail` | `"vertical_stabilizer"` | 1 (sole member) |
| `engine_detach` | `engine_right` | `"engine_core"` | 1 primary (engine_core) |
| `fuselage_rupture` | `fuselage` | `"center_fuselage"` | 1 primary (any) |

A single `StructuralBreakupEvent` is written for each newly-activated break
mode. If two groups activate in the same timestep, two events are written
(e.g. `wing_loss` for left + `wing_loss` for right → two events, both with
`break_mode = wing_loss`).

## 4. Breakup State Determination

`breakup_state` is derived from the set of currently-active break modes:

| Active break modes | `breakup_state` | `airframe_breakup` |
| --- | --- | --- |
| 0 | `intact` | `false` |
| 1 mode, not `fuselage_rupture` | `partial_detachment` | `false` |
| `fuselage_rupture` alone | `partial_breakup` | `false` |
| 2 modes (any combination) | `partial_breakup` | `false` |
| 3 modes | `partial_breakup` | `false` |
| ≥4 distinct break-mode families active | `full_breakup` | `true` |

Distinct families: `wing_loss` (left and/or right count as one family),
`tail_loss` (any tail group counts as one family), `engine_detach` (one
family), `fuselage_rupture` (one family). Maximum = 4 families.

`airframe_breakup = true` only when `breakup_state == full_breakup`.

### 4.1 `multi_axis` break mode

When 3+ distinct families are active simultaneously, an additional
`StructuralBreakupEvent` with `break_mode = multi_axis` is written. This is
a synthetic break mode indicating the airframe is failing across multiple
structural axes. It does not replace the individual break-mode events; both
are emitted.

## 5. Default DB vs TG-P7 DB

| Aspect | Default (26 components) | TG-P7 opt-in (32 components) |
| --- | --- | --- |
| `wing_spar_center` | Monolithic; ≤0.25 triggers both `wing_loss` modes | Split: S3+S4→wing_left, S6+S7→wing_right, S5→fuselage |
| `engine_core` | Monolithic; ≤0.15 triggers `engine_detach` | Split: 2+ of S0/S1/S2 ≤0.15 triggers `engine_detach` |
| Component→group mapping | 26 entries | 32 entries |
| Feature flag | None (always active) | `A2_TARGET_GEOMETRY_PROXY_F16C_R22` |

MLF-6 P3 implementation must check for the presence of TG-P7 split receivers
in `ComponentDamageState` and automatically apply the correct mapping. The
feature flag gates which component names exist in the ECS world; MLF-6 does
not need to read the flag directly — it infers the surface from which
component keys are present.

If any TG-P7 split receiver name (S0-S7) appears in `component_integrity`,
the TG-P7 mapping is used. Otherwise, the default mapping is used. This
auto-detection avoids a hard dependency on the feature flag.

## 6. Engineering Rationale

### 6.1 Threshold values

All thresholds are `evidence_level = engineering_assumption`. They are chosen to:

- **0.15 (engine_core)**: Engine mounts are among the strongest structural
  elements. An engine core at 15% integrity implies the mount structure is
  severely compromised.
- **0.20 (single-member tail groups, intake duct, carrythrough)**:
  Single-member groups have no redundancy; the threshold is set slightly
  stricter than multi-member groups to avoid false triggers from minor damage.
- **0.25 (wing spar, rudder)**: Wing spars are primary structure. At 25%
  integrity, the spar can no longer carry flight loads. Same for rudder.
- **0.30 (fuel cell)**: Fuel cells are thin-walled; rupture at 30% integrity
  is plausible as a structural breach.

### 6.2 Contributing-only components

Control surface actuators (`aileron_actuator`, `flap_actuator`) are classified
as "contributing" rather than "primary" because:
- Actuator failure primarily affects flight control (MLF-7 domain), not the
  wing's structural integrity.
- However, multiple actuator failures on the same wing combined with spar
  degradation indicate the wing is structurally compromised.
- A single actuator failure alone does NOT mean the wing falls off.

### 6.3 No threshold for `none`-group components

Avionics, sensors, and non-structural components have no integrity threshold
because their failure does not cause structural breakup. Their failure
consequences (sensor degradation, mission kill) are handled by existing
`damage_system_air.h` and `damage_system_common.h` paths, and will be
extended by MLF-7.

## 7. Validation Plan

```bash
# Verify the mapping covers all 26 default components
python3 -c "
import json
with open('examples/config/database/aircraft/units/f16c_block50.json') as f:
    db = json.load(f)
names = set()
for hb in db.get('damage_model', {}).get('hitboxes', []):
    for c in hb.get('components', []):
        names.add(c['name'])
# All 26 must be classified
classified = {
    'wing_left': ['wing_spar_center', 'left_aileron_actuator', 'left_leading_edge_flap_actuator', 'left_wing_fuel_cell'],
    'wing_right': ['wing_spar_center', 'right_aileron_actuator', 'right_leading_edge_flap_actuator', 'right_wing_fuel_cell'],
    'tail_left': ['left_horizontal_tail_actuator_or_surface_component'],
    'tail_right': ['right_horizontal_tail_actuator_or_surface_component'],
    'vertical_tail': ['rudder_actuator'],
    'engine_right': ['engine_core', 'afterburner_nozzle'],
    'fuselage': ['center_fuselage_fuel_cell', 'dedicated_intake_lip_or_duct_component'],
    'none': ['apg68_radar_array', 'cockpit_crew_station', 'data_link_terminal',
             'dedicated_canopy_surface_component', 'electrical_power_bus',
             'engine_fuel_control_unit', 'flight_control_computer', 'iff_interrogator',
             'inertial_navigation_unit', 'mission_computer', 'nose_avionics_bay',
             'tail_hydraulic_pump'],
}
all_classified = set()
for group, comps in classified.items():
    for c in comps:
        all_classified.add(c)
missing = names - all_classified
extra = all_classified - names
assert not missing, f'Missing from classification: {missing}'
assert not extra, f'Extra in classification: {extra}'
# wing_spar_center counted twice (cross-region), that's expected
print(f'All {len(names)} components classified — OK')
print(f'wing_spar_center is cross-region: counted in wing_left AND wing_right')
"
```

## 8. Residuals

- All thresholds are `engineering_assumption`. They should be tuned during
  P4 validation based on focused test results. The current values are a
  starting point, not final.
- `afterburner_nozzle` co-condition (`engine_core ≤ 0.40`) is the most
  uncertain rule. P4 should test whether nozzle-only damage ever occurs in
  practice without core damage; if not, the co-condition can be simplified.
- `wing_spar_center` (default DB) triggering both `wing_loss` modes
  simultaneously may be too aggressive. If P4 shows this produces excessive
  full_breakup events from single hits, consider requiring an additional
  contributing-member failure on each side.
- Breakup state → `airframe_breakup` mapping (4 families = full_breakup) is
  conservative. A real F-16 with both wings lost should already be
  `full_breakup` even without engine detachment. P4 may adjust the threshold
  downward (e.g. 2 families = full_breakup).
- TG-P7 auto-detection by component name presence is a design choice; if
  component names are not stable across database versions, fall back to
  explicit feature-flag reading.
