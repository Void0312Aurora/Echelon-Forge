# Air Scripted Algorithm Substitution Research — 2026-09-26

Language: English canonical; Chinese companion: not maintained (English-only
review surface).

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/architecture/reviews/air_scripted_algorithm_substitution_research_20260926.md`
Owner: `architecture/cross-domain-agency/air`
Review basis: `e0dd37a6` on
`codex/scripted-agent-system-architecture-plan`, plus the current source tree
and focused Air/cross-domain tests.

## Decision Summary

The Air scripted line has good module separation for independent testing, but
its internal strategies are not yet dependency-inverted. The current registry
can replace the complete `AirScriptedEngagementModel`; it cannot replace only
the planner or only the post-launch assessor without changing the orchestrator.

The next architecture slice is therefore **strategy composition**, not another
algorithm implementation. It must introduce typed Air-owned strategy seams,
inject the default planner and assessor through those seams, and preserve the
existing action/event behavior when the default implementations are selected.

This review does not promote Air from `playable_candidate`, does not authorize
a second global registry, and does not make RL a dependency. It is a planning
and research record for the next implementation batches.

Implementation status: ALG-0, ALG-1, and ALG-2 are now implemented in the
dedicated worktree. The strategy implementation is physically layered under
`python/tasking_contracts/air/strategy`; the former flat Air strategy paths were
removed and repository consumers use the canonical modules directly. The
engagement model now orchestrates injected observation and action adapters;
the default adapters preserve the maintained 17/12 layouts and fire-latch
behavior.

## Current Dependency Map

```text
DecisionModelRegistry / DecisionRuntimeAgent
                |
                v
AirScriptedEngagementModel
  |             |                 |                 |
  v             v                 v                 v
AirScriptedExecutionModel  AirObservationAdapter  AirTacticalPlanner  AirPostLaunchAssessor
                                |                         |
                                v                         v
                         AirActionAdapter         AirWeaponEnvelope
```

The neutral lifecycle is correctly located in `python/tasking_contracts`, with
Air-owned policy code under `python/tasking_contracts/air`, and does not import
RL. The Air engagement model now performs orchestration and lifecycle work;
mission/contact decoding, target-contact edge state, fire-latch state, and
17/12 action mapping are owned by the injected Air adapters. The planner and
assessor remain replaceable algorithms behind their typed protocols.

## Replacement Assessment

| Surface | Current isolation | Replacement today | Required seam |
| --- | --- | --- | --- |
| Weapon profile loader | high | replace JSON/profile input directly | typed source/profile contract |
| `AirEngagementPlanner` | medium-high | replace only if the new class preserves `plan` and `apply_guidance` shape | `AirTacticalPlanner` protocol |
| `AirPostLaunchAssessment` | high in unit tests, medium in runtime | replace only if it returns the current report fields | `AirPostLaunchAssessor` protocol |
| Mission/contact decoding | high | replace through `AirObservationAdapter` | typed `AirTacticalObservation` |
| 17/12 element action mapping | high | replace through `AirActionAdapter` | typed `AirActionApplication` |
| Whole engagement model | high | replace through existing model registry | keep `DecisionModel` lifecycle |

## Target Composition

The next Air-owned composition should have this shape:

```text
AirObservationAdapter
    ObservationPacket + event packet
        -> AirPlanningContext

AirTacticalPlanner
    AirPlanningContext + doctrine/profile
        -> AirTacticalDecision

AirPostLaunchAssessor
    AirAssessmentInput
        -> AirAssessmentReport

AirActionAdapter
    maintained flight action + AirTacticalDecision
        -> versioned Air action

AirScriptedEngagementModel
    owns lifecycle and orchestration only
```

The context and decision DTOs must stay Air-owned. Only fields with a second
domain consumer or an existing architecture authority may move into a common
envelope. This avoids turning the cross-domain layer into a weapon/geometry
mega-schema.

## Proposed Contract Shape

The exact names may change during implementation, but the responsibilities
must remain separate:

- `AirPlanningContext`: normalized C2/ROE state, target track geometry,
  weapon-profile reference, communication state, and observation provenance;
- `AirTacticalDecision`: mode, candidate identity, fire recommendation,
  bounded guidance, reason codes, and diagnostics;
- `AirAssessmentInput`: release/event facts, pending state, in-flight count,
  target contact/freshness, and shot budget;
- `AirAssessmentReport`: state, outcome, confidence, reattack gate, reason
  codes, and provenance;
- `AirActionAdapter`: the only owner of action-index layout and pulse/latch
  transport details.

The planner must not receive raw mission arrays. The action adapter must not
recompute tactical utility. The assessor must not write rewards, damage, or
terminal state.

## Migration Batches

### ALG-0 — Contract and parity fixture

Implemented slice: record the normalized context/decision fields and add
contract tests for invalid values and bounded guidance. The default planner
projects its rich audit record onto `AirTacticalDecision`; the legacy
primitive planner entry point remains available for compatibility. A full
scenario replay fixture remains part of the later parity gate.

### ALG-1 — Protocols and default injection

Implemented slice: add Air-owned `AirTacticalPlanner` and
`AirPostLaunchAssessor` protocols and update `AirScriptedEngagementModel` to
accept injected implementations while constructing the current implementations
by default. The default route remains behavior-compatible.

### ALG-2 — Adapter extraction

Implemented slice: move `_mission_values` and `_contact_geometry` into the
Air-owned `AirMissionContactObservationAdapter`, and move the 17/12 action
index mapping, target-contact edge pulse, and fire-latch transport into
`AirActionLayoutAdapter`. `AirScriptedEngagementModel` now owns orchestration
and lifecycle only. The default adapters are injected automatically, while
custom adapters are checked against the typed protocols. The native event/fire
gate remains the owner of final release acceptance.

### ALG-3 — Alternate strategy proof

Implemented proof slice: the maintained cooperative 2v1 compiled scenario can
run through the default adapter route or through per-slot recording adapters
that delegate to the same default behavior. The regression compares terminal
state, event/release steps, roster, reports, runtime decisions, and replay
identity, while asserting both injected adapters were exercised. Planner and
assessor replacement remains covered by the pure contract doubles.

The next strategy work is ALG-4 only if a second maintained Air consumer needs
a different algorithm profile; test-only doubles do not justify another
registry or runtime selection surface.

### ALG-4 — Strategy selection surface

If two maintained Air consumers require different algorithms, add a versioned
strategy profile or factory selection under the existing model registry. Do not
create a second process-wide strategy registry merely to select test doubles.
Any profile must declare its expected observation mode, action mode, and
evidence label.

## Acceptance Gates

The strategy-composition slice is complete only when all of the following are
true:

1. default planner/assessor behavior preserves the current bounded release,
   replay, and 4v4 terminal traces;
2. a fake planner can suppress fire without modifying the engagement model;
3. a fake assessor can block reattack without modifying the planner;
4. action-layout tests prove planner replacement does not alter transport
   indices or fire-gate ownership;
5. adapter and strategy modules remain free of `python.rl`, `gym_envs`,
   World Truth, reward, and native-kernel imports;
6. no new common field is added without a named second-domain consumer;
7. the Air capability label stays `playable_candidate` until the existing
   command/report, target-effect, visualization, and terminal gates close.

## Open Research Questions

- Should target-effect events be represented by a typed Air event packet or by
  a common report/event envelope with an Air extension?
- Does the current five-column contact token need a versioned adapter before
  close-combat and formation algorithms can share the planner seam?
- Should action layout adaptation be selected by `action_mode`, by an
  `ActionInterface` declaration, or by a maintained Air adapter factory?
- Which two non-Air consumers justify promoting any strategy fields into the
  cross-domain contract?

Until these questions have an owner and acceptance fixture, the default Air
planner and assessor remain the maintained implementations, and alternate
algorithms remain test-only substitutes.
