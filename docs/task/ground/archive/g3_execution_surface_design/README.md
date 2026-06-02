# G3 Execution Surface Design

Status: `2026-05-22` G3 design preflight accepted by main-thread integration;
`G4` is released with one bounded tasking-only lifecycle-proof slice.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn task slice.

Inputs:

- [G1 contract skeleton](../g1_contract_skeleton/README.md)
- [G2 content and test seed](../g2_content_test_seed/README.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Design the first ground execution surface before runtime behavior is written.

## Output

- [G3 execution surface preflight cluster](g3_execution_surface_preflight_cluster_20260521.md)
- [G3 subagent dispatch packets](g3_subagent_dispatch_packets_20260522.md)

## Scope

In scope:

- decide whether the first runtime slice is tasking-only or includes a tiny
  command surface
- define stage coverage beyond G1
- name consumed and produced packets
- define observation/reporting surface candidates
- map terrain/environment dependencies and explicit deferrals

Out of scope:

- implementing movement, sensing, fire-control, or observation export
- large `MissionCommand` expansion
- terrain realism implementation

## Gate

G3 is mergeable when it names one safe G4 runtime slice and records all
deferred surfaces honestly.

Accepted G3 decision:

- selected G4 candidate:
  `tasking-only lifecycle proof through normalized ground TaskOrder ->
  LeaderIntent -> PilotReport status shell`
- produced report surface: `PilotReport` only
- held packet/runtime surfaces: `CommandPacket`, `ObservationPacket`,
  `TrackPacket`, formal `P3 CommandDelivery`, formal `P10 ObservationExport`,
  movement, sensing, fires, terrain, and broad `MissionCommand`
- G4 write scope: shared entry-point lifecycle proof plus the narrowest runtime
  plumbing needed so ground loaders resolve through the maintained
  `tasking_profile` bridge rather than an air-only mission-command shortcut
- G4 test plan: focused ground profile/contract tests, one shared batch/runtime
  lifecycle proof, and narrow air/naval compatibility guards

## Dispatch Shape

G3 is split into three parallel-safe diagnostics streams plus one serial
integration pass:

- `G3-A Candidate And Stage/Packet Map`: choose the most credible G4 candidate
  and freeze its stage / packet map.
- `G3-B Observation/Reporting And Environment Boundary`: define the first
  reporting surface and the terrain / line-of-sight / radio / mobility
  dependency map.
- `G3-C G4 Release Envelope And Test Plan`: define the bounded write scope,
  compatibility guard expectations, and focused test plan required before G4 is
  released.
- `G3-D Main-Thread Integration`: integrate A-C and publish the final G3
  release decision for G4.

The main thread owns the canonical G3 decision. Parallel workers should return
bounded preflight packets instead of editing the same normative table.
