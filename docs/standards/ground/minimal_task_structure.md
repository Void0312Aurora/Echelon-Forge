# Ground Minimal Task Structure

Language:
- English canonical: `minimal_task_structure.md`
- Chinese companion: [minimal_task_structure.zh.md](minimal_task_structure.zh.md)

Status: `2026-05-21` G0 minimum tasking baseline.

This note freezes the smallest useful ground tasking structure that G1 work must
respect.

It is intentionally narrow. It captures the minimum semantics needed to connect
the shared contract, the Army service profile, and the dedicated `ground`
specialization before runtime behavior is implemented.

## Scope

Supported starter task shapes:

- `TASK_MOVE`
- `TASK_OCCUPY`
- `TASK_SUPPORT`

These three entries are the only G0 starter task shapes. They are the minimal
entries that can express the first ground-domain tasking plan without importing
air sortie language, naval station-keeping semantics, or deferred ground
execution surfaces.

Deferred task shapes:

- `TASK_SCREEN`
- `TASK_SECURE`
- `TASK_PATROL`
- `TASK_DIRECT_FIRE`
- `TASK_INDIRECT_FIRE`
- `TASK_SUSTAIN`

The deferred shapes are plausible ground tasks, but they require more explicit
mobility, sensing, fires, or sustainment semantics than G0 should freeze.
They must not be treated as first-wave task orders, enum defaults, or required
profile outputs until a later accepted plan promotes them.

## Layered Structure Rules

When `tasking_profile = ground`, `tasking_profile = land`, or
`service_profile = Army`:

- the normalized maintained tasking profile is `ground`
- `tactical_unit_type` defaults to a platoon-centered tactical unit for the
  first maintained slice
- `parent_node_id` is the preferred command-hierarchy anchor
- `supported_node_id` and `supporting_node_id` express support relationships
- `task_group_id` remains a shared optional organization hook, not the primary
  land task owner
- company, battalion, brigade, division, and corps may exist as scenario or
  tasking metadata, but the first tight-loop task owner is platoon-centered

## Minimal Semantic Map

The minimal semantic set absorbed by the ground specialization is:

- `ground`
- `platoon`
- `move`
- `occupy`
- `support`
- `ground_squad_leader`
- `ground_platoon_commander`
- `ground_company_commander`

### `TASK_MOVE`

- semantic meaning: move a platoon-centered unit toward a route, phase line, or
  objective reference
- current code representation: `GroundTaskMode::MoveStatic`; this preserves the
  G0/G1 static DTO boundary and does not release route traversal or movement
  dynamics
- `task_family = Maneuver` when that enum exists; otherwise use the nearest
  generic route/movement family and keep the ground-specific meaning in the
  tasking profile
- expected owner: a platoon-centered tactical unit; higher echelons remain
  scenario or tasking metadata
- `coordination_mode = Independent` by default unless a support relationship is
  declared
- `parent_node_id` is the command owner fallback
- `supported_node_id / supporting_node_id` are optional
- exact route traversal, movement dynamics, terrain interaction, sensing
  cadence, and execution command surface are deferred

### `TASK_OCCUPY`

- semantic meaning: move to and hold a ground objective, battle position, or
  named area
- `task_family = Maneuver` when that enum exists; otherwise use the nearest
  generic task family and keep `occupy` in the ground profile
- expected owner: a platoon-centered tactical unit; company, battalion, brigade,
  division, and corps are not promoted to tight-loop owners by this task
- `coordination_mode = Independent` by default
- `parent_node_id` is the command owner fallback
- occupation is a tasking intent only; terrain realism, cover, concealment,
  obstacle/breach behavior, damage effects, and detailed occupation geometry are
  deferred

### `TASK_SUPPORT`

- semantic meaning: act in a supporting relationship to another ground unit or
  task node
- `task_family = Support` when that enum exists; otherwise use a generic
  support-capable family and keep the ground-specific meaning in the tasking
  profile
- `coordination_mode = Support`
- `supporting_node_id` should identify the supporting unit when known
- `supported_node_id` should identify the supported unit or task node when
  known
- support expresses relationship and intent only; fires, sustainment,
  logistics-specific behavior, damage effects, observation export, and track
  fusion are deferred

## Agency Defaults

The first ground tasking profile should recognize these role defaults:

| Role | Authority scope | Typical task responsibility |
|------|-----------------|-----------------------------|
| `ground_squad_leader` | squad | execute assigned move/occupy/support tasks |
| `ground_platoon_commander` | platoon | own first-wave tasking and delegation |
| `ground_company_commander` | company | coordinate platoons; runtime coordination deferred |

## Information Defaults

The first ground tasking profile should assume:

- ground sensing is terrain-masked and line-of-sight constrained
- shared tactical picture is constrained by radio range and relay topology
- no maintained ground policy should consume world truth directly
- formal `ObservationPacket` and `TrackPacket` surfaces are deferred

## Clock Defaults

The first ground tasking profile should assume:

- base tactical evaluation cadence: `1 Hz`
- movement and sensing cadence: deferred
- any future lower-rate ground updates must still enter the shared
  causal-temporal scheduler and evidence model

## Deferred Realism Guardrails

G0 starter tasking must not require maintained implementations for:

- observation export or track fusion
- movement dynamics or route traversal
- direct fires or indirect fires
- logistics, sustainment, or recovery flow
- damage, effects, suppression, or attrition behavior
- terrain traversal, cover, concealment, obstacles, or breach realism

Those topics remain valid future ground work, but they are not part of the G0
minimum task vocabulary.

## Non-goals

This document does not define:

- ground movement dynamics
- terrain traversal, cover, concealment, or breach behavior
- direct-fire or indirect-fire runtime
- logistics or sustainment runtime
- ground-specific `MissionCommand` fields
- observation export schema
- damage or effects behavior

It exists to freeze the minimum useful contract, not to describe the whole land
warfare model.

## MVP Scenario Use

The first maintained MVP scenario uses `TASK_OCCUPY` because it can validate
the ground tasking status chain without implying maintained movement runtime.
This does not promote occupation geometry, terrain effects, or hold behavior to
runtime-supported semantics.
