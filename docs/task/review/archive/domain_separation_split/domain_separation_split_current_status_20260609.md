# Domain Separation Split Current Status

Status: `2026-06-10` accepted after direct compatibility-entry retirement and broad architecture guard closure.

Parent: [Domain Separation Split](README.md)

## Summary

The audit has been promoted into an executable subproject. The direct large
split is approved as the planning frame: no Naval demonstration-domain gate is
required before splitting the mixed Air/Naval/Ground ownership hotspots.

The main combat/model ownership hotspots named in the 2026-06-09 dispatch have
implementation evidence now: component ownership, combat damage systems, naval
logistics extraction, effects routing, and sensor routing are implemented and
focused-validated. The old domain-split public compatibility paths are now
retired instead of retained: source consumers include common/domain owner
headers directly, and generic logistics/instrument code uses
`components/physics/propulsion_readouts.h` instead of Air system readout
helpers. The refreshed build, runtime selectors, retired include search,
structural selector, compatibility quarantine, full structural-boundary guard,
and scoped diff check pass. The subproject acceptance gate is satisfied.

DS-P0-B has produced a read-only ownership inventory for the current hotspots.
This inventory is diagnostic fact-gathering only. It is not implementation
acceptance and does not change any cluster status by itself.

## Current Evidence Table

| Surface | Current owner state | Evidence | Status | Next gate |
| --- | --- | --- | --- | --- |
| Subproject docs | Owner surface created | `docs/task/review/domain_separation_split/**` | pass | DS-C1-A / DS-C1-B dispatch |
| Parent review index | Linked | `docs/task/review/README*` | pass | Keep synced during DS-D1-A |
| Air runtime systems | Canonical Air owner; old physics/tuning public paths retired | `src/systems/domains/air/**`, `src/components/domains/air/platform/**`; deleted old physics/tuning paths | pass | Focused build/guard evidence refreshed |
| Combat damage data | Domain-owned headers; old public aggregate retired | `src/components/combat/{common,air,naval,ground}/damage_*.h`; deleted `src/components/combat/damage.h` | pass | Include guard evidence refreshed |
| Combat damage ECS | Domain-owned system headers; old public registrar retired | `src/systems/combat/damage_system_{common,air,naval,ground}.h`; deleted `src/systems/combat/damage_system.h` | pass | Include guard evidence refreshed |
| Weapon data | Domain-owned headers; old public aggregate retired | `src/components/combat/{common,air,naval,ground}/weapon_*.h`; deleted `src/components/combat/weapon.h` | pass | Include guard evidence refreshed |
| Naval logistics | Naval underway resupply owned in `systems/domains/naval`; generic readouts use physics helper | `src/systems/domains/naval/naval_logistics_system.h`; `src/systems/systems/logistics_system.h`; `src/components/physics/propulsion_readouts.h`; `src/core/engine/simulation_kernel_systems.cpp` | pass | Focused build evidence refreshed |
| Effects model | Generic router with Air/Naval/Ground owner paths | `src/models/weapons/detail/default_effects_domain_routing_detail.inc`; `src/models/domains/air/default_effects_air_domain.h`; `src/models/domains/naval/default_effects_naval_domain.h`; `src/models/domains/ground/default_effects_ground_domain.h` | pass | Naval/Ground paths are placeholders only |
| Sensor model | Generic sensor routes ship-specific reads through Naval adapter | `src/models/systems/default_sensor_model.cpp`; `src/models/domains/naval/naval_sensor_maritime_adapter.h` | pass | Acoustic model `ShipPlatform` access is outside DS-M1-B |
| Architecture guards | Focused domain split guard updated for retired paths; broad architecture guards pass | `tests/architecture/structural_boundaries/test_structural_guardrails.py`; `tests/architecture/compatibility_quarantine/test_guard_enforcement.py` | pass | Full structural-boundary and compatibility quarantine selectors pass |

## DS-P0-B Inventory

This section records read-only `rg` / file-inspection facts from the 2026-06-09
working tree before code edits. It identifies likely target owners and next
clusters, but it is not proof that any split has been implemented or accepted.

| Hotspot | Target owner | Current coupling | Direct evidence | Recommended next cluster |
| --- | --- | --- | --- | --- |
| `src/components/combat/damage.h` | Common damage primitives plus Air/Naval/Ground component-owned headers. | `DamageComponent`, `Hitbox`, `ComponentDamageState`, `SystemHealth`, and `PlatformDamageState` share the same generic header with Air-specific vulnerability/state/baseline types. Naval flooding is embedded in `PlatformDamageState`; Ground damage has no owner type here. | `rg` shows `AircraftVulnerabilityEvidenceRow` at line 118, `AircraftVulnerabilityProfile` at 170, `SystemHealth` at 230, `ComponentDamageState` at 236, `PlatformDamageState` at 270, `flooding_severity` at 275, `ongoing_hull_breach` at 277, `AircraftDamageState` at 284, `AircraftDamageBaseline` at 704, `clamp_aircraft_damage_state` at 727, and `apply_aircraft_damage_state_to_platform` at 794. No `GroundDamage` / ground-owned damage type appears in this header. | `DS-C1-A` first; downstream consumers should wait for the split surface. |
| `src/systems/combat/damage_system.h` | Common fuze / event routing plus Air/Naval/Ground update systems behind domain-owned headers or adapters. | One header includes `components/combat/damage.h`, `components/combat/weapon.h`, `components/domains/naval/platform/ship_platform.h`, physics, logistics, sensors, EW, and effects interfaces. One `register_damage_system` owns common `ProximityFuze`, Air `AircraftDamageStateUpdate`, and Naval `NavalDamageStateUpdate`; no Ground update path is present. | `rg` shows the naval include at line 19, `register_damage_system` at 1171, `ProximityFuze` at 1172, `AircraftDamageStateUpdate` at 1690 gated by `UnitType::Aircraft` / `UnitType::C2Node`, and `NavalDamageStateUpdate` at 1840 over `ShipPlatform`. Air helper blocks include structural envelope, sensor, fuel leak, cascade, and component dependency consumers at lines 758-1124. | `DS-S1-A`, after `DS-C1-A` stabilizes the public component surface. |
| `src/components/combat/weapon.h` | Common weapon profiles/runtime, Air release state, Naval weapon system state, and future Ground weapon owner shells. | `WarheadProfile`, `FuzeProfile`, and `Missile` are generic but air-shaped through seeker/guidance/fuze runtime. `PilotWeaponReleaseState` and naval weapon types live in the same generic file; Ground weapon ownership is absent. | `rg` shows `WarheadProfile` at line 14, `FuzeProfile` at 24, `Missile` at 71, `MissileSharedLaunchRuntimeState` at 164, `PilotWeaponReleaseState` at 296, `NavalWeaponType` at 306, `NavalWeaponMountDefinition` at 313, and `NavalWeaponSystem` at 332. No `GroundWeapon` or ground-owned weapon type appears in this header. | `DS-C1-B`. |
| `src/systems/systems/logistics_system.h` | Common/base logistics plus Air fuel-consumption ownership or adapter, and Naval underway resupply in `systems/domains/naval`. | `FuelConsumption` lives in the generic platform-system file but includes `systems/domains/air/propulsion_system.h` and calls `flight_dynamics::propulsion_fuel_flow_kg_per_s`. `ResupplyLogic` is a common/base loop with plane/ground assumptions and a `ResupplyState` that already carries naval fields. `NavalUnderwayResupply` is a naval ECS body inside the generic file. | `rg` shows the Air include at line 16, `FuelConsumption` at 20, `MassUpdate` at 64, `LogisticsAction` at 90, `ResupplyLogic` at 111, and `NavalUnderwayResupply` at 189. `components/systems/logistics.h` defines `NavalStores`, `ResupplyKind::NavalUnderway`, and `NavalResupplyStage` at lines 57-88. | `DS-S1-C` for naval extraction; `DS-S1-B` must verify the Air fuel-flow dependency/wrapper policy. |
| `src/models/weapons/default_effects_model.cpp` and `detail/*.inc` | Common effects router plus Air/Naval/Ground model-owned detail implementations. | The main model includes `components/combat/damage.h` and routes structured damage only through `is_structured_damage_air_target`; non-structured targets use legacy health/randomized fallback. Detail files are common geometry/warhead helpers plus Air platform resolution; no Naval/Ground detail path exists. | `rg --files` lists 10 detail fragments. The main file includes `default_effects_air_platform_resolution_detail.inc` at line 62. `is_structured_damage_air_target` at lines 32-42 requires `UnitType::Aircraft` / `UnitType::C2Node`, `HitboxConfig`, `SystemHealth`, and `PlatformDamageState`. `rg 'Naval|Ground|Ship|ship|naval|ground'` over the main file and detail fragments returns no matches. Air evidence appears in `default_effects_state_detail.inc` (`processed_air_systems`, Air hit flags) and `default_effects_air_platform_resolution_detail.inc` (`AircraftDamageState`, `AircraftVulnerabilityProfile`, platform consequence blocks). | `DS-M1-A`, after `DS-C1-A` and `DS-S1-A` settle shared damage/effects surfaces. |
| `src/models/systems/default_sensor_model.cpp` | Common sensor model with a Naval maritime adapter/router for ship-specific state. | The generic sensor model directly includes `components/domains/naval/platform/ship_platform.h`, reads `ShipPlatform` for maritime state, checks `UnitType::Ship` for sea clutter, and reads target ship height for radar horizon. | `rg` shows the naval include at line 5, `entity.get<ShipPlatform>()` in `maritime_state_for` at line 143, ship sea-state fields at lines 149-151, `target_is_ship` / `UnitType::Ship` at lines 173-174, and target `ShipPlatform` height use at lines 359-360. | `DS-M1-B`. |
| Air partial candidate: `src/systems/domains/air`, `src/components/air`, old wrappers | Canonical Air runtime and tuning ownership under `systems/domains/air` / `components/air`, with old physics paths as compatibility wrappers only. | Air owner directories exist and are used directly by `simulation_kernel_systems.cpp`, `content/unit_definition.h`, Python bindings, and model factory. Old `systems/physics/{aero_state,aerodynamics,control,propulsion}_system.h` and `components/physics/flight_dynamics_tuning.h` are include-only wrappers. The candidate is still partial because Air systems still consume `components/combat/damage.h` for `AircraftDamageState`, and generic physics/logistics files include `systems/domains/air/propulsion_system.h`. | `rg --files` lists `src/systems/domains/air/{aero_state_system.h,aerodynamics_system.h,control_system.h,propulsion_system.h}` and `src/components/domains/air/platform/flight_dynamics_tuning.h`. Wrapper inspection shows each old air physics header only includes the new Air header. Include use shows `simulation_kernel_systems.cpp` includes the Air headers directly at lines 36-44 and registers Air systems at lines 182-187; `systems/domains/air/aerodynamics_system.h` and `propulsion_system.h` still include `components/combat/damage.h`. | `DS-S1-B` verification now; coordinate with `DS-C1-A` for the Air damage type include dependency. |

## Known Worktree Risk

The DS-P0-B inventory above is a historical `2026-06-09` snapshot taken before
the implementation clusters landed. It should not be re-read as the current code
state after DS-S1-C / DS-M1. Future tracking should validate the domain-split
paths by pathspec and keep unrelated review/test archive movement out of the
acceptance decision.

## Non-Blocking Follow-Up

1. Keep Naval/Ground effects paths documented as placeholder ownership shells; do not claim full domain damage fidelity.
2. Plan later Ground movement/sensing/fires/damage implementation packages if full Ground runtime maturity is required.
3. Keep calibration and realism upgrades separate from this ownership split.

## Status Legend

- `active`: execution surface exists and is being prepared.
- `planned`: finite cluster exists but has not started.
- `partial`: implementation candidate exists but is not accepted.
- `held`: known hotspot with no accepted split.
- `pass`: cluster met its closure gate.
- `accepted`: subproject-level acceptance gate is satisfied.
