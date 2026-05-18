<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/document_alignment_map.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/document_alignment_map.md. Review before treating this file as authoritative. -->

# Document Alignment Map

This document clarifies which documents are currently the primary reference, which are specialized supplements, and which have been archived.

## 1. Currently Active Primary References

### 1.1 Joint/Common Core

Current joint-layer primary references:

- [Joint Standards Overview](joint/README.md)
- [Joint Command Relationship and Modeling Baseline](joint/command_and_modeling_baseline.md)

They are responsible for defining:

- Joint-layer command relationships
- Authority delegation
- Generic templates for task organization
- Common skeleton for commander intent / order / report

### 1.2 Service Profiles

Current service profile primary references:

- [USAF Profile](services/air_force.md)
- [US Army Profile](services/army.md)
- [US Navy Profile](services/navy.md)
- [US Marine Corps Profile](services/marine_corps.md)

They are responsible for defining:

- Which levels are suitable for entering the tight-loop runtime
- Which levels should only be retained at the operation / scenario / campaign layer
- How the joint/common core is concretely implemented in each service

## 2. Currently Still Valid but Specialized Supplement Documents

### 2.1 Air Platform/Mission Specialization

The following documents are still valid but no longer serve as project-wide common standards:

- [Air Standards Overview](air/README.md)
- [obs.md](air/obs.md)
- [act.md](air/act.md)
- [aim.md](air/aim.md)
- [rep.md](air/rep.md)

They are only responsible for:

- Observation, action, command, and report semantics for air platforms

They are not responsible for:

- Defining the joint/common core
- Unifying naval or ground warfare chains of command

## 3. Archived Documents

The following documents are retained solely for historical reference:

- `docs/Archive/air_first_standards/com/*.md`
- `docs/Archive/air_first_standards/com/two_ship/*.md`
- `docs/Archive/architecture/*.md`
- `docs/Archive/architecture/layers/*.md`

These documents are archived not because they are entirely wrong, but because they were built on the path of "air-first then attempt generalization" and are no longer suitable as the current primary baseline.

## 4. Direct Alignment Implications for Project Code

From the document standards perspective, subsequent code-level work should align in the following directions:

### 4.1 Concepts That Should Be Lifted to Common Core as Much as Possible

- `command relationship`
- `authority scope`
- `task_family`
- `service_profile`
- `tactical_unit_type`
- `role_code`
- `coordination_mode`
- `recovery_site_id`

The ownership of these concepts in the standards tree should be fixed as:

- The `joint/common core` is responsible for defining field names, hierarchical relationships, and minimal semantic boundaries.
- The runtime/standards bridge is only responsible for aligning existing code objects to this common skeleton.
- The bridge should not reverse-promote a service-specific currently convenient terminology into a project-wide core naming.

In other words, the bridge layer may temporarily accommodate air-first historical fields, but its ownership should stand on the `common/core` side, not on the air task side.

### 4.2 Concepts That Should Be Sunk to Air Specialization as Much as Possible

- `CAP`
- `runway`
- `approach_type`
- `wingman`
- `element`
- `flight`

Explanation:

- The air-specific terms above remain useful in air combat implementations.
- However, they should no longer dominate the core layer naming and generic templates.

### 4.3 Document Ownership for the Runtime/Standards Bridge

If a document aims to answer "which layer should own the fields/objects in the current runtime", it should follow these rules:

1. First, determine whether it is describing the `joint/common core` skeleton or the concrete implementation of a specific profile.
2. If it describes the common shell of `Task Order / Tactical Intent / Execution Command / Report`, the document should belong to `joint/` or this alignment map.
3. If it describes `CAP`, `runway recovery`, `wingman`, `ILS approach`, the document should belong to `air/`.
4. If it describes future naval warfare `task group / task unit / warfare commander / officer in tactical command`, the document should first belong to `services/navy.md`, and later be handled by `naval/` specialized documents for platform/task refinement.

The purpose of this rule is not to limit implementation, but to prevent runtime bridge documents from continuing to mistakenly write "fields already existing in the current air code" as "project-wide common core".

### 4.4 Landing Points for Future Naval Profile

From the standard ownership perspective, the future naval profile landing points should be:

- `joint/common core`
  - `task_group_id`
  - `supported_node_id`
  - `supporting_node_id`
  - `coordination_mode`
  - `recovery_site_id`
- `services/navy`
  - `officer_in_tactical_command`
  - `warfare_role_code`
  - `task group / task unit` level control scope
- Future `naval/` specialized documents
  - Ship/formation geometry
  - Recovery/replenishment/deck operations
  - Naval platform-specific execution command semantics

Therefore, during the WP0 documentation phase, ownership landing points should be clarified first, rather than pre-writing execution parameter details for domains outside air in the common/core documents.

## 5. Recommended Maintenance Approach

When adding new documents subsequently, first determine their layer:

1. If cross-service common relationships, place in `joint/`
2. If service organization and control methods, place in `services/`
3. If platform or mission-specific semantics, place in `air/` or future `naval/`, `land/`
4. If historical design and deprecated path, explicitly mark `ARCHIVED`
