# MLF-6 P1 Component Inventory

Status: `2026-06-17` read-only inventory for MLF-6B. Three deliverables:

1. Every `ComponentDamageState` field MLF-6 will read at runtime.
2. Every F-16C component name with structural group classification.
3. Every `structural_integrity` write site MLF-6 must NOT touch.

## 1. ComponentDamageState — Runtime Read Surface

Source: `src/components/combat/common/damage_common.h:123-147`

MLF-6's `StructuralFailureUpdate` system reads the following fields each tick
via ECS `get<ComponentDamageState>(aircraft_entity)`:

| Field | Type | Read by MLF-6? | Purpose in MLF-6 |
| --- | --- | --- | --- |
| `component_integrity` | `map<string, double>` | **YES** | Primary input. Per-component values (0.0–1.0) are compared against P2 break-mode integrity thresholds. A wing-spar at 0.3 triggers `wing_loss`; a stabilator at 0.2 triggers `tail_loss`. |
| `component_primary_failure_mode` | `map<string, string>` | **YES** | Distinguishes `structural_weakening` from `puncture`/`cut`/etc. Structural-weakening failures accumulate toward break-mode thresholds; non-structural failures (e.g. `electrical_loss`) do not. |
| `component_redundancy_group` | `map<string, string>` | **YES** | Groups components sharing a structural role. E.g. `left_wing_fuel_cell` and `right_wing_fuel_cell` may share a wing-spar group; failure of either contributes to `wing_loss`. |
| `redundancy_group_availability` | `map<string, double>` | **cond.** | If P2 mapping uses group-level thresholds (e.g. "wing group availability < 0.4"), this field is read. Otherwise not. |
| `redundancy_group_member_count` | `map<string, uint32>` | **cond.** | Same as above; only if group-level thresholds are chosen. |
| `redundancy_group_failed_count` | `map<string, uint32>` | **cond.** | Same as above. |
| `component_system` | `map<string, string>` | **NO** | Used during P2 design to classify components, but not read at runtime. |
| `component_redundancy_weight` | `map<string, double>` | **NO** | Not structural; weights are used for system-health aggregation, not breakup. |
| `component_failure_mode_severity` | `map<string, map<string, double>>` | **NO** | Too granular. MLF-6 only needs the primary failure mode. |
| `pending_dependency_effects` | `vector<PendingDependencyEffect>` | **NO** | Dependency propagation is handled by `AircraftDamageStateUpdate`; MLF-6 runs after it. |
| `has_fire_suppression_components` | `bool` | **NO** | Fire-suppression components are not structural. |

## 2. F-16C Component → Structural Group Classification

### 2.1 Current unit database (26 components)

Source: `examples/config/database/aircraft/units/f16c_block50.json`
(`damage_model.hitboxes[].components[].name`)

| # | Component name | System tag | Tentative structural group | Notes |
| --- | --- | --- | --- | --- |
| 0 | `afterburner_nozzle` | engine | `engine_right` or `fuselage` | Nozzle damage is engine-related but not engine-core; needs P2 decision |
| 1 | `apg68_radar_array` | sensor | `none` | Nose avionics; not a structural member |
| 2 | `center_fuselage_fuel_cell` | fuel | `fuselage` | Fuselage fuel cell; rupture contributes to fuselage damage |
| 3 | `cockpit_crew_station` | crew | `none` | Crew station; not structural |
| 4 | `data_link_terminal` | sensor | `none` | Avionics; not structural |
| 5 | `dedicated_canopy_surface_component` | surface | `none` | Canopy; cosmetic/sensor surface only |
| 6 | `dedicated_intake_lip_or_duct_component` | surface | `fuselage` | Intake duct is forward fuselage structure |
| 7 | `electrical_power_bus` | electrical | `none` | Electrical; not structural |
| 8 | `engine_core` | engine | `engine_right` | **Retired by TG-P7 split.** Replaced by 3 segments below. |
| 9 | `engine_fuel_control_unit` | engine | `none` | Engine accessory; not structural |
| 10 | `flight_control_computer` | control | `none` | Avionics; not structural |
| 11 | `iff_interrogator` | sensor | `none` | Avionics; not structural |
| 12 | `inertial_navigation_unit` | sensor | `none` | Avionics; not structural |
| 13 | `left_aileron_actuator` | control | `wing_left` | Left wing control surface; loss contributes to wing damage |
| 14 | `left_horizontal_tail_actuator_or_surface_component` | control | `tail_left` | Left stabilator; loss contributes to tail damage |
| 15 | `left_leading_edge_flap_actuator` | control | `wing_left` | Left wing leading edge; loss contributes to wing damage |
| 16 | `left_wing_fuel_cell` | fuel | `wing_left` | Left wing fuel cell; rupture contributes to wing damage |
| 17 | `mission_computer` | sensor | `none` | Avionics; not structural |
| 18 | `nose_avionics_bay` | sensor | `none` | Nose avionics; not structural |
| 19 | `right_aileron_actuator` | control | `wing_right` | Right wing control surface |
| 20 | `right_horizontal_tail_actuator_or_surface_component` | control | `tail_right` | Right stabilator |
| 21 | `right_leading_edge_flap_actuator` | control | `wing_right` | Right wing leading edge |
| 22 | `right_wing_fuel_cell` | fuel | `wing_right` | Right wing fuel cell |
| 23 | `rudder_actuator` | control | `vertical_tail` | Rudder; loss contributes to vertical tail damage |
| 24 | `tail_hydraulic_pump` | hydraulic | `fuselage` | Tail-mounted pump; fuselage-adjacent |
| 25 | `wing_spar_center` | structure | `wing_left` + `wing_right` | **Retired by TG-P7 split.** Cross-region; replaced by 5 segments below. |

### 2.2 TG-P7 split receivers (8 new, 2 parents retired)

Source: `docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.json`

| # | Split receiver name | Parent | Tentative structural group | Notes |
| --- | --- | --- | --- | --- |
| S0 | `engine_core_afterburner_segment` | `engine_core` | `engine_right` | Aft section; afterburner+nozzle overlap proxy |
| S1 | `engine_core_hot_section_segment` | `engine_core` | `engine_right` | Mid section; turbine/combustor |
| S2 | `engine_core_forward_compressor_segment` | `engine_core` | `engine_right` | Forward section; compressor |
| S3 | `wing_spar_center_left_inner_wing_segment` | `wing_spar_center` | `wing_left` | Left inner wing spar section |
| S4 | `wing_spar_center_left_root_segment` | `wing_spar_center` | `wing_left` | Left root spar section |
| S5 | `wing_spar_center_carrythrough_segment` | `wing_spar_center` | `fuselage` | Center carrythrough (fuselage crossing) |
| S6 | `wing_spar_center_right_root_segment` | `wing_spar_center` | `wing_right` | Right root spar section |
| S7 | `wing_spar_center_right_inner_wing_segment` | `wing_spar_center` | `wing_right` | Right inner wing spar section |

### 2.3 Effective component surface for MLF-6

After TG-P7 split (opt-in, not yet default): **32 components** (26 base + 8 new − 2 retired parents). Default database: **26 components** (TG-P7 not activated).

MLF-6 P2 must design the break-mode mapping for both surfaces:
- **Default (26)**: `engine_core` and `wing_spar_center` are single monolithic components.
- **Opt-in TG-P7 (32)**: engine and spar are split into segments with finer spatial resolution.

The mapping design must produce correct break-mode behavior on both surfaces.

### 2.4 Structural group summary

| Group | Component count (default) | Component count (TG-P7) | Triggered break mode |
| --- | --- | --- | --- |
| `wing_left` | 3 (left aileron, left flap, left wing fuel + wing_spar_center shared) | 5 (+ S3, S4) | `wing_loss` |
| `wing_right` | 3 (right aileron, right flap, right wing fuel + wing_spar_center shared) | 5 (+ S6, S7) | `wing_loss` |
| `tail_left` | 1 (left stabilator) | 1 | `tail_loss` |
| `tail_right` | 1 (right stabilator) | 1 | `tail_loss` |
| `vertical_tail` | 1 (rudder actuator) | 1 | `tail_loss` |
| `engine_right` | 2 (engine_core, afterburner_nozzle) | 4 (S0, S1, S2, afterburner_nozzle) | `engine_detach` |
| `fuselage` | 4 (center fuel cell, intake duct, tail hydraulic pump, wing_spar_center) | 5 (+ S5, − monolithic wing_spar_center) | `fuselage_rupture` |
| `none` | 11 | 12 (+ iff_interrogator split awareness; detail unchanged) | — |

Note: F-16C has a single engine, so `engine_left` is empty. The group is named
`engine_right` for consistency with the contract, but the break mode is simply
`engine_detach`.

## 3. `structural_integrity` Write Sites — Forbidden Touch List

Per D2, MLF-6 must not read or write `AircraftDamageState::structural_integrity`.
The following code sites are the authoritative write surface. MLF-6 acceptance
tests must verify that none of these sites are modified by MLF-6 code.

### 3.1 Component declaration

| File | Line | Role |
| --- | --- | --- |
| `src/components/domains/air/combat/damage_air.h` | 114 | **Declaration.** `double structural_integrity = 1.0;` |

### 3.2 Damage-system writes (per-tick degradation)

| File | Line | Write | Trigger |
| --- | --- | --- | --- |
| `src/systems/combat/damage_system_air.h` | 54 | `aircraft.structural_integrity -= structural_loss` | Envelope flutter damage when `structural_integrity < 0.985` |
| `src/systems/combat/damage_system_air.h` | 180 | `aircraft.structural_integrity -= 0.0060 * fire * dt_s` | Fire damage to structure |
| `src/systems/combat/damage_system_air.h` | 205 | `aircraft.structural_integrity -= ...` | Structural overstress from excessive G |
| `src/systems/combat/damage_system_air.h` | 419 | **Read.** `aircraft_damage_capability_floor(aircraft->structural_integrity, 0.35)` | Clamps `max_g`, `min_g`, `max_speed` |
| `src/systems/combat/damage_system_air.h` | 433 | **Read.** `1.0 + 0.35*(1.0 - structural_integrity)` | Increases `min_speed` |
| `src/systems/combat/damage_system_air.h` | 436 | **Read.** `1.0 + 0.20*(1.0 - structural_integrity)` | Increases `takeoff_speed` |

### 3.3 Component state handoff writes

| File | Line | Write | Trigger |
| --- | --- | --- | --- |
| `src/components/domains/air/combat/damage_air.h` | 365-366 | `aircraft_damage.structural_integrity = min(aircraft_damage.structural_integrity, availability)` | Component dependency effect applies structural cap |
| `src/components/domains/air/combat/damage_air.h` | 458 | `aircraft_damage->structural_integrity -= 0.03 + 0.08 * bounded_impulse` | Ground contact impulse |
| `src/components/domains/air/combat/damage_air.h` | 544 | `state.structural_integrity = clamp(state.structural_integrity, 0.0, 1.0)` | Sanitization clamp during state serialize/deserialize |
| `src/components/domains/air/combat/damage_air.h` | 586 | **Read.** `state.structural_integrity <= 0.35` | `forced_landing_required` gate |
| `src/components/domains/air/combat/damage_air.h` | 613 | **Read.** `min(platform.survivability_margin, aircraft.structural_integrity)` | Feeds into survivability cap |

### 3.4 Effects-model writes

| File | Line | Write | Trigger |
| --- | --- | --- | --- |
| `src/models/domains/air/default_effects_air_domain.h` | 218 | `aircraft_damage.structural_integrity -= localized_effect_delta(...)` | Blast effect on structural integrity |
| `src/models/domains/air/default_effects_air_domain.h` | 273 | `aircraft_damage.structural_integrity -= localized_effect_delta(...)` | Fragment effect on structural integrity |
| `src/models/domains/air/default_effects_air_domain.h` | 351 | `aircraft_damage->structural_integrity -= localized_effect_delta(...)` | Generic localized effect on structural integrity |

### 3.5 Observer / recording reads (no structural impact)

| File | Line | Role |
| --- | --- | --- |
| `src/core/interfaces/engagement_event_recorder.h` | 29 | `double structural_integrity = 1.0;` — snapshot field declaration |
| `src/core/engine/simulation_kernel_engagement_event_store.cpp` | 116, 140, 245 | Reads for damage-report state strings and deltas |
| `src/core/engine/simulation_kernel_observation_api.cpp` | 249 | Reads for observation export |
| `src/systems/domains/air/aerodynamics_system.h` | 219 | **Read.** `clamp(aircraft_damage->structural_integrity, 0.0, 1.0)` — aero modifier |

### 3.6 Write site summary

| Category | Write count | Files |
| --- | --- | --- |
| Per-tick envelope degradation | 3 | `damage_system_air.h:54,180,205` |
| Component-dependency structural cap | 1 | `damage_air.h:365-366` |
| Ground contact impulse | 1 | `damage_air.h:458` |
| Sanitization clamp | 1 | `damage_air.h:544` |
| Localized effects (blast/fragment/generic) | 3 | `default_effects_air_domain.h:218,273,351` |
| **Total write sites** | **9** | 3 files |

MLF-6 must leave all 9 write sites untouched. MLF-7 may later add a 10th write
path that sets `structural_integrity` as a function of `StructuralBreakupState`,
but that decision is out of MLF-6's scope.

## 4. Additional Forbidden Touch Surfaces

Per D2 and D6, MLF-6 must also not modify:

| Component / System | File | Key fields |
| --- | --- | --- |
| `FlightModel` | `src/components/physics/performance.h` | `max_turn_rate`, `max_accel`, `max_climb_rate`, `max_g`, `min_g`, `max_speed`, `min_speed` |
| `Propulsion` | `src/components/physics/forces.h` | `mil_thrust_n`, `ab_thrust_n` |
| `Health` | `src/components/combat/health.h` | `current_hp`, `max_hp` |
| `PlatformDamageState` | `src/components/combat/common/damage_common.h:160-172` | `loss_state`, `survivability_margin`, `mission_capability` |
| `AircraftDamageState` (any field) | `src/components/domains/air/combat/damage_air.h` | All fields including `structural_integrity`, `flight_control_integrity`, `propulsion_integrity`, `hydraulic_integrity`, etc. |

## 5. Validation

```bash
# Verify all referenced paths exist
ls src/components/combat/common/damage_common.h
ls examples/config/database/aircraft/units/f16c_block50.json
ls docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.json
ls src/components/domains/air/combat/damage_air.h
ls src/systems/combat/damage_system_air.h
ls src/models/domains/air/default_effects_air_domain.h

# Verify component count consistency
python3 -c "
import json
with open('examples/config/database/aircraft/units/f16c_block50.json') as f:
    db = json.load(f)
names = set()
for hb in db.get('damage_model', {}).get('hitboxes', []):
    for c in hb.get('components', []):
        names.add(c.get('name'))
assert len(names) == 26, f'Expected 26, got {len(names)}'
print(f'Default components: {len(names)} — OK')
"
```

## 6. Residuals

- The tentative structural group classification in §2 is a **starting point** for
  P2 design. Final group assignments and integrity thresholds are the P2
  deliverable, not this inventory.
- `engine_left` is empty for F-16C (single engine). MLF-6 must handle this
  gracefully: the `engine_detach` break mode maps to `engine_right` group only.
- TG-P7 split receivers are opt-in (gated behind `A2_TARGET_GEOMETRY_PROXY_F16C_R22`
  feature flag). MLF-6 P2 must design mapping for both default (26) and opt-in
  (32) component surfaces.
- `tail_hydraulic_pump` classification as `fuselage` is tentative. It is
  physically in the tail but is a hydraulic component, not a structural member.
  P2 should decide whether it contributes to `tail_loss` or `none`.
- `afterburner_nozzle` classification as `engine_right` is tentative. The nozzle
  is part of the engine assembly but at the extreme aft; damage to it may or may
  not imply engine detachment.
- Pending dependency effects are not consumed by MLF-6. If future evidence shows
  that dependency cascades (e.g. engine fire → spar weakening) should accelerate
  break-mode thresholds, that belongs in MLF-7.
