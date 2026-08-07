# US Marine Corps Profile

Language:
- English canonical: `marine_corps_profile.md`
- Chinese companion: [marine_corps_profile.zh.md](marine_corps_profile.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/joint/service_profiles/standards/marine_corps_profile.md`
Owner: `domains/joint/service-profiles`
Last verified: `2026-08-08`

Status: `2026-05-18` authoritative for USMC service-profile placement.

This document defines how the repository should interpret U.S. Marine Corps
organization as a service profile.

The goal is not to claim that a dedicated Marine runtime already exists. The
goal is to define how Marine Corps force packaging and command relationships
should constrain future standardization work.

This profile interprets the Joint common core for Marine Corps force packaging
and command relationships. It does not own air, naval, or ground execution
contracts.

## Real-World Basis

The official Marine Corps doctrinal baseline still treats Marine operations as
an integrated service-and-component problem built around Marine air-ground task
forces rather than around a single-domain template.

Official reference:

- [MCDP 1-0 w/ CH 1-3](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1323621/mcdp-1-0-w-ch-1-3/)

The current official MCDP 1-0 page states that the publication focused on:

- the role of the Marine Corps component at the operational level
- how the Marine expeditionary force, the largest MAGTF, conducts operations at
  the tactical level

That is enough for this repository's standards boundary. The USMC should not be
modeled as an ad hoc sum of Army, Navy, and Air Force terms. It needs its own
service-profile interpretation layer.

## Layer Boundaries

### `joint/common core`

The common layer should retain the cross-service skeleton:

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

These fields remain shared. The Marine Corps profile explains how a MAGTF-style
force package reads them.

### Marine Corps service-profile interpretation

The USMC service profile owns the Marine reading of the shared skeleton:

- MAGTF-style packaging
- command element responsibilities
- ground, aviation, and logistics element relationships
- when a Marine organizational layer is just force packaging and when it should
  be interpreted as a tactical runtime unit

This layer owns service interpretation, not execution mechanics.

### `air`, `naval`, and ground specialization

Current domain execution semantics continue to live elsewhere:

- air execution contracts belong in `air/`
- maritime execution contracts belong in `naval/`
- land execution contracts beyond shared tasking/schema bootstrap belong in the
  dedicated ground layer

The Marine profile should therefore coordinate those layers through shared
fields rather than redefining their command or sensor surfaces.

## Runtime Boundary

### Layers that should remain scenario or mission-packaging metadata

The following concepts are real and important, but should stay above the
tight-loop runtime in the current repository:

- Marine component-level operational framing
- MEF / MEB / MEU force packaging when used as campaign organization
- large-scale amphibious or expeditionary task organization
- cross-domain task assignment that has not yet been specialized into current
  air, naval, or ground execution contracts

These layers belong in:

- scenario design
- force packaging metadata
- authority and support relationships
- operation-level orchestration

### Layers that can touch the current executable boundary

Today, Marine concepts can only enter the executable boundary through maintained
shared or specialized contracts:

- shared command-and-report skeleton in `joint/common core`
- air tactical units routed through the maintained `air/` contracts
- naval tactical units routed through the maintained `naval/` contracts

There is no maintained standalone Marine execution DTO set yet. This document
should not imply otherwise.

## Direct Constraints On Standards Design

### Do not model the USMC as a pasted-together service bundle

The Marine Corps profile should not be reduced to:

- Army ground structure
- plus Navy sea basing
- plus Air Force air support

The standard should preserve the fact that Marine task organization is intended
to integrate these elements under a single service profile.

### Use shared fields to express MAGTF relationships

The following fields are the right shared anchors for Marine standardization:

- `task_group_id`
- `authority_scope`
- `command_relationship`
- `supported_node_id`
- `supporting_node_id`
- `coordination_mode`
- `role_code`

These fields let the service profile define multi-element relationships without
pretending that the current runtime already has a dedicated Marine control
surface.

### Push execution details down to the specialized layers

Examples:

- aviation command semantics must flow through `air/`
- ship, screen, recovery, or sea-based positioning semantics must flow through
  `naval/`
- later ground maneuver semantics should wait for the dedicated ground layer

That keeps the MAGTF profile honest and prevents a second parallel command
surface from emerging inside the service-profile owner.

## Relationship To Current Repository Contracts

In the current repository, the Marine profile mainly serves as a coordination
boundary:

- joint/common fields provide the shared command skeleton
- Air Force and Navy profiles show how service interpretations route into
  separate domain execution layers below that skeleton
- the Marine profile ensures future expeditionary standards can compose those
  layers without collapsing back into an air-first ontology

This is why the Marine Corps profile must stay focused on ownership and
cross-domain interpretation.

## Related Documents

- [Service Profile Overview](../README.md)
- [Air Platform Specialization](../../../air/README.md)
- [Naval Specialization](../../../../standards/naval/README.md)
- [Joint Command and Modeling Baseline](../../standards/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../../standards/command_link_and_reporting_baseline.md)
