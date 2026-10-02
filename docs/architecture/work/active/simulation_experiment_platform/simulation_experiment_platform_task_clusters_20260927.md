# Simulation Experiment Platform Task Clusters

Status: `2026-09-27` finite task-cluster plan for [Simulation Experiment Platform](README.md).

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/simulation_experiment_platform_task_clusters_20260927.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-27`

## Boundary Decision

This project owns the experiment/session/trace/branch boundary and its
evidence. The maintained simulation runtime remains the authority for world
state and semantics. The project must not recover the deleted counterfactual
facade by copying historical code, and it must not introduce a second stepping
owner in Python.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | n/a / n/a | Freeze architecture boundary and evidence baseline. | `README.md`, `*_current_status_*.md`, this plan | No runtime API or policy changes. | `git diff --check`; link inspection; source census. | README, status, and plan agree on current/held surfaces. | Serial first. | 1 | `pass` |
| `P1-A` | main thread | n/a / n/a | Define session, snapshot identity, transition, decision-window, and branch contracts. | `src/runtime/contracts/experiment_*.h`; `python/experiment/contracts.py`; focused contract tests | No backend snapshot implementation. | C++ build; `pytest tests/experiment/`; schema roundtrip tests. | Each field has owner, version, provenance, and rejection behavior. | After P0; serial with P1-B. | 2 | `planned` |
| `P1-B` | main thread | n/a / n/a | Define manifest, event journal, trace lineage, and export format. | `python/experiment/manifest.py`; `python/experiment/trace.py`; `tests/experiment/test_trace_contract.py` | No replacement of existing episode files. | Unit tests; deterministic digest fixtures; `git diff --check`. | Same input produces stable manifest/trace identity. | After P0; can follow P1-A, not edit its normative headers. | 2 | `planned` |
| `P2-A` | main thread | n/a / n/a | Build reference session and immutable timeline graph. | `python/experiment/reference_session.py`; `python/experiment/timeline.py`; `tests/experiment/test_timeline.py` | No claim of physical realism. | Focused pytest; branch serialization; restore/fork isolation tests. | Reference backend passes determinism, restore, and sibling isolation gates. | Requires P1-A/B. | 3 | `planned` |
| `P2-B` | main thread | n/a / n/a | Turn the existing toy canary into protocol fixtures without widening its evidence claim. | `python/experiment/counterfactual_toy.py`; `tests/experiment/test_counterfactual_toy.py`; toy README only if needed | No maintained runtime or training conclusion. | Existing six tests plus protocol fixture checks. | Toy outputs carry explicit `synthetic`/`toy` evidence labels. | Requires P1-B; parallel with P2-A after contracts. | 2 | `planned` |
| `P3-A` | main thread | n/a / n/a | Adapt `RuntimeFacade`/`WorldBatchVecEnv` to the session interface. | `src/runtime/facade/`; `src/runtime/contracts/`; `python/rl/runtime/`; `tests/runtime/` | No policy-visible truth widening; no GPU requirement. | C++ focused tests; runtime smoke; deterministic selected-slice replay. | Maintained CPU runtime passes the reference contract suite. | Requires P2-A; serial public API integration. | 3 | `planned` |
| `P3-B` | main thread | n/a / n/a | Implement authoritative snapshot/restore and branch isolation at the backend boundary. | `src/core/engine/`; `src/runtime/facade/`; `src/runtime/contracts/`; `src/tests/` | No observation-only pseudo-snapshot; no historical API copy. | Snapshot identity, RNG/event order, continuation equivalence, rejection tests. | Full declared snapshot scope restores an equivalent continuation. | Requires P3-A; serial with P3-A. | 4 | `planned` |
| `P4-A` | main thread | n/a / n/a | Add audited trace projections for PPO, BC, world-model, and evaluation consumers. | `python/experiment/`; `python/training/`; `python/world_model/`; `tests/experiment/` | No learner-specific ownership of runtime truth. | Fixed split/seed projection tests; checkpoint identity tests. | Projections preserve branch ancestry and comparison protocol. | Requires P3; can split by consumer after common schema. | 3 | `planned` |
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
python -m pytest tests/experiment/test_counterfactual_toy.py -q
python -m pytest tests/experiment -q
python -m ruff check python/experiment tests/experiment
git diff --check
cmake --build build --target ef_test -j2
```

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

- P1 contracts and trace manifest are not implemented yet.
- The existing toy canary remains synthetic.

Follow-on:

- Native runtime snapshot/restore and event-journal integration.
- Training projection integration with existing PPO/Dreamer surfaces.

Deferred:

- Distributed scheduler, remote service adapter, GPU-resident branch execution,
  and large-scale multi-agent search.
