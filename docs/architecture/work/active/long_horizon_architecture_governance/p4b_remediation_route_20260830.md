# P4-B Remediation Route: Provenance And Durable Transfer

Status: `2026-08-30` planning artifact; P4-B remains `repair-required`.
Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/p4b_remediation_route_20260830.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-30`

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
