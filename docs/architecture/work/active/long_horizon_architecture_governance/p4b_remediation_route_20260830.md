# P4-B Remediation Route: Provenance And Durable Transfer

Status: `2026-09-13` repaired implementation checkpoint; independent review
passed for the dark/shadow candidate. P4-B is not accepted for production.
Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/p4b_remediation_route_20260830.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-13`

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

## Resolved child-entity transfer closure (2026-09-13)

The transferred ECS set is the transitive `SimObject` closure returned by
`SimulationKernel::spawn_unit`. The host-level spawn path tags every
factory-owned `ChildOf` descendant, including embarked aircraft and loadout
munitions, so cleanup, barrier counts, and state transfer observe one explicit
native truth set. The serializer carries `ChildOf` edges as logical-name pairs
and restores them only after all entities exist.

Every declared entity-bearing scalar and vector reference is logical-name
remapped or rejected; tactical track identities and generic command arguments
retain their typed logical scalar semantics, while target-bearing compatibility
messages remap `msg_arg` only for the declared entity-bearing kinds. Raw source-
local entity IDs never cross the boundary.
`EmbarkedAirOps.active_helo_entity_id` remains a transferred scalar reference:
it is remapped when the child is in the admitted closure, and an unresolved
non-zero value fails closed rather than being silently reset or carried into
the target. The maintained database-platform round-trip, including mutated
embarked-helo and loadout-munition children, strict `SimObject`/subset collision
rejection, and a destroyed-child case, is green. A live WAL object also
truncates an interrupted tail before same-instance recovery.

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
- ECS export maps every declared entity-bearing scalar/vector reference through
  logical entity identities and rejects unknown source-local ids; tactical track
  identities and generic command arguments retain their typed scalar domain,
  while target-bearing compatibility messages remap `msg_arg` only for the
  declared entity-bearing kinds. Factory-owned `ChildOf` descendants are
  admitted into the `SimObject` closure, so `EmbarkedAirOps.active_helo_entity_id`
  is remapped as ordinary transferred truth; any unresolved non-zero entity
  reference still fails closed.
  `SystemHealth` decoding rejects missing required keys. World and
  component-subset restore paths take a pre-image and compensate mutation
  failures, while name collisions with non-`SimObject` entities fail closed.
- The Python cache rederive path clears and rebuilds command-chain, behavior,
  scripted-controller, and reward mirror state. Host-bound native owner
  registries require a target callback for invoking that hook after native
  import, while host-neutral fixtures may omit it.

These changes close the corresponding implementation defects within the
declared candidate scope. The independent reviewer re-ran the integrated audit
and returned `pass` for the dark/shadow candidate. This does not turn the branch
into a production-qualified P4-B release; P5 production-boundary findings remain
gated and any future candidate-scope Critical/High finding remains an acceptance
blocker.

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
