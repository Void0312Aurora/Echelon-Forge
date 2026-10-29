# P3 Runtime Adapter Boundary

Status: `2026-10-18` selected CPU boundary implemented; maintained C++ facade
identity and native child owner are now available through the binding.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/p3_runtime_adapter_boundary_20261017.md`
Owner: `cross-domain architecture`
Last verified: `2026-10-29`

## What is closed

`python/experiment/runtime_facade_backend.py` now provides the maintained
`RuntimeFacadeAdapter` session boundary for the selected setup/step/observation
slice. It executes one setup callback during construction, then requires all
of the following from its caller:

- maintained setup and `step_batch` bindings, with setup returning exactly one
  maintained ref for each session Agent;
- maintained observation request and packet export capabilities;
- an explicit action applier that writes maintained facade assignments;
- an explicit native identity owner returning `RuntimeSnapshotFacts` before
  and after each step; and
- an explicit reward reader whose values cover exactly the session Agents.

The adapter calls the maintained facade step exactly once per accepted
transition, rejects external identity changes, checks one-step identity
advancement, and binds packet reads through explicit Agent refs using
`facade_observation_packet` provenance. It never derives state, event, or RNG
identity from observations, entity refs, packet versions, or Python mirrors.

The Python adapter exposes `fork_branch`, `checkpoint_branch`, and descendant
forks when the caller supplies `branch_action_applier`. That owner translates
the session's Agent actions into native pilot assignments; the adapter never
guesses this mapping. Without it, branch and checkpoint capabilities remain
false and the surface fails closed. The maintained C++ facade supplies the
lower-level native owner seam directly: `native_snapshot_facts()` reads
state/RNG identity from the world owner, while `fork_native_branch()` creates
an opaque child restored from the complete native world, RNG, and clock bundle.
The child accepts native pilot assignments and exports an Agent observation
packet without linking the candidate host extension.

## Failed-batch fence

`native_snapshot_facts()` and `fork_native_branch()` read raw world state, so
they bypass `WorldBatchRuntime`'s own failure fence. Since `2026-10-29` the CPU
facade backend applies the same fence first: on an unhealthy batch both raise
`std::logic_error`, with the reset or host-recreate instruction that
`batch_failure_status()` reports. After `reset_batch()` they work again. The
facade failure regression in `src/tests/test_world_batch_runtime.cpp` covers
the rejected and recovered cases.

## Validation

The maintained-facade build, focused Python boundary tests, native state-owner
test, and include-direction gate pass:

```text
cmake --build /tmp/cmo-routeb-build -j2
success
ctest --test-dir /tmp/cmo-routeb-build --output-on-failure -R '^runtime_host_candidate$'
1 passed
CMO_BUILD_DIR=/tmp/cmo-routeb-build PYTHONPATH=/tmp/cmo-routeb-build:. \
  pytest -q tests/experiment/test_runtime_facade_backend.py \
  tests/experiment/test_runtime_facade_observation.py \
  tests/experiment/test_runtime_candidate.py \
  tests/runtime/facade/test_runtime_facade_native_branch.py
42 passed
CMO_BUILD_DIR=/tmp/cmo-routeb-build PYTHONPATH=/tmp/cmo-routeb-build:. \
  pytest -q tests/architecture/governance/test_cpp_include_direction.py
7 passed
```

The backend tests cover one-time setup, Agent-ref completeness, maintained step
ordering, packet capture, external identity mutation, malformed identity
digests, missing packet capability, missing native identity, and absent
branch-owner fail-closed behavior.

## Remaining boundary

The native identity and child-resource owner gate is closed for the maintained
CPU facade binding and covered by direct runtime and session tests. This does
not promote the candidate host's twelve-owner episode executor into the facade: the
maintained child uses the shared native world/RNG/clock codec and a local branch
step/observation seam. Generic Python session branch publication is available
through the explicit injected action/ref owner; callers that omit that owner
remain single-path. GPU, remote, and distributed execution remain P5 work.
