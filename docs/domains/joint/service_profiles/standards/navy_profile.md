# US Navy Profile

Language:
- English canonical: `navy_profile.md`
- Chinese companion: [navy_profile.zh.md](navy_profile.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/joint/service_profiles/standards/navy_profile.md`
Owner: `domains/joint/service-profiles`
Last verified: `2026-08-08`

Status: `2026-08-08` authoritative for Navy service-profile placement.

This document defines the Navy service profile used when the project models naval warfare and maritime operations.

It is no longer a placeholder. Its job is to describe how the Navy interprets
the shared Joint common-core contract and where it hands off to the dedicated
naval specialization. It does not own naval execution semantics.

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

### 2.1 Joint common core

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

### 2.2 Navy service-profile interpretation

The Navy service profile explains the Navy-specific reading of the shared
skeleton:

- `task_group` / `task_unit` hierarchy
- `officer_in_tactical_command`
- `warfare_role_code`
- which common anchors the Navy actually relies on in runtime planning and task packaging

This layer should define ownership and meaning, not execution mechanics.

### 2.3 Naval domain specialization

`naval` is the dedicated specialization for tight-loop maritime runtime semantics:

- `screen / support / station / recover`
- ship and formation tasking behavior
- station keeping, recovery, and maritime role geometry
- naval execution and reporting specialization

This layer should not re-declare shared contract fields unless it is clarifying their naval interpretation.

## 3. Minimal Interpretation Set

The Navy profile owns these service-level interpretations:

- `task_group`
- `task_unit`
- `warfare_role_code`
- `officer_in_tactical_command`

The naval owner, not this profile, owns the execution meaning of:

- `screen`
- `support`
- `station`
- `recover`

Together these are the smallest useful service and domain terms for the current
naval task plan and runtime bridge; their ownership remains split across the two
layers.

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
3. Require the naval owner to define `screen / support / station / recover` as
   the minimal naval control vocabulary.
4. Only then extend deeper ship-specific or formation-specific behavior.

This avoids forcing air-first assumptions into the naval runtime.

## 5. Ownership and Bridge Responsibilities

The Navy service profile is responsible for stating:

- which common fields the Navy profile depends on
- which semantic layer interprets them
- which naval roles and task levels own tactical control

It is not responsible for defining platform-specific command execution, sensor behavior, or weapon logic.

The dedicated naval owner owns those runtime semantics once the common skeleton
is in place.

## Related Documents

- [Service Profile Overview](../README.md)
- [Naval Standards Overview](../../../../standards/naval/README.md)
- [Joint Command and Modeling Baseline](../../standards/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../../standards/command_link_and_reporting_baseline.md)
- [Scenario Configuration Guide](../../../../standards/bridge/scenario_guide.md)
