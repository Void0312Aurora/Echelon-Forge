# G3 Execution Surface Preflight Cluster

Status: `2026-05-22` accepted by `G3-D` main-thread integration; G4 released
with one bounded tasking-only lifecycle-proof slice.

Inputs:

- [G3 README](README.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Select and specify the first ground execution surface. This is a design and
preflight task; it should not implement runtime behavior.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `G3-A1` | Runtime-slice candidate | Choose one bounded G4 candidate, such as tasking-only lifecycle proof or minimal command delivery. |
| `G3-A2` | Stage map | Declare exact P0-P10 participation for the selected candidate. |
| `G3-A3` | Packet map | Name consumed, produced, and deferred packet families. |
| `G3-A4` | Observation/reporting design | Decide first reporting surface without exposing world truth. |
| `G3-A5` | Environment dependency map | Record terrain, line-of-sight, radio, and mobility assumptions as implemented, placeholder, or deferred. |
| `G3-A6` | Test plan | Name focused tests required before G4 can claim maintained behavior. |

## Parallel Cluster Map

| Stream | Main concern | Dependency | Acceptance |
|--------|--------------|------------|------------|
| `G3-A Candidate And Stage/Packet Map` | Select one safe G4 candidate and freeze its stage and packet participation. | none | One bounded candidate is chosen and its stage/packet map is explicit enough for later test ownership. |
| `G3-B Observation/Reporting And Environment Boundary` | Define the first report surface and the terrain / LOS / radio / mobility dependency map. | none | The first reporting surface avoids world-truth leakage and the environment assumptions are honestly marked as implemented, placeholder, or deferred. |
| `G3-C G4 Release Envelope And Test Plan` | Define write scope, compatibility guards, no-private-path proof shape, and focused tests for G4. | none | G4 receives one bounded write scope plus a focused validation plan that does not assume movement, fires, or observation export already exist. |
| `G3-D Main-Thread Integration` | Integrate A-C into the final G3 decision and release or hold G4. | waits for A-C | The authoritative G3 packet records the chosen G4 candidate, write scope, test plan, residual map, and any standards follow-up. |

## Parallel Rule

- `G3-A`, `G3-B`, and `G3-C` may run in parallel only as bounded diagnostics or
  preflight streams.
- They must not split the same normative table across concurrent authors.
- The main thread owns the canonical cluster table and final wording of the G3
  release decision.
- Standards follow-up is allowed only if a worker proves that current
  terminology or ownership is inconsistent with the selected candidate.
- `G3-D` is serial and starts only after A-C return.

## Write Scope

Allowed:

- `docs/task/ground/g3_execution_surface_design/**`
- updates to `docs/task/ground/README.md`
- standards follow-up only if a G3 decision changes normative ownership

Do not edit:

- runtime implementation
- profile implementation from G1 unless integration owner requests a narrow doc
  update
- fixture implementation from G2
- the same canonical G3 decision table from multiple workers at once

## Suggested Validation

```bash
git diff --check
```

## Handoff

Return:

- selected G4 candidate
- stage and packet maps
- observation/reporting decision
- deferred assumptions
- test plan
- any standards update needed before G4

Recommended worker split:

- `G3-A` should return the candidate ranking plus the chosen stage/packet map.
- `G3-B` should return the reporting surface recommendation plus environment
  dependency / deferral map.
- `G3-C` should return the G4 write scope, compatibility guard plan, and
  focused tests.
- `G3-D` should integrate the three returns into the authoritative G3 packet.

## Accepted G3-D Result

- `G3-A` selected the safest candidate as
  `tasking-only lifecycle proof through normalized ground TaskOrder ->
  LeaderIntent -> PilotReport status shell`.
- `G3-B` accepted `PilotReport` as the only first reporting surface and kept
  `ObservationPacket` / `TrackPacket` deferred.
- `G3-C` released G4 only for a bounded shared-entry-point lifecycle proof and
  rejected broad command, movement, terrain, sensing, fires, DTO/binding, and
  facade expansion.

Accepted stage map:

- `P0`: compatibility ingress only through accepted content/setup evidence.
- `P2`: primary maintained ground stage for the first runtime slice.
- `P3`: deferred as a formal command-delivery surface.
- `P6`: deferred.
- `P10`: deferred formally; only `PilotReport` status-shell evidence is allowed
  in the first slice.

Accepted packet map:

- `Consumed`: existing tasking-core equivalents, `AgentRole`, accepted ground
  profile aliases, and accepted G2 seed/contracts.
- `Produced`: normalized `TaskOrder`, defaulted `LeaderIntent`, compatibility
  `PilotReport`.
- `Deferred`: `CommandPacket`, `ObservationPacket`, `TrackPacket`.

Accepted environment map:

- `terrain = placeholder`
- `line-of-sight = placeholder`
- `radio = placeholder`
- `mobility = deferred`

Accepted G4 release test plan:

- existing `tests/leader/test_ground_profile_semantics.py`
- existing `tests/contracts/unit/ground/*.json`
- one focused runtime/shared-batch lifecycle proof for ground assignment/report
  propagation through maintained shared entry points
- narrow compatibility guards on common-core and naval mission/profile behavior

## Available G1-G2 Evidence

- G1 accepted a Python-profile-only ground slice with `army`, `ground`, `land`,
  and `ServiceProfile.Army` normalizing to `ground`.
- G1 accepted starter defaults for `TASK_MOVE`, `TASK_OCCUPY`, and
  `TASK_SUPPORT` through common-core fields only.
- G2 accepted a non-auto-loaded platoon-centered content seed at
  `examples/config/database/ground/units/ground_platoon_starter.seed`.
- G2 accepted runnable starter contracts under `tests/contracts/unit/ground/`.

Design preflight must not convert that evidence into runtime movement, terrain,
sensing, fires, weapon, damage, or combat claims.
