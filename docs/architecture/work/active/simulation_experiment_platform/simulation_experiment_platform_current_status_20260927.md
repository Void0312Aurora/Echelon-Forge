# Simulation Experiment Platform Current Status

Status: `2026-10-18` P0/P1/P2 are complete. P3 supports the selected native
CPU checkpoint/session lifecycle, typed flight controls, explicit speed-change
scoring, and a fixed branch comparison with verified replay. P4-A now provides
an audited lineage-preserving trace projection with fixed training/evaluation
seed splits. P4-A now has an explicit RuntimeFacade Agent-packet bridge and
optional persisted EpisodeStore exports for selected native branches. P3-A/B
now includes the maintained C++ identity/child owner and an explicit Python
session owner-injection path, validated through nested branches and Agent packet
reads. Broader mission coverage and durable recovery remain incomplete.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/simulation_experiment_platform_current_status_20260927.md`
Owner: `cross-domain architecture`
Last verified: `2026-10-18`

## Baseline Revision

- Preparation branch: `codex/counterfactual-experiment-prep`
- Initial baseline: `origin/main` at `9ee4558e` (2026-09-27)
- Current baseline checked for the preflight: `origin/main` at `81bf21f093` on 2026-10-14
- Existing preparation package: `docs/learning/work/issues/adaptive_counterfactual_search/`
- P3 preflight: [`p3_runtime_owner_decision_preflight_20261014.md`](p3_runtime_owner_decision_preflight_20261014.md)
- P3-B native branch design: [`p3b_native_branch_consumer_design_20261014.md`](p3b_native_branch_consumer_design_20261014.md)
- Native session checkpoint/replay: [`native_session_checkpoint_replay_20261015.md`](native_session_checkpoint_replay_20261015.md)
- Native flight-control comparison: [`native_pilot_action_comparison_20261015.md`](native_pilot_action_comparison_20261015.md)

## What Changed Since The Initial Baseline

- `origin/main` landed the long-horizon architecture governance program. It
  owns `ExperimentRequest`, `ResolvedCompositionPlan`, `RunReceipt`, the native
  `StateCheckpoint`, and the `echelon_forge.canonical_json.v2` envelope. This
  package now routes durable authority there instead of defining its own.
- P0-A closure: owner/index links, document metadata, the bilingual registry
  entries for the two edited owner README pairs, and the document tier census
  were reconciled. The README and this file no longer carry two different
  residual lists.

## Evidence Census

| Surface | Finding | Evidence boundary |
| --- | --- | --- |
| Runtime facade | Maintained batch setup, stepping, observations, tasking, events, window execution, native identity facts, and an opaque CPU child branch exist. | The branch is in-process; Python publication requires an explicit caller-owned action/ref translator and does not provide portable recovery. |
| Python runtime | `WorldBatchVecEnv` owns maintained batch adapter behavior and SB3-compatible lifecycle. | It must not become the long-term branch graph owner. |
| Provenance | Agent-shim vocabulary distinguishes maintained observation, decision belief, raw truth, and diagnostics. | Branch traces must retain these labels. |
| Replay | CUDA resident replay contracts define selected-field comparison and snapshot-version reporting. | They are candidate backend replay evidence, not a generic counterfactual contract. |
| Episode storage | `EpisodeStore` stores arrays and optional expert actions. | It lacks immutable branch lineage, runtime profile, and manifest identity. |
| Native checkpoint | Route B branch execution and opaque checkpoint cloning reuse the twelve-row owner registry and native transfer authority. | In-process, dark/shadow, one CPU world; no portable checkpoint format or production publication. |
| Toy canary | Candidate selection, deterministic toy branches, horizon effects, and interaction residual are tested. | Results are synthetic/toy only. |
| Candidate discovery | `python/experiment/candidate_discovery.py` branches a synthetic causal world through the reference session and compares uniform, reward, TD, and oracle selectors on held-out seeds. | Synthetic only; results live in the counterfactual search issue. |
| Experiment contracts | The reference session and native CPU candidate adapter produce the shared session, snapshot, branch, transition, and manifest contracts. | Python retains identity projections and opaque handles; authoritative payloads stay native. |

## Maturity Matrix

| Capability | State | Next gate |
| --- | --- | --- |
| Stable experiment ownership | accepted | P0-A closed |
| Versioned session/branch contracts | pass (P1-A) | P2-A reference session consumes them |
| Canonical trace/manifest | pass (P1-B) | P2-A reference session emits them |
| Reference timeline backend | pass (P2-A) | P2-B toy evidence labels; P3 owner decision |
| CPU runtime candidate adapter | Selected flight controls, explicit scoring, saved checkpoint restore, replay, maintained facade identity, native child owner, and injected Python branch-owner tests pass | Mission-specific owners, broader mission coverage, and durable recovery |
| Native full-state snapshot | Selected CPU checkpoint continuation, historical/nested forks, and trace replay pass | Broader owner coverage and durable recovery remain unproven |
| Training projections | partial (P4-A) | `trace_projection.py`, `numeric_observation_adapter.py`, and `runtime_facade_observation.py` provide lineage-safe projections, a RuntimeFacade Agent-packet bridge, and optional persisted `EpisodeStore` exports; the fixed native pilot remains open-loop |
| GPU/distributed execution | deferred | P5 selected-slice parity |

## Explicit Non-Claims

This package currently does not establish:

- causal validity of counterfactual results;
- generic or persisted runtime snapshot/restore support; the session restores
  explicitly saved in-process CPU checkpoints into fresh continuation branches;
- generic action-dependent combat comparisons; the demonstrated comparison is
  one fixed open-loop flight-control diagnostic with a declared speed evaluator;
- policy improvement or knowledge transfer;
- combat effectiveness, lethality, or real-world validity;
- GPU or distributed branch throughput;
- superiority of reward-triggered or TD-triggered candidate selection.

## Immediate Sequence

1. Integrate explicit action/ref owners for additional mission surfaces while
   keeping native state ownership in the maintained C++ facade.
2. Broaden scenario and state-owner coverage beyond the fixed flight-control
   diagnostic, retaining explicit action and evaluator definitions.
3. Broaden maintained runtime numeric observation sources and direct
   learner-dataset exports beyond the fixed pilot across admitted mission
   surfaces; keep the native candidate evidence label.
4. Extend durable recovery through the existing native checkpoint authority,
   then qualify alternate backends under the shared semantics.

The checkpoint/session integration is implemented: save a native clone, advance
the source, restore or fork from saved history, fork descendants through their
own handle, and verify a recorded continuation before adding it to the manifest.
Three real aircraft seeds exercise this lifecycle. Source traces and siblings
stay unchanged, and failed replay attempts do not enter the manifest.

Done since the initial baseline: the toy uniform selector now probes evenly
spaced points and the doubling-horizon stopping hazard is pinned (P2-B baseline
correction); P1-A/P1-B contracts landed; the P2-A reference session passes
determinism, restore, and sibling-isolation tests, and mutation probes confirmed
those tests fail when isolation, intervention, fork admission, seed binding, or
determinism is broken. P2-B passed: the Phase 1 candidate-discovery benchmark
runs every oracle branch through a pluggable reference world, labels its output
`synthetic`, and binds each seed to a trace-manifest digest.

## Residual Register

This is the single residual register for the package.

| ID | Owner | Reason | Exit condition |
| --- | --- | --- | --- |
| `R1` | `architecture/runtime-facade` with the long-horizon governance checkpoint owner | Native CPU checkpoint, typed flight actions, explicit scoring, and fixed comparison pass; broader mission/owner coverage and durable recovery remain incomplete. | Broader declared mission coverage and durable recovery pass continuation/isolation/provenance tests beyond the fixed flight diagnostic. |
| `R2` | `architecture/runtime-workflow` | The Python world-batch adapter still owns substantial step-time orchestration. | A session adapter consumes maintained facade request/result contracts only. |
| `R3` | `learning/training` | The fixed native pilot captures maintained Agent packets at native export barriers; a RuntimeFacade packet bridge and optional persisted PPO `EpisodeStore` export now exist, but production publication across admitted mission surfaces and BC/world-model coverage remain unproven. | The maintained RuntimeFacade-backed packet provider feeds admitted mission surfaces and persists learner-compatible PPO/BC/world-model exports while preserving the projection digest and split boundary. |
| `R4` | `architecture/runtime-backend` | GPU-resident replay contracts are backend-specific and quarantined. | P5 selected-slice parity contract is shared by each admitted backend. |
| `R5` | `learning/training` | The adaptive toy canary has synthetic evidence only. | An adaptive-selection experiment runs on maintained mission observations with a fixed protocol; the candidate flight diagnostic alone does not close this residual. |

## Status Rule

The package stays `active` while P0/P1 contracts are being implemented. It may
not be marked `accepted` from toy tests alone. Runtime and training claims need
their own evidence records and acceptance gates.
