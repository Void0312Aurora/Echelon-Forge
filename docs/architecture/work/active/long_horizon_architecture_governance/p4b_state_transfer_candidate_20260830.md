# P4-B State Transfer And Episode Candidate

Status: `2026-08-30` implementation snapshot; **repair-required and not
accepted**. This document records the dark/shadow contract work on the isolated
`codex/long-horizon-governance-architecture` branch. It does not authorize
production truth publication, caller migration, or retirement of the existing
runtime path.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/p4b_state_transfer_candidate_20260830.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-30`

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
- Python `NativeEpisodeMirror` remains a receipt mirror only; reset and episode
  truth remain native-owned.

## Verification evidence

The isolated Windows/MSVC target currently passes:

```text
ef_runtime_host_candidate_test: 37 test cases, 925 assertions
focused Python architecture/mirror tests: 12 passed
```

The CMake target is deliberately static and links only `ef_runtime_contracts`.
The CI smoke workflow now builds and runs the native host boundary plus the
state-transfer and Python mirror contract gates.

## Non-acceptance blockers

The implementation remains a contract candidate rather than a production
state-transfer implementation:

1. No maintained production owner adapters currently decode ECS, RNG, clock,
   queue, pending-command, episode, device, in-flight, side-effect, or mirror
   state into the typed artifact payloads. Existing test registries still
   synthesize deterministic bytes and observations.
2. `RuntimeInstanceControl` and its registries are still supplied by the
   caller at candidate construction. The host now separates source and target
   registries, but production admission still needs opaque host-issued owner
   handles or an equivalent authenticated binding that cannot be replaced by a
   caller DTO.
3. Import commit/abort remains a synchronous callback protocol. A production
   implementation needs durable one-shot transaction state, bounded
   cancellation/deadline behavior, explicit commit/abort outcome reporting,
   and recovery after process interruption.
4. The artifact envelope carries typed bytes and digests but does not yet
   define the per-category decoder/migration matrix, unknown-field policy, or
   durable replay log needed for exact N/N-1 operation.
5. Multi-world transfer, durable journal admission, RunReceipt binding,
   storage/authenticity, and production canary/backout remain P5 obligations.

These are architectural blockers, not reasons to reduce the program to a
short-term fixture or cleanup wave.

## Long-horizon completion route

P4-B can move to accepted only after each category owner publishes a maintained
source exporter and target importer with opaque host binding, exact payload
decoders, replay/rollback semantics, interruption recovery, and a versioned
compatibility matrix. P4-C may then integrate the candidate kernel seam while
remaining dark/shadow. P5-B/P5-D must still qualify durable RunReceipt,
ArtifactLedger, authenticity, canary/backout, supported topology, and the
single production cutover before any maintained caller changes authority.

The independent review gate is mandatory after this iteration. A reviewer may
replace a mechanism, but may not close P4-B by deleting the typed transfer,
provenance, durability, compatibility, or recovery obligations.
