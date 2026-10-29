# Current Main Integration Record

Status: `2026-10-18` local Route B/P4-A implementation checkpoint; no remote
publication.

This record captures the first selective integration of the cf-exp experiment
package onto the current `origin/main` tip. It is an integration checkpoint,
not a runtime acceptance record.

## Revisions

- Base: `origin/main` at `81bf21f093a34baff64d43c01f7975e15fb09dc1`
- Source: `codex/counterfactual-experiment-p3` at `222b5cb2d5676e2305eb8cff121fd70710e198b6`
- Integration branch: `codex/counterfactual-experiment-integration`
- Integration commits: `fae82d58a0` (experiment package restore),
  `c1103131ab` (integration record), and `2eeb0bc8af` (native branch admission
  contract). The follow-up checkpoint extends that contract with a native
  sibling executor, opaque native checkpoint cloning, session restore/verified
  replay, maintained owner-adapter coverage, and typed flight-control
  comparisons with explicit speed-change scoring.

## Scope

The integration branch restores the experiment-layer contracts, reference
session, discovery/stopping/interaction modules, trace contracts, the
backend-neutral `runtime_candidate` adapter, their tests, and the related
architecture records. Route B now adds an explicit branch barrier, a
host-neutral native sibling executor, a fresh child coordinator/resource
identity, twelve-row owner export/import, and an optional native child episode
control. `RuntimeHostCandidate` now supplies the active coordinator, source
registry, lifecycle ticket, and mutation fence, so the caller cannot author
the parent source authority. `RuntimeKernelCandidate::fork_native_branch`
creates an independent child `SimulationKernel`, WAL, owner registry, and
episode control only after that transfer succeeds. A branch can now create a
second opaque native checkpoint child through the same owner transfer path;
no serialized state payload crosses the experiment boundary. The separate `ef_runtime_candidate_py` experiment extension binds those
objects, and
`RuntimeKernelCandidateBackend` feeds their native facts into
`RuntimeCandidateSession`; a missing native method or rejected admission still
fails closed. The executor remains dark/shadow and is not published through a
production host slot.

The session now retains explicitly saved native checkpoint handles, restores
them into fresh continuation branches, and forks from saved history or an
existing child's native handle. Verified replay checks the recorded suffix on
a private clone and adds it to the manifest only after all transitions match.
The original trace and sibling branches remain intact. Details and limits are
recorded in [the session lifecycle record](native_session_checkpoint_replay_20261015.md).

## Lifecycle Checkpoint Verification

From the integration worktree:

```text
CMO_BUILD_DIR=/tmp/cmo-routeb-build python -m pytest tests/experiment -q
339 passed in 33.42s
git diff --check
```

The experiment suite therefore runs against the current mainline checkout.
This verifies Python contract compatibility, deterministic reference/toy
behavior, and the selected bound native CPU sibling continuation.

The native checkpoint and branch executor pass:

```text
cmake --build /tmp/cmo-routeb-build -j2
ctest --test-dir /tmp/cmo-routeb-build --output-on-failure
100% tests passed, 0 tests failed out of 25
```

`runtime_host_candidate`, `runtime_kernel_candidate`, and
`runtime_kernel_candidate_parity` passed after building their targets. Focused
coverage includes the branch barrier, real child continuation receipt,
parent/child and sibling isolation, RNG/event-order rejection, failure
rollback, a real `SimulationKernel` twelve-row owner-registry transfer, and a
checkpoint child that continues with the same state/event/RNG digests as its
source branch (51 native assertions, including saved-history descendant
intervention binding and depth). The built `ef_runtime_candidate_py` extension was also
exercised directly through the same checkpoint continuation.

The focused Python candidate suite passes 25 tests. Three seeds run session
checkpoint/restore, historical/nested forks, verified replay, and manifest
round trips with a real moving aircraft. Failure injection verifies that state,
RNG, event-cursor, terminal, or reward drift rejects a replay without changing
the manifest or source checkpoint.

The candidate binding now lives in a separate, source-only
`ef_runtime_candidate_py` extension under the runtime integration owner.
`ef_py`, `ef_facade`, and `ef_facade_backend` cannot transitively reach the
candidate targets; the real-module test also checks that `ef_py` does not
expose `RuntimeKernelCandidate`. Facade-only builds omit the experiment
extension.

The maintained-facade P3 boundary is explicit in
`python/experiment/runtime_facade_backend.py`. It requires maintained setup,
step, and packet capabilities plus an injected native identity owner; it calls
`RuntimeFacadeAdapter.step_batch()` exactly once per transition and rejects
identity changes outside that boundary. When a caller also supplies the
explicit branch action/ref owner, the same adapter exposes native branch,
checkpoint, descendant-fork, and packet operations; without that owner it
remains fail-closed and single-path.

Governance was compared in detached checkouts of the unchanged base
`81bf21f093` and the previous integration head `d814a651bc`: respectively six
and eight tests failed. Separating the extension fixes the two integration
dependency violations. The document census was refreshed for the tracked
990-document surface, including the new lifecycle record. The resulting
governance run has `210 passed, 5 failed, 1 xfailed`; each remaining failure
also occurs at the mainline baseline: unrelated review metadata, a duplicate
bilingual registry entry, unavailable Windows sustainability build artifacts,
diagnostics script sprawl, and the broadphase source-layout assertion. This
is not an all-green repository governance result. Internal-code governance
reports zero errors and warnings; Ruff and diff checks pass.

The pinned Flecs JSON writer now preserves round-trip double precision and
negative zero. Its JSON number reader consumes signed exponents, distinguishes
exponent forms from large integers, and rejects malformed or oversized tokens
before copying into its fixed buffer. The owner adapter uses ordinary JSON
serialization instead of expanding floats into long decimal tokens. Native
coverage includes ordinary, near-underflow, subnormal, maximum finite, large
integral, and negative-zero values through whole-world transfer, plus invalid
number rejection (302 focused assertions). An isolated AddressSanitizer check
of the patched reader passed; this is not a full-runtime sanitizer result.

## Typed Action Comparison Verification

The follow-up [flight-control comparison](native_pilot_action_comparison_20261015.md)
adds actual maintained pilot commands, logical entity resolution after import,
an explicit evaluator, and a fixed open-loop protocol. Three seeds each compare
idle/full throttle for 20 steps from the same checkpoint and verify complete
replay of both alternatives without changing their source. Both decelerate;
full throttle finishes 0.965 m/s faster. The fixture has no random disturbance
and establishes no statistical robustness or policy-improvement claim.

## P4-A Trace Projection Verification

`python/experiment/trace_projection.py` projects the canonical manifests into
one deterministic compatibility table for `ppo`, `bc`, `world_model`, and
`evaluation`. Split assignment is session-seed based, so all branches and
descendants in one manifest stay together. The projection retains manifest and
branch identity, parentage, state digests, actions, integer rewards, termination,
and observation provenance; it deliberately does not invent numeric observation
vectors. The native report regenerates all four consumer summaries from its
three manifests: 243 rows total, 162 training rows from seeds 19/83, and 81
evaluation rows from seed 191.

The targeted Agent-packet adapter and native comparison tests pass 25 tests. The full report
contains projection digests and two independent CLI invocations remain
byte-identical at SHA-256
`17615fbe740af01cd1f57ee2225cc1f3e02246ee90aae5024f4b6c9c95f15d36`.
This closes the common projection contract. The maintained
`python/experiment/numeric_observation_adapter.py` boundary now accepts an
explicit packet sequence from one declared Agent observation interface, records
Agent and packet identity/provenance, and writes an auditable `EpisodeStore`
sidecar carrying the projection digest and split/lineage metadata. Selected
branch digests are required; replay and baseline branches are not implicitly
learner episodes. The fixed native pilot remains a candidate diagnostic and
now captures Agent packets at each native export barrier from the shadow
candidate packet owner and builds a PPO export for explicitly selected
branches, and `--numeric-export-root` now persists those selected
PPO episodes through `EpisodeStore` with an auditable sidecar digest. The new
`RuntimeFacadeAgentObservationProvider` supplies the maintained packet-reader
surface from explicit Agent refs, including direct facade vector-overload
adaptation; missing surfaces, missing maintenance status, ambiguous refs, and
missing packet identity fail closed. This remains candidate evidence until
admitted production mission surfaces consume the provider.

Final checks after this change:

```text
CMO_BUILD_DIR=/tmp/cmo-routeb-build python -m pytest tests/experiment -q
373 passed
cmake --build /tmp/cmo-routeb-build -j2
ctest --test-dir /tmp/cmo-routeb-build --output-on-failure
100% tests passed, 0 tests failed out of 25
CMO_BUILD_DIR=/tmp/cmo-routeb-build python -m pytest tests/architecture/governance -q
5 failed, 210 passed, 1 xfailed in 33.85s
```

The five governance failures match the preceding lifecycle checkpoint and its
mainline comparison listed above. The tracked document census is now 991;
all nine census checks pass. Ruff passes for experiment sources/tests and
formatting of the three new Python files. Internal-code governance against
`origin/main` reports zero errors and warnings. Diff checks pass.

Two independent CLI invocations produced byte-identical full reports with
SHA-256 `17615fbe740af01cd1f57ee2225cc1f3e02246ee90aae5024f4b6c9c95f15d36`.
The committed [summary report](evidence/native_pilot_comparison_20261015.json)
replaces each run's `TraceManifest` payload with its digest and keeps every
other field; it has SHA-256
`6f5fdf67ec6411aa91c4471a63da871e4feca7631470879043f48930302a25ea`.
The full report is regenerated, not committed:

```bash
PYTHONPATH=<build>:. python -m python.experiment.native_pilot_comparison --output full.json
PYTHONPATH=<build>:. python -m python.experiment.native_pilot_comparison --summary --output summary.json
```

On `2026-10-29` the regenerated full report on HEI matched the `2026-10-15`
report byte for byte (SHA-256
`17615fbe740af01cd1f57ee2225cc1f3e02246ee90aae5024f4b6c9c95f15d36`),
and the summary's per-seed results, branch identities and manifest digests
matched it.

## Remaining Gate

Portable/persisted snapshot restore, unsupported backends, production
authorization, GPU execution, distributed branches, policy improvement, causal
validity, and real-world validity remain closed claims. The session restore
surface operates on explicitly saved in-process native CPU handles after an
accepted action boundary. The digest-only lifecycle backend retains its zero
placeholder rewards. The separate typed pilot backend dispatches actual
`PilotAction` commands and scores speed changes under a bound fixed protocol;
see the [flight-control comparison](native_pilot_action_comparison_20261015.md).
The event cursor remains the coordinator action sequence. Production
RuntimeFacade mission-wide publication beyond the selected native CPU child
seam, BC/world-model export coverage, broader mission coverage, and persisted
recovery remain future work. Callers that do not provide an explicit Agent
action/ref owner remain single-path by design.
