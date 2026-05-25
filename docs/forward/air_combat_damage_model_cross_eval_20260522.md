# Air Combat Damage Model — Cross-Evaluation Against Codebase Reality

Status: `2026-05-22` — cross-referencing [air_combat_damage_model_evaluation_20260522.md](air_combat_damage_model_evaluation_20260522.md)
against the actual C++ implementation.

## 1. Document Accuracy Assessment

### 1.1 What The Document Gets Right

| Claim | Code Evidence | Verdict |
|-------|---------------|---------|
| Two-path split: HP vs Subsystem | [default_effects_model.cpp:144-259](src/models/weapons/default_effects_model.cpp#L144-L259) — literal branching structure | **Correct** |
| HP-first bypass kills target before geometric code runs | `hp->current_hp -= missile.damage` at line 146, then `hp->current_hp <= 0` check at line 151 → `target_entity.destruct()` + `return` at line 158 | **Correct — and more severe than the doc suggests** |
| `armor_mm` loaded but never read | [damage.h:15](src/components/combat/damage.h#L15) — field declaration; zero references in any `.cpp` | **Correct** |
| `NavalDamageStateUpdate` queries `ShipPlatform` → won't match aircraft | [damage_system.h:130](src/systems/combat/damage_system.h#L130) — `ecs.system<Health, PlatformDamageState, const ShipPlatform>` | **Correct — critical blocker not called out explicitly** |
| RNG-based hit probability | [damage_system.h:109-112](src/systems/combat/damage_system.h#L109-L112) — `damage_rand_uniform01(m[i].rng_state) > hit_prob` | **Correct** |
| `damage` field not physically grounded | Default 120 for all AAMs; loosely mapped from warhead mass | **Correct** |

### 1.2 What The Document Misses Or Understates

| Gap | Code Evidence | Severity |
|-----|---------------|----------|
| **The HP bypass is architecturally wired as FIRST, not an accident.** | Effects model calls `hp -= damage` at line 146 BEFORE the geometric code at line 162. The `return` at line 158 means geometric code is dead for any HP-lethal hit. | **CRITICAL** — The recommended "Phase 1" cannot work without reversing lines 144-160 and 162-259 |
| **`PlatformLossState` has no `ForcedLanding` slot.** | [damage.h:33-39](src/components/combat/damage.h#L33-L39) — `CombatCapable=0, MissionKill=1, MobilityKill=2, SensorKill=3, Lost=4`. Adding `ForcedLanding` requires renumbering or inserting a new enum value. | **HIGH** — Enum renumbering may break existing naval state machines |
| **Subsystem matching is string-based, not component-based.** | [default_effects_model.cpp:187-207](src/models/weapons/default_effects_model.cpp#L187-L207) — `system_name_matches(system, "radar")` uses substring matching on hardcoded strings. `"radar_dish"` would match `"radar"`. `"engine_left"` requires explicit `system == "engine_left"` check at line 221. | **MEDIUM** — Fragile, doesn't scale to many aircraft subsystems |
| **`NavalDamageStateUpdate` is filtered by `ShipPlatform` tag** — so it will never tick on aircraft even with `PlatformDamageState` present. Phase 1 must either remove that filter or create a parallel aircraft system. | [damage_system.h:130](src/systems/combat/damage_system.h#L130) — `ecs.system<..., const ShipPlatform>(...)` — `ShipPlatform` is a required component for this system to match. | **HIGH** — Undocumented architectural blocker |
| **`PlatformDamageState` has naval-specific fields.** | `flooding_severity`, `ongoing_hull_breach` (lines 46-47) are meaningless for aircraft. If Phase 1 routes aircraft through the same struct, these fields will be populated with zeros or stale values. | **LOW** — Cosmetic, but the doc's "directly reusable" claim needs qualification |
| **Phase 1 `spawn` path not detailed.** | Aircraft entities are spawned through `spawn_unit(type_name)` in [simulation_kernel.cpp](src/core/engine/simulation_kernel.cpp). Adding `HitboxConfig + SystemHealth + PlatformDamageState` requires either JSON hitbox definitions per aircraft (content work) or generated fallback geometry (code work). The doc mentions generated geometry in Section 6 but doesn't specify who generates it. | **MEDIUM** — Content gap is larger than estimated |
| **Phase 4 (deterministic fuze) removes the only damage-vs-evasion coupling.** | Currently, evasion affects `hit_prob` directly (line 108). If Phase 4 removes the RNG roll without adding evasion → miss-distance coupling in the guidance model, evasion becomes purely cosmetic for damage purposes. | **MEDIUM** — The doc says "evasion affects miss distance through guidance" but doesn't confirm the current PN guidance model responds to target maneuver in a way that produces meaningfully varied miss distances |

### 1.3 Design Stance vs Codebase Consistency

The Design Stance states:
> "`Health.current_hp` is not a kill model. It may remain as a derived compatibility/readout field, but it must not be the primary effects or kill authority for air combat."

And Section 6 states:
> "New high-fidelity tests should fail if an air target with structured damage can be destroyed through the HP-first bypass."

**Assessment:** The Design Stance is self-consistent and architecturally sound, but it contradicts the current code where `Health.current_hp` is indisputably the primary kill authority (lines 144-158 execute before and can preempt the geometric code at lines 162-259). Implementing this stance means **reversing the execution order in `on_proximity_hit()`**: geometric subsystem damage must run FIRST, and `hp` must be derived from `PlatformDamageState` (as already happens at lines 242-248), not decremented directly.

---

## 2. Phase-by-Phase Feasibility Assessment

### Phase 1: Extend Hitbox System To Aircraft

**Feasibility:** PARTIALLY BLOCKED

| Prerequisite | Status | Action Required |
|-------------|--------|-----------------|
| Reverse HP-first bypass | Not done | Swap lines 144-160 and 162-259 in `on_proximity_hit()`. Move HP decrement to AFTER geometric damage, and derive `hp` from `survivability_margin` rather than subtracting `missile.damage`. |
| Remove `ShipPlatform` filter | Not done | Either create `AircraftDamageStateUpdate` parallel system (querying `AirPlatform` or equivalent tag) or make `NavalDamageStateUpdate` generic by removing `ShipPlatform` filter |
| Aircraft hitbox JSON | None exist | Create per-aircraft-type JSON hitbox configs, OR implement a generated "whole-aircraft" hitbox fallback (Section 6.1) |
| Aircraft spawn path | Not wired | `spawn_unit()` must populate `HitboxConfig`, `SystemHealth`, `PlatformDamageState` when the unit definition contains hitbox data |

**Actual risk:** MEDIUM-HIGH (not the LOW-MEDIUM claimed). The HP bypass reversal is a **behavioral change** — it changes what happens when a missile hits a target with both `Health` and `HitboxConfig`. Currently HP is decremented unconditionally; after reversal, HP would be derived from subsystem damage. This affects every existing air combat scenario.

### Phase 2: Aircraft-Specific Subsystem Effects

**Feasibility:** BLOCKED by Phase 1 architectural reorder

**Specific concerns:**
- Propulsion scaling: the current `NavalDamageStateUpdate` scales `propulsion->mil_thrust_n` relative to `ship.max_speed_mps * 100000.0` (line 181). Aircraft propulsion uses a different reference frame (thrust in Newtons, not speed-derived). The aircraft system must use `Propulsion::mil_thrust_n` directly with a mobility_capability multiplier, not the ship-derived formula.
- Fuel leak: `Mass::fuel_leak_rate_kg_s` already exists and is used (line 231), but aircraft fuel consumption models differ from ship models. Aircraft fuel leaks are time-critical (minutes of flight remaining vs hours for ships).
- Structural g-limit: no `struct_g_limit` field exists in any aircraft component. This is a **new component** or field that must be added to `Propulsion` or a new `AirframeStructuralState`.

### Phase 3: Warhead Profile Model

**Feasibility:** FEASIBLE but scope warning

The `WarheadProfile` struct in Section 4.5 is well-defined. However:

- **Blast overpressure decay** requires altitude-dependent ambient pressure. The current environment model may not provide this. Fallback to sea-level standard atmosphere is acceptable for Phase 3.
- **Fragmentation pattern** requires computing fragment density at the target's exposed area from the missile's detonation geometry (relative position, velocity, orientation). This is non-trivial 3D geometry — the current hitbox code does OBB intersection in body-frame but doesn't compute exposed area by aspect.
- **Backward compatibility**: existing weapon JSON must load through a "synthetic" warhead profile (Section 6.3). The synthetic profile must be explicitly labeled as such in diagnostics.

### Phase 4: Deterministic Fuze

**Feasibility:** FEASIBLE but with a caveat

The deterministic model:
```
if (min_dist <= lethal_radius):       damage_factor = 1.0
elif (min_dist <= 2*lethal_radius):   damage_factor = linear decay
else:                                 miss
```

**Caveat:** This removes the only place where target maneuver (evasion) affects hit outcome. The doc says "evasion affects miss distance through guidance," but in the current PN guidance model, target maneuver affects the LOS rate term — it does not necessarily produce large enough miss distances to cross the `lethal_radius` threshold for a well-tuned missile. This means:

- With deterministic fuze: a PN-guided missile with 35g capability against a 9g maneuvering target will almost always score a hit (miss distance < lethal radius), making air combat outcomes near-deterministic
- With RNG fuze: the same engagement has ~0.05-0.98 hit probability, introducing variance

**Recommendation:** Phase 4 should NOT be implemented until the guidance model is verified to produce physically realistic miss distances across a range of engagement geometries. Alternatively, retain a small stochastic component representing sensor noise / fuze timing jitter but document it explicitly as such.

### Phase 5: Vulnerability / Pk Evidence

**Feasibility:** FUTURE — no blocking issues

This is additive and well-scoped. The data provenance requirement ("defensible source data or clearly labeled assumptions") is the primary challenge.

---

## 3. Undocumented Dependencies And Risks

### 3.1 Enum Renumbering Hazard

`PlatformLossState` is an `enum class : int` used by:
- [damage_system.h:163-173](src/systems/combat/damage_system.h#L163-L173) — loss state assignment
- [damage.h:33-39](src/components/combat/damage.h#L33-L39) — definition
- [engagement_contracts.h](src/runtime/contracts/engagement_contracts.h) — `DamageReport::loss_state_from`, `loss_state_to`
- Python bindings — exposed to Python via nanobind

Adding `ForcedLanding` between `SensorKill=3` and `Lost=4` means `Lost` becomes 5. If any code stores `PlatformLossState` as raw `int` and compares against literal `4`, it will silently break.

**Mitigation:** grep for `PlatformLossState` comparisons, especially `== 4`, `!= 4`, `< 4`, `>= 4`, and any `static_cast<int>` conversions.

### 3.2 HP Observer Impact

Python code at 9+ locations checks `health > 0.0` or `is_unit_active(agent_id)`:
- `world_batch/adapter.py:94`
- `gym_envs/scenario_loader/reward_runtime/objectives.py`
- Contract tests: `env_regression.py`, `unit/kernel.py`

After Phase 1, `hp.current_hp` is derived from `PlatformDamageState.survivability_margin`, not decremented directly. The mapping `survivability_margin ≤ 0 → hp = 0` at [damage_system.h:163](src/systems/combat/damage_system.h#L163) already handles this, but **the semantic change from "HP was decremented by missile damage" to "HP reflects platform survival state"** means HP no longer monotonically decreases with each hit — it jumps when thresholds are crossed. This may confuse existing training reward functions that track `health` as a continuous signal.

### 3.3 RL Reward Coupling

Current kill reward is hardcoded at [default_effects_model.cpp:154](src/models/weapons/default_effects_model.cpp#L154): `score->total_reward += 1000.0`.

The Design Stance says:
> "RL reward shaping and curriculum shortcuts must consume the resulting `EffectsEvent`, `DamageReport`, and platform state."

This means the `Score` component update at line 154 should move OUT of the effects model and into a separate reward computation layer that reads `EffectsEvent` + `DamageReport` outputs. This is a **Phase 1 prerequisite** that the implementation strategy doesn't explicitly schedule.

---

## 4. Revised Implementation Risk Assessment

| Phase | Doc's Risk | Actual Risk | Key Unstated Dependency |
|-------|-----------|-------------|------------------------|
| Phase 1 | "Low to medium" | **MEDIUM-HIGH** | HP bypass reversal + `ShipPlatform` filter removal + JSON hitbox content + `Score` reward decoupling |
| Phase 2 | "Medium" | **MEDIUM** | New `AirframeStructuralState` component; propulsion scaling reference frame |
| Phase 3 | "Medium" | **MEDIUM** | Exposed area computation; ambient pressure model; synthetic warhead JSON mapping |
| Phase 4 | "Low" | **MEDIUM** (deferred) | PN guidance model miss-distance validation must PRECEDE deterministic fuze |
| Phase 5 | "Medium" | **LOW** (additive) | External data provenance |

---

## 5. Prerequisite Checklist Before Any Phase Begins

These must be verified before starting Phase 1:

- [ ] **Grep `PlatformLossState` comparisons**: confirm no raw integer comparisons against `Lost = 4` exist outside `damage.h` and `damage_system.h`
- [ ] **Grep `health > 0` / `is_unit_active`**: catalog all Python callers to prepare for semantic change
- [ ] **Grep `ShipPlatform` filter consumers**: confirm `NavalDamageStateUpdate` is the ONLY system that filters on `ShipPlatform` — if others exist, they'll need the same treatment
- [ ] **Aircraft JSON inventory**: list all aircraft types in `examples/config/database/aircraft/` that need hitbox configs (or confirm the generated fallback strategy)
- [ ] **Score component**: identify all locations that write `score->total_reward` or `score->kills_confirmed` to plan the decoupling
- [ ] **PN guidance miss-distance benchmark**: run a matrix of engagement geometries (head-on, tail-chase, beam, high-off-boresight) to establish current miss-distance distributions before removing RNG fuze

---

## 6. Summary

The document's **architectural direction is correct**: the HP-first bypass must be removed, the naval subsystem model must be extended to aircraft, and the damage pipeline should be event-driven with physical warhead profiles.

However, the document **underestimates the difficulty of Phase 1** by classifying it as "low to medium risk." The HP-bypass reversal in `on_proximity_hit()` is a **behavioral breaking change** that gates all subsequent phases. Coupled with the `ShipPlatform` filter lockout on the damage state update system and the absence of aircraft hitbox JSON content, Phase 1 is closer to **medium-high complexity** with cross-cutting impacts on: the C++ effects pipeline, ECS system registration, Python health observers, and RL reward computation.
