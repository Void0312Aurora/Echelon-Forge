# Ground Standards

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-05-21` G0 specialization baseline.

This directory contains the authoritative standards for the dedicated `ground`
specialization.

It is the standard landing point for the third-domain G0 work. Its job is to
separate `joint/common core`, `services/army`, and `ground` clearly enough that
future tasking, content, profile, and runtime work can proceed without
importing air or naval execution assumptions.

Within that boundary, `army` is a service profile and accepted
tasking-profile alias, `land` is an accepted descriptive alias, and both
normalize to the maintained `ground` execution specialization. Neither `army`
nor `land` names a separate ground runtime stack.

## 1. Layer Model

### `joint/common core`

The shared layer keeps the cross-service contract stable.

It owns fields such as:

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `command_relationship`
- `authority_scope`
- `coordination_mode`
- `role_code`
- `supported_node_id / supporting_node_id`
- `task_group_id`
- `recovery_site_id`

These are service-neutral shapes. They are not ground execution semantics.

### `services/army`

The Army service profile explains how the shared contract should be read for
Army land forces.

It owns the interpretation of:

- echelon-aware organization
- command and support relationships
- which layers are plausible tactical runtime units
- which layers remain scenario, operational, or campaign metadata
- maneuver, fires, sustainment, and support as Army profile concerns before
  they become execution semantics

### `ground`

The `ground` specialization owns the tight-loop land execution semantics that
the service profile intentionally does not define:

- platoon-centered starter tasking
- move, occupy, and support task semantics
- ground command/support execution vocabulary
- ground agency roles and authority scopes
- terrain-masked information-state assumptions
- future ground mobility, sensing, direct-fire, indirect-fire, sustainment, and
  reporting extensions

## 2. G0 Baseline Decisions

The G0 baseline freezes these defaults for the first ground-domain work:

- maintained specialization name: `ground`
- accepted tasking-profile aliases: `army`, `ground`, `land` (`army` remains
  the service profile; `land` remains an alias)
- normalized tasking-profile name: `ground`
- first tight-loop tactical unit: `platoon`
- first task family vocabulary: `move / occupy / support`
- first tasking cadence assumption: `1 Hz` tactical evaluation

These defaults are frozen for G0. Later work may only change them through an
accepted standards update; any worker that needs a different default must stop
instead of editing these canonical terms in place.

## 3. Minimal Semantic Contract

The minimal ground semantic set now treated as first-class is:

- `ground`
- `platoon`
- `move`
- `occupy`
- `support`
- `ground_squad_leader`
- `ground_platoon_commander`
- `ground_company_commander`
- terrain-masked sensing
- radio-range-constrained shared tactical picture

These are the smallest terms needed to make the third-domain task plan
meaningful without overfitting to air sortie or maritime station language.

## 4. Stage Coverage Rules

The first ground slice participates in the shared lifecycle through these
declared stages:

These declarations are architecture commitments for planning and contract shape.
They are not claims that maintained ground runtime behavior already exists.

| Stage | Ground baseline |
|-------|-----------------|
| `P0 ContentCompile` | Ground platform definitions should lower through capability bundles. |
| `P2 TaskingIntent` | Ground task orders, leader intents, echelon metadata, command relationships, and support relationships. |
| `P3 CommandDelivery` | Deferred until a minimal ground command surface is accepted. |
| `P6 SenseTrackLink` | Deferred until terrain masking, line-of-sight, radio range, and relay topology are specified. |
| `P10 ObservationExport` | Deferred for formal observation export; status/report contract tests may land earlier. |

Any ground implementation that touches additional stages must update this
standard or a derived accepted standards document first.

Clock-domain default: `1 Hz` is the tactical evaluation baseline for ground
tasking. Motion and sensing updates remain low-rate, event-driven, or deferred
until a later accepted execution design, and any cadence must merge through the
shared causal-temporal scheduler rather than a private ground loop.

## 5. Capability Composition Rules

Ground platforms must be defined through capability composition, not as a new
canonical hardcoded type-name dispatch path.

First-wave capability-family declarations:

| Family | Ground baseline |
|--------|-----------------|
| `PlatformFamily` | `dismounted_unit`, `ground_vehicle_section` |
| `MotionFamily` | `ground_mobility`; wheeled, tracked, and dismounted variants remain future details |
| `SensorFamily` | `ground_visual`, `ground_acoustic`; deferred to execution design |
| `LauncherFamily` | `direct_fire_platform`, `indirect_fire_battery`; deferred to execution design |
| `DoctrineFamily` | `land_tactics` for move, occupy, support, and later screen/secure |
| `EffectsFamily` | deferred |

`spawn_unit(type_name)` may remain only as a compatibility wrapper. It must not
become the long-term canonical ground construction path.

## 6. Agency And Information State

Ground roles must declare:

- `role`
- `authority_scope`
- `information_state_source`
- `decision_model_ref`
- `action_interface`

First-wave role defaults:

| Role | Authority scope | Information source | Decision model ref | Action interface |
|------|-----------------|--------------------|--------------------|------------------|
| `ground_squad_leader` | squad | sensed state plus agent observation | scripted land-task execution; later learned policy | task-order execution |
| `ground_platoon_commander` | platoon | shared tactical picture plus agent observation | scripted platoon tasking; later doctrine profile | leader intent and task-order delegation |
| `ground_company_commander` | company | shared tactical picture | company coordination doctrine, deferred | coordination intent, deferred |

Ground information state follows the six-layer architecture model:

- `World Truth` remains internal to the shared runtime when implemented.
- `Sensed State` defaults to terrain-masked and line-of-sight constrained.
- `Track State` may use visual/acoustic correlation; maintained fusion is
  deferred.
- `Shared Tactical Picture` is constrained by radio range, relay topology,
  latency, and permission.
- `Agent Observation` is view-spec-shaped and must not expose world truth.
- `Decision Belief` must declare which observation or shared-picture inputs
  produced it.

These information-state statements are boundaries and deferrals for future
work. They do not claim that maintained terrain, sensing, tracking, relay, or
observation-export runtime behavior already exists.

## 7. What Belongs Here

Documents in this directory should describe ground-specific semantics, such as:

- platoon-centered tasking defaults
- move, occupy, support, screen, secure, and later fires task semantics
- ground command/support authority interpretation
- terrain-masked sensing and radio-constrained information sharing
- ground agency roles
- future ground execution and reporting specialization

## 8. What Does Not Belong Here

The following should remain in `joint/`, `services/army`, or bridge documents:

- shared `command_relationship`, `authority_scope`, `task_family`,
  `service_profile`, `tactical_unit_type`, and `coordination_mode` definitions
- Army service organization summary that does not define execution semantics
- scenario/runtime adapter details or a private ground runtime path
- implementation-specific C++ DTO memory layout
- claims that complete terrain, mobility, direct-fire, indirect-fire, damage, or
  logistics runtime behavior exists before those workstreams have accepted task
  plans

This overview is normative for standards placement only; it does not implement
or authorize a ground-only runtime pipeline.

## 9. Relationship With Air And Naval

`ground` is not a rename of air or naval documentation.

Ground documentation should avoid default air concepts such as:

- `wingman`
- `element lead`
- `runway`
- `takeoff`
- `formation slot`
- `recovery approach`

Ground documentation should also avoid treating naval terms such as `station`,
`task group`, or maritime `screen` as the default land baseline unless a ground
document explicitly redefines the land-specific meaning.

## 10. Related Documents

- [Ground Minimal Task Structure](minimal_task_structure.md)
- [US Army Profile](../services/army.md)
- [Joint Command and Modeling Baseline](../joint/command_and_modeling_baseline.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)
- [Ground Domain Bootstrap Plan](../../task/ground/ground_domain_bootstrap_plan_20260521.md)
