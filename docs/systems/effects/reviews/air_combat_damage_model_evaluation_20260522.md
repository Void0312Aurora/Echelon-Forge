# Air Combat Damage Model — Evaluation And Realistic Upgrade Recommendation

Language:
- English canonical: `air_combat_damage_model_evaluation_20260522.md`
- Chinese companion: not available.

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/effects/reviews/air_combat_damage_model_evaluation_20260522.md`
Owner: `systems/effects`
Last verified: `2026-05-22`
Review basis: `2026-05-22`
Review status: advisory snapshot; factual claims were not reverified during the
2026-08-07 ownership migration.

Historical path note: `src/components/combat/damage.h` and
`src/systems/combat/damage_system.h` were later removed. Their names below are
snapshot evidence labels, not live links. Current code is split across
[damage_common.h](../../../../src/components/combat/common/damage_common.h) and
[damage_system_common.h](../../../../src/systems/combat/damage_system_common.h),
but this review does not claim line-level equivalence.

Status: `2026-05-22` compiled from full engagement/damage pipeline audit.

## Design Stance

This track is a high-fidelity simulation track, not an RL-convenience track.
Training stability, short smoke episodes, and legacy `health > 0` callers are
secondary integration concerns. They must adapt to the damage model rather than
define it.

Non-negotiable principles:

- `Health.current_hp` is not a kill model. It may remain as a derived
  compatibility/readout field, but it must not be the primary effects or kill
  authority for air combat.
- Weapon effects originate from a detonation/impact event: fuze state, miss
  distance, relative geometry, warhead family, fragment/blast/rod distribution,
  and target vulnerability.
- Damage first mutates local structure and subsystems. Platform-level kill
  state is derived from those mutations.
- A target can be combat-ineffective without being physically destroyed.
  Mission kill, sensor kill, mobility kill, forced landing, and catastrophic
  loss are distinct outcomes.
- Randomness is allowed only when it represents explicitly modeled uncertainty
  or stochastic physical sampling. It must not hide missing geometry or missing
  vulnerability data.
- RL reward shaping and curriculum shortcuts must consume the resulting
  `EffectsEvent`, `DamageReport`, and platform state. They must not feed back
  into the physical damage authority.

## 0. Phase 0 Preconditions

Phase 1 does not start until these audits are closed and recorded:

| Gate | Why it matters | Current audit result |
|---|---|---|
| `PlatformLossState` naked integer audit | Enum extension must not silently break old serialized or numeric comparisons | No direct code-level naked comparison surfaced in the current textual grep, but this remains a hard gate |
| Python health observer audit | Existing `health > 0` and `is_unit_active()` callers will see different semantics once HP becomes derived | Broad surface confirmed across RL runtime, contract tests, and air-combat tests |
| `ShipPlatform` consumer audit | The damage system filter cannot be changed casually because `ShipPlatform` is used by other ship-only systems | `NavalDamageStateUpdate` is the blocker; other `ShipPlatform` consumers are legitimate and must remain intact |
| Aircraft JSON inventory | Phase 1 needs authored hitboxes or an explicitly documented generated fallback | Aircraft types currently include `F-16C_Block50`, `MH-60R_MVP`, `E-3_Sentry_AWACS`, `MQ-9_Reaper`, `Su-35S_Flanker-E` |
| `Score` write-point audit | Reward writes must move out of physical effects resolution | Score writes exist in `default_effects_model.cpp` and `simulation_kernel_weapon_api.cpp` |
| PN miss-distance baseline matrix | Deterministic fuze work is not defensible without measured miss-distance distributions | No dedicated head-on / tail-chase / beam / high-off-boresight matrix exists yet |

Phase 0 acceptance means the planning is backed by concrete callsites and
baseline evidence, not just by intent.

## 1. Current State

### 1.1 Two Parallel Damage Paths

The damage system has a split personality:

| | Path A — "Legacy Air" | Path B — "Naval Subsystem" |
|---|---|---|
| **Trigger** | `Health` component present, no `HitboxConfig` | `HitboxConfig` + `SystemHealth` + `PlatformDamageState` present |
| **Damage model** | `hp -= missile.damage` | Subsystem health reduction -> cascading capability loss |
| **Kill condition** | `hp <= 0` -> instant destruct | Progressive: mission_kill -> mobility_kill -> sensor_kill -> Lost |
| **Hit location** | Ignored (scalar damage only) | Body-frame coordinate hitbox intersection |
| **Critical hits** | None | Yes — per-system effects (fuel leak, radar degradation, engine thrust loss) |
| **Persistent damage** | None | Fire propagation, flooding growth, hull breach spread |
| **Armor** | `armor_mm` field loaded but **never read** | Same — field exists, unused |
| **Kill levels** | Binary (alive/dead) | 4-tier: CombatCapable → MissionKill → MobilityKill/SensorKill → Lost |
| **Used by** | Aircraft, legacy units | Ships (naval domain) |

**Critical finding**: the maintained air-combat path still allows the legacy
HP-first branch to decide the outcome before subsystem effects can matter. An
AIM-120C-class hit can still collapse to `hp -= damage`, with no authoritative
answer to where the missile detonated, which structures were cut, which systems
lost function, or whether the aircraft is mission-killed rather than destroyed.
That branch is structural, not accidental, and it is unacceptable as the
authority for a high-fidelity 1v1 air-combat simulation.

### 1.2 Proximity Fuze Hit Resolution

Historical file: `src/systems/combat/damage_system.h`

```
quality = 1.0 - min_dist / fuse_distance    // [0, 1] — how close the pass was
hit_prob = (0.35 + 0.65*quality)             // base hit probability
         * (1.0 - 0.3*evasion)               // target evasion modifier
hit_prob = clamp(hit_prob, 0.05, 0.98)       // bounded
damage   = base_damage * (0.6 + 0.4*quality) // near-miss does partial damage
```

This is a useful diagnostic abstraction but not an adequate high-fidelity fuze
or effects authority:
- RNG-based hit/miss with a flat random roll -- real fuze logic is governed by
  relative geometry, sensor/fuze timing, miss distance, detonation timing, and
  warhead pattern rather than a post-hoc dice roll
- Evasion is derived from `ActionCommand::turn_rate_cmd` rather than actual maneuver state (g-load, aspect angle)
- No differentiation between radar-guided and IR-guided missile fuze behavior
- No consideration of target aspect (head-on vs tail-chase vs beam engagement geometry)

### 1.3 What's Configurable Per Weapon

The JSON weapon definitions support 35+ parameters — [see examples](../../../../examples/config/database/weapons/air_to_air/). The key ones for damage are:

| Parameter | AIM-120C | AIM-9X | R-77-1 |
|-----------|----------|--------|--------|
| Warhead mass (kg) | 20 | 9.4 | 22 |
| Lethal radius (m) | 15 | 8 | 18 |
| `damage` scalar | 120 (default) | 120 (default) | 120 (default) |
| Warhead type | `Frag` | `Frag` | `Frag` |

The `damage` field is loosely mapped from warhead mass (see
`unit_definition_loader.cpp`) but is **not physically grounded**: there is no
blast impulse model, no fragment/rod pattern, no vulnerability model, and no
explicit kill-state derivation from damaged subsystems.

---

## 2. What's Missing — Unrealistic Gaps

### 2.1 No Subsystem Damage For Aircraft

A missile hit on an aircraft's wingtip should have different consequences than a hit on the cockpit, engine, or fuel tank. Currently all hits are identical.

Realistic aircraft subsystems that should be modeled:
- **Flight controls**: aileron/elevator/rudder damage → reduced maneuverability
- **Engine(s)**: single-engine failure → reduced thrust, asymmetric thrust
- **Fuel system**: fuel leak → reduced range/endurance, fire risk
- **Avionics/radar**: sensor degradation → reduced SA, loss of BVR capability
- **Hydraulics**: control surface loss → progressive handling degradation
- **Structure**: wing spar damage → g-load limit reduction
- **Cockpit/pilot**: pilot injury → degraded decision-making or immediate loss

### 2.2 No Kill-Level Progression For Aircraft

Real air combat has distinct kill levels:
- **Catastrophic kill (K-Kill)**: aircraft disintegrates — pilot must eject
- **Mission kill**: aircraft cannot complete mission but may be flyable (e.g., radar destroyed, fuel leak forcing early RTB)
- **Maneuver kill**: aircraft can fly but cannot maneuver effectively (control surface damage)
- **Forced landing**: aircraft damaged but recoverable to nearest base

Current system: HP > 0 = fully operational. HP <= 0 = instantly destroyed with "SPLASH!" and +1000 reward.

### 2.3 Armor/Penetration Loaded But Unused

`Hitbox::armor_mm` is parsed from JSON but **never referenced in any damage calculation**. All hits penetrate fully regardless of armor. For air combat this is partially defensible (modern AAMs typically achieve catastrophic kill on fighter-sized targets), but for ground attack (A-10 vs tanks) or naval aviation, armor penetration is critical.

### 2.4 Single Damage Scalar

Warhead effects are collapsed into a single `damage` number. Real warheads have:
- **Blast overpressure**: decays with distance, affected by ambient pressure (altitude)
- **Fragmentation**: pattern, velocity, mass distribution
- **Continuous rod**: expanding ring — different damage mechanism entirely
- **Hit-to-kill (HTK)**: kinetic energy transfer, no warhead at all

### 2.5 No pk Curve Integration

Real weapon effectiveness assessment uses Probability of Kill (pk) curves — functions of:
- Engagement geometry (aspect angle, closure rate)
- Target type and vulnerability
- Warhead characteristics
- Fuze characteristics

The current system computes pk from a linear quality function + RNG rather than a weapon-specific pk curve.

### 2.6 No Structural Failure Modeling

Aircraft have structural limits (g-load, flutter boundaries). Battle damage should reduce these limits. Currently:
- `Propulsion::mil_thrust_n` and `ab_thrust_n` are reduced at 50% engine health (Path B, naval only)
- Air units have no structural model to degrade

---

## 3. What Already Exists That Can Be Reused

The naval damage infrastructure provides a solid foundation:

| Component | File | Current Use | Reuse Potential |
|-----------|------|-------------|-----------------|
| `Hitbox` | `src/components/combat/damage.h` | Naval ships only | **Directly reusable** — aircraft just need different hitbox layouts |
| `SystemHealth` | `src/components/combat/damage.h` | Naval ships only | **Directly reusable** — map aircraft systems instead of ship systems |
| `PlatformDamageState` | `src/components/combat/damage.h` | Naval ships only | **Directly reusable** — same capability dimensions apply to aircraft |
| `PlatformLossState` | `src/components/combat/damage.h` | 4-tier: CombatCapable → Kill → Lost | **Directly reusable** — add ForcedLanding for aircraft |
| `DamageReport` | [engagement_contracts.h](../../../../src/runtime/contracts/engagement_contracts.h) | All domains | **Already cross-domain** |
| `EffectsEvent` | [engagement_contracts.h](../../../../src/runtime/contracts/engagement_contracts.h) | All domains | **Already cross-domain** |
| Hitbox geometry loader | [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp) | Naval + loaded for all | **Already loads for aircraft** — just not consumed |
| Proximity fuze system | `src/systems/combat/damage_system.h` | All missiles | **Already cross-domain** — needs location-aware damage routing |
| `IEffectsModel` interface | [effects_model.h](../../../../src/core/interfaces/effects_model.h) | Abstract | **Extension point** — add aircraft-specific model |
| Naval damage state update | `src/systems/combat/damage_system.h` | Ships only | **Template** — create aircraft damage state update |

---

## 4. Recommended Architecture

### 4.1 Unified Multi-Domain Damage Model

Replace the two-path split with a **unified event-driven physical effects
model**. Capability state is an output of the physical damage model, not the
model itself:

```
Weapon event (impact/proximity detonation/self destruct)
    │
    ├──→ Fuze solution
    │     ├── nearest approach and relative velocity
    │     ├── detonation delay and lead timing
    │     └── valid / dud / late / self-destruct state
    │
    ├──→ Warhead field
    │     ├── blast impulse / overpressure
    │     ├── fragment cloud or continuous-rod ring
    │     └── directional pattern and density at target
    │
    └──→ Target vulnerability projection
          ├── exposed area by aspect
          ├── structure/hitbox intersection
          ├── armor / skin / spar / engine / avionics vulnerability
          └── local penetration and energy deposition
                    │
                    ├── SystemHealth reduction per subsystem
                    ├── structural integrity and failure-margin updates
                    ├── cascading capability effects
                    │     ├── Propulsion (thrust reduction, flameout, fire)
                    │     ├── Flight controls (surface loss, actuator lag)
                    │     ├── Sensors (range/SNR/track degradation)
                    │     ├── Fuel (leak, fire, starvation)
                    │     ├── Structure (g-limit and flutter-boundary loss)
                    │     └── Pilot / cockpit / life-support effects
                    │
                    └── PlatformDamageState / PlatformLossState evaluation
                          ├── CombatCapable
                          ├── MissionKill
                          ├── SensorKill
                          ├── MobilityKill
                          ├── ForcedLanding
                          └── Lost
```

### 4.2 Aircraft Hitbox Template

Each aircraft type should define hitboxes in body-frame coordinates, mirroring the naval pattern:

```json
{
  "hitboxes": [
    {
      "name": "cockpit",
      "center": {"forward_m": 4.0, "right_m": 0.0, "up_m": 1.5},
      "half_extents": {"forward_m": 1.2, "right_m": 0.6, "up_m": 0.6},
      "armor_mm": 0,
      "protected_systems": ["pilot", "avionics", "flight_controls"]
    },
    {
      "name": "engine_left",
      "center": {"forward_m": -2.0, "right_m": -1.5, "up_m": 0.5},
      "half_extents": {"forward_m": 2.0, "right_m": 0.8, "up_m": 0.8},
      "armor_mm": 5,
      "protected_systems": ["engine_left", "fuel", "hydraulics"]
    },
    {
      "name": "engine_right",
      "center": {"forward_m": -2.0, "right_m": 1.5, "up_m": 0.5},
      "half_extents": {"forward_m": 2.0, "right_m": 0.8, "up_m": 0.8},
      "armor_mm": 5,
      "protected_systems": ["engine_right", "fuel", "hydraulics"]
    },
    {
      "name": "wing_left",
      "center": {"forward_m": 0.0, "right_m": -3.5, "up_m": 0.0},
      "half_extents": {"forward_m": 3.0, "right_m": 0.5, "up_m": 0.3},
      "armor_mm": 0,
      "protected_systems": ["fuel_left", "aileron_left", "flaps_left", "structure"]
    },
    {
      "name": "wing_right",
      "center": {"forward_m": 0.0, "right_m": 3.5, "up_m": 0.0},
      "half_extents": {"forward_m": 3.0, "right_m": 0.5, "up_m": 0.3},
      "armor_mm": 0,
      "protected_systems": ["fuel_right", "aileron_right", "flaps_right", "structure"]
    },
    {
      "name": "fuselage",
      "center": {"forward_m": 0.0, "right_m": 0.0, "up_m": 0.0},
      "half_extents": {"forward_m": 5.0, "right_m": 1.0, "up_m": 1.0},
      "armor_mm": 3,
      "protected_systems": ["avionics", "fuel_main", "hydraulics", "structure"]
    },
    {
      "name": "radome",
      "center": {"forward_m": 5.5, "right_m": 0.0, "up_m": 0.3},
      "half_extents": {"forward_m": 1.0, "right_m": 0.4, "up_m": 0.4},
      "armor_mm": 0,
      "protected_systems": ["radar"]
    }
  ]
}
```

### 4.3 Aircraft Subsystem → Capability Mapping

| Subsystem | Capability Affected | Effect at 50% Health | Effect at 0% Health |
|-----------|-------------------|----------------------|---------------------|
| radar | sensor_capability | max_range × 0.5 | radar inoperative |
| rwr/ecm | sensor_capability | detection range × 0.5 | electronic warfare blind |
| engine (single) | mobility_capability | thrust × 0.5 | engine dead |
| engine (twin, one hit) | mobility_capability | thrust × 0.7 + asymmetric thrust | single-engine ops |
| flight_controls | mobility_capability | roll/pitch/yaw rate × 0.7 | limited to trim-only flight |
| fuel system | mission_capability | fuel_leak += 5 kg/s | forced RTB in ~2 min |
| structure (spar) | survivability_margin | g-limit × 0.6 | risk of structural failure above 3g |
| structure (skin) | survivability_margin | flutter boundary reduced | progressive structural failure |
| avionics | mission_capability | navigation degraded | IFR/combat incapable |
| pilot | all capabilities | +100ms decision delay | pilot incapacitated |
| hydraulics | mobility_capability | control surface rate × 0.5 | manual reversion only |

### 4.4 Unified Kill-Level System

Keep the shared loss-state vocabulary stable. If an aircraft-only
`ForcedLanding` outcome is needed, add it append-only or model it as a separate
aircraft overlay state. Do not renumber existing shared values.

```
CombatCapable → MissionKill → MobilityKill / SensorKill → ForcedLanding → Lost
```

| Kill Level | Primary Condition | Aircraft Behavior |
|-----------|-------------------|-------------------|
| MissionKill | mission-critical systems below threshold, or task cannot be completed with remaining fuel/sensors/weapons | Cannot continue assigned mission; RTB or diversion logic becomes dominant |
| SensorKill | radar/EO/RWR/datalink capability below threshold | Cannot detect, track, or employ relevant weapons effectively |
| MobilityKill | propulsion/control/structure margin below threshold | Cannot maneuver or remain inside the required flight envelope |
| ForcedLanding | still controllable but survivability, fuel, or fire margin is below recovery threshold | Must divert or descend; combat task is over |
| Lost | catastrophic structural failure, pilot incapacitation, unrecoverable fire/explosion, or aircraft inactive | Aircraft destroyed or unrecoverable |

Reward or curriculum mapping belongs in a separate consumer layer that reads
`EffectsEvent`, `DamageReport`, and platform state. It does not belong in the
physical damage authority.

### 4.5 Warhead Model Enhancement

Replace the single `damage` scalar with a warhead profile:

```cpp
struct WarheadProfile {
    double explosive_mass_kg;        // TNT-equivalent
    double fragmentation_angle_deg;  // Frag pattern cone angle (360 = omnidirectional)
    double fragmentation_velocity_mps;
    double fragment_mass_g;          // Average fragment mass
    double fragment_count;
    double continuous_rod_radius_m;  // 0 if not CR warhead
    WarheadType type;                // BlastFrag, ContinuousRod, HitToKill, HE
};
```

Blast overpressure decays as: `P(r) = P0 * (r / r0)^(-n)` where n ≈ 1.5-2.0 for free-air blast.

Fragmentation hit probability: `p_hit = min(1.0, fragment_density_at_range * target_presented_area)`.

### 4.6 Deterministic Fuze Model

Replace the RNG-based hit probability with a geometry-first fuze/effects model.
The minimum acceptable version is deterministic, but this work is deferred until
the PN miss-distance baseline matrix exists:

```
if (min_dist <= lethal_radius):
    guaranteed_damage_factor = 1.0  // within guaranteed kill zone
elif (min_dist <= 2 * lethal_radius):
    guaranteed_damage_factor = (2 * lethal_radius - min_dist) / lethal_radius
    // decreasing damage out to 2× lethal radius
else:
    // miss — no damage
```

This eliminates the post-hoc hit dice. Evasion affects the missile's ability to
get close through guidance, seeker state, and final miss distance. If uncertainty
is needed, it should enter through explicit sensor/fuze/fragment sampling fields,
not through a generic hit-probability clamp.

---

## 5. Implementation Strategy

### Phase 0: Preflight Audits And Guidance Baselines (Mandatory)

**Scope:** Close the six audit gates listed in Section 0 before any behavior
change lands.
**Changes:**
- Record the `PlatformLossState` enum audit and choose append-only or overlay
  semantics for `ForcedLanding`
- Catalog Python `health > 0`, `get_unit_health`, and `is_unit_active` consumers
- Confirm the `ShipPlatform` filter boundary and choose parallel aircraft update
  vs generic damage update
- Inventory aircraft JSON content and choose authored hitboxes vs generated
  fallback per type
- Catalog `Score` write points and define the event-driven scoring consumer
- Build the PN miss-distance benchmark matrix before deterministic fuze work
**Risk:** Medium
**Test:** doc-backed grep/audit evidence plus a runnable benchmark entry for
miss-distance distributions

### Phase 1: Extend Hitbox System To Aircraft (Medium-High Risk)

**Scope:** Reverse the HP-first bypass, route aircraft through the structured
damage pipeline, and make kill states derive from platform damage state rather
than direct HP depletion.
**Changes:**
- Add hitbox configs to aircraft JSON unit definitions
- Add `HitboxConfig` + `SystemHealth` + `PlatformDamageState` to aircraft spawn path
- Remove the aircraft HP-first kill bypass in `default_effects_model.cpp`
- Split the damage-state update path so aircraft are not blocked by the
  `ShipPlatform` filter
- Move score/reward writes out of the effects model and into a separate consumer
  layer
- Map aircraft subsystems to capability dimensions
**Risk:** Medium-High
**Main blockers:** HP bypass reversal, `ShipPlatform` filter removal or
parallelization, aircraft JSON hitbox content, score decoupling

### Phase 2: Add Aircraft-Specific Subsystem Effects (Medium Risk)

**Scope:** Implement aircraft-specific cascading effects from subsystem damage.
**Changes:**
- Add `aircraft_damage_state_update` system (or extend existing naval one)
- Implement aerodynamic degradation: g-limit reduction, control surface effectiveness, asymmetric thrust
- Implement fuel leak rate, fire propagation for aircraft
- Implement avionics degradation
- Add `AirframeStructuralState` or an equivalent component for structural limits
- Use aircraft propulsion reference frames, not ship-derived speed scaling
**Risk:** Medium — touches flight dynamics systems
**Test:** Fire weapon at specific hitboxes, verify expected subsystem effects

### Phase 3: Warhead Profile Model (Medium Risk)

**Scope:** Replace single `damage` scalar with warhead profile + blast/fragmentation model.
**Changes:**
- Add `WarheadProfile` struct to weapon definition
- Implement blast overpressure decay function
- Implement fragmentation pattern calculation
- Update `DefaultEffectsModel` to route through warhead profile
**Risk:** Medium — changes damage calculation path
**Test:** Verify damage values are physically reasonable for known warhead types

### Phase 4: Deterministic Fuze (Deferred)

**Scope:** Replace RNG hit probability with deterministic lethal-radius model.
**Changes:**
- Remove `splitmix64` RNG call from fuze logic
- Implement deterministic quality → damage mapping
- Route evasion through guidance model (affects miss distance, not hit probability)
**Risk:** Medium, but deferred until the PN miss-distance benchmark matrix is
available
**Test:** verify deterministic fuze outcomes across controlled miss distances,
aspects, and target sizes. Do not proceed until the benchmark matrix exists.

### Phase 5: Vulnerability / Pk Evidence Integration (Future)

**Scope:** Weapon- and target-specific vulnerability data for higher-fidelity
kill assessment.
**Changes:**
- Add vulnerability or Pk evidence data to weapon/target JSON
- Support tables/functions keyed by aspect, closure, miss distance, target class,
  and warhead family
- Treat Pk curves as evidence-backed calibration of the physical model, not as
  an opaque replacement for effects events and damage reports
**Risk:** Medium -- additive, but data provenance matters
**Note:** This requires defensible source data or clearly labeled assumptions

---

## 6. Migration And Compatibility Boundaries

Backward compatibility is allowed only as an interface boundary, not as a
physics constraint:

1. Aircraft without authored hitbox configs may use generated vulnerability
   geometry, but the generated geometry must still route through the
   event-driven damage pipeline.
2. `Health.current_hp` may be projected from `PlatformDamageState` for old
   observers. It must not be decremented directly by air-combat weapon effects
   when structured damage state is present.
3. Existing weapon JSON may load through a documented synthetic warhead profile,
   but the synthetic profile must be labeled in diagnostics and provenance.
4. Legacy binary kill reward remains a training-layer fallback only. It is not
   an acceptance criterion for the damage model.
5. New high-fidelity tests should fail if an air target with structured damage
   can be destroyed through the HP-first bypass.

---

## 7. Key Files To Modify

| File | Change |
|------|--------|
| `src/components/combat/damage.h` | Add `WarheadProfile` struct; add `ForcedLanding` only through append-only enum semantics or an aircraft overlay state |
| `src/models/weapons/default_effects_model.cpp` | Replace `hp -= damage` with warhead profile → hitbox routing; add aircraft subsystem effects |
| `src/systems/combat/damage_system.h` | Split or generalize `NavalDamageStateUpdate`; add aircraft damage state logic; defer deterministic fuze until PN baselines exist |
| `src/content/unit_definition.h` | Add `WarheadProfileDefinition`; extend `HitboxConfig` for aircraft defaults |
| `src/content/unit_definition_loader.cpp` | Parse warhead profile JSON; parse aircraft hitbox configs |
| `examples/config/database/aircraft/*.json` | Add hitbox definitions for each aircraft type |
| `examples/config/database/weapons/air_to_air/*.json` | Add warhead profile fields |
| RL / training adapters | Consume kill-level and damage-report outputs without shaping the physical damage authority |
| `src/runtime/contracts/engagement_contracts.h` | Export loss states without depending on raw enum numeric values |

---

## 8. Summary

The current HP-first damage model for air combat is not an acceptable
high-fidelity authority. The naval subsystem damage system -- hitboxes,
cascading effects, persistent platform state, and multi-tier kill assessment --
is a useful starting point, but the air-combat target is stricter: weapon
events must produce physically interpretable effects before platform kill state
is declared.

The primary gap is no longer only content. Aircraft hitboxes and warhead
profiles are required, but the HP-first bypass, generic `damage` scalar, RNG
fuze dice, and reward-shaped binary kill semantics must also be removed from
the authoritative air-combat effects path.

The revised rollout therefore starts with Phase 0 evidence collection. Phase 1
is medium-high risk because it must reverse the HP bypass, separate aircraft
damage updates from the `ShipPlatform` filter, provide aircraft hitbox content,
and decouple score writes from physical effects. Deterministic fuze work is
explicitly deferred until PN miss-distance behavior is measured.
