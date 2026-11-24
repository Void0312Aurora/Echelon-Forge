# Simulation Experiment Platform Task Clusters

Status: `2026-10-18` finite task-cluster plan for [Simulation Experiment Platform](README.md); P3-B selected CPU checkpoint/session lifecycle and verified replay are implemented, and P3-A now has a fail-closed maintained-facade session boundary backed by native identity facts plus a bounded maintained C++ child owner and explicit Python branch-owner injection. Typed flight actions, explicit speed-change scoring, and a fixed native comparison with verified replay pass. P4-A now includes a RuntimeFacade Agent-packet bridge and optional persisted PPO export; broader mission, BC/world-model coverage, and durable recovery remain active.

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/simulation_experiment_platform_task_clusters_20260927.md`
Owner: `cross-domain architecture`
Last verified: `2026-10-18`

## Boundary Decision

This project owns the experiment/session/trace/branch boundary and its
evidence. The maintained simulation runtime remains the authority for world
state and semantics. The project must not recover the deleted counterfactual
facade by copying historical code, and it must not introduce a second stepping
owner in Python.

Durable execution authority (`ExperimentRequest`, `ResolvedCompositionPlan`,
`RunReceipt`, native `StateCheckpoint`, canonical JSON v2 envelope) belongs to
the [long-horizon architecture governance](../long_horizon_architecture_governance/README.md)
program. No cluster here writes those artifacts or a parallel checkpoint
format.

The current P3 mapping and route decision inputs are recorded in the
[runtime owner-decision preflight](p3_runtime_owner_decision_preflight_20261014.md).
The selected native branch contract is recorded in the
[P3-B design](p3b_native_branch_consumer_design_20261014.md).

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | n/a / n/a | Freeze architecture boundary and evidence baseline. | `README.md`, `*_current_status_*.md`, this plan, owner README index entries, bilingual registry rows for edited owner READMEs, tier census baseline | No runtime API or policy changes. | `git diff --check`; governance suite compared with the `origin/main` baseline; link audit. | README, status, and plan agree on current/held surfaces; no new governance failure versus baseline. | Serial first. | 2 | `pass` |
| `P1-A` | main thread | n/a / n/a | Define session, snapshot identity, transition, decision-window, and branch contracts. | `python/experiment/contracts.py`; `tests/experiment/test_experiment_contracts.py` | No backend snapshot implementation; no C++ header until a C++ consumer exists (P3). | `pytest tests/experiment/`; round-trip and rejection tests. | Each field has owner, version, provenance, and rejection behavior. | After P0; serial with P1-B. | 2 | `pass` |
| `P1-B` | main thread | n/a / n/a | Define the trace manifest, branch lineage, and export payload. | `python/experiment/trace.py`; `tests/experiment/test_trace_contract.py` | No replacement of existing episode files; no event journal until a backend emits events (P3). | Unit tests; deterministic digest fixtures; `git diff --check`. | Same input produces stable manifest/trace identity. | After P0; can follow P1-A, not edit its normative headers. | 2 | `pass` |
| `P2-A` | main thread | n/a / n/a | Build reference session and immutable timeline graph. | `python/experiment/reference_session.py`; `tests/experiment/test_reference_session.py`; toy step-reward factoring in `python/experiment/counterfactual_toy.py` | No claim of physical realism; no separate timeline module while the session is its only consumer. | Focused pytest; branch serialization; restore/fork isolation tests; mutation probes on the isolation and determinism gates. | Reference backend passes determinism, restore, and sibling isolation gates. | Requires P1-A/B. | 3 | `pass` |
| `P2-B` | main thread | n/a / n/a | Correct the toy canary baselines, pin the horizon-stopping hazard, then turn it into protocol fixtures without widening its evidence claim. | `python/experiment/counterfactual_toy.py`; `tests/experiment/test_counterfactual_toy.py`; toy README only if needed | No maintained runtime or training conclusion. | Toy tests plus protocol fixture checks. | Uniform probing is evenly spaced; the stopping hazard is pinned; toy outputs carry explicit `synthetic`/`toy` evidence labels. | Baseline correction may run before P1; label work requires P1-B. | 2 | `pass` |
| `P3-A` | main thread | n/a / n/a | Keep a capability-negotiated session adapter for setup/step/observation and report native branch support. | `python/experiment/runtime_candidate.py`; `python/experiment/runtime_facade_backend.py`; `src/runtime/facade/`; `python/rl/runtime/`; `tests/experiment/`; `tests/runtime/` | No policy-visible truth widening; Python fork publication requires an explicit caller-owned action/ref translator. | Adapter contract tests; runtime smoke; deterministic selected-slice replay; maintained native child smoke; bound session branch test. | Maintained setup runs once and returns exact Agent refs; each accepted step advances native identity exactly once; native C++ identity and child owner remain authoritative; missing identity, packet capability, external mutation, and missing branch owner reject closed. | Requires P2-A; the maintained CPU C++ owner and explicit Python owner-injection seam are implemented. | 3 | `pass (selected slice; owner injection required)` |
| `P3-B0` | main thread | n/a / n/a | Freeze the native branch lifecycle, state scope, identity, isolation, and acceptance contract. | `p3b_native_branch_consumer_design_20261014.md`; native contract headers/tests | No implementation that aliases replacement transfer to branching. | Design review; state-category and failure-path matrix; link/diff checks. | Owner authority and branch gates are explicit before executor code. | Serial first within P3-B. | 2 | `pass` |
| `P3-B` | main thread | n/a / n/a | Expose branch restore through the native checkpoint authority with branch isolation at the backend boundary. | `src/core/engine/`; `src/runtime/host/`; `src/runtime/facade/`; `src/runtime/contracts/`; `src/tests/` | No observation-only pseudo-snapshot; no historical API copy; no second checkpoint format. | Snapshot identity, RNG/event order, continuation equivalence, sibling isolation, rejection tests. | The selected twelve-owner CPU scope restores an equivalent continuation and keeps the parent usable; the maintained C++ facade exposes a bounded native child owner and the Python session can consume it through explicit owner injection. Broader mission coverage remains separate. | Requires P3-B0; selected native implementation, maintained CPU owner, and Python owner seam are complete. | 4 | `pass (selected CPU + maintained native owner)` |
| `P3-C` | main thread | n/a / n/a | Connect typed flight controls and an explicit diagnostic evaluator to native branches. | `python/experiment/native_pilot.py`; `native_pilot_comparison.py`; native integration action codec; focused tests | Candidate CPU diagnostic only; no maintained policy-observation or training claim. | Three-seed fixed paired controls, actual motion difference, full reward/state replay, invalid-action rejection. | Declared controls change native state; source remains isolated and both continuations replay. | Requires selected P3-B checkpoint support. | 3 | `pass` |
| `P4-A` | main thread | n/a / n/a | Add audited trace projections and a validated numeric learner export boundary for PPO, BC, world-model, and evaluation consumers. | `python/experiment/trace_projection.py`; `python/experiment/numeric_observation_adapter.py`; `python/experiment/runtime_facade_observation.py`; `native_pilot_comparison.py`; focused experiment tests | No learner-specific ownership of runtime truth; no fabricated observation vectors; no implicit action/reward encoding. | Fixed split/seed projection tests; checkpoint/manifest identity tests; explicit source/shape rejection; `EpisodeStore` sidecar round trip; persisted selected-branch export. | Projections preserve branch ancestry and comparison protocol; the fixed native pilot captures packets at export barriers and can persist selected PPO branches through `EpisodeStore`; production publication across admitted mission surfaces and broader learner coverage remain open. | Requires P3; can split by consumer after common schema. | 3 | `partial` |
| `P5-A` | main thread | n/a / n/a | Add alternate branch executors and scheduler capability negotiation. | `python/experiment/`; `src/runtime/contracts/`; `tests/experiment/`; selected backend adapters | No premature remote/distributed deployment. | Selected-slice parity and cost/provenance reports. | Alternate executors pass common semantics and report unsupported capabilities. | Requires P3/P4; serial acceptance. | 3 | `planned` |
| `P6-A` | main thread | n/a / n/a | Produce acceptance, residual, index, and archive updates. | `*_acceptance_*.md`; architecture indexes; review package | No expansion of accepted capability claims. | Closure audit, focused tests, link checks. | Owner README and residual map synchronized. | Serial last. | 1 | `planned` |

## Dispatch Rules

- Every implementation packet maps to exactly one cluster above.
- Public contracts, normative tables, and status lines have one serial owner.
- Acceptance and closure clusters remain serial.
- A cluster that reaches its round cap is re-scoped before another wave is added.
- Toy, synthetic, runtime, and maintained evidence labels remain separate.
- No branch executor may bypass observation provenance or runtime action
  legality.

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
evidence boundary:
```

## Validation Plan

```bash
python -m pytest tests/experiment -q
python -m ruff check python/experiment tests/experiment
python -m pytest tests/architecture/governance -q   # compare with origin/main baseline
python -m tools.maintenance.internal_code_governance --changed-from origin/main
git diff --check
```

In a linked worktree without a local build, set `CMO_BUILD_DIR` to a checkout
build that contains `ef_py`: `tests/conftest.py` requires one even for
standard-library tests. Runtime clusters (P3+) add their C++ build/test
commands.

Runtime and backend clusters must add their exact focused commands to the
cluster handoff. Full-suite execution is not a substitute for the selected
contract gates.

## Acceptance Criteria

- The reference session and maintained runtime share versioned contracts.
- A full snapshot has explicit scope, identity, restore barriers, and failure
  behavior.
- Branch results are immutable, lineage-preserving, and policy-provenance safe.
- Training exports can be regenerated from canonical traces.
- Backend-specific acceleration does not create a second semantic authority.

## Residual Map

Immediate:

- The native CPU branch barrier, child executor, checkpoint clone, and session
  restore/historical fork/verified replay integration are implemented.
- The typed pilot backend dispatches maintained flight controls and measures
  speed changes under a bound fixed protocol. Both alternatives pass full
  native replay; the digest-only lifecycle backend retains placeholder rewards.
- The P4-A projection contract now produces fixed training/evaluation seed
  splits for PPO, BC, world-model, and evaluation consumers, preserving branch
  ancestry and provenance. The learner adapter now requires an explicit packet
  sequence for one Agent and explicit branch selection; the fixed native pilot
  captures barrier-time packets from the shadow candidate owner and can persist
  selected PPO exports with an auditable `EpisodeStore` sidecar. The
  RuntimeFacade packet bridge is explicit about Agent refs and source surface.
  The toy canary stays synthetic; production mission-wide publication and
  BC/world-model exports remain open.

Follow-on:

- Persisted native checkpoint recovery, event-journal export, and broader owner
  coverage beyond the selected in-process CPU lifecycle.
- Training projection integration with existing PPO/Dreamer surfaces.

Deferred:

- Distributed scheduler, remote service adapter, GPU-resident branch execution,
  and large-scale multi-agent search.
