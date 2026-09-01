# P4-B State Transfer And Episode Candidate

Status: `2026-08-31` implementation snapshot; **candidate implementation
complete, independent review pending, and not accepted for production**. This document records the dark/shadow contract work on the isolated
`codex/long-horizon-governance-architecture` branch. It does not authorize
production truth publication, caller migration, or retirement of the existing
runtime path.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/p4b_state_transfer_candidate_20260830.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-31`

## Purpose

P4-B makes the P4-A host lifecycle consume an explicit native episode barrier
and a complete owner-directed state-transfer protocol. The long-horizon target
is executable state transfer with source-bound provenance, typed schema bytes,
transactional target import, replay evidence, N/N-1 decoding, and fail-closed
recovery. A green fixture or mirror test is not sufficient for acceptance.

## Implemented candidate surface

- `RuntimeEpisodeCoordinatorCandidate` owns episode phase, step, reset
  generation, barrier sequence, idempotency receipts, and native mutation
  serialization.
- `RuntimeHostCandidate` issues host-bound episode capabilities and obtains a
  slot-owned `RuntimeNativeEpisodeControl`; submission no longer accepts an
  arbitrary caller control.
- Replacement quiescence binds the active slot's source owner registry and the
  candidate slot's target owner registry separately. The source registry emits
  a census plus typed `RuntimeStateOwnerArtifact` payloads; the target registry
  receives that export and returns observations plus a rollback-capable import
  transaction.
- Validation pins host transfer work before owner callbacks, checks exact
  category membership, schema windows, artifact digests, source census equality,
  target observation equality, native barrier identity, and host revalidation.
- Import transactions have an abort guard on every validation failure and are
  committed outside transfer and host mutexes. Host/native/state-transfer
  in-flight counters prevent reclaim, shutdown, timeout, fault, or abort races.
- The current contract accepts schema generation N=2 and N-1=1 only, normalizes
  the candidate entry hash to N, and explicitly rejects multi-world replacement
  until a per-world transfer protocol is admitted.
- The candidate now exposes one twelve-row decoder/replay matrix with explicit
  owner/schema pairs, N/N-1 bounds, unknown-field policy, replay disposition,
  migration digest, and rollback obligation.
- Python `NativeEpisodeMirror` remains a receipt mirror only; reset and episode
  truth remain native-owned.
- The decoder/replay matrix now has a canonical profile factory, so callers
  cannot rename an owner/schema or widen the N/N-1 window while constructing a
  transfer profile. The project-internal source surfaces for the twelve owner
  categories are tracked in
  [p4b_owner_adapter_inventory_20260830.md](p4b_owner_adapter_inventory_20260830.md).

## Latest bounded repair slice (2026-08-31)

- The owner-import seam now exposes statusful `Prepared`/`Committing`/
  `Committed`/`Aborting`/`Aborted`/`Ambiguous` phases, bounded commit and abort
  entry points, interruption recovery, journal sequence, and an explicit
  durability bit.
- Host publication passes the observed tick and candidate drain deadline into
  the statusful commit path. A timeout or non-committed outcome fails closed
  and leaves the host stopped for quarantine review.
- Publication now requires a terminal `Committed` status with a non-zero owner
  journal sequence and `durable=true`; a non-durable or otherwise ambiguous
  result cannot advance host authority.
- Ambiguous commit/abort outcomes are retained as an explicit transfer
  lifecycle state; source rollback and barrier release are withheld until an
  owner recovery operation returns a terminal `Aborted` or `Committed` status.
- Legacy `void noexcept` owner hooks remain only as a source-compatibility
  bridge for shadow fixtures. Their default status is deliberately
  non-durable.
- A concrete fixed twelve-owner registry now validates registration identity,
  invokes exact N/N-1 migration callbacks, binds owner bytes to census digests,
  and aborts every already-prepared child in reverse order when a later owner
  fails validation.
- `RuntimeStateTransferFileJournal` now supplies a checksummed append-only local
  WAL with monotonic per-transaction phases, synchronous file flush, terminal
  reopen, interrupted-phase owner reconciliation, torn-tail truncation and
  complete-frame corruption rejection. This is local candidate evidence; it is
  not the P5-B ledger/checkpoint/media durability qualification.
- The uninstalled `ef_runtime_state_owner_adapters_candidate` target now binds
  all twelve categories to maintained `SimulationKernel`/host surfaces. ECS
  transfer has reflected registrations, dedicated codecs, stable logical entity
  references, strict whole-payload preflight, rollback, generic/database family
  coverage, and N-1 WAL import. Delayed/command subsets, episode reward and
  termination state, Python cache rederive, CPU backend rehydrate policy, and
  host-fenced in-flight drain all have exact decoders, N-1 migration, and
  durable candidate transactions. Composition/RNG/clock, explicit external
  `not-applicable`, and telemetry reset policies retain their barrier-bound
  vectors. The integrated host replacement test commits all twelve rows and
  reopens the target WAL to recover the terminal composite transaction.
- World restore validates every result, entity reference, tag, reflected field,
  and dedicated codec before deleting or creating target entities. Unknown or
  malformed fields therefore fail closed without leaving a partially restored
  world.
- Replacement publication now requires an explicit current clock sample. The
  one-argument overload was removed so a default tick of zero cannot bypass an
  expired owner-commit deadline.
- Host-bound integration registries must provide a resource identity, logical
  clock sampler, and Python rederive callback together; the registry carries
  an opaque owner-instance token and validation rejects same-owner
  source/target pairing. `RuntimeInstanceControl` has a fail-closed transfer
  fence default, so a control that has not implemented real target exclusivity
  cannot authorize import.

## Verification evidence

The isolated Windows/MSVC target currently reports:

```text
targeted native candidate tests: 60 test cases, 59 passed / 1 failed;
                                 1607 assertions, 1607 passed
focused Python architecture/mirror tests: 16 passed
configured CTest lane: 20/21 passed; ef_test_all retains two pre-existing
fixed-air CPU-reference identity assertions (entity ids 1469/expected 581)
```

Remeasured `2026-09-01` on the committed tree. The earlier `1609 assertions`
figure was recorded before the final repair pass and no longer reproduces; the
single failing case throws before reaching its remaining assertions, which is
why the assertion count is both lower and fully green.

The failing case is `ECS owner covers maintained database platform definitions`.
It is an unresolved child-entity transfer-scope decision, not a codec defect —
see the open-defect section of the
[P4-B remediation route](p4b_remediation_route_20260830.md). It must be
dispositioned by the independent reviewer before P4-B acceptance.

The other P4-B-specific CTest lanes remain green; the fixed-air failures are
outside this transfer slice and are recorded rather than reclassified as transfer
evidence.

The host-neutral CMake target remains static and links only
`ef_runtime_contracts`. The separate owner-integration probe links `ef_core`, is
not installed, and is allowed only as an explicit host consumer. The CI smoke
workflow builds and runs the native host boundary plus the state-transfer and
Python mirror contract gates.

## Acceptance boundaries (not implementation blockers)

The implementation slice is complete as a dark/shadow contract candidate. It
is not a production state-transfer implementation because the following
separate gates remain:

1. The fixed registry and local WAL are candidate-only. Production process
   restart, checkpoint/media durability, ACL/retention, and ArtifactLedger
   admission remain P5-B qualification work.
2. The candidate host binds owner registries through host-issued admission
   handles, but no maintained production owner adapters or authenticated
   deployment boundary have been qualified yet; caller DTO replacement must
   remain impossible at production admission.
3. Cross-release/process replay, real backend lease-provider restart behavior,
   and a future non-empty external side-effect outbox remain unqualified. The
   current external row is explicitly `not-applicable`; telemetry resets at
   target by policy.
4. Multi-world transfer, durable journal admission, RunReceipt binding,
   storage/authenticity, and production canary/backout remain P5 obligations.

These are acceptance boundaries, not a blockage in the P4-B implementation
slice and not reasons to reduce the program to a short-term fixture or cleanup
wave.

## Long-horizon completion route

P4-B implementation is complete on this branch. It can move to accepted only
after the mandatory independent integrated review confirms the twelve-row
owner evidence and no unresolved Critical/High (or safety-relevant Medium)
finding. P4-C may then integrate the candidate kernel seam while remaining
dark/shadow. P5-B/P5-D must still qualify durable RunReceipt,
ArtifactLedger, authenticity, canary/backout, supported topology, and the
single production cutover before any maintained caller changes authority.

The independent review gate is mandatory after this iteration. A reviewer may
replace a mechanism, but may not close P4-B by deleting the typed transfer,
provenance, durability, compatibility, or recovery obligations.
