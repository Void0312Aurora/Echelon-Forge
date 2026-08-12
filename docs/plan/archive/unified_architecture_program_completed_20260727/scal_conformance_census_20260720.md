# SCAL Conformance Census (2026-07-20)

Language:
- English canonical: `scal_conformance_census_20260720.md`
- Chinese companion: [scal_conformance_census_20260720.zh.md](scal_conformance_census_20260720.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/archive/unified_architecture_program_completed_20260727/scal_conformance_census_20260720.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-20`
Baseline commit: `779a821b`

Status: T0 stage-conformance and information-state census for the
[Unified Architecture Program](README.md). Findings below are the evidence
basis for baseline amendments (a)-(e), merged into
[Simulation System Architecture Design](../../../architecture/standards/simulation_system_architecture_design.md)
as sections 1.5, 6.1/7.1, and 15-17. This document is a descriptive census
register (`reference`), not an independent review: it records findings for
the verified baseline state and carries no review verdict. Independent
review of the T0 iteration is dispatched separately.

## 1. Violation Register

Stage-conformance and information-state-layer violations found against the
amended baseline. Compliant paths are omitted; only violations are listed.

| ID | Category | Location | Violation |
|----|----------|----------|-----------|
| V1 | Loader stage aggregation | `ScenarioLoader` (`loading.py` load/finalize chain; `core.py` `compute_full_step`) | Concentrates `P0`/`P1`/`P2`/`P3`/`P10` in one object with no declared stage contract. |
| V2 | Loader stage aggregation | `finalize_loaded_world` | Spans `P1`/`P2`/`P6` and reads `World Truth` directly instead of through a sensed/track export. |
| V3 | Observation adapter cross-layer consumption | `get_policy_agent_observation` / `get_policy_instrument_state` | Policy-path consumers read `World Truth` directly; no declared information-state layer. |
| V4 | Observation adapter cross-layer consumption | `mission_observation` python-owned modes: `naval_screen_station_v1`; `air_combat_c2_roe_v1`/`v2` | Parallel lifecycle plus truth leak: the naval mode reads Track+Picture+Agency outside a facade export; the air modes read Track+Picture+Agency and source `truth.contacts` from the truth layer. |
| V5 | Reward truth leak | `reward_runtime/air_combat.py` | Reads `WorldTruth` fields `engagement`/`kill`/`missiles_remaining` directly. |
| V6 | Reward truth leak | `reward_runtime/naval.py` | Reads `WorldTruth` entity position directly. |
| V7 | VecEnv cross-stage bundling | `step_evaluation` | Bundles `P9`+`P10` (effects/damage and observation export) with no stage boundary. |
| V8 | VecEnv cross-stage bundling | `WorldBatchVecEnv.step` | Aggregates `P4`/`P5`/`P10` (control, physics, observation export) inside one step call. |
| V9 | Single-world parallel lifecycle | `single_world_batch_runtime` | Wraps the batch runtime with a second lifecycle implementation instead of reusing the shared one. |

## 2. Cross-Boundary Bypass Inventory

Direct-construction paths on the maintained surface (`python/` and
`gym_envs/`, excluding test and diagnostics surfaces), measured against
Kernel Invariant G1 (target = 1, facade only). Re-verified against baseline
`779a821b` by source search for `ef_py.SimulationKernel(` and
`ef_py.WorldBatchRuntime(` construction sites.

| Item | Finding |
|------|---------|
| Maintained cross-boundary path count | 1 — the facade path itself: `RuntimeFacadeAdapter` constructs `ef_py.RuntimeFacade(world_count)` (`python/rl/runtime/world_batch/adapter.py`). Zero additional `ef_py.SimulationKernel(` or `ef_py.WorldBatchRuntime(` construction sites exist on the maintained surface, so on the direct-construction axis the G1 target (one, facade only) is structurally met. |
| `UniversalEnv` status | Already demoted: `gym_envs/universal_env.py` is a fail-fast compatibility shell whose constructor raises "raw ef_py.SimulationKernel constructor path has been removed"; the WP24 architecture gate `test_wp24_universal_env_raw_kernel_constructor_path_is_removed` pins the removal. It is not a bypass path at this baseline. |
| WP24 exemption entries | 1 — `tests/runtime/engagement/test_facade_engagement_evidence_gates.py` (one `ef_py.WorldBatchRuntime(` construction; `diagnostics_only` / `test_only`). The scoped escape-hatch allowlist's maintained tier is empty by gate assertion. |
| Test/diagnostics direct-construction paths | Present and catalogued (world-batch/runtime/GPU test suites, the `python/testing/contracts/` harness, `tools/` diagnostics and geometry probes, the `examples/viz` demo server); excluded from the maintained metric by definition. |
| Convergence gap | `ScenarioLoader`'s kernel-reference seam: the loader still stores an untyped runtime handle (`self.sim`) with a wide `loader.sim` call surface (tasking bridge, behavior runtime, loading, vec-env support), inventoried by WP22 marker gates rather than typed by a declared contract. On the maintained batch path the handle is the facade-backed `_ScenarioLoaderRuntimeProxy` built by `RuntimeFacadeAdapter.make_scenario_loader`, not a raw kernel; raw-kernel injection survives only in the contract-test harness. The gap is contracting this loader seam, not `UniversalEnv` migration. |

## 3. G4 Declaration Mechanism And First-Batch Consumers

G4 ("every observation/reward consumer declares its information-state layer")
is proposed as three parts, styled on the `mission_obs_taxonomy` `OWNER`
mapping precedent:

1. Module-level constants — `INFORMATION_LAYER_CONSUMED` /
   `INFORMATION_LAYER_PRODUCED` / `SEMANTIC_STAGE` frozenset declarations;
   zero runtime overhead.
2. Centralized registry — a `python/architecture/information_layer_registry.py`-style
   module.
3. AST gate — checks declaration presence, registry consistency, and bans
   non-diagnostic consumers from reading `WorldTruth` unless the path is
   facade-compiled.

First-batch consumers, in priority order:

| # | Consumer | Priority | Register entry |
|---|----------|----------|-----------------|
| 1 | `mission_observation` python-owned modes | Highest | V4 |
| 2 | `reward_runtime/air_combat.py` | High | V5 |
| 3 | `reward_runtime/naval.py` | High | V6 |
| 4 | `execution_runtime` / mainline | Medium | — |
| 5 | `step_evaluation` | Medium | V7 |
| 6 | `universal_env` observation assembly | Medium | — |
| 7 | `world_batch` vec-env observation batching | Low | already conformant |

## 4. Composition-Rule Enforceability Assessment

Enforceability of the three cross-graph composition rules named in the
program README (semantic-to-causal lowering, causal-to-temporal via
read/write sets, information-to-agency via view specs).

| Rule | Anchor | Immediately gateable | Deferred |
|------|--------|----------------------|----------|
| Semantic -> Causal | Scenario compiler's `CompiledScenario` | Compiled-product immutability (frozen dataclass; AST ban on post-`P1` mutation) | `scenario_data["task_order"]` is still mutated by `finalize`. |
| Causal -> Temporal | `runtime_window_coordinator` and the WP16 spine fixture's `read_set`/`write_set` declarations | Fixture declarations checked against the facade call graph for consistency | Python-side steps carry no declared read/write sets (blocked on the T2 substrate). |
| Information -> Agency | `run_maintained_window`'s `AgentRole` provenance enforcement | Extend the provenance-tag check to non-window paths | `ObservationViewSpec` is not yet a runtime structure (materializes at T8). |

Amendments (a)-(e) drafted from this census are recorded in
[Simulation System Architecture Design](../../../architecture/standards/simulation_system_architecture_design.md).
Registry refresh and iteration-ledger registration are out of scope for this
document.
