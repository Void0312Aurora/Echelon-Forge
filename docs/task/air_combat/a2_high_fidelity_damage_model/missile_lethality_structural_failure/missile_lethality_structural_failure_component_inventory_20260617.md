# MLF-6 P1 Component Inventory

Status: `2026-06-17` v2 — corrected: added `.inc` write sites (5 missed), raw
system tags restored, wing_spar_center double-count resolved, forbidden-surface
write sites concretely listed. Read-only inventory for MLF-6B.

Three deliverables:

1. Every `ComponentDamageState` field MLF-6 will read at runtime.
2. Every F-16C component name with raw JSON `system` and structural group
   classification.
3. Every `structural_integrity` write site MLF-6 must NOT touch, including
   every `FlightModel`, `Propulsion`, `Health`, and `PlatformDamageState` write
   site MLF-6 must NOT touch.

## 1. ComponentDamageState — Runtime Read Surface

Source: `src/components/combat/common/damage_common.h:123-147`

MLF-6's `StructuralFailureUpdate` system reads the following fields each tick
via ECS `get<ComponentDamageState>(aircraft_entity)`:

| Field | Type | Read by MLF-6? | Purpose in MLF-6 |
| --- | --- | --- | --- |
| `component_integrity` | `map<string, double>` | **YES** | Primary input. Per-component values (0.0–1.0) are compared against P2 break-mode integrity thresholds. |
| `component_primary_failure_mode` | `map<string, string>` | **YES** | Gates break-mode accumulation. Only *structurally-damaging* failure modes (`structural_weakening`, `puncture`, `cut`, `blast_deformation`) count toward break-mode thresholds. Purely functional modes (`fuel_leak`, `electrical_loss`, `hydraulic_pressure_loss`, `data_loss`, `fire_source`) do not, even if the component's integrity drops. |
| `component_redundancy_group` | `map<string, string>` | **YES** | Groups components sharing a structural role for cumulative damage assessment. |
| `component_system` | `map<string, string>` | **YES** | Raw system tag from unit database. Used to classify components into structural groups (e.g. `wings` system → `wing_left`/`wing_right` group). |
| `redundancy_group_availability` | `map<string, double>` | **cond.** | If P2 mapping uses group-level thresholds, this field is read. |
| `redundancy_group_member_count` | `map<string, uint32>` | **cond.** | Same as above. |
| `redundancy_group_failed_count` | `map<string, uint32>` | **cond.** | Same as above. |
| `component_redundancy_weight` | `map<string, double>` | **NO** | Not structural; used for system-health aggregation. |
| `component_failure_mode_severity` | `map<string, map<string, double>>` | **NO** | Too granular. MLF-6 only needs the primary failure mode. |
| `pending_dependency_effects` | `vector<PendingDependencyEffect>` | **NO** | Dependency propagation is handled by `AircraftDamageStateUpdate`. |
| `has_fire_suppression_components` | `bool` | **NO** | Fire-suppression components are not structural. |

## 2. F-16C Component → Structural Group Classification

### 2.1 Current unit database (26 components)

Source: `examples/config/database/aircraft/units/f16c_block50.json`
(`damage_model.hitboxes[].components[]`)

| # | Component name | Raw JSON `system` | Normalized system | Tentative structural group | Notes |
| --- | --- | --- | --- | --- | --- |
| 0 | `afterburner_nozzle` | `engine` | engine | `engine_right` | Aft engine assembly; nozzle damage may or may not imply engine detachment. P2 decision. |
| 1 | `apg68_radar_array` | `radar` | sensor | `none` | Nose radar; not structural. |
| 2 | `center_fuselage_fuel_cell` | `fuel` | fuel | `fuselage` | Fuselage fuel cell; rupture contributes to fuselage structural degradation. |
| 3 | `cockpit_crew_station` | `cockpit` | crew | `none` | Crew station; not structural. |
| 4 | `data_link_terminal` | `data_link` | sensor | `none` | Data link; not structural. |
| 5 | `dedicated_canopy_surface_component` | `cockpit` | surface | `none` | Canopy surface; not structural. |
| 6 | `dedicated_intake_lip_or_duct_component` | `engine` | engine | `fuselage` | Intake duct is forward fuselage structure despite `engine` system tag. P2 decision. |
| 7 | `electrical_power_bus` | `avionics` | electrical | `none` | Electrical bus; not structural. |
| 8 | `engine_core` | `engine` | engine | `engine_right` | Retired by TG-P7 split (opt-in). Replaced by S0-S2 below. |
| 9 | `engine_fuel_control_unit` | `engine` | engine | `none` | Engine accessory; not structural. |
| 10 | `flight_control_computer` | `flight_control` | control | `none` | Flight computer; not structural. |
| 11 | `iff_interrogator` | `avionics` | sensor | `none` | IFF avionics; not structural. |
| 12 | `inertial_navigation_unit` | `navigation` | sensor | `none` | INS avionics; not structural. |
| 13 | `left_aileron_actuator` | `flight_control` | control | `wing_left` | Left aileron; loss contributes to left wing structural degradation. |
| 14 | `left_horizontal_tail_actuator_or_surface_component` | `flight_control` | control | `tail_left` | Left stabilator; loss contributes to left tail degradation. |
| 15 | `left_leading_edge_flap_actuator` | `flight_control` | control | `wing_left` | Left wing leading edge; loss contributes to left wing. |
| 16 | `left_wing_fuel_cell` | `fuel` | fuel | `wing_left` | Left wing fuel cell; rupture contributes to left wing. |
| 17 | `mission_computer` | `avionics` | sensor | `none` | Mission computer; not structural. |
| 18 | `nose_avionics_bay` | `avionics` | sensor | `none` | Nose avionics bay; not structural. |
| 19 | `right_aileron_actuator` | `flight_control` | control | `wing_right` | Right aileron. |
| 20 | `right_horizontal_tail_actuator_or_surface_component` | `flight_control` | control | `tail_right` | Right stabilator. |
| 21 | `right_leading_edge_flap_actuator` | `flight_control` | control | `wing_right` | Right wing leading edge. |
| 22 | `right_wing_fuel_cell` | `fuel` | fuel | `wing_right` | Right wing fuel cell. |
| 23 | `rudder_actuator` | `flight_control` | control | `vertical_tail` | Rudder; loss contributes to vertical tail degradation. |
| 24 | `tail_hydraulic_pump` | `hydraulic` | hydraulic | `none` | Tail-mounted hydraulic pump; not a structural member. P2 decision. |
| 25 | `wing_spar_center` | `wings` | structure | `wing_left` + `wing_right` | **Cross-region component.** Retired by TG-P7 split. Contributes to both left and right wing groups. Replaced by S3-S7 below. |

Normalized system column maps raw JSON tags into broader categories for
readability, but structural group classification uses the raw tag and component
name as ground truth. Normalization rules:

| Raw JSON `system` | Normalized |
| --- | --- |
| `avionics`, `data_link`, `navigation`, `radar` | `sensor` |
| `cockpit` | `crew` or `surface` (context-dependent) |
| `engine` | `engine` |
| `flight_control` | `control` |
| `fuel` | `fuel` |
| `hydraulic` | `hydraulic` |
| `wings` | `structure` |

### 2.2 TG-P7 split receivers (8 new, 2 parents retired)

Source: `docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.json`

| # | Split receiver name | Parent | Raw system | Structural group | Notes |
| --- | --- | --- | --- | --- | --- |
| S0 | `engine_core_afterburner_segment` | `engine_core` | `engine` | `engine_right` | Aft afterburner+nozzle overlap proxy |
| S1 | `engine_core_hot_section_segment` | `engine_core` | `engine` | `engine_right` | Turbine/combustor mid section |
| S2 | `engine_core_forward_compressor_segment` | `engine_core` | `engine` | `engine_right` | Forward compressor section |
| S3 | `wing_spar_center_left_inner_wing_segment` | `wing_spar_center` | `wings` | `wing_left` | Left inner wing spar |
| S4 | `wing_spar_center_left_root_segment` | `wing_spar_center` | `wings` | `wing_left` | Left root spar |
| S5 | `wing_spar_center_carrythrough_segment` | `wing_spar_center` | `wings` | `fuselage` | Center carrythrough crossing fuselage. P2 decision: this segment structurally belongs to fuselage, not wings. |
| S6 | `wing_spar_center_right_root_segment` | `wing_spar_center` | `wings` | `wing_right` | Right root spar |
| S7 | `wing_spar_center_right_inner_wing_segment` | `wing_spar_center` | `wings` | `wing_right` | Right inner wing spar |

### 2.3 Effective component surface for MLF-6

- **Default database (26 components)**: `engine_core` and `wing_spar_center` are
  single monolithic components. `wing_spar_center` spans both wing groups
  (double-counted in group membership).
- **TG-P7 opt-in (32 components)**: engine and spar split into segments with
  finer spatial resolution; `wing_spar_center_carrythrough_segment` (S5) moves
  to fuselage group.

P2 mapping must produce correct break-mode behavior on both surfaces.

### 2.4 Structural group summary

Each component belongs to exactly one primary structural group, or `none`.
`wing_spar_center` (default) is the sole exception — it is a cross-region
monolithic component that contributes to two groups. This exception is
resolved by the TG-P7 split.

| Group | Default count (26) | TG-P7 count (32) | Triggered break mode |
| --- | --- | --- | --- |
| `wing_left` | 3 + wing_spar_center share | 5 | `wing_loss` |
| `wing_right` | 3 + wing_spar_center share | 5 | `wing_loss` |
| `tail_left` | 1 | 1 | `tail_loss` |
| `tail_right` | 1 | 1 | `tail_loss` |
| `vertical_tail` | 1 | 1 | `tail_loss` |
| `engine_right` | 1 + afterburner_nozzle (tentative) | 4 | `engine_detach` |
| `fuselage` | 2 (center fuel cell, intake duct) | 3 (+ S5 carrythrough) | `fuselage_rupture` |
| `none` | 12 | 13 | — |

Notes:
- `wing_left` and `wing_right` counts include wing-adjacent flight_control
  actuators and fuel cells, not just the spar.
- `engine_left` is empty on F-16C (single engine). `engine_detach` maps to
  `engine_right` group only. MLF-6 state machine must handle this without a
  paired left-engine group.
- `tail_hydraulic_pump` (raw system: `hydraulic`) is classified as `none` —
  it is a hydraulic component, not a structural member. P2 may reclassify.
- `afterburner_nozzle` (raw system: `engine`) is tentatively `engine_right` but
  P2 must decide whether nozzle-only damage without core-engine damage triggers
  `engine_detach`.

## 3. `structural_integrity` Write Sites — Forbidden Touch List

Per D2, MLF-6 must not read or write `AircraftDamageState::structural_integrity`.
The following code sites are the authoritative write surface.

### 3.1 Declaration

| File | Line | Role |
| --- | --- | --- |
| `src/components/domains/air/combat/damage_air.h` | 114 | Declaration: `double structural_integrity = 1.0;` |

### 3.2 Envelope / degradation writes

| ID | File | Line | Write expression | Trigger |
| --- | --- | --- | --- | --- |
| SI-01 | `src/systems/combat/damage_system_air.h` | 54 | `aircraft.structural_integrity -= structural_loss` | Flutter envelope damage (integrity < 0.985) |
| SI-02 | `src/systems/combat/damage_system_air.h` | 180 | `aircraft.structural_integrity -= 0.0060 * fire * dt_s` | Fire damage per tick |
| SI-03 | `src/systems/combat/damage_system_air.h` | 205 | `aircraft.structural_integrity -= ...` | Structural overstress from G-load |

### 3.3 Component-dependency and state-handoff writes

| ID | File | Line | Write expression | Trigger |
| --- | --- | --- | --- | --- |
| SI-04 | `src/components/domains/air/combat/damage_air.h` | 365-366 | `aircraft_damage.structural_integrity = min(aircraft_damage.structural_integrity, availability)` | Component dependency structural cap |
| SI-05 | `src/components/domains/air/combat/damage_air.h` | 458 | `aircraft_damage->structural_integrity -= 0.03 + 0.08 * bounded_impulse` | Ground contact impulse |
| SI-06 | `src/components/domains/air/combat/damage_air.h` | 544 | `state.structural_integrity = clamp(state.structural_integrity, 0.0, 1.0)` | Sanitization clamp |

### 3.4 Effects-model writes (air-domain)

| ID | File | Line | Write expression | Trigger |
| --- | --- | --- | --- | --- |
| SI-07 | `src/models/domains/air/default_effects_air_domain.h` | 218 | `aircraft_damage.structural_integrity -= localized_effect_delta(...)` | Blast structural effect |
| SI-08 | `src/models/domains/air/default_effects_air_domain.h` | 273 | `aircraft_damage.structural_integrity -= localized_effect_delta(...)` | Fragment structural effect |
| SI-09 | `src/models/domains/air/default_effects_air_domain.h` | 351 | `aircraft_damage->structural_integrity -= localized_effect_delta(...)` | Generic localized structural effect |

### 3.5 Effects-model writes (component-damage detail)

Source: `src/models/weapons/detail/default_effects_component_damage_detail.inc`

| ID | File | Line | Write expression | Trigger |
| --- | --- | --- | --- | --- |
| SI-10 | `.../default_effects_component_damage_detail.inc` | 671 | `aircraft_damage->structural_integrity -= 0.06 + 0.10 * impulse` | Puncture mode, `air_structure` system — component-damage impulse path |
| SI-11 | `.../default_effects_component_damage_detail.inc` | 752 | `aircraft_damage->structural_integrity -= 0.015 + 0.05 * impulse` | Puncture mode, `air_structure` system — per-entry effects loop |
| SI-12 | `.../default_effects_component_damage_detail.inc` | 765 | `aircraft_damage->structural_integrity -= 0.015 + 0.05 * impulse` | Cut mode, unconditional (all systems) |
| SI-13 | `.../default_effects_component_damage_detail.inc` | 768 | `aircraft_damage->structural_integrity -= 0.02 + 0.06 * impulse` | Blast-deformation mode, unconditional (all systems) |
| SI-14 | `.../default_effects_component_damage_detail.inc` | 805 | `aircraft_damage->structural_integrity -= 0.035 + 0.11 * impulse` | Structural-weakening mode, unconditional |

### 3.6 Observer / recording reads

| File | Line | Role |
| --- | --- | --- |
| `src/core/interfaces/engagement_event_recorder.h` | 29 | Snapshot field declaration |
| `src/core/engine/simulation_kernel_engagement_event_store.cpp` | 116, 140, 245 | Damage-report state strings and deltas |
| `src/core/engine/simulation_kernel_observation_api.cpp` | 249 | Observation export |
| `src/systems/domains/air/aerodynamics_system.h` | 219 | Read: `clamp(aircraft_damage->structural_integrity, 0.0, 1.0)` — aero modifier |
| `src/systems/combat/damage_system_air.h` | 419, 433, 436 | Read: max_g/min_g/takeoff_speed/landing_speed modifiers |
| `src/components/domains/air/combat/damage_air.h` | 586 | Read: `state.structural_integrity <= 0.35` → forced_landing gate |
| `src/components/domains/air/combat/damage_air.h` | 613 | Read: `min(platform.survivability_margin, aircraft.structural_integrity)` → survivability cap |

### 3.7 Write site summary

| Category | Write count | IDs |
| --- | --- | --- |
| Envelope degradation | 3 | SI-01, SI-02, SI-03 |
| Component-dependency / handoff | 3 | SI-04, SI-05, SI-06 |
| Air-domain effects | 3 | SI-07, SI-08, SI-09 |
| Component-damage detail (.inc) | 5 | SI-10, SI-11, SI-12, SI-13, SI-14 |
| **Total write sites** | **14** | 4 files |

MLF-6 must leave all 14 write sites untouched.

## 4. Forbidden Touch Surfaces — Write Sites in Damage/Effects Path

Per D2, D6, and the acceptance checklist, MLF-6 must not modify any field in
the following ECS components. This section lists the write sites in the
air-combat damage/effects propagation path — the systems and models adjacent
to where `StructuralFailureUpdate` will register (after
`AircraftDamageStateUpdate`). Write sites in unrelated systems (propulsion
control, sensor processing, navigation, etc.) are excluded because MLF-6 has
no code path that would touch them.

### 4.1 FlightModel

Declaration: `src/components/physics/performance.h:3`

All write sites in `src/systems/combat/damage_system_air.h`:

| ID | Line | Field written | Expression |
| --- | --- | --- | --- |
| FM-01 | 423 | `flight_model->max_turn_rate` | `baseline->max_turn_rate * control` |
| FM-02 | 424 | `flight_model->max_accel` | `baseline->max_accel * mobility` |
| FM-03 | 425 | `flight_model->max_climb_rate` | `baseline->max_climb_rate * mobility` |
| FM-04 | 426 | `flight_model->max_g` | `baseline->max_g * structure` |
| FM-05 | 427 | `flight_model->min_g` | `baseline->min_g * structure` |
| FM-06 | 428 | `flight_model->max_speed` | `baseline->max_speed * floor(propulsion_integrity, 0.45)` |
| FM-07 | 431 | `flight_model->min_speed` | `baseline->min_speed * (1.0 + 0.35*(1.0 - structural_integrity))` |
| FM-08 | 434 | `flight_model->takeoff_speed` | `baseline->takeoff_speed * (1.0 + 0.20*(1.0 - structural_integrity))` |
| FM-09 | 437 | `flight_model->landing_speed` | `baseline->landing_speed * (1.0 + 0.25*(1.0 - pitch_control))` |
| FM-10 | 440 | `flight_model->taxi_turn_rate` | `baseline->taxi_turn_rate * yaw_control` |

### 4.2 Propulsion

Declaration: `src/components/physics/dynamics.h:14`

All write sites in `src/systems/combat/damage_system_air.h`:

| ID | Line | Field written | Expression |
| --- | --- | --- | --- |
| PR-01 | 447 | `propulsion->mil_thrust_n` | `baseline->mil_thrust_n * propulsion_scale` |
| PR-02 | 449 | `propulsion->ab_thrust_n` | `max(propulsion->mil_thrust_n, baseline->ab_thrust_n * propulsion_scale)` |

(`propulsion_scale = aircraft_damage_capability_floor(propulsion_integrity, 0.15)`)

### 4.3 Health

Declaration: `src/components/combat/health.h:3`

All write sites in `src/systems/combat/damage_system_air.h`:

| ID | Line | Field written | Expression |
| --- | --- | --- | --- |
| HP-01 | 483 | `health[i].current_hp` | `0.0` (when `loss_state == Lost`) |

### 4.4 PlatformDamageState

Declaration: `src/components/combat/common/damage_common.h:160-172`

Write sites in `src/systems/combat/damage_system_air.h`:

| ID | Line | Field written | Expression |
| --- | --- | --- | --- |
| PD-01 | 472 | `damage[i].fire_severity` | `max(damage[i].fire_severity, fire_progress)` |
| PD-02 | 473 | `damage[i].mission_capability` | `-= 0.0012 * fire_progress * dt_s` |
| PD-03 | 474 | `damage[i].sensor_capability` | `-= 0.0010 * fire_progress * dt_s` |
| PD-04 | 475 | `damage[i].mobility_capability` | `-= 0.0010 * hydraulic_damage * dt_s` |
| PD-05 | 476 | `damage[i].survivability_margin` | `-= ((0.0018*fire + 0.0010*leak + 0.0012*overstress)) * dt_s` |
| PD-06 | 481 | `damage[i].loss_state` | Via `sync_platform_damage_loss_state(health[i], damage[i])` |

`sync_platform_damage_loss_state` (in `src/systems/combat/damage_system_common.h:403-429`)
also writes `health.mission_kill`, `health.mobility_kill`, `health.sensor_kill`.

### 4.5 Forbidden surface summary

| Component | Declaration file | Write site file | Write count |
| --- | --- | --- | --- |
| `FlightModel` | `src/components/physics/performance.h:3` | `damage_system_air.h` | 10 |
| `Propulsion` | `src/components/physics/dynamics.h:14` | `damage_system_air.h` | 2 |
| `Health` | `src/components/combat/health.h:3` | `damage_system_air.h` | 1 |
| `PlatformDamageState` | `src/components/combat/common/damage_common.h:160` | `damage_system_air.h` + `damage_system_common.h` | 6 |
| `structural_integrity` | `damage_air.h:114` | 4 files | 14 |
| **Total forbidden writes** | | | **33** |

## 5. Validation

```bash
# Verify all referenced paths exist
ls src/components/combat/common/damage_common.h
ls examples/config/database/aircraft/units/f16c_block50.json
ls docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.json
ls src/components/domains/air/combat/damage_air.h
ls src/systems/combat/damage_system_air.h
ls src/systems/combat/damage_system_common.h
ls src/models/domains/air/default_effects_air_domain.h
ls src/models/weapons/detail/default_effects_component_damage_detail.inc
ls src/components/physics/performance.h
ls src/components/physics/dynamics.h
ls src/components/combat/health.h

# Verify component count and raw system values
python3 -c "
import json
with open('examples/config/database/aircraft/units/f16c_block50.json') as f:
    db = json.load(f)
names = set()
systems = set()
for hb in db.get('damage_model', {}).get('hitboxes', []):
    for c in hb.get('components', []):
        name = c.get('name', '')
        sys = c.get('system', '')
        if name:
            names.add(name)
            systems.add(sys)
assert len(names) == 26, f'Expected 26, got {len(names)}'
assert systems == {'avionics','cockpit','data_link','engine','flight_control','fuel','hydraulic','navigation','radar','wings'}, f'Unexpected systems: {systems}'
print(f'Default components: {len(names)} — OK')
print(f'Raw system tags: {sorted(systems)}')
"

# Verify structural_integrity write count
echo "Expected: 14 write sites across 4 files"
grep -c 'structural_integrity\s*-=' src/systems/combat/damage_system_air.h src/components/domains/air/combat/damage_air.h src/models/domains/air/default_effects_air_domain.h src/models/weapons/detail/default_effects_component_damage_detail.inc 2>/dev/null
```

## 6. Residuals

- `wing_spar_center` (default DB) is a cross-region monolithic component. It is
  the **only** component that contributes to two structural groups. P2 must
  define how shared components contribute to multi-group break-mode thresholds.
  The TG-P7 split resolves this for the opt-in surface.
- `engine_left` is empty on F-16C (single engine). P2 mapping and P3 state
  machine must handle this without error.
- 5 tentative structural group classifications are flagged for P2 resolution
  (afterburner_nozzle, intake_duct, tail_hydraulic_pump, engine_fuel_control_unit,
  wing_spar_center_carrythrough).
- P2 must define mapping for both default (26) and TG-P7 opt-in (32) surfaces.
- Dependency cascades (e.g. engine fire → spar weakening) are deferred to MLF-7.
- `SI-11` and `SI-12` are on the same code path (blast_deformation mode). If
  they are semantically identical, P2 may count them as one logical write site;
  the inventory conservatively lists every `-=` occurrence.
- `Propulsion` was incorrectly cited as `forces.h` in P1 v1; corrected to
  `dynamics.h` in v2.
