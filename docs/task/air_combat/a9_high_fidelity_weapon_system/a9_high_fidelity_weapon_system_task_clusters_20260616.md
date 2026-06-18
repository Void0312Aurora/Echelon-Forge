# A9 High-Fidelity Weapon System — Task Clusters

Status: `2026-06-17` **accepted**. All phases complete. 23 pass, 5 explicitly deferred, 0 open residuals.

Parent: [README.md](README.md)

## Boundary Decision

This task-cluster plan defines the finite, bounded work packets for the a9
high-fidelity weapon system subproject. **Final statuses are tracked in the
[dispatch queue](a9_high_fidelity_weapon_system_dispatch_queue_20260616.md)
(23 pass, 5 deferred).** The tables below retain original planning estimates
(dependencies, write sets, round caps); the Status column reflects the
original plan, not the final outcome.

---

## Phase P0: Boundary (Current)

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P0-A | main thread | — | Create subproject structure, README (en/zh), task clusters doc, current status doc, archive README. Link from parent air_combat README. | `docs/task/air_combat/a9_high_fidelity_weapon_system/*`, `docs/task/air_combat/README.md` | No code changes. No capability claims beyond planning surface. | Markdown link check: all internal links resolve. Parent README contains a9 entry. | Subproject files exist and parent README links a9. | — | 2 | active |
| P0-B | main thread | — | Audit current runtime for each of the 6 subsystems. Produce per-subsystem gap tables comparing proxy behavior to target high-fidelity behavior. | `docs/task/air_combat/a9_high_fidelity_weapon_system/*` (gap audit docs) | No code changes. No new capability claims. | Gap audit references specific code locations and test files. | 6 gap tables exist with code references. | P0-A complete | 1 | planned |

---

## Phase P1: Evidence Collection

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P1-A | main thread | sonnet | Compile web research source ledger for all 6 subsystems: APN guidance, Kalman filter seeker, three-loop autopilot, radar proximity fuze, warhead lethality (Gurney, fragment decay, continuous-rod), missile aerodynamics (Mach-dependent Cd₀, induced drag). Annotate every source with URL, retrieval date, and non-authoritative admission. | `docs/task/air_combat/a9_high_fidelity_weapon_system/p1_evidence/source_ledger_*.md` | No ITAR/classified sources. No weapon-specific parameters claimed as truth. | Every parameter value traces to a public source. Admissions are explicit. | Source ledger complete with per-subsystem parameter tables and non-authoritative annotations. | P0-B complete | 1 | planned |
| P1-B | main thread | sonnet | Define benchmark parameter tables for each subsystem. For each parameter, list: proxy value (current code), research-grade target value, public-source basis, uncertainty range, and configurable tuning knob name. | `docs/task/air_combat/a9_high_fidelity_weapon_system/p1_evidence/benchmark_parameters_*.md` | No code changes. No authority claims. | Every parameter has current-value, target-value, and source columns. | 6 benchmark parameter tables exist. Tuning knob names map to MissileTuning fields. | P1-A complete | 1 | planned |
| P1-C | main thread | sonnet | Map existing test coverage per subsystem. Identify tests that must continue to pass, tests that need updating, and coverage gaps requiring new tests. | `docs/task/air_combat/a9_high_fidelity_weapon_system/p1_evidence/test_coverage_map.md` | No code changes. | References specific test files and class/method names. | Coverage map complete. Gap list prioritized. | P0-B complete | 1 | planned |

---

## Phase P2: Implementation

### P2-A: APN Guidance (G1)

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P2-A1 | implementation worker | opus | Implement APN guidance law in C++: add target-acceleration feed-forward term to the existing PN computation. Compute target acceleration estimate from seeker track state. Add `apn_target_accel_gain` and `apn_nav_ratio` tuning parameters to `MissileTuning`. | `src/models/weapons/default_guidance_model.cpp`, `src/core/engine/simulation_kernel_missile_tuning.h`, `src/components/combat/common/weapon_common.h` | No IMM/adaptive filtering. No optimal guidance law (OGL) variants. | Compile + run `weapon_guidance_realism/launch_guidance.py` tests. APN reduces miss distance vs PN against maneuvering target. | APN term active, configurable via tuning params, existing tests pass, new APN-vs-PN comparison test passes. | P1-B complete | 3 | planned |
| P2-A2 | implementation worker | opus | Add target acceleration estimation from seeker track: compute `estimated_target_accel` from filtered track state differences over a configurable window. | `src/models/weapons/default_guidance_model.cpp` | No Kalman filter here (that's G2). | Target accel estimate is physically plausible (bounded by target G limits). | Estimate converges within configurable window. | P2-A1 complete | 2 | planned |

### P2-B: Kalman Filter Seeker (G2)

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P2-B1 | implementation worker | opus | Implement 9-state EKF tracker in a new `kalman_seeker.h/.cpp` model file. State vector: relative position (3), velocity (3), acceleration (3) in Cartesian world frame. Measurement: bearing, elevation, range (from seeker or datalink). Process noise: Singer model with configurable maneuver time constant τ_m and max acceleration σ_max. | `src/models/weapons/kalman_seeker.h`, `src/models/weapons/kalman_seeker.cpp` | No IMM banks. No adaptive process noise. No ECM effects. | Compile. Unit test: track a constant-velocity target, verify covariance convergence. Unit test: track a weaving target, verify track continuity. | EKF compiles, passes unit tests, produces physically plausible covariance. | P1-B complete | 3 | planned |
| P2-B2 | implementation worker | opus | Add EKF configuration to `MissileTuning`: process noise σ_a, measurement noise σ_angle and σ_range, initial covariance diagonal, track memory behavior. | `src/core/engine/simulation_kernel_missile_tuning.h`, `src/components/combat/common/weapon_common.h` | — | Tunable parameters round-trip through Python bindings. | New fields exist in MissileTuning and Missile component. Python can read/write them. | P2-B1 complete | 2 | planned |
| P2-B3 | implementation worker | opus | Wire EKF into guidance system. Replace `exp_smooth` calls with EKF predict/update cycle. Maintain backward compatibility: when `use_kalman_seeker = false`, fall back to first-order smoothing. | `src/systems/combat/guidance_system.h`, `src/models/weapons/default_guidance_model.cpp` | — | Existing guidance tests pass with `use_kalman_seeker=false`. EKF mode produces track states consumed by guidance. | Both modes work. EKF mode demonstrably smoother than first-order baseline. | P2-B2 complete | 2 | planned |

### P2-C: Three-Loop Autopilot (G3)

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P2-C1 | implementation worker | sonnet | Implement three-loop autopilot transfer function. Model as configurable second-order system parameterized by closed-loop time constant τ and damping ζ. Preserve existing G-limiting and rate saturation. | `src/models/weapons/default_guidance_model.cpp` | No actuator dynamics (fin rate/position limits). No non-minimum-phase zeros. | Compile. Unit test: step response matches expected τ/ζ. | Autopilot response is physically plausible. Existing G-limit tests pass. | P1-B complete | 2 | planned |
| P2-C2 | implementation worker | sonnet | Add autopilot configuration to `MissileTuning`: `autopilot_tau_s` (refined), `autopilot_damping`, `autopilot_order` (1/2/3), `actuator_bandwidth_hz`. | `src/core/engine/simulation_kernel_missile_tuning.h` | — | Round-trip through Python bindings. | New tuning fields exist and are configurable. | P2-C1 complete | 1 | planned |

### P2-D: Sensor-Driven Fuze Surrogate (G4)

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P2-D1 | implementation worker | opus | **Refine the existing PF-R4 surrogate** (do NOT re-implement PF-R3). P0-B gap audit must first determine what mechanism coverage differentiation already exists in `damage_mechanism_coverage_score` (continuous_rod already receives lateral/axial geometry correction; blast_frag uses range score directly). Add only differentiation dimensions that are genuinely missing — e.g., directional fragmentation band overlap, rod cutting plane alignment, or fuze-to-warhead orientation coupling. Preserve all existing PF-R4 diagnostic fields. Must not regress PF-R5 validation residuals. | `src/systems/combat/damage_system_common.h` | No real fuze constants. No `deterministic_fuze_authority`. No Pk claim. No re-implementation of existing `damage_mechanism_coverage_score` logic. | Existing PF-R4/PF-R5 fuze tests pass. P0-B audit identifies what is already covered vs. genuinely missing. New differentiation is additive, not duplicative. | Coverage differentiation gaps filled without duplicating existing logic. PF-R5 residuals not widened. | P0-B complete (gap audit of existing coverage), PF-R4/PF-R5 test baseline verified | 2 | planned |
| P2-D2 | implementation worker | opus | Add fuze refinement parameters to `MissileTuning` and `FuzeProfile` (extend, don't replace, existing PF-R4 fields): `fuze_mechanism_coverage_table` (per-mechanism-family coverage factors). | `src/core/engine/simulation_kernel_missile_tuning.h`, `src/components/combat/common/weapon_common.h` | — | Round-trip through Python bindings. | New fuze refinement fields configurable. | P2-D1 complete | 1 | planned |

### P2-E: Mach-Dependent Aerodynamics (G5)

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P2-E1 | implementation worker | sonnet | Replace fixed `Cd₀` with a Mach-indexed lookup table. Add power-on/power-off base-drag distinction. Implement proper induced drag: `C_Di = k(M) * CL²` with Mach-dependent k factor. | `src/models/weapons/default_guidance_model.cpp`, `src/models/weapons/missile_guidance_types.h` | No CFD-calibrated tables. No fin/tail-specific drag components. | Compile. Speed profile across Mach envelope is physically plausible. Power-on drag lower than power-off. | Mach table interpolates smoothly. Induced drag scales with lateral acceleration. | P1-B complete | 2 | planned |
| P2-E2 | implementation worker | sonnet | Add aero configuration to `MissileTuning`: `cd0_mach_table` (vector of Mach,Cd₀ pairs), `cd0_power_on_ratio`, `induced_drag_k_mach_table`. | `src/core/engine/simulation_kernel_missile_tuning.h` | — | Round-trip through Python bindings. | Tables configurable from Python. | P2-E1 complete | 1 | planned |

### P2-F: Physics-Based Warhead Refinements (G6)

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P2-F1 | implementation worker | opus | Add Gurney fragment velocity model: `V₀ = √(2E) · √((C/M)/(1 + C/2M))`. Add atmospheric fragment decay: `V(s) = V₀ · exp(-C_D·ρ·A·s/(2m))`. Add directional efficiency factor for blast-frag warheads. | `src/models/weapons/detail/default_effects_warhead_detail.inc` | No AIM-120C-specific fragment distribution. No 3D fragment ray-tracing. | Fragment velocity follows Gurney equation. Decay curve is physically plausible. | Existing warhead tests pass. Fragment velocity and decay diagnostics observable. | P1-B complete | 2 | planned |
| P2-F2 | implementation worker | opus | Add continuous-rod expansion kinematics: velocity cap at weld-limited threshold (<1,150 m/s), rod-opening radius as function of time and C/M ratio, cutting threshold at minimum striking velocity (>610 m/s). | `src/models/weapons/detail/default_effects_warhead_detail.inc` | No specific rod material properties. No weld-failure simulation. | Rod velocity capped. Cutting margin respects velocity threshold. | Existing continuous-rod tests pass. Expansion kinematics observable in diagnostics. | P1-B complete | 2 | planned |
| P2-F3 | implementation worker | sonnet | Add warhead parameters to `MissileTuning` and `WarheadProfile`: `explosive_mass_kg`, `case_mass_kg`, `gurney_constant_mps`, `fragment_mass_kg`, `fragment_count`, `directional_efficiency`, `rod_count`, `rod_mass_kg`, `weld_velocity_cap_mps`. | `src/core/engine/simulation_kernel_missile_tuning.h`, `src/components/combat/common/weapon_common.h` | — | Round-trip through Python bindings. | New warhead fields configurable. | P2-F1, P2-F2 complete | 1 | planned |

---

## Phase P3: Integration

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P3-A | integration worker | sonnet | Update Python bindings for all new `MissileTuning` fields across G1-G6. Ensure round-trip read/write for all new parameters. | `src/interfaces/python/bindings_core.cpp` | No Python-side logic changes. | Python test: set all new fields, read them back, verify equality. | All new tuning params round-trip through Python. | P2-A2, P2-B3, P2-C2, P2-D2, P2-E2, P2-F3 complete | 2 | planned |
| P3-B | integration worker | sonnet | Update `debug_get_missile_runtime_state` to expose new runtime diagnostics: APN accel components, EKF covariance trace, autopilot state, fuze surrogate fields, aero table index, warhead fragment velocity. | `src/interfaces/python/bindings_core.cpp` | — | Python test: read runtime state and verify field presence. | All new diagnostic fields exposed. | P3-A complete | 1 | planned |
| P3-C | integration worker | sonnet | Update scenario JSON schema and loader to accept new tuning fields. Provide example scenario configs exercising the new fidelity parameters. | `src/content/unit_definition_loader.cpp`, `scenarios/air_combat/` (new example) | No production scenario changes. | Example scenario loads and runs without error. | Example scenario exercises new params. | P3-A complete | 2 | planned |
| P3-D | integration worker | sonnet | Run full existing air_combat test suite. Identify and fix regressions. Document any intentional behavior changes with rationale. | Any file with test failures | No silent test weakening. | `pytest tests/runtime/air_combat/ -x --timeout=120` passes or failures documented with rationale. | Test suite green or regressions documented. | P3-C complete | 2 | planned |

---

## Phase P4: Validation

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P4-A | validation worker | opus | Run engagement geometry sweep: head-on, tail-chase, beam (90°), high off-boresight (135°). For each geometry, compare APN+EKF vs classical PN+first-order across miss distance, fuze trigger quality, and component damage outcome. | `docs/task/air_combat/a9_high_fidelity_weapon_system/p4_validation/` (CSV, heatmaps) | No Pk claim. No "better" claim without statistical significance. | Sweep produces CSV with ≥100 runs per geometry bucket. | Matrix CSV and heatmaps retained. | P3-D complete | 2 | planned |
| P4-B | validation worker | opus | Run parameter sensitivity: vary nav_ratio [3,4,5], autopilot τ [0.05,0.10,0.20]s, fuze detection range [5,10,15,20]m, Cd₀ scale [0.8,1.0,1.2]. Measure miss distance sensitivity. | `docs/task/air_combat/a9_high_fidelity_weapon_system/p4_validation/` (CSV, heatmaps) | No "optimal" parameter claims. | Sensitivity data covers full parameter ranges. | Sensitivity CSV and heatmaps retained. | P3-D complete | 2 | planned |
| P4-C | validation worker | sonnet | Compare upgraded model (APN+EKF+3loop+surrogate fuze+Mach aero+Gurney) against proxy baseline (classical PN+first-order+single-lag+distance fuze+fixed Cd) on identical engagement scenarios. Produce side-by-side comparison artifacts. | `docs/task/air_combat/a9_high_fidelity_weapon_system/p4_validation/` (comparison summary) | No "superior" claim. Comparison is descriptive only. | Side-by-side comparison shows physically explainable differences. | Comparison summary with key difference drivers documented. | P4-A, P4-B complete | 1 | planned |

---

## Phase P5: Closure

| Cluster | Owner | Model | Goal | Write set | Non-goals | Validation | Closure gate | Dependency | Round cap | Status |
|---------|-------|-------|------|-----------|-----------|------------|-------------|------------|-----------|--------|
| P5-A | main thread | — | Write acceptance closeout document: accepted scope, validation outcomes, evidence artifacts, residual register, forbidden claims. | `docs/task/air_combat/a9_high_fidelity_weapon_system/a9_acceptance_*.md` | No capability promotion. | All acceptance gate conditions from README addressed. | Acceptance doc complete. | P4-C complete | 1 | planned |
| P5-B | main thread | — | Update parent air_combat README, A2 follow-on README, and relevant standards docs to reflect a9 completion. Sync archive boundary. | `docs/task/air_combat/README.md`, other affected README files | No capability promotion in parent docs. | Links resolve. Status vocabulary is scoped. | Parent docs updated, archive boundary clear. | P5-A complete | 1 | planned |

---

## Dispatch Rules

1. Every worker packet must map to exactly one cluster.
2. Do not allow two workers to edit the same file concurrently.
3. P0, P1, and P5 clusters are serial (main thread only).
4. P3 and P4 clusters are serial within their phase.
5. If a cluster exceeds its round cap, stop and re-scope before adding a
   follow-up wave.
6. All workers must follow `docs/standards/governance/subagent_usage_policy.md`.

### P2 Serialization Constraints (CRITICAL)

The following clusters share write surfaces and **MUST NOT be dispatched
concurrently**. The Dependency column in each cluster row encodes these
constraints, but the physical file overlaps are made explicit here:

| Shared file | Clusters touching it | Constraint |
|-------------|---------------------|------------|
| `default_guidance_model.cpp` | P2-A1, P2-A2, P2-B3, P2-C1, **P2-E1** | **Serial only.** Dispatch order: P2-A1 → P2-A2 → P2-B3 → P2-C1 → P2-E1. P2-E1 modifies drag computation in `update_mass_and_drag_state`. |
| `simulation_kernel_missile_tuning.h` | P2-A1, P2-B2, P2-C2, P2-D2, P2-E2, P2-F3 | **Serial only.** All six clusters add fields to the same struct. Dispatch in numerical order (A1 → B2 → C2 → D2 → E2 → F3) to minimize merge conflicts. |
| `weapon_common.h` | P2-A1, P2-B2, P2-D2, P2-F3 | **Serial only.** Dispatch in A1 → B2 → D2 → F3 order. |
| `damage_system_common.h` | P2-D1 (single cluster) | Single-cluster file; no concurrency risk. |
| `default_effects_warhead_detail.inc` | P2-F1, P2-F2 | **Serial within G6.** F1 must complete before F2. |
| `kalman_seeker.h/.cpp` | P2-B1 (new file) | New file; no concurrency risk with other clusters. |
| `bindings_core.cpp` | P3-A, P3-B | **Serial.** P3-A before P3-B. |

### Safe Parallelism Within P2

Only these cluster pairs touch **completely disjoint** file sets and can run in
parallel:

| Parallel group | Clusters | Rationale |
|---------------|----------|-----------|
| G2+G6 | P2-B1, P2-F1 | `kalman_seeker.h/.cpp` (new) vs `default_effects_warhead_detail.inc` — no overlap |
| G2+G5 (partial) | P2-B1, P2-E2 | `kalman_seeker.h/.cpp` vs `simulation_kernel_missile_tuning.h` — no overlap, BUT P2-E2 depends on P2-E1 which touches `default_guidance_model.cpp` and must serialize with G1 clusters |

**All other P2 cluster pairs share at least one file and MUST be serialized.**
In particular, P2-A1 and P2-E1 both touch `default_guidance_model.cpp` — they
CANNOT run in parallel despite being different subsystems (G1 vs G5).
When in doubt, serialize.

## Worker Packet Requirements

Every completed cluster must produce:

```
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan Summary

| Phase | Validation Method | Key Metric |
|-------|-------------------|------------|
| P2-A | Unit tests + PN comparison | Miss distance reduction vs maneuvering target |
| P2-B | Unit tests + track continuity | Covariance convergence time |
| P2-C | Step response test | Rise time matches τ specification |
| P2-D | Contract tests | Diagnostic field population |
| P2-E | Speed profile test | Plausible Mach sweep |
| P2-F | Physics check | Gurney velocity match, rod cap enforcement |
| P3-D | Regression suite | `pytest tests/runtime/air_combat/` green |
| P4-A | Geometry sweep | CSV with ≥100 runs/bucket |
| P4-B | Sensitivity analysis | Full parameter range coverage |
| P4-C | A/B comparison | Descriptive side-by-side |

## Acceptance Criteria

This task-cluster plan is accepted when:

- All 28 clusters (2 P0 + 3 P1 + 14 P2 + 4 P3 + 3 P4 + 2 P5) have a status
  of `pass`, `accepted`, or `closed`, OR blocked/failed clusters have documented
  residual entries.
- No cluster has exceeded its round cap without re-scope documentation.
- The acceptance closeout document (P5-A) names every residual.
- Forbidden overclaims (`pk_authority`, `deterministic_fuze_authority`, stock
  weapon truth) remain refused in all outputs.
