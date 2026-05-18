# US Army Profile

Language:
- English canonical: `army.md`
- Chinese companion: [army.zh.md](army.zh.md)

Status: `2026-05-18` authoritative for Army service-profile placement.

This document defines how the repository should interpret Army organizational
layers and command relationships before any future ground specialization is
implemented.

It is intentionally narrower than a full Army doctrine summary. Its purpose is
to prevent air-first runtime assumptions from leaking into future land modeling.

## Real-World Basis

The Army's official public doctrine resources continue to frame land operations
around mission command, command and control, and echeloned formations rather
than around sortie packages.

Official references:

- [Mission Command Center of Excellence (MCCoE)](https://usacac.army.mil/Organizations/Centers-of-Excellence-CoE/MCCoE)
- [Mission Command Resources](https://usacac.army.mil/Organizations/Centers-of-Excellence-CoE/MCCoE/Mission-Command-Resources)
- [CADD Command and Control Division](https://usacac.army.mil/Article-Library/View-Content-2/Command-and-Control-Division?ArtMID=437&ArticleID=331)

The current MCCoE public mission statement says it leads the Mission Command
Force Modernization Proponent and the Command and Control Warfighting Function.
The Mission Command Resources page directly points to `ADP 6-0 Mission Command:
Command and Control of Army Forces`, and the Command and Control Division page
states that the division produces keystone doctrine including `ADP 6-0`.

For standards purposes, that is the important reality anchor:

- Army organization is echeloned
- command and control is a first-class concern
- the repository should model land units through command relationships and
  tactical echelons, not through air sortie terminology

## Layer Boundaries

### `joint/common core`

The common layer should keep the shared cross-service skeleton:

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `authority_scope`
- `command_relationship`
- `coordination_mode`
- `task_group_id`
- `role_code`
- `supported_node_id`
- `supporting_node_id`
- `recovery_site_id`

These fields are portable. They should not be renamed into air-only or
ship-only language.

### `services/army`

The Army service profile explains the Army reading of that skeleton:

- echelon-aware unit organization
- maneuver, fires, sustainment, and support relationships
- which layers count as tactical runtime units
- which layers should remain operational or campaign metadata

This layer owns interpretation, not platform execution details.

### Future land specialization

A future ground specialization would own the execution vocabulary that does not
yet exist as a maintained repository contract:

- maneuver geometry
- frontage, bounds, routes, and battle positions
- direct-fire and indirect-fire execution surfaces
- sustainment and mobility-control details
- domain-specific observations, actions, and reporting extensions

Until such a specialization exists, `services/army` should act as a boundary
document, not as a speculative runtime API.

## Runtime Boundary

### Layers that should remain scenario or operational metadata

The current repository should keep these echelons above the tight-loop runtime:

- corps
- division
- brigade
- battalion when it is acting primarily as an operational mission-management
  node rather than a direct tactical controller

These layers are better represented as:

- scenario organization
- mission assignment and authority framing
- logistics and fires allocation metadata
- operational boundaries and force packaging

### Layers that are plausible tactical runtime units

If land modeling is expanded, the first useful tight-loop units are likely to be:

- squad / section
- platoon
- company / troop / battery

Battalion-sized control can still exist in the scenario and tasking picture,
but the executable loop should first stabilize around the smaller tactical
formations above.

## Direct Constraints On Standards Design

### Do not reuse air vocabulary as the land baseline

Army-oriented standards should not treat these as generic terms:

- `wingman`
- `element lead`
- `runway`
- `takeoff`
- `formation slot`
- `recovery approach`

Those are air terms, not land common-core terms.

### Preserve support and hierarchy fields in the common core

The Army profile strengthens the case for keeping the following shared anchors:

- `tactical_unit_type`
- `authority_scope`
- `supported_node_id`
- `supporting_node_id`
- `role_code`
- `coordination_mode`

These fields are much closer to a service-neutral land baseline than any
aircraft-centric DTO shape.

### Keep service profile separate from future maneuver APIs

This document should not invent a fake ground action surface. It should only
state:

- what the tactical echelon boundary should be
- what relationships must survive in common core
- what must remain open until a dedicated ground specialization is implemented

## Relationship To Current Repository Contracts

The current repository does not yet maintain a dedicated Army execution layer.
That means the Army profile is mainly a standardization guardrail for future
design:

- shared tasking and reporting flow should remain `TaskOrder -> LeaderIntent ->
  MissionCommand -> Report`
- common fields should remain portable enough for land use
- air-specific command details should not be promoted into the Army baseline

This is exactly why `services/army` matters before a ground runtime exists.

## Related Documents

- [Service Profile Overview](README.md)
- [Joint Command and Modeling Baseline](../joint/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../joint/command_link_and_reporting_baseline.md)
- [Simulation Conventions](../foundation/conventions.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)
