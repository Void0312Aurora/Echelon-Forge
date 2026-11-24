# P3-B Native Branch Consumer Design

Status: `2026-10-17` route B selected for the long-term architecture; design,
selected CPU lifecycle, action dispatch, and evaluation are implemented in the
declared shadow scope. No production activation is implied.

## Decision

The experiment platform will treat a native branch consumer as the long-term
execution path. The existing native checkpoint/state-transfer authority remains
the only owner of authoritative state. The experiment layer may retain branch
references and trace records, but it must never serialize or restore a second
copy of runtime truth.

The current `RuntimeStateTransferCandidate` is a replacement-scoped authority.
It cannot be called a branch executor by renaming its replacement barrier. A
branch consumer must add an explicit parent barrier, immutable source snapshot,
child resource identity, and sibling isolation proof.

## Required lifecycle

1. **Open parent barrier.** The native episode coordinator reaches a transition
   boundary. All truth-mutating leases are closed, in-flight work is settled or
   rejected, and the parent episode cannot mutate while its branch snapshot is
   sealed.
2. **Export the declared state scope.** The twelve existing state categories
   are evaluated by their owner registrations. A branch fork fails if any
   truth-affecting category is omitted, unknown, or only represented by a
   Python-side mirror.
3. **Create the child resource.** The child gets a fresh runtime resource and
   incarnation identity. Its composition and executable plan must match the
   parent unless the request explicitly declares a supported plan transition.
4. **Import and prove isolation.** The child imports the exact native-owned
   state bundle. Parent and child must have different owner-binding tokens,
   leases, event queues, RNG streams, and external-effect dispositions. Raw
   process/device handles are rejected.
5. **Resume and execute.** The parent may resume only after the immutable
   branch snapshot has been sealed. Each child transition receipt binds the
   parent snapshot identity, branch identity, child snapshot identity, action
   digest, and observation provenance.
6. **Close the branch.** A terminal child is finalized with a deterministic
   trace digest. An abandoned child is explicitly discarded. Neither outcome
   mutates the parent snapshot or silently publishes a production result.

## Contract boundary

The branch request must carry:

- the native episode barrier and source snapshot identity;
- branch identity and parent branch ancestry;
- action/intervention digest and fixed decision-window metadata;
- the admitted plan/configuration/seed/policy binding;
- the requested state profile and backend capability set.

The native result must carry:

- source and child incarnation/resource identities;
- the complete state-scope census and bundle digest;
- parent snapshot and child snapshot identities for every transition;
- RNG draw position, event cursor/barrier sequence, terminal state, and receipt
  digest;
- explicit disposition for Python caches, device allocations, in-flight work,
  external side effects, and diagnostics;
- rejection reason when any branch precondition is not provable.

`SnapshotRef` in Python remains an identity-only projection of these native
facts. It must not gain a payload field or become a second checkpoint format.

## Acceptance gates

The first implementation slice is one CPU world, one fixed composition plan,
one seed, and one action interface. It must pass all of the following:

- **Continuation equivalence:** parent and child started from the same sealed
  snapshot produce byte-equivalent results for identical actions;
- **Sibling isolation:** a child mutation changes neither the parent state
  digest nor the parent's subsequent continuation;
- **RNG/event parity:** identical child actions preserve draw positions,
  event order, and barrier sequences;
- **Lease fencing:** open truth leases, unsettled requests, and stale parent
  barriers reject the fork;
- **State completeness:** every declared truth category has an owner digest;
  unknown truth fields and raw handles fail closed;
- **Provenance:** policy-visible observations use an admitted maintained
  observation label and retain source snapshot ancestry;
- **Failure hygiene:** terminal, abandoned, deadline, import ambiguity, and
  unsupported backend paths leave the parent usable and the child unpublished;
- **Determinism:** equal request, plan, seed, and action inputs produce equal
  branch and trace digests.

## Implementation sequence

1. Add a native branch vocabulary and validation helpers next to the existing
   state-transfer authority, reusing `RuntimeEpisodeCoordinatorSnapshot` and
   owner registrations rather than defining checkpoint bytes again.
2. Add a branch barrier capability distinct from replacement barriers. It must
   be single-use, source-bound, and released only after the immutable export is
   sealed.
3. Add a CPU branch executor behind the internal candidate target. It should
   use the existing owner adapters for export/import and allocate a fresh
   native resource identity for every sibling.
4. Add native tests for continuation, isolation, RNG/event parity, stale and
   incomplete-state rejection, and deterministic receipt digests.
5. Connect the Python `SimulationSession` only after the native selected slice
   passes. Keep the existing `runtime_candidate` adapter as a capability
   negotiation surface; it must report branch support from the native producer
   rather than infer it.

## Native execution checkpoint — 2026-10-15

The native branch vocabulary and fail-closed validators now live beside the
state-transfer authority in `runtime_branch_contract.{h,cpp}`. The explicit
`BranchBarrier` preserves the existing replacement phase values, and the
executor uses the same twelve owner registrations for a branch export/import.
`RuntimeHostCandidate::execute_shadow_sibling_branch` supplies the active
coordinator and source owner/fence facts from host state, closing the caller
forging gap at the lifecycle boundary.
The result can carry a resource-bound child episode control; if that control is
absent, the branch remains creation-only rather than inventing a step surface.
The Python `runtime_candidate` adapter now negotiates this native seam through
an opaque handle and keeps fork disabled when either native method is absent.

The current checkpoint passed:

```text
cmake --build /tmp/cmo-routeb-build -j2
ctest --test-dir /tmp/cmo-routeb-build --output-on-failure
100% tests passed, 0 tests failed out of 25
```

the complete `runtime_host_candidate`, `runtime_kernel_candidate`, and
`runtime_kernel_candidate_parity` CTest targets, the focused native branch
tests, and the real `SimulationKernel` owner-registry branch transfer. The
Python experiment suite includes a bound native candidate
fork and child continuation.

The 2026-10-17 packet DTO decoupling was rebuilt and rechecked with the
candidate lifecycle targets:

```text
cmake --build /tmp/cmo-routeb-build -j2 -> ninja: no work to do
ctest --test-dir /tmp/cmo-routeb-build --output-on-failure \
  -R '^runtime_kernel_candidate(_parity)?$'
100% tests passed, 0 tests failed out of 2
CMO_BUILD_DIR=/tmp/cmo-routeb-build PYTHONPATH=/tmp/cmo-routeb-build:. \
  pytest -q tests/experiment
380 passed
```

The candidate extension now owns its observation packet DTO, so the
dark/shadow consumer no longer includes the maintained facade type header.
The caller inventory and C++ include-direction checks pass for that boundary.

The twelve-owner episode branch executor remains dark/shadow. Separately, the
maintained `ef_py` facade now exposes a bounded native child owner using the
shared world/RNG/clock codec; it does not link the candidate host extension.
The candidate `ef_runtime_candidate_py` binding and Python session adapter
continue to consume the candidate handle. The real
owner-registry test proves the current 12-row serializer/import path under a
branch barrier; `RuntimeKernelSiblingBranch::checkpoint()` repeats that native
transfer from an existing branch without exporting a payload. Exact double
formatting is preserved through the pinned Flecs JSON path, and the focused
checkpoint test proves identical same-action state, event, and RNG digests.
The pinned JSON reader now handles signed exponents and bounds numeric token
copies. Whole-world tests preserve subnormal and maximum finite doubles and
negative zero; malformed and oversized tokens are rejected. The patched reader
also passed an isolated AddressSanitizer check.
This does not establish production coverage for every future runtime owner.

The [session checkpoint/replay integration](native_session_checkpoint_replay_20261015.md)
now connects explicit native checkpoint retention to historical forks, fresh
restore continuations, nested branches, and verified trace replay. Each native
descendant binds its requested intervention digest and derives its depth from
the actual source branch. A replay is recorded only after every transition
matches; rejected replay attempts preserve the source and saved checkpoint.
Real aircraft tests exercise this lifecycle at three seeds.

## Explicit non-claims

This design does not yet prove that the current `SimulationKernel` serializer
covers every branch-relevant queue or external effect. The native checkpoint is
exposed only as an in-process opaque handle through the session save/restore
surface, with no portable checkpoint format. The digest-only lifecycle backend
retains placeholder rewards; the separate typed flight backend dispatches
entity commands and uses a declared speed-change evaluator.
It does not authorize GPU or distributed branches, production
publication, policy improvement, causal validity, or combat/real-world
conclusions.

The [typed flight-control comparison](native_pilot_action_comparison_20261015.md)
now carries actual maintained `PilotAction` DTOs through coordinator admission,
resolves imported entities by the existing logical-name identity, and verifies
scored action-dependent continuations. This remains a candidate CPU diagnostic.
