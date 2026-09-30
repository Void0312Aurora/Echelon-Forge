# P1-A Host Lifecycle And Episode Authority Decision

Status: `2026-08-25` frozen P1-A decision candidate; implementation is not
authorized until the integrated P1 independent review passes.

Parent subproject: [Long-Horizon Architecture Governance](../README.md)

Document kind: `decision`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/decisions/p1a_host_lifecycle_and_episode_authority_decision_20260825.md`
Owner: `runtime architecture`
Last verified: `2026-08-25`

## Decision

The maintained production kernel is immutable after construction from an
admitted `ResolvedCompositionPlan`. Truth-affecting replacement is owned by one
process-local `RuntimeHost`, not by `SimulationKernel`, `WorldBatchRuntime`, a
backend, a Python environment, or a binding.

The host publishes exactly one immutable-identity `PublishedRuntimeSlot` at one
atomic linearization point. The immutable publication snapshot binds host
identity, monotonically increasing incarnation epoch, plan identity, and stable
pointers to the runtime instance, native episode coordinator, lease service and
receipt service. Runtime truth, lease counters and journal state remain mutable
only through those synchronized services; their authority identity and service
pointers cannot be replaced in place. All maintained world, entity, request,
and result references carry the slot identity and epoch. Publication of a
candidate and transition of the previous slot to draining are one serialized
operation.

Production in-place composition rebuild is not part of the target path. The
existing rebuild surface remains a compatibility implementation until the P5-D
cutover and rollback window pass. A future in-place exception requires an
independently accepted identity-preserving consumer and the same state,
fencing, rollback, and evidence obligations as host replacement.

## Current Source Basis

The decision addresses these observed repository facts:

- `SimulationKernel` owns a raw Flecs world, RNG, time step, missile tuning,
  composition object, a recursive lifecycle mutex, mutation flags, exact-stage
  frame state, and shutdown state.
- its current world leases hold only that kernel's recursive mutex and raw world
  pointer; they contain no host incarnation or publication fence;
- in-kernel rebuild fails closed after raw-world exposure, ECS mutation,
  `SimObject` creation, or an active exact-stage frame, and has no maintained
  non-test caller;
- `WorldBatchRuntime` owns a resizable vector of `unique_ptr<SimulationKernel>`;
  shrink destroys kernels and regrow creates new generation-one kernels;
- public `WorldEntityRef` contains only `world_index` and `entity_id`;
- `RuntimeFacade` owns a bare backend pointer plus a local composition
  incarnation used for shrink/regrow evidence, while CUDA experiments have a
  separate device lease epoch. Neither mechanism is a host-wide reference and
  replacement protocol;
- Python `WorldBatchVecEnv` computes termination/reward, resets accounting and
  loader caches, calls `_reset_single_world`, and performs autoreset from its
  `reward_episode` stage. `ExecutionEpisodeState` is a transfer DTO populated
  from Python mirrors, not the unique native episode phase authority.

These local protections are retained as implementation details where useful;
they are not treated as proof of the target lifecycle.

## Ownership And Identity Model

| Object | Singular owner | Required identity | Authority |
| --- | --- | --- | --- |
| `RuntimeHost` | native facade/runtime host | stable `host_id` plus process `boot_id` | replacement serialization and publication |
| `PublishedRuntimeSlot` | `RuntimeHost` | `(host_id, boot_id, incarnation_epoch)` | currently admitted execution instance |
| `RuntimeInstance` | published slot | slot identity plus `plan_id/plan_sha256` | immutable kernel/batch/backend resources |
| world | native instance | slot identity, `world_slot`, `world_generation` | world truth and clock |
| entity | native world | world reference plus `entity_id/entity_generation` | entity truth; no bare ID outside private internals |
| episode | native `EpisodeCoordinator` | world reference plus `episode_id/episode_generation` | phase, step, termination, reset and completion |
| request/result | native host | slot/episode identity plus monotonic request sequence | admission, cancellation, completion and stale-result rejection |

Epoch and generation zero are invalid. `incarnation_epoch` increases for every
published instance and is never reused within a host/boot identity. A runtime
instance has immutable world-slot cardinality: resize/shrink/regrow requires a
new instance epoch. Within an instance, each world materialization or episode
reset increments the world's generation; each entity-slot reuse increments its
entity generation; each native reset increments episode generation; and each
admitted request consumes a never-reused request sequence. Tombstones preserve
the last generation for destroyed world/entity/episode namespaces. References
bind every enclosing generation, so reuse at an inner level cannot pass a stale
outer reference. Exhaustion of any epoch, generation or sequence fails closed;
no counter wraps or resets in place.

A process restart creates a new unguessable boot identity so references from
the previous process cannot become valid even if an in-memory counter restarts.
Multi-process persistence and leader fencing are not inferred from this rule;
P1-C keeps that topology disabled until a linearizable epoch store is admitted.

Public DTOs introduced in P3-A must be engine-independent. Flecs objects,
`SimulationKernel*`, backend pointers, component headers, and raw device handles
cannot appear in public references. Private compatibility adapters may unwrap a
validated epoch-bearing reference only while holding an instance lease.

## Lifecycle State Machine

| State | May receive new work | May publish results | Permitted successors | Required invariant |
| --- | ---: | ---: | --- | --- |
| `absent` | no | no | `constructing`, host `shutting_down` | no published instance owns resources |
| `constructing` | shadow-only internal probes | no | `validating`, `candidate_failed`, host `shutting_down` | candidate is unreachable from production readers |
| `validating` | shadow-only | no | `ready`, `candidate_failed`, host `shutting_down` | static plan/resource checks pass; no claim of final transferred state |
| `ready` | no | no | `initial_commit_ready`, host transaction `quiescing`, `recovery_commit_ready`, `candidate_failed`, host `shutting_down` | immutable candidate shell and receipt/storage preconditions are sealed |
| `initial_commit_ready` | no | no | `publishing`, `candidate_failed`, host `shutting_down` | expected published slot is absent; plan-defined baseline plus host lifecycle receipt/storage preconditions are validated |
| `quiescing` | no new truth-affecting work on old slot | old already-admitted work only until the native barrier | `transfer_commit_ready`, pre-commit abort to `active`, `active_faulted`, host `shutting_down`, `quarantined` | admission gate is closed and all truth-mutating leases settle/cancel before final export |
| `transfer_commit_ready` | no | no | `publishing`, `candidate_failed`, `active_faulted`, host `shutting_down` | old slot is frozen at its barrier and candidate matches the final transfer fence |
| `recovery_quiesced` | no | no | candidate `recovery_commit_ready`, host `shutting_down`, `quarantined` | faulted slot admission is closed and truth-mutating leases are fenced/settled; no state export is permitted |
| `recovery_commit_ready` | no | no | `publishing`, `candidate_failed`, host `shutting_down` | candidate imported a previously durable admitted checkpoint; expected slot is the fenced faulted slot |
| `publishing` | no | no | candidate `active` and optional old `draining`, `candidate_failed` before CAS, host `shutting_down` | one lifecycle ticket and slot CAS are exclusive; successful CAS cannot be undone in place |
| `active` | yes | yes | `quiescing`, `active_faulted`, host `shutting_down` | exactly one slot is authoritative |
| `active_faulted` | no | no | `recovery_quiesced`, host `shutting_down`, `quarantined` | admission is closed; every formerly active instance still obeys lease settlement |
| `shutting_down` | no | no | published instance `draining`, unpublished candidate `candidate_failed`, host `stopped` after settlement | terminal lifecycle ticket is held; no candidate publication or state transfer occurs |
| `draining` | no new work | fenced read-only/result settlement only | `reclaiming`, `quarantined` | no truth mutation occurs after the transaction's transfer, recovery or terminal mutation fence |
| `reclaiming` | no | no | `retired`, `quarantined` | active lease count is zero and resource release is verified |
| `quarantined` | no | no | `reclaiming`, operator termination | resources remain isolated; no unsafe forced destruction |
| `candidate_failed` | no | no | `reclaiming`, `quarantined` | candidate was never authoritative; any internal lease still settles before release |
| `retired` | no | no | none | reached only from `reclaiming`; identity is tombstoned and resources are zero |
| `stopped` | no | no | none | host-terminal state; repeated shutdown returns the same terminal receipt/result |

Candidate construction, static validation and optional shadow replay occur
before quiescence. The target mechanism then closes truth-affecting admission on
the old slot, settles or cancels every truth-mutating lease at the native episode
barrier, exports the final canonical state, imports and validates it, and seals a
`transfer_fence_sequence`. No old truth may mutate after that fence. The
candidate enters `transfer_commit_ready` only when its imported state hash and
sequence equal the frozen old slot.

All publication uses one `publish_slot(expected_slot_identity, candidate,
new_epoch, transaction_kind)` compare-and-swap primitive, one monotonic host
lifecycle ticket and one receipt authority. Its mutually exclusive transactions
are:

1. `initial`: `expected_slot_identity = absent`; the candidate reaches
   `initial_commit_ready` from the plan-defined baseline and durable host
   lifecycle receipt, then publishes epoch one without inventing an old
   transfer/drain. No run/episode truth mutates until that attempt separately
   passes P1-B durable RunJournal admission;
2. `replacement`: the expected active slot is quiesced and the candidate reaches
   `transfer_commit_ready` from its final canonical snapshot; successful CAS
   makes the candidate active and old slot draining;
3. `checkpoint_recovery`: the expected slot is `recovery_quiesced`; the candidate
   imports a previously durable native checkpoint, never exports truth from the
   faulted source, and publishes a new epoch while the old slot drains.

If recovery has no compatible admitted checkpoint, or faulted truth-mutating
leases cannot settle/fence, the host fail-stops or uses P1-C package restart; it
never substitutes default/empty state. A new lease acquisition and the active-
slot/admission-gate read share the same linearization protocol, so a caller
receives either a valid old lease before quiescence or a complete new lease after
publication, never a lease in the transfer gap. There is no interval with two
production writers and no second publication point in Python, a backend, or a
package adapter.

The initial production mechanism is barrier quiescence, not live delta replay.
A future snapshot-plus-ordered-delta optimization is separately admissible only
if it proves complete sequence capture, final-fence catch-up and identical
failure semantics; it cannot weaken the barrier contract.

If candidate import/validation fails before the publication CAS, a durable abort
receipt discards the candidate and may reopen admission on the same frozen old
slot without changing its epoch. After a successful CAS there is no reopen path;
fault or rollback uses drain and a new epoch.

Concurrent replacement requests are serialized by a monotonic replacement
ticket. A request whose expected active epoch no longer matches is rejected;
replacement is never silently rebased onto a newer slot.

## Terminal Shutdown Transaction

Shutdown uses the same host lifecycle ticket/CAS domain but is a terminal
transaction, not replacement or failure. The first shutdown request obtains the
terminal ticket; repeats join the same operation and return its final receipt.
It closes admission, prevents every not-yet-committed publication, cancels and
reclaims unpublished candidates, settles/cancels truth-mutating leases, drains
published instances, finalizes journals/receipts, releases resources in reverse
dependency order, and enters `stopped` only after every non-quarantined instance
is retired. It performs no state transfer and publishes no candidate.

The race rule is determined by the single slot CAS/ticket sequence:

- if shutdown wins before a publication CAS, that CAS fails, the candidate moves
  through `candidate_failed`, and the currently published slot (if any) enters
  `shutting_down -> draining`;
- if initial/replacement/recovery publication CAS wins first, shutdown observes
  the newly published epoch, immediately closes its admission and moves that
  slot through `shutting_down -> draining`; any old slot already draining
  continues under the same terminal wait;
- an absent host with no candidate moves directly through `shutting_down` to
  `stopped` after its durable terminal receipt;
- a deadline with live leases enters quarantine and returns an explicit failed
  shutdown/fail-stop result; it never reports clean `stopped` or frees leased
  memory.

Normal shutdown is never labeled `active_faulted`. Shutdown during quiescence
discards transfer output rather than reopening or publishing it.

## Lease, Drain, Backpressure And Reclamation

An `InstanceLease` is a strong lifetime reference to one published slot and
contains the expected host, boot, epoch, episode and request identities. Request
admission obtains the lease before exposing private runtime state. Every result
is validated against its lease before it can reach a caller.

When quiescence begins, truth-affecting admission on the old slot closes. The
host then:

1. records the drain deadline and sends cooperative cancellation to cancellable
   work;
2. settles already admitted non-cancellable truth-mutating work before the
   final transfer fence; after that fence only read-only/result settlement may
   continue, and every completion remains tagged with the old epoch;
3. applies bounded backpressure to replacement requests and new callers rather
   than allocating unbounded candidate/retired instances;
4. reclaims only after native episode quiescence, request settlement, device
   release, and lease count zero;
5. quarantines an instance when a deadline expires with live leases. It never
   destroys memory still protected by a lease.

The long-term host supports at most one active, one candidate, one draining and
one quarantined instance process-wide, not per caller-chosen lane. The presence
of an unresolved quarantine freezes all further replacement in that host.
Exceeding the quarantine budget requires fail-stop/operator termination after
safe external handoff; a new lane name cannot bypass the limit. Further
replacements fail with a typed backpressure result. Shutdown closes admission,
cancels/drains, finalizes receipts, releases instances in reverse dependency
order, and returns only after reclamation or an explicit quarantine/operator-
failure result.

## Native Episode Barrier And Python Handshake

Each world has one native `EpisodeCoordinator`. It owns `episode_id`, episode
generation, phase, step sequence, terminal decision, reset decision, state
checkpoint identity, and the barrier at which replacement or reset may occur.
Python owns policy interaction and derived presentation/accounting state; it
does not author episode phase or advance a world to the next episode.

The P4-B handshake is versioned and idempotent:

1. Python submits an action or reset intent with expected host epoch, world
   generation, episode identity, step sequence, and idempotency key.
2. Native code accepts or rejects it before mutation and returns a transition
   receipt containing the resulting sequence, terminal/reset state and state
   snapshot identity.
3. Python applies the receipt to its mirrors. Repeated receipts are idempotent;
   gaps or mismatched identities force resynchronization, not local guessing.
4. Autoreset is expressed as an intent. The native coordinator performs the
   episode barrier and world reset, then supplies the new episode reference and
   initial snapshot.

Until P5-D, current Python autoreset remains production authority and the new
protocol may run only dark/shadow. Cutover must migrate the whole barrier in one
release gate; a mixed mode in which Python and native code can both reset is
forbidden.

## State Transfer Census And Rules

Replacement is allowed only at a native episode barrier unless a profile has an
independently accepted mid-episode transfer contract. Each admitted profile
must publish a versioned state census with an owner and one of `transfer`,
`rederive`, `cancel`, `drain`, `reject`, or `not-applicable` for every row.

| State category | Target rule | Minimum evidence |
| --- | --- | --- |
| composition/provider/system graph | never transferred; rebuilt only from the closed plan | candidate plan/hash equality or accepted version transition |
| ECS/component truth | versioned canonical snapshot; unknown truth-affecting fields reject | round-trip, negative unknown-field and replay comparison |
| RNG | transfer full engine/stream state and draw position, not seed alone | next-draw and replay equivalence |
| clock/cadence | transfer simulation time, step/window counters and barrier sequence | monotonicity and no duplicate/omitted step |
| delayed events and queues | transfer ordered payload, due time, sequence and cancellation state | order, duplicate and loss fault tests |
| commands, links and pending intent | transfer owner/version/ack state or cancel explicitly | no duplicated command or stale link |
| episode/reward/termination | native coordinator snapshot is authoritative | barrier, idempotency and terminal/reset replay |
| Python loader/controller/caches | rederive from native snapshot unless explicitly admitted as intent state | mirror resync and cache-poison negatives |
| backend/device allocations and leases | rehydrate in candidate; raw handles never transfer | device failure, stale lease and cleanup tests |
| in-flight requests/results | drain or cancel with typed receipt; replay only when idempotent | late-result fencing and duplicate request tests |
| external side effects | transactional outbox/receipt or replacement rejected | crash-before/after-commit recovery |
| diagnostics/telemetry | may be rederived; continuity gaps are explicit | epoch-tagged metrics and gap reporting |

An incomplete census is a hard failure. A default value is not evidence that a
state field is safely rederived. State format upgrades follow the N/N-1 reader
rules in P1-B/P1-C and reject unknown truth-affecting fields.

## Failure And Concurrency Matrix

| Condition | Required behavior | Forbidden behavior |
| --- | --- | --- |
| construction/plan validation failure | fail/reclaim candidate; keep old slot active when one exists, otherwise remain absent | partially publish candidate or invent initial truth |
| initial publication expected slot is not absent | reject stale lifecycle ticket and reclaim candidate | overwrite or treat existing slot as bootstrap |
| state export/import failure | keep old slot active; record failing category/version | fall back to empty/default state |
| checkpoint recovery lacks compatible admitted checkpoint | fail-stop or use admitted package-restart path | export from faulted truth or use default/empty state |
| compare-and-swap loses race | reject stale replacement ticket and reclaim candidate | rebase or publish a second time |
| request arrives during publication | acquire either complete old or complete new slot; old admission closure is respected | observe mixed pointers/epochs |
| old read-only/result work completes after cutover | settle old lease and record old-epoch completion; deliver only to the exact pre-cutover request contract if it admits such completion | mutate old truth or label result with new epoch |
| drain deadline expires | cancel, quarantine and page/fail the operation | free leased memory or wait without bound |
| active instance faults after publication | close admission, enter `active_faulted`, drain/quarantine, and invoke the applicable P1-C rollback path | jump directly to reclaim/retire or mutate failed instance in place |
| process crash | next boot rejects old references and reconciles incomplete receipt journal | accept pre-crash references by counter coincidence |
| shutdown races initial/replacement/recovery | lifecycle ticket/CAS winner rule applies; shutdown cancels pre-CAS candidate or immediately drains the just-published slot | publish after shutdown wins, reopen admission, or label normal shutdown as failure |
| epoch/sequence exhaustion | fail closed and require new identity | wrap or reset in place |

Same-binary instance rollback publishes a separately admitted instance at a new
epoch. It never reactivates an old epoch, rewrites a finalized receipt, or
restores a raw pointer. Binary/wheel/package rollback is a different P1-C path:
it stops the process after receipt/checkpoint handoff and starts the old package
under a new boot identity. State rollback is permitted only to a compatible
native checkpoint declared by P1-B/P1-C; otherwise the host stops rather than
fabricating continuity.

## Caller Compatibility Map

This crosswalk reuses the accepted P0 closure surface IDs; it is not a new
registry. The nine surfaces cover the frozen 23 caller paths.

| P0 surface ID and current paths | Target classification/API/package | P3/P4 route | P5-D cutover, rollback and retirement |
| --- | --- | --- | --- |
| `runtime_facade.maintained_host`: `python/rl/runtime/world_batch/adapter.py`; `tools/maintenance/runtime_host_batch_parity_contract.py` | maintained production facade; production wheel | epoch DTO/plan shell, then dark host and native episode handshake | release decision migrates both; package rollback restarts old wheel; facade remains |
| `simulation_kernel.default_compatibility` / `.github/workflows/ci-smoke.yml` | maintained release-qualification lane | replace raw wheel smoke with facade/host and explicit diagnostics-package negative/opt-in checks | cut over with P5-C/P5-D package; no production raw-kernel assertion remains |
| same surface / `examples/viz/web_viz/server.py` | maintained visualization example through facade | facade snapshot/action adapter in P3/P4 shadow | release routing selects production facade; old raw example path retires after behavior parity |
| same surface / `python/testing/contracts/loader_command_chain.py` | maintained contract-test caller | test adapter over facade/epoch DTO; may use explicit test-only hooks | migrates before raw binding removal; retained as qualification evidence, not production authority |
| same surface / `python/testing/contracts/route_generator.py` | maintained contract-test caller | test adapter over facade/epoch DTO | same-release/package rollback follows tested facade; raw constructor last reader retires |
| same surface / `python/testing/contracts/unit/comm.py` | maintained command/communication contract-test caller | facade command/query contracts plus test fixtures | migrates in P5-D qualification; remains a test, not diagnostics package content |
| same surface / `python/testing/contracts/unit/kernel.py` | maintained kernel-behavior contract test | facade-host behavior adapter; raw-only assertions split to test target | maintained semantics survive; production raw construction retires |
| same surface / `tools/diagnostics/benchmarks/scenario_compiler.py` | diagnostics-only benchmark | named diagnostics module/target with epoch-tagged output | never shipped transitively or allowed to publish truth; explicit opt-in remains |
| same surface / `tools/diagnostics/benchmarks/spatial_query.py` | diagnostics-only benchmark | named diagnostics module/target | same diagnostic isolation and last-reader gate |
| same surface / `tools/diagnostics/kill_chain_decoupling_probe.py` | diagnostics/evidence probe | named diagnostics CLI/module; any maintained comparison consumes receipt-linked outputs | cannot be production router; raw access remains opt-in only |
| same surface / `tools/geometry/target_geometry_damage_event_trace.py` | diagnostics/calibration evidence tool | named diagnostics CLI/module with receipt/provenance binding | retained for evidence where owned; excluded from production package/authority |
| same surface / `tools/geometry/target_geometry_lethality_matrix_probe.py` | diagnostics/calibration evidence tool | named diagnostics CLI/module with receipt/provenance binding | retained for evidence where owned; excluded from production package/authority |
| `simulation_kernel.native_default_callers`: `src/core/engine/world_batch_runtime.cpp`; `src/main.cpp` | backend-private adapter and maintained standalone facade host | internal host adapter in shadow; standalone accepts explicit plan | production construction routes through host; same-binary rollback uses new epoch; direct default construction retires |
| `simulation_kernel.python_binding_exposure`: `src/interfaces/python/bindings_core_simulation_kernel.cpp` | diagnostics-only Python module | separated target/module and negative production-wheel link test | absent from production wheel; old wheel rollback only during bounded window; raw binding retirement has import telemetry |
| `world_batch_runtime.native_backend_owner`: `src/runtime/facade/internal/flecs_cpu_backend.cpp` | private CPU-exact backend implementation | adapts epoch DTOs under a host lease; never exported | retained behind facade host; cannot become second publisher |
| `world_batch_runtime.python_binding_exposure`: `src/interfaces/python/bindings_runtime_engine.cpp` | diagnostics-only Python module | separated from maintained bindings and package | absent from production wheel; explicit diagnostics package retains bounded compatibility |
| `runtime_facade.python_binding_exposure`: `src/interfaces/python/bindings_runtime_facade.cpp` | maintained production binding | binds final contracts/plan/episode handshake only | selected by the sole rollout decision; package restart rollback; remains maintained |
| `simulation_kernel.explicit_manifest`: `src/tests/test_cordis_runtime_conformance.cpp` | contract/conformance test, no execution authority | reads plan adapter and native rejection surface | migrates to plan byte/admission conformance; retained while it detects the lasting writer/reader invariant |
| `simulation_kernel.test_fault_injection`: `src/core/engine/testing/simulation_kernel_composition_test_access.cpp`; `.h`; `src/tests/test_simulation_kernel_smoke.cpp` | test-only lifecycle/failure hooks | moves to host state/transfer fault injection without public export | old in-kernel mutation hooks retire after defect-replay coverage; lasting host failure tests remain |

CUDA resident/device experiments are not part of the P0 production caller
closure. Their private leases may adapt to host epoch only in shadow mode and
remain noncanonical until separately admitted.

No caller is removed in P1. P3 provides final public types; P4 proves the host
in dark/shadow; P5-C proves physical packages; P5-D is the sole production
caller cutover and rebuild-retirement point.

## Rejected Alternatives

- Extending the current recursive kernel mutex into a host protocol is rejected:
  it does not fence references or survive shrink/regrow and process restart.
- Treating facade composition incarnation or CUDA device epoch as the universal
  epoch is rejected: both are locally scoped and public CPU references omit them.
- Destroy-and-recreate on `WorldBatchRuntime::resize` without epoch-bearing
  references is rejected because it permits ABA and stale entity reuse.
- Letting Python remain reset authority while native code owns replacement is
  rejected because replacement and episode barriers could race.
- Forced destruction at a drain timeout is rejected because it converts a
  liveness failure into memory-safety or wrong-instance execution.
- Keeping production in-place rebuild as a second path "for flexibility" is
  rejected absent a real identity-preserving consumer and full transfer proof.

## Implementation And Acceptance Gates

This decision authorizes no production change. Required sequence:

1. P3-A lands engine-independent epoch-bearing DTOs.
2. P3-B/P3-C land the plan and rollout contracts used by host slots.
3. P4-A implements lifecycle, leases and fencing only in dark/shadow.
4. P4-B completes the state census and native episode handshake.
5. P4-C migrates only internal test/shadow adapters.
6. P5-A/B/C close plan, receipt and package authority.
7. P5-D performs the only production cutover, rollback window and rebuild
   retirement.

P1-A is accepted only when an independent reviewer finds no unresolved
critical/high omission in identity, publication, state transfer, episode
authority, failure, concurrency, shutdown, rollback or caller compatibility.

## Residuals

- Exact state schemas and transfer code are P4-B deliverables, not proven here.
- Numeric drain and rollback SLOs and their measurement baseline are owned by
  P1-C/P2-B.
- Multi-process leader/epoch persistence remains disabled under P1-C.
- Dynamic identity-preserving in-place replacement remains unadmitted.
- CPU exact remains canonical; this decision does not promote CUDA.
