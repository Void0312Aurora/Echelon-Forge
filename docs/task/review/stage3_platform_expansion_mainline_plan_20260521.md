# Stage 3 Platform Expansion — Mainline Plan

Status: `2026-05-21` mainline design, opened as the `WP17` task family.

Inputs:

- [Stage 1 closure (WP0-WP9)](consolidated_remaining_work_and_roadmap_20260520.md)
- [Stage 2 closure (WP10-WP15)](post_wp9_gap_analysis_20260520.md)
- [WP13 backend fidelity expansion](../simulation_architecture/wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.md)
- [WP14 capability composition](../simulation_architecture/wp14_capability_composition/capability_composition_wp14_20260521.md)
- [WP15 counterfactual experiment generation](../simulation_architecture/wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.md)
- [WP16 runtime spine consolidation](../simulation_architecture/wp16_runtime_spine_consolidation/runtime_spine_consolidation_wp16_20260521.md)
- [WP17 Stage 3 runtime materialization and cleanup](../simulation_architecture/wp17_stage3_runtime_materialization_cleanup/stage3_runtime_materialization_cleanup_wp17_20260521.md)
- [Simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)

## 1. Current State: The Contract-Runtime Gap

WP10-WP15 built contract surfaces, evidence boundaries, and architecture tests. WP16
will consolidate them into a maintained runtime spine. But none of WP13-WP15
changed the simulation engine itself. A precise inventory:

| WP | Contract surface status | Runtime status |
|----|------------------------|----------------|
| **WP13** Backend Fidelity | `RuntimeCapabilities` struct exists (WP9). Fidelity profile request/rejection vocabulary defined. Backend profile registry complete (WP6). Parity budget templates defined (WP6). | `RuntimeFacade::capabilities()` now returns conservative baseline/candidate metadata, but there is still no fidelity-profile request API, no `ModelProvider` dispatch abstraction, and no fidelity profile consumed by stage execution. GPU code remains behind `EF_ENABLE_CUDA_EXPERIMENTS`. |
| **WP14** Capability Composition | `CapabilityBundle` contract defined. Content definition lowering schema specified. Spawn resolution bridge spec exists. Compatibility validation tests pass. | `DefaultUnitFactory` now has internal `CapabilityBundle` template/resolved-plan support, but `spawn_unit(type_name)` and `spawn_units_batch` remain the canonical runtime creation path. Public `spawn_platform` is still intentionally absent and guarded. |
| **WP15** Counterfactual Experiment | `ReplayEnvelope`, `BranchPoint`, `WorldlineBranchMetadata` contracts defined. Counterfactual admission gate with fail-closed checks. Scenario generation request surface. Experiment evidence bridge schema. | Zero snapshot/restore mechanism. Zero counterfactual rollout execution. Scenario generation is hand-written JSON files. No experiment orchestration runtime. |
| **§8 示例** Multi-Rate | `ActionHoldPolicy` DTO exists (WP11). `StageNodeManifest.clock_domain` field exists (WP10). Window loop skeleton with injection/barrier/export (WP10). WP16 added selected-slice cadence evidence. | Global runtime cadence is still effectively single-rate. `kWp10ClockDomainAdvisoryOnly = true` remains true. The architecture §8 policy/control/physics example is not runnable. |
| **§8/§9** ModelProvider | No dedicated contract surface beyond backend profiles. | Zero abstraction. Physics, guidance, effects models are direct `I*Model` interface pointers in `SimulationKernel`. No surrogate/learned/analytical dispatch. |
| **§3** Information Transformations | `InformationStateSource` vocabulary defined (WP11). `information_transform_contracts.h` with validators (WP12). | Transformations are implicit in system code. No runtime-enforced layer transition. |

**Stage 3 must close this gap.** It takes the contract surfaces from WP13-WP15 and
makes them runtime behavior. It also closes the two largest architecture gaps that
survived stages 1-2: multi-rate scheduling and ModelProvider dispatch.

`WP17` now turns this plan into the final refactor task family. Its first
business-facing cleanup slice is not to delete `WorldBatchRuntime`, but to
migrate maintained batch/training readers away from `batch_runtime` access and
make the old path compatibility-only behind tests.

## 2. Four Mainline Tracks

The work decomposes into four tracks. Each takes a completed Stage 2 contract
surface and makes it runtime.

### Track A: Multi-Fidelity Runtime Materialization

Takes: WP13 (Backend Fidelity) contracts + WP6 (Backend Profile) registries

Current: `RuntimeCapabilities` struct exists but `capabilities()` returns empty.

Target: A fidelity profile is queryable, rejectable, and affects which backend
computes a stage node's output.

```
capabilities() → populated from maintained backend profile registries
fidelity profile request → accepted / rejected with explicit reason
ModelProvider dispatch → stage node declares which provider family it needs;
  provider selected from profile; fallback to reference (CPU exact)
```

Concrete deliverables:

| ID | Item | Starting state | Target state |
|----|------|---------------|--------------|
| MF-1 | `capabilities()` population | Returns `RuntimeCapabilities{}` | Populated from WP6 registry: `cpu_exact.reference` is `true`; GPU helpers are queryable but `supports_exact_gpu_backend = false` |
| MF-2 | Fidelity profile rejection | No rejection path | Profile request that requires `accelerated_exact` on a reference-only deployment → explicit rejection with `rejection_reason` and `required_profile_class` |
| MF-3 | `ModelProvider` dispatch | Direct `I*Model` pointers in kernel | `ModelProvider` enum (physics/surrogate/learned/table/analytical). Stage node manifest declares `provider_family`. Kernel dispatches to reference or surrogate based on fidelity profile. First slice: physics provider for P5 PhysicsStep. |
| MF-4 | Fidelity facade surface | `BackendCapabilityFacade` named but not implemented | `query_capabilities()`, `request_fidelity_profile()`, profile acceptance/rejection visible through facade |

Prerequisite: WP16 spine consolidation complete.

### Track B: Capability Composition Runtime

Takes: WP14 (Capability Composition) contracts

Current: `spawn_unit(type_name)` → `DefaultUnitFactory` with ~1000 lines of
hardcoded type-name→component dispatch.

Target: `spawn_platform({capabilities...})` as the canonical creation path.
`spawn_unit(type_name)` remains as a compatibility wrapper that internally
expands to a capability bundle.

```
CapabilityBundle = {
  mobility: {type: "jet_fighter", params: {...}},
  sensor: {type: "aesa_radar", params: {...}},
  launcher: {type: "pylon_aim120", params: {...}},
  communication: {type: "link16"},
  survivability: {type: "airframe_damage_model"},
  command: {type: "flight_lead_doctrine"},
}
  → spawn_platform(bundle)
  → capability resolver
  → ECS entities + components
```

Concrete deliverables:

| ID | Item | Starting state | Target state |
|----|------|---------------|--------------|
| CC-1 | `CapabilityBundle` → definition lowering | No lowering path | `CapabilityBundle` expands to a set of component factories. Each capability type has a registered resolver. |
| CC-2 | `spawn_platform({capabilities...})` | Does not exist | Facade-level creation API. Internally calls capability resolver chain. |
| CC-3 | `spawn_unit(type_name)` compatibility | Only creation path | Becomes a wrapper: looks up type_name → expands to `CapabilityBundle` → calls `spawn_platform()`. Existing behavior preserved. |
| CC-4 | Air/naval proof | Air and naval platforms defined by separate code paths in `DefaultUnitFactory` | F-16 and DDG-51 defined as capability bundles. Same resolver chain produces both. Proof: same `spawn_platform()` call with different capability bundles produces valid air and naval entities. |

Prerequisite: WP16 spine consolidation complete. Independent of Track A.

### Track C: Counterfactual And Experiment Runtime

Takes: WP15 (Counterfactual Experiment) contracts + WP8 (Learning Face) schemas

Current: Contracts and admission gates exist (tests pass). Zero runtime behavior.

Target: One slice of snapshot/restore enables counterfactual branching. Scenario
generation becomes programmatic rather than hand-written JSON.

```
snapshot_world(world_id) → Snapshot
restore_world(world_id, snapshot) → restore
branch_from(snapshot, mutation) → new world_id
counterfactual rollout → independent world execution
compare_worldlines(a, b) → causal difference
```

Concrete deliverables:

| ID | Item | Starting state | Target state |
|----|------|---------------|--------------|
| CF-1 | Snapshot/restore for physics shard | No snapshot mechanism | `snapshot_physics_shard(world_id)` captures position/velocity/orientation for all entities. `restore_physics_shard(world_id, snapshot)` restores. First shard only. |
| CF-2 | Branch point creation | No branching | `branch_at(snapshot, mutation_spec)` creates a new world whose physics state is the snapshot plus mutation. New world has independent RNG seed derived from parent + branch id. |
| CF-3 | Counterfactual rollout execution | No rollout | Two worlds from same branch point run independently. `compare_worldlines()` produces `CausalDifference` with state deltas at each barrier. |
| CF-4 | Programmatic scenario generation | Hand-written JSON files | `generate_scenario(ScenarioGenerationSpec)` produces a valid scenario JSON. First generator: simple parameter variation (starting distance, altitude, speed). |
| CF-5 | Experiment evidence collection | Contracts only | `ExperimentRun` struct collects observations, rewards, terminations, and traces across all worlds in an experiment. Queryable through facade. |

Prerequisite: WP16 spine consolidation + Track A (multi-fidelity, for snapshot scope).

### Track D: Multi-Rate Scheduling (GAP-9 → Architecture §8 Example)

Takes: WP10 window loop + WP2.5 scheduler semantics + `ActionHoldPolicy` DTO (WP11)

Current: WP16-B will enforce clock-domain trigger/skip for the spine slice. But
the architecture document's §8 example (policy 10Hz, control 20Hz, physics 60Hz)
is nowhere near runnable.

Target: The §8 example runs. Policy inference at 10Hz produces one
`ActionIntentPacket` per 100ms window. `ActionHoldPolicy.hold_last` makes it
visible to six control-rate ticks (20Hz) and ten physics substeps (60Hz).
Observation is sampled at the policy cadence and carries the correct barrier
version.

```
Window N, dt=0.1s:
  input_injection: policy action A_N, effective_time = t
  P3 CommandDelivery: consumes A_N (same-window, post-injection)
  P4 PlatformControl: 20Hz → runs 2x in this window
    tick 1: consumes delivered command
    tick 2: hold_last from tick 1 if no new command
  P5 PhysicsStep: 60Hz → runs 6x in this window
    each substep: consumes latest force/torque from P4
  P10 ObservationExport: snapshot at t+dt
  facade returns observation to policy

Window N+1: policy uses Window N observation → emits A_N+1
```

Concrete deliverables:

| ID | Item | Starting state | Target state |
|----|------|---------------|--------------|
| MR-1 | Nested clock-domain trigger | All systems run every 60Hz tick | Base tick 60Hz. P4 declares 20Hz (every 3rd tick). P2 declares event-driven. P10 declares per-window. Nodes skip with evidence when not triggered. |
| MR-2 | `ActionHoldPolicy` runtime consumption | DTO exists, zero runtime use | Between P4 ticks within one window, `hold_last` applies the most recent valid action. `interpolate` derives intermediate. `expiry` drops after `valid_until`. |
| MR-3 | Policy cadence integration | No policy clock domain | Policy inference at 10Hz. Observation sampled at policy boundary. Action injected with `effective_time` for next window. |
| MR-4 | §8 example runnable | Not runnable | Test fixture: policy 10Hz, control 20Hz, physics 60Hz. Multi-window trace verifies: correct number of P4/P5 ticks per window, observation at correct barrier, action hold across ticks. |

Prerequisite: WP16-B (clock-domain enforcement). Strongly dependent on WP16
spine being the default path.

## 3. Dependency Map

```
WP16 (spine consolidation)
 │
 ├── Track A (multi-fidelity) ────── independent of B, C ──┐
 │                                                          │
 ├── Track B (capability composition) ── independent of A, C │
 │                                                          │
 ├── Track D (multi-rate) ── prerequisite for C ───────────┤
 │                        │                                 │
 └────────────────────────┼─────────────────────────────────┤
                          ▼                                 ▼
                    Track C (counterfactual + experiment) ── post-WP16
```

Tracks A, B, D can start in parallel after WP16. Track C waits for D (needs
deterministic replay) and A (needs snapshot scope from fidelity profiles).

## 4. What Stage 3 Does Not Cover

These are correctly excluded from Stage 3:

- **Full counterfactual rollout at scale.** Track C delivers one slice (physics
  shard snapshot/restore, two-world branch, single-mutation comparison). Full
  worldline architecture with arbitrary branching depth is later work.
- **Full experiment orchestration.** Track C delivers `ExperimentRun` collection
  and programmatic scenario generation for parameter variation. Full curriculum
  learning, adversarial scenario generation, and capability profiling runtime are
  WP8 follow-on work.
- **All fidelity profiles.** Track A delivers CPU exact + one surrogate model
  provider for the physics shard. Sensor, weapon, and communication surrogates
  are later.
- **All capability types.** Track B delivers mobility + sensor + launcher
  composition. Survivability, command, and doctrine capabilities are later.
- **Independent clock domains.** Track D delivers nested triggering (multiples of
  base tick). Truly independent clocks with deterministic merge remain deferred.

## 5. Evidence Standard

Stage 3 tracks are runtime work. Evidence must be code-owned:

- Contract surface → C++ header or runtime struct
- Runtime behavior → test that exercises the new path, not just the contract shape
- Facade visibility → at least one facade method or binding that exposes the new
  capability
- Regression guard → existing tests (WP3-WP15 + smoke suite) continue to pass

## 6. Suggested First Track

Track D (Multi-Rate Scheduling) should be the first Stage 3 track because:

1. It closes GAP-9 completely — the last open gap from the post_wp9 analysis
2. It makes the architecture document's central example (§8, policy 10Hz /
   control 20Hz / physics 60Hz) runnable for the first time
3. It is the prerequisite for Track C (counterfactual needs deterministic replay)
4. It is the most architecturally significant change to the engine since WP0
5. `kWp10ClockDomainAdvisoryOnly = true` has been waiting for this since WP10
