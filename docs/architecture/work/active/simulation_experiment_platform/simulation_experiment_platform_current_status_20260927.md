# Simulation Experiment Platform Current Status

Status: `2026-09-27` initial baseline for the active architecture package.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/simulation_experiment_platform_current_status_20260927.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-27`

## Baseline Revision

- Preparation branch: `codex/counterfactual-experiment-prep`
- Preparation revision: `a3e6d704`
- Baseline runtime revision: `origin/main` at `9ee4558e`
- Existing preparation package: `docs/learning/work/issues/adaptive_counterfactual_search/`

## Evidence Census

| Surface | Finding | Evidence boundary |
| --- | --- | --- |
| Runtime facade | Maintained batch setup, stepping, observations, tasking, events, and window execution exist. | No generic full-state snapshot/restore/fork is exposed. |
| Python runtime | `WorldBatchVecEnv` owns maintained batch adapter behavior and SB3-compatible lifecycle. | It must not become the long-term branch graph owner. |
| Provenance | Agent-shim vocabulary distinguishes maintained observation, decision belief, raw truth, and diagnostics. | Branch traces must retain these labels. |
| Replay | CUDA resident replay contracts define selected-field comparison and snapshot-version reporting. | They are candidate backend replay evidence, not a generic counterfactual contract. |
| Episode storage | `EpisodeStore` stores arrays and optional expert actions. | It lacks immutable branch lineage, runtime profile, and manifest identity. |
| Toy canary | Candidate selection, deterministic toy branches, horizon effects, and interaction residual are tested. | Results are synthetic/toy only. |

## Maturity Matrix

| Capability | State | Next gate |
| --- | --- | --- |
| Stable experiment ownership | accepted | P0-A package and owner routing accepted |
| Versioned session/branch contracts | planned | P1-A contract review |
| Canonical trace/manifest | planned | P1-B deterministic digest fixtures |
| Reference timeline backend | planned | P2-A restore and isolation tests |
| Maintained CPU runtime adapter | held | P3-A after reference contracts |
| Native full-state snapshot | held | P3-B explicit state-ownership review |
| Training projections | held | P4-A fixed split and provenance tests |
| GPU/distributed execution | deferred | P5 selected-slice parity |

## Explicit Non-Claims

This package currently does not establish:

- causal validity of counterfactual results;
- runtime snapshot/restore support;
- policy improvement or knowledge transfer;
- combat effectiveness, lethality, or real-world validity;
- GPU or distributed branch throughput;
- superiority of reward-triggered or TD-triggered candidate selection.

## Immediate Sequence

1. Complete P0-A documentation and source-boundary review.
2. Freeze P1 session, snapshot, branch, transition, and manifest vocabulary.
3. Build a reference backend whose tests define the contract for future runtime
   adapters.
4. Only then design the maintained CPU snapshot and facade integration.

## Residual Register

| ID | Owner | Reason | Exit condition |
| --- | --- | --- | --- |
| `R1` | `architecture/runtime-facade` | No generic full-state snapshot API. | P1 contract accepted and P3 implementation passes restore gates. |
| `R2` | `architecture/runtime-workflow` | Current Python adapter owns substantial step-time orchestration. | Session adapter consumes maintained facade request/result contracts. |
| `R3` | `learning/training` | Existing episode files cannot express branch lineage. | Canonical trace projection and compatibility export are accepted. |
| `R4` | `architecture/runtime-backend` | Backend-specific replay contracts are not common semantics. | Selected-slice parity contract is shared by each admitted backend. |

## Status Rule

The package stays `active` while P0/P1 contracts are being implemented. It may
not be marked `accepted` from toy tests alone. Runtime and training claims need
their own evidence records and acceptance gates.
