# US Navy Profile

This document defines the Navy service profile used when the project models naval warfare and maritime operations.

It is no longer a placeholder. Its job is to describe how the Navy maps onto the shared `common` contract and how the dedicated `naval` specialization should read that contract.

## 1. Real-World Basis

Public Navy materials show that naval tactical organization is mission-tailored and commonly expressed through `Task Force`, `Task Group`, `Task Unit`, and `Composite Warfare Commander (CWC)` constructs.

Current public references:

- [U.S. 7th Fleet, CTF 71 establishment](https://www.c7f.navy.mil/Media/News/Display/Article/2641477/ctf-71-establishment-enhances-readiness-in-7th-fleet/)
- [TTGP Warfare Commanders Conference I](https://www.ttgp.navy.mil/OFRP-Syllabus/Warfare-Commanders-Conference-I/)
- [NAVIFOR, IW Has a Seat at the Table](https://www.navifor.usff.navy.mil/Press-Room/News-Stories/Article/2395110/iw-has-a-seat-at-the-table/)
- [COMPHIBRON 5 About](https://www.surfpac.navy.mil/Ships/Amphibious-Squadron-COMPHIBRON-5/About/)

These sources support three conclusions:

- `Task Force / Task Group / Task Unit` are real mission-organized naval levels.
- Naval control is centered on warfare commander roles rather than air-style `lead / wingman` pairs.
- `Officer in Tactical Command` is a real command-authority concept in fleet and formation contexts.

## 2. Layer Boundaries

### 2.1 `common`

`common` should keep the cross-service skeleton that all services can share:

- `service_profile`
- `task_family`
- `task_group_id`
- `command_relationship`
- `authority_scope`
- `coordination_mode`
- `supported_node_id / supporting_node_id`
- `recovery_site_id`
- `tactical_unit_type`

For Navy, these fields keep their shared shape, but their meaning is interpreted through naval organization rather than air sortie terminology.

### 2.2 `services/navy`

`services/navy` explains the Navy-specific reading of the shared skeleton:

- `task_group` / `task_unit` hierarchy
- `officer_in_tactical_command`
- `warfare_role_code`
- which common anchors the Navy actually relies on in runtime planning and task packaging

This layer should define ownership and meaning, not execution mechanics.

### 2.3 `naval`

`naval` is the dedicated specialization for tight-loop maritime runtime semantics:

- `screen / support / station / recover`
- ship and formation tasking behavior
- station keeping, recovery, and maritime role geometry
- naval execution and reporting specialization

This layer should not re-declare shared contract fields unless it is clarifying their naval interpretation.

## 3. Minimal Semantic Set

The Navy profile should absorb the following minimal semantics as first-class terms:

- `task_group`
- `task_unit`
- `warfare_role_code`
- `officer_in_tactical_command`
- `screen`
- `support`
- `station`
- `recover`

These are the smallest useful terms for the current naval task plan and runtime bridge.

### 3.1 Meaning of the minimal terms

- `task_group`: the primary naval mission grouping.
- `task_unit`: the subordinate tactical unit inside the group.
- `warfare_role_code`: the active warfare role assigned to the unit or commander.
- `officer_in_tactical_command`: the authority node that owns tactical control.
- `screen`: protective positioning around a higher-value force.
- `support`: escort, sustainment, or enabling relation.
- `station`: a relative position that must be held or restored.
- `recover`: return-to-control or recovery semantics, including ship/aircraft recovery context where applicable.

## 4. Planning Implications

For current task planning, the Navy profile should guide the order of implementation as follows:

1. Keep the common contract stable.
2. Bind Navy task planning to `task_group / task_unit` and `officer_in_tactical_command`.
3. Add `screen / support / station / recover` as the minimal naval control vocabulary.
4. Only then extend deeper ship-specific or formation-specific behavior.

This avoids forcing air-first assumptions into the naval runtime.

## 5. Ownership and Bridge Responsibilities

`services/navy` is responsible for stating:

- which common fields the Navy profile depends on
- which semantic layer interprets them
- which naval roles and task levels own tactical control

It is not responsible for defining platform-specific command execution, sensor behavior, or weapon logic.

The dedicated `naval` layer should own those runtime semantics once the common skeleton is in place.
