# P3 Runtime Owner-Decision Preflight

Status: `2026-10-18` draft; the selected adapter boundary, maintained CPU
facade native owner, and explicit Python branch-owner injection are implemented.

Document kind: `decision-preflight`
Lifecycle: `draft`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/p3_runtime_owner_decision_preflight_20261014.md`
Owner: `cross-domain architecture` with `architecture/runtime-facade` and the long-horizon checkpoint owner
Preparation branch: `codex/counterfactual-experiment-p3`

## Purpose

This record maps the completed experiment-layer contracts to the current
maintained runtime and records the implemented P3 boundary. It admits the
selected CPU native owner seam and caller-injected Python action/ref translation
while keeping broader counterfactual claims outside the evidence boundary.

The experiment baseline is `b74b4219b5` on the local continuation branch. The
remote mainline checked during this preflight is `origin/main` at
`81bf21f093`. The old preparation tracking branch is gone. The two revisions
must remain separate until the owner decision identifies the small runtime
surface that can be integrated without deleting the completed experiment
package.

## Decision Summary

The current surfaces support a bounded runtime candidate and a maintained CPU
child owner. The generic Python session branch contract is available when its
caller supplies the explicit action/ref owner required to translate Agent
actions into native assignments:

- `RuntimeFacade` exposes setup, stepping, observations, tasking, engagement
  packets, and maintained windows.
- The native state-transfer candidate exposes episode identity, transition
  receipts, barrier tokens, a twelve-category state census, and replacement
  transfer validation.
- The maintained C++ facade exposes an admitted native identity read and an
  opaque sibling child whose parent remains independently usable while native
  pilot assignments execute. The Python session adapter accepts a caller-owned
  branch action/ref translator and fails closed when it is absent.
- The state-transfer candidate is replacement-scoped and dark/shadow. Its
  state categories and transfer fences must not be reinterpreted as a
  counterfactual snapshot API.

Therefore P3-A is a capability-negotiated runtime adapter, while the
maintained CPU C++ owner closes the identity/child-resource gate for its
selected native slice. Generic Python session publication is admitted only
with an explicit action/ref translation owner.

## 2026-10-17 Boundary Update

The bounded P3-A implementation now lives in
[`runtime_facade_backend.py`](../../../../../python/experiment/runtime_facade_backend.py).
It calls the maintained `RuntimeFacadeAdapter` setup/step/packet surfaces, but
requires native identity facts for state, event, and RNG. The maintained C++
facade now supplies those facts and an opaque child resource through
`native_snapshot_facts()` and `fork_native_branch()`. The Python adapter wires
branch, checkpoint, and descendant operations when a caller supplies
`branch_action_applier`; it rejects those operations when that owner is absent.

The selected CPU Route B branch executor and P3-C typed action comparison are
implemented and validated in their declared in-process shadow scope. Each
mission adapter still has to provide its explicit Agent action/ref translation
owner before publishing branches through the maintained C++ child seam.

## Contract Mapping

| Experiment contract | Current runtime evidence | Mapping state | Required decision or evidence |
| --- | --- | --- | --- |
| `SessionSpec` | `RuntimeBatchConfig`, setup requests, composition evidence, and the long-horizon plan/release/run authority | `partial` | Bind session identity to the existing runtime authority; do not let the Python contract mint a second execution plan or receipt. |
| `SnapshotRef` | `RuntimeEpisodeTransitionReceipt` carries snapshot identity/hash, episode identity, step sequence, and barrier sequence; the state census carries category digests | `partial` | Define which native identity is the source of `state_digest`, `event_cursor`, and `rng_digest`; reject a ref if any required component is unavailable. |
| `BranchRef` | Maintained C++ `RuntimeFacade::fork_native_branch` creates an opaque child from the complete native world/RNG/clock state; the Python adapter accepts an explicit caller-owned action/ref translator | `pass (selected slice)` | Keep owner-injection and native child isolation tests green; callers without the owner remain fail-closed. |
| `DecisionWindow` | `RuntimeWindowRequest`/`RuntimeWindowResult` and maintained window evidence exist | `partial` | Bind window identity, source snapshot, horizon, action owner, and termination to one runtime result; reject windows whose source identity is synthetic or stale. |
| `Transition` | `step_batch`, observation/tasking packets, window results, and episode receipts exist | `partial` | Produce one transition record with source/target state identities and admitted observation provenance; do not infer rewards or state identity from Python mirrors. |
| `TraceManifest` | No maintained runtime producer binds all branches, policy identity, and canonical trace ancestry | `blocked` | Add a runtime-candidate producer only after session and branch identity are authoritative; keep the existing manifest as the experiment-layer projection. |

The reference backend remains the normative semantic test. Its
`SnapshotRef` is an identity-only reference, its `BranchRef` records parentage
and intervention, and its `TraceManifest` rejects missing parents, broken
state chains, and policy/provenance drift. A runtime adapter must either satisfy
the same checks or fail closed with an explicit unsupported capability.

## State-Ownership Preflight

The native transfer candidate names these state categories:

1. composition/provider/system graph;
2. ECS component truth;
3. RNG state;
4. clock cadence;
5. delayed events and queues;
6. commands, links, and pending intent;
7. episode reward and termination;
8. Python loader/controller caches;
9. backend device allocations and leases;
10. in-flight requests and results;
11. external side effects;
12. diagnostics and telemetry.

This is useful ownership evidence, but it does not prove a branch snapshot.
For a counterfactual branch, the owner decision must additionally specify:

- the exact snapshot boundary and event cursor at the fork;
- whether every RNG stream and delayed queue is copied, replayed, or rejected;
- how parent and sibling writes are isolated at the authoritative backend;
- how action legality and observation provenance are checked per branch;
- how external side effects and in-flight work are rejected or made branch-local;
- how the branch result binds to the source snapshot and trace manifest;
- how terminal, stale, unsupported, and failed restores are reported.

The current candidate's replacement fence, import transaction, and N/N-1
decoder rules answer host replacement concerns. They do not answer these
branch-specific questions.

## P3 Gates

### P3-A: Runtime adapter

P3-A can proceed only as a `runtime_candidate` adapter with explicit capability
negotiation. Its first selected slice should cover one CPU world, one fixed
scenario/configuration, one seed, and one admitted action interface. Required
checks are:

- identical setup and action inputs produce identical selected-slice results;
- the source session/config/seed/policy identity is retained;
- observations expose only an admitted policy-input provenance label;
- source and target state identities are present for every transition;
- unsupported snapshot/fork operations fail closed rather than fabricating a
  Python snapshot;
- the runtime adapter does not become a second step or truth owner.

P3-A does not authorize a maintained-runtime causal claim.

### P3-B: Branch restore

The selected CPU P3-B branch executor is implemented and validated in the
declared in-process shadow scope. Its written design names the native
checkpoint producer, backend branch executor, state scope, and isolation proof.
The acceptance slice passes continuation equivalence, RNG/event-order parity,
sibling isolation, stale/terminal rejection, and deterministic trace identity.
The maintained C++ binding now supplies native identity and an isolated child
resource for the selected CPU slice. A replacement-scoped
`RuntimeStateTransferCandidate` alone still cannot close generic Python
publication; the Python adapter needs a separate action/ref translation owner.

## Required Owner Decision

Before runtime code is added, the owners must choose one of these bounded
routes:

| Route | Meaning | Consequence |
| --- | --- | --- |
| `A: candidate adapter only` | Admit setup/step/observation/window evidence and reject fork operations | Allows P3-A selected-slice work; P3-B remains held and all results stay `runtime_candidate`. |
| `B: native branch consumer` | Extend the native checkpoint authority with branch identity, copy/replay semantics, and isolation gates | The selected CPU shadow scope, maintained C++ child owner, and explicit Python action/ref owner seam are admitted; callers still opt in to branch publication by supplying that owner. |
| `C: prefix-replay executor` | Keep native state immutable and reconstruct branches by deterministic prefix replay | Avoids full native cloning but requires replay-complete inputs, event/RNG identity, and a cost/coverage report. |

Route `A` was the only route that could be started without a new native branch
authority decision. The long-term direction now selects route `B`; route `C`
remains a later executor under the same native branch contract. Neither route
may be implied by existing replay, replacement, or shadow evidence.

### Route A implementation slice

The continuation branch now contains
[`python/experiment/runtime_candidate.py`](../../../../../python/experiment/runtime_candidate.py)
and its focused tests. The maintained-facade boundary is now implemented in
[`runtime_facade_backend.py`](../../../../../python/experiment/runtime_facade_backend.py):
it accepts authoritative identity facts only through an injected native owner,
validates them against the P1 contracts, records a single-path
`runtime_candidate` manifest. The maintained C++ owner is available below that
adapter boundary, and Python branch/checkpoint/descendant operations are wired
when `branch_action_applier` is supplied; the adapter stays single-path when the
caller does not provide that owner.

### Route B continuation

The long-term native branch design is recorded in
[`p3b_native_branch_consumer_design_20261014.md`](p3b_native_branch_consumer_design_20261014.md).
The native candidate branch barrier and fresh child resource are implemented in
the selected shadow scope, and the maintained C++ facade has a bounded
world/RNG/clock child owner. Mission adapters provide explicit Python action/ref
translation at the session boundary; replacement transfer is not reinterpreted
as branching.

## Integration Rule

Do not rebase `codex/counterfactual-experiment-p3` onto `origin/main`. Route B
work continues on the separate integration branch from current `origin/main`,
with the experiment package and native runtime changes kept in separate
reviewable commits. Route A remains a fail-closed bring-up seam. Route C can be
added later as another executor of the native branch contract. Any generic
Python branch publication must retain the same native-owner evidence boundary.

## Current Evidence Boundary

This preflight establishes the selected CPU native child owner, direct binding
smoke, and caller-injected Python session branch path. Portable recovery, causal
validity, policy improvement, GPU execution, and real-world/combat validity
remain outside the evidence boundary.
