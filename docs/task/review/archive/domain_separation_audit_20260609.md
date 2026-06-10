# Domain Separation Audit — 2026-06-09

## Scope

Assessment of Air / Naval / Ground domain separation across the three C++ layers: `components/`, `systems/`, and `models/`. Evaluates whether the current implementation conforms to the `foundation → bridge → joint → services → air/naval/ground` layering defined in `docs/standards/`.

## Overall Verdict

**The `command` and `tasking` layers already demonstrate that per-domain subdirectory splitting is feasible, but the `combat` and `physics` layers lag significantly.** The most severe issue is that `damage.h` + `damage_system.h` (2,720 lines combined) cram Air/Naval damage data structures and ECS system logic into the same two files, while the Ground domain is completely missing.

---

## 1. Properly Separated Areas

| Layer | Path | Separation |
|-------|------|------------|
| components/command | `air/` `common/` `ground/` `naval/` | Per-domain subdirectories with README |
| components/tasking | `air/` `common/` `ground/` `naval/` | Per-domain subdirectories |
| components/naval | `ship_platform.h` `submarine_platform.h` `embarked_air_ops.h` | Dedicated naval directory |
| systems/domains/naval | 5 files + README | Dedicated naval system directory |
| models/domains/air | `default_control_model.cpp` + README | Dedicated air model directory |

## 2. Domain Coupling Hotspots

### Hotspot 1: `damage.h` + `damage_system.h` — Largest Multi-Domain Monolith

**Files**: `src/components/combat/damage.h` (843 lines) + `src/systems/combat/damage_system.h` (1,877 lines)

| Domain | Data Structures | % of damage.h | ECS System | % of damage_system.h |
|--------|----------------|---------------|------------|----------------------|
| **Air** | `AircraftDamageState` (31 fields), `AircraftVulnerabilityProfile`, `AircraftDamageBaseline` | ~60% | `AircraftDamageStateUpdate` ~150 lines | ~60% |
| **Naval** | `PlatformDamageState` (reused, with `flooding_severity`, `ongoing_hull_breach`) | ~10% | `NavalDamageStateUpdate` 35 lines | ~3% |
| **Common** | `SystemHealth`, `Hitbox`, `ComponentDamageState`, `PlatformLossState` | ~30% | `ProximityFuze`, hit geometry, coordinate transforms | ~37% |
| **Ground** | **Does not exist** | 0% | **Does not exist** | 0% |

**Key issues**:

- 70% of `damage.h` is aviation-specific logic masquerading as a cross-domain component under `components/combat/`
- `PlatformDamageState` has only 8 fields; `flooding_severity` and `ongoing_hull_breach` are naval-specific but hardcoded into the "generic" state
- Naval ECS system is only 35 lines: basic fire/flooding/breach decay, no compartment flooding graph, damage control parties, watertight integrity, or magazine explosion risk
- Ground domain has zero damage data structures or ECS systems

### Hotspot 2: `weapon.h` — Air + Naval Types Mixed

**File**: `src/components/combat/weapon.h`

```
├── Missile, FuzeProfile, WarheadProfile    ← generic (but air-shaped)
├── PilotWeaponReleaseState                  ← air-only
├── NavalWeaponType                          ← naval-only (mixed into generic file)
├── NavalWeaponMountDefinition               ← naval-only
├── NavalWeaponSystem                        ← naval-only
└── (GroundWeapon: none)
```

### Hotspot 3: `logistics_system.h` — Air + Naval ECS Systems Mixed

**File**: `src/systems/systems/logistics_system.h`

| ECS System | Domain | Notes |
|------------|--------|-------|
| `FuelConsumption` | Air | |
| `LogisticsAction` | Common | |
| `MassUpdate` | Common | |
| `NavalUnderwayResupply` | **Naval** | Mixed into generic file |
| `ResupplyLogic` | Common | Contains naval-specific state machine |

### Hotspot 4: `default_sensor_model.cpp` — Ship-Specific Code in Generic Sensor

**File**: `src/models/systems/default_sensor_model.cpp`

```cpp
#include "components/domains/naval/platform/ship_platform.h"   // Generic sensor depends on naval component

// Radar sea clutter (hardcoded in generic sensor)
state.sea_state = std::max(0.0, ship->sea_state);

// Domain check in generic code
const bool target_is_ship = target_key && target_key->type == UnitType::Ship;
```

### Hotspot 5: `default_effects_model.cpp` — Detail Files Are All Air-Specific

**File**: `src/models/weapons/default_effects_model.cpp` + `detail/` (10 `.inc` files)

The only branching path in the main `.cpp` is air vs legacy (HP subtraction). There are no naval/ground-specific detail files and no naval/ground damage resolution paths.

### Hotspot 6: Air-Only Physics Systems in Generic `systems/physics/`

| File | Actual Domain | Evidence |
|------|---------------|----------|
| `aerodynamics_system.h` | Air-only | Directly reads `AircraftDamageState` |
| `control_system.h` | Air-only | FlightControl, FBW protection |
| `propulsion_system.h` | Air-only | `AircraftDamageState::propulsion_integrity` drives thrust degradation |
| `aero_state_system.h` | Air-only | Aero state computation |
| `flight_dynamics_tuning.h` | Air-only | `AeroTuning` struct (CL/CD/CM curves) |

These files exist at the same abstraction level as `systems/domains/naval/ship_motion_system.h` but lack a `systems/domains/air/` directory.

---

## 3. Domain Separation Landscape

```
                        components/          systems/            models/
                        ───────────          ────────            ───────
command/tasking         ✅ air/common/       N/A                 N/A
                           naval/ground

Air     dedicated       ❌ no air/ dir       ❌ no air/ dir       ✅ air/
        actual loc      combat/damage.h      physics/aerodynamics  default_control
                        combat/weapon.h       physics/control       effects scattered
                                              physics/propulsion
                                              combat/damage_system

Naval   dedicated       ✅ naval/            ✅ naval/            ❌ no naval/
        actual loc      combat/damage.h      combat/damage_system  effects shared
                        combat/weapon.h       systems/logistics    sensor embedded

Ground  dedicated       ❌ no ground/ comp   ❌ no ground/ sys    ❌ no ground/ model
        actual loc      (completely missing)  (completely missing)  (completely missing)
```

---

## 4. Migration Priorities

| Priority | Change | Rationale |
|----------|--------|-----------|
| **P0** | Split `damage.h` → `damage_air.h` + common `damage.h` | 843-line monolith, 60% air-specific |
| **P0** | Split `damage_system.h` → `damage_system_air.h` + `damage_system_naval.h` | 1,877-line monolith |
| **P1** | Create `systems/domains/air/`, move aerodynamics/control/propulsion/aero_state | 4 air-only systems disguised as generic physics |
| **P1** | Split `weapon.h` → extract `weapon_naval.h` | Air/Naval types mixed |
| **P1** | Create `components/domains/ground/combat/` + `systems/domains/ground/` | Completely missing |
| **P2** | Split `NavalUnderwayResupply` from `logistics_system.h` → `systems/domains/naval/` | Localized mixing |
| **P2** | Remove `ShipPlatform` dependency from `default_sensor_model.cpp` | Generic sensor should not know about ShipPlatform |
| **P2** | Create `models/domains/naval/` + `models/domains/ground/`, add domain detail files | Complete model layer coverage |

---

## 5. Naval as Exemplar Domain

The `command` and `tasking` layers already demonstrate that per-domain subdirectory splitting is feasible. Naval has the most complete structural separation at the systems layer (5 independent system files + README), lacking only the models layer and combat components. Completing Naval's three-layer structure would provide a reference template for subsequent Air and Ground refactoring.

---

*Audit based on 2026-06-09 working tree. All file references and line counts are reproducible.*
