# P4-B Remediation Route: Provenance And Durable Transfer

Status: `2026-09-01` implementation-complete checkpoint with one open owner
decision (child-entity transfer scope, see the open-defect section); independent
review pending. P4-B is not yet accepted for production.
Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/p4b_remediation_route_20260830.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-31`

## Objective

Close caller-forgeable owner provenance and non-durable import transactions.
This route is long-horizon; fixture compatibility is evidence only.

## Work packages

1. **Host-issued owner capability**: construct owners behind a host-owned
   admission factory; return an opaque single-use handle bound to host boot
   identity, slot incarnation, resource identity, generation and authenticator;
   reject copied, replayed, cross-host, cross-slot and post-reclaim handles.
2. **Durable import transaction**: replace synchronous `void noexcept` hooks with
   monotonic status, deadline, cancellation, idempotent commit/abort and
   interruption recovery; persist pre-mutation and terminal records; quarantine
   ambiguous records fail-closed.
3. **Typed decoder and replay matrix**: maintain production owner adapters for
   the following twelve categories and dispositions (the P1-A table remains the
   semantic authority):

   | Category | Required disposition |
   | --- | --- |
   | CompositionProviderSystemGraph | rederive |
   | EcsComponentTruth | transfer |
   | RngState | transfer |
   | ClockCadence | transfer |
   | DelayedEventsQueues | drain/cancel |
   | CommandsLinksPendingIntent | transfer or reject, explicitly admitted per owner |
   | EpisodeRewardTermination | transfer |
   | PythonLoaderControllerCaches | rederive |
   | BackendDeviceAllocationsLeases | drain/cancel or reject |
   | InFlightRequestsResults | drain/cancel/idempotent replay |
   | ExternalSideEffects | outbox/receipt or reject |
   | DiagnosticsTelemetry | rederive |

   Each row needs a maintained production owner, exact N/N-1 behavior,
   unknown-field policy, migration hashes, a durable replay log, directional
   compatibility vectors, and rollback semantics. Synthetic fixture bytes
   cannot satisfy this gate.
4. **Acceptance**: review independently after each work package and run a final
   integrated review; require native,
   Python, boundary, interruption-recovery and replay evidence. P4-C remains
   dark/shadow and P5 durability/authenticity/canary gates remain separate.

## Current branch checkpoint (2026-08-31)

- Work package 1 has a host-issued, single-use owner handle candidate bound to
  host/slot/resource/admission intent; replay, cross-host use and reuse are
  rejected. Production deployment qualification remains open.
- Work package 2 now has a checksummed append-only local WAL, `_commit`/`fsync`
  before mutation, monotonic phase validation, bounded commit/abort/recovery,
  terminal reopen, torn-tail handling and fail-closed corruption detection.
  It remains a P4-B local owner journal, not the P5-B ArtifactLedger,
  checkpoint/media or production process-restart qualification.
- Work package 3 now has a fixed twelve-owner callback registry, executable
  current/N-1 migration calls, exact source/artifact binding, strict unknown-
  field rejection, partial-import cleanup and a canonical directional matrix.
  The uninstalled `SimulationKernel` probe binds all twelve maintained owner
  surfaces. ECS, delayed/command subsets, episode reward/termination, Python
  cache rederive, CPU backend rehydrate policy, and host-fenced in-flight drain
  now have real candidate codecs and WAL-backed N-1 imports. The integrated
  host replacement test commits all twelve rows and recovers the terminal
  composite transaction after target-journal reopen. External effects remain an
  explicit `not-applicable` policy and diagnostics reset continuity at target.
- Work package 4 implementation is complete on this branch with fresh local
  native, Python, and boundary evidence. The mandatory independent integrated
  review remains pending; this is an acceptance gate, not an implementation
  blockage. Production authentication, P5 durability, cross-process replay,
  and caller cutover remain separately gated.

## Open defect: child-entity transfer scope (2026-09-01)

Measured native state is **59/60 cases, 1607/1607 assertions**. One case,
`ECS owner covers maintained database platform definitions`, fails closed:

```text
ECS snapshot contains an unresolved entity reference
(active_helo_entity_id=1475) on entity 'p4b-simobject-1474'
```

Root cause is an ownership boundary, not a codec defect.
`SimulationKernel::spawn_unit` adds the `SimObject` tag only to the entity the
factory returns. `DefaultUnitFactory::spawn_embarked_helo` pre-spawns the
embarked helo through the factory's own internal `spawn()` and reparents it with
`child_of`, so that helo never receives the tag. The snapshot query is
`terms[0].id = SimObject`, so the helo is outside the transferred set while the
ship's `EmbarkedAirOps::active_helo_entity_id` still references it. The export
refuses to emit an id that a target could resolve to an unrelated entity, which
is the intended fail-closed behavior.

The same applies to the munition child entities created per loadout station
(`unit_name + "_Stn_" + station`), which are also untagged children.

This is **not** patched here because every available repair changes an authority
that belongs to an owner decision:

1. Tagging the pre-spawned helo `SimObject` widens the transferred set and, when
   probed locally, immediately exposed a second gap: `ChildOf` pairs reach the
   snapshot and the Flecs JSON emits `"ChildOf":#...`, which the strict parser
   rejects. Hierarchy transfer needs a pair-remap design, and the restore path
   currently rejects any non-empty `pairs`. Tagging also changes
   `ecs.count<SimObject>()`, which gates the rebuild barrier, and
   `delete_with<SimObject>()` cleanup semantics.
2. Declaring `active_helo_entity_id` a rederive field contradicts the P1-A
   disposition table, where `EcsComponentTruth` is `transfer`.
3. Removing the field from the scalar reference set would let a dangling
   source-local id reach a target, which is the exact defect the guard exists to
   prevent.

Required owner decision before P4-B acceptance: whether the transferred ECS set
is the `SimObject` set (then factory-internal children need either explicit
admission plus `ChildOf` pair remap, or a declared rederive policy), or a
hierarchy closure over it. The independent reviewer must disposition this rather
than accept a widened tag as an incidental fix.

## Post-audit repair pass (2026-08-31)

The first independent audit returned `repair-required` with two critical and
multiple high-severity findings. The following repairs are now implemented and
covered by the local regression suites:

- Host publication keeps the pre-CAS authority snapshot, invokes durable owner
  recovery before deciding commit/rollback, and retains an explicit
  source-slot link for retryable ambiguous outcomes. A recovery retry can
  restore the source or complete the target publication; unresolved outcomes
  remain fail-closed and quarantined.
- Owner transactions now expose explicit recovery/compensation hooks. Composite
  imports compensate already-committed children in reverse order, terminal WAL
  rows require owner verification on reopen, torn tails are truncated during
  journal construction, and the file append path takes an OS-level writer lock.
- The decoder matrix disposition is enforced at profile admission, source and
  target registries must be distinct and owner-bound, and replacement proofs
  require a non-zero drain deadline. Target controls must expose a real
  transfer fence around the owner reservation; the base control fails closed
  until that fence is implemented.
- ECS export rejects unresolved `msg_arg` references and maps that field
  through logical entity identities; `SystemHealth` decoding rejects missing
  required keys. World and component-subset restore paths take a pre-image and
  compensate mutation failures.
- The Python cache rederive path clears and rebuilds command-chain, behavior,
  scripted-controller, and reward mirror state. Host-bound native owner
  registries require a target callback for invoking that hook after native
  import, while host-neutral fixtures may omit it.

These changes close the corresponding implementation defects but do not turn
the branch into a production-qualified or accepted P4-B release. The same
independent reviewer must re-run the integrated audit, and any residual
critical/high finding remains an acceptance blocker.

## Authority and handoff

The phase definitions, task clusters, dispatch queue and acceptance contract
remain authoritative. This route is a subordinate work packet and must not
create a second status source. P5 handoff includes P5-A executable plan,
P5-B RunReceipt/ArtifactLedger/restore and journal admission, P5-C facade-only
package/ABI, and P5-D unique canary plus same-release/process-restart rollback,
supported topology, SLO, operator and security evidence.

## Non-goals and exit criteria

No caller migration, production publication, rebuild retirement, multi-world
 enablement or fixture-only reduction is authorized. Accept only when handles are
 host-authenticated with full host/slot/world/episode/request/plan/barrier
 binding and linear consumption, transactions have WAL-backed durable terminal
 state and crash reconciliation, all decoders pass the directional compatibility
 and replay matrix, and the final integrated review has no unresolved
Critical/High (or safety-relevant Medium) finding.

The project-internal owner mapping for the next adapter slices is maintained in
[`p4b_owner_adapter_inventory_20260830.md`](p4b_owner_adapter_inventory_20260830.md).
