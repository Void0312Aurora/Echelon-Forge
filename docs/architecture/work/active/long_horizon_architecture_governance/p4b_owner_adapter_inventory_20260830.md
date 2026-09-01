# P4-B Owner Adapter Inventory

Status: `2026-08-31` implementation checkpoint  
Document kind: `evidence / task support`  
Canonical phase: P4-B state-transfer repair

This inventory records the project-internal runtime surfaces bound by the P4-B
candidate. “Real state” means state read from these maintained owners at the
native episode barrier; it does not mean an external dataset or user-supplied
file. The rows below are candidate evidence, not production qualification.

| P4-B category | Current maintained source surface | Current status | Adapter work still required |
| --- | --- | --- | --- |
| CompositionProviderSystemGraph | `runtime::providers::DefaultSimulationComposition`, provider catalog and resolved composition digest | candidate exports all three maintained composition digests, imports N-1 through the owner journal, rederives on the target and rejects a target-plan mismatch | add a genuinely different N/N-1 provider graph release vector rather than the current same-byte reader promotion |
| EcsComponentTruth | `SimulationKernel::ecs`, guarded by the kernel composition/world mutex | candidate uses reflected registrations plus dedicated codecs, stable logical entity references, strict whole-payload preflight, rollback, N-1 import, and generic/database platform-family round trips | add cross-release/process replay qualification and keep reflection/codecs synchronized with new components |
| RngState | `SimulationKernel::rng`, seeded in `SimulationKernel::reset()` and passed to providers | dark codec serializes `mt19937` plus draw position; known kernel RNG call sites advance the counter; a real N-1 artifact imports through the owner WAL, reopens terminal state and proves the next 16 engine draws | keep the draw-site census current and add cross-release/process replay qualification |
| ClockCadence | Flecs `ecs_world_info_t::world_time_total`, `SimulationKernel::time_step`, exact replay time hook | candidate round-trips world time/timestep, imports N-1 through the owner WAL, binds host barrier counters, and rejects trailing bytes or stale barrier metadata; host replacement includes the row | add cross-release/process replay qualification |
| DelayedEventsQueues | `SimulationKernelEngagementEventStore` and delayed-delivery systems | candidate serializes the maintained delayed component subset with exact schema, strict fields, N-1 migration, WAL commit/abort and rollback evidence | extend the subset as new delayed store truth is admitted and add cross-release replay |
| CommandsLinksPendingIntent | `MissionCommandControlState`, `CommandLink`, typed command APIs and command-link systems | candidate serializes the maintained command/link subset with exact schema, N-1 migration, duplicate-safe WAL import and target verification | keep owner/version census current and add cross-release replay |
| EpisodeRewardTermination | `RuntimeEpisodeCoordinatorCandidate` and native episode capability | candidate imports the N-1 exact host-issued replacement-barrier snapshot plus maintained Score/Health/lifecycle subset; host replacement commits the row and reopens its WAL | qualify release/process crash reconciliation beyond the local journal |
| PythonLoaderControllerCaches | Python bindings/facade mirror surfaces | candidate emits an explicit native-authority rederive policy; the Python loader hook applies target-native terminal state and clears poisoned eval/reward/C2 caches, with negative tests | integrate with a production caller only after P5 package/authentication gates |
| BackendDeviceAllocationsLeases | CPU-exact backend profile and host lease accounting | candidate emits a strict CPU rehydrate policy, forbids raw handle transfer, and journals N-1 import; no CUDA handle is claimed as transferred | qualify a real backend lease provider and cleanup/restart behavior; never transfer raw handles |
| InFlightRequestsResults | `RuntimeHostSlot` lease/in-flight counters and request-related host admission state | candidate exports exact read-only-result lease count, requires cooperative cancellation acknowledgement, journals a fenced drain receipt, and verifies late-result drain during host replacement | add process-level idempotent replay evidence |
| ExternalSideEffects | engagement/weapon-release event stores and side-effect call sites | the kernel adapter now executes the matrix's explicit `not-applicable` decision: no external outbox/receipt is transferred, trailing policy fields reject, and N-1 admission is journaled | retain the explicit rejection unless a real external effect is introduced; any future effect requires outbox/receipt and crash-before/after proof |
| DiagnosticsTelemetry | engagement event export and runtime diagnostic surfaces | target-rederive policy now records `continuity=reset-at-target`, validates barrier metadata and imports N-1 through the owner journal; it does not claim telemetry continuity | connect any maintained telemetry sink and preserve/report gaps if continuity becomes required |

## Implementation rule

The next adapter slice must wrap the source surfaces above rather than invent
fixture-only payloads.  Where a source surface has no aggregate export/import
API, P4-B adds that API at the owning layer or records an explicit
`not-applicable`/`reject` decision.  The existing decoder/replay matrix and
`runtime_state_transfer_profile_from_decoder_matrix()` only freeze the
contract; they do not by themselves qualify production adapters or durable
journals.
