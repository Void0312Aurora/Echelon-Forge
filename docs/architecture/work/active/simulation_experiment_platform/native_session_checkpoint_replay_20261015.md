# Native Session Checkpoint And Replay

Status: `2026-10-15` selected CPU session lifecycle implemented. Typed flight
actions and explicit evaluation are covered by the follow-up comparison record.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/native_session_checkpoint_replay_20261015.md`
Owner: `cross-domain architecture`
Last verified: `2026-10-15`

## Behavior

The native candidate is loaded from the separate, source-only
`ef_runtime_candidate_py` extension. It imports the existing `ef_py` setup DTOs
without adding candidate types or candidate link dependencies to `ef_py`.
Facade-only builds omit the experiment extension.

`RuntimeCandidateSession.checkpoint(branch)` retains an independent opaque
native clone and returns its existing `SnapshotRef`. The retained handle is
private to the session. The native owner registry continues to own every
payload, serializer, import transaction, and resource identity.

`restore(snapshot, parent=..., intervention=..., label=..., horizon=...)`
creates a fresh continuation branch from a saved checkpoint. It preserves the
source trace and descendants. The caller supplies the first-step intervention,
which remains part of the existing branch identity contract. A historical
`fork` uses the same saved native handle. A current-head fork on a child uses
that child's native handle rather than the baseline candidate.

```python
session.step(actions, observation_provenance="decision_belief_packet")
saved = session.checkpoint()
session.step(actions, observation_provenance="decision_belief_packet")

restored = session.restore(
    saved, intervention=actions, label="restored", horizon=1
)
session.step_branch(
    restored, actions, observation_provenance="decision_belief_packet"
)
replayed = session.replay(session.baseline, saved, label="verified_replay")
assert session.head(replayed) == session.head()
```

`replay` executes the recorded suffix from the checkpoint on a private child.
Each transition must match the original action, reward, source/target snapshot,
step, termination, and observation provenance. Snapshot identity includes the
native state digest, RNG digest, and event cursor. Only a fully matching replay
is added to the session manifest. A failed replay leaves the source trace and
saved checkpoint usable. Export uses the existing `TraceManifest` and introduces
no checkpoint wire format.

Checkpoint support requires the native checkpoint and descendant-fork methods.
A step-only or partially implemented backend advertises no restore capability.
Invalid, duplicate, foreign-session, unsaved, and wrong-parent requests fail
before branch allocation. A rejected native identity is never cached as a
checkpoint. The current native producer requires a running boundary after at
least one accepted action; step-zero and terminal checkpoint creation remain
unsupported. An earlier running checkpoint can be restored after its source
branch terminates.

## Evidence And Limits

The integration tests use a real `SimulationKernel` with a moving aircraft at
three seeds (`19`, `83`, `191`). They prove checkpoint continuation, saved
historical and nested forks, parent/sibling isolation, deterministic replay,
and trace-manifest round trips. Failure injection separately checks reward,
state, RNG, event-cursor, and terminal drift and verifies that a rejected replay
does not enter the manifest. Native descendant tests also check intervention
binding and depth.

The final checks are the full experiment suite (339 tests), all 25 CTest
targets, Ruff, and the dependency/include boundary audits. Repository-wide
governance retains five failures reproduced at `origin/main` (`81bf21f093`);
the two prior integration dependency failures are fixed, and the document
census is synchronized. The [integration record](current_main_integration_20261014.md)
records the baseline comparison and the remaining failures.

This is an in-process CPU lifecycle result. The action strings currently bind
an action-envelope digest; the native control advances the kernel but does not
dispatch those strings into entity control commands. Rewards from
`RuntimeKernelCandidateBackend` are zero placeholders. The event cursor is the
native coordinator's action sequence, not a separately exported event journal.
These tests do not establish useful action interventions, scored
counterfactual comparisons, complete future owner coverage, durable recovery,
training improvements, or GPU/distributed execution.

The follow-up [flight-control comparison](native_pilot_action_comparison_20261015.md)
adds a separate typed backend with actual entity control, explicit speed-change
scoring, and isolated paired branches. The digest-only backend described above
remains a lifecycle probe. Persisted replay and broader state-owner coverage
remain separate follow-ups.
