<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/navy.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/navy.md. Review before treating this file as authoritative. -->

# US Navy Profile

This document defines the US Navy profile used when the project models naval warfare / maritime operations.

## 1. Official Real-world Basis

Public Navy materials indicate that naval tactical organization is more “mission-tailored” than the Army, and that `Task Force` and `Composite Warfare Commander (CWC)` systems are widely employed for tactical control.

Current publicly available official sources:

- [U.S. 7th Fleet, CTF 71 establishment](https://www.c7f.navy.mil/Media/News/Display/Article/2641477/ctf-71-establishment-enhances-readiness-in-7th-fleet/)
- [TTGP Warfare Commanders Conference I](https://www.ttgp.navy.mil/OFRP-Syllabus/Warfare-Commanders-Conference-I/)
- [NAVIFOR, IW Has a Seat at the Table](https://www.navifor.usff.navy.mil/Press-Room/News-Stories/Article/2395110/iw-has-a-seat-at-the-table/)
- [COMPHIBRON 5 About](https://www.surfpac.navy.mil/Ships/Amphibious-Squadron-COMPHIBRON-5/About/)

These official pages confirm the following:

- `Task Force` is an actual mission-organized unit.
- Capabilities such as sea combat / amphibious / information warfare are organized around the `CWC table` and warfare commanders.
- `Officer in Tactical Command` and `Composite Warfare Commander` are real-world roles in fleet / formation scenarios.

## 2. Modeling Conclusions

### 2.1 Layers That Should Not Enter the Tight-Loop Runtime

- numbered fleet
- major theater maritime component

These are better suited as:

- operation-level command nodes
- scenario tasking and force packaging nodes

### 2.2 Layers That Are More Suitable for the Tight-Loop Runtime

The naval tight-loop runtime is more appropriately placed at:

- tactical groupings at the `task group / task unit` level
- role coordination at the `warfare commander` level
- `single ship / ship section`

Explanation:

- The key in the Navy profile is not to separate into “elements” like the Air Force, but rather `task organization + warfare commander role`.

## 3. Impact on Project Common Templates

If the project later expands into naval warfare, the joint/core layer must be able to express:

- `task_group_id`
- `warfare_role_code`
- `supported/supporting relation`
- `officer_in_tactical_command`

and must not presuppose core coordination objects such as:

- `lead / wingman`

Those are only suitable for air sortie-level formations, not for fleet / formation control.

## 4. Direct Constraints for Upcoming Naval Module

If the current `tasking / command` is further split into `common + air + naval`, the Navy profile should be positioned as follows:

### 4.1 Objects That Should Remain in `common`

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `command_relationship`
- `authority_scope`
- `coordination_mode`
- `task_group_id`
- `supported_node_id / supporting_node_id`
- `recovery_site_id`

These fields remain valid in the Navy, but their meaning should be interpreted by the Navy profile, not changed to air terminology.

### 4.2 Objects That Should Go into `naval`

- `warfare_role_code`
- `officer_in_tactical_command`
- interpretation of naval `task force / task group / task unit` organizational hierarchy
- fleet semantics of formation / station / screen / support
- dedicated tasking semantics for ship sections, surface action groups, amphibious groups, etc.

### 4.3 Objects That Should Not Be Directly Copied from Air into Naval Core

- `lead / wingman`
- `element lead`
- `runway`
- `approach type`
- `takeoff clearance`
- air sortie phase–driven `LeaderPhase`

If the Navy also needs “who follows whom, who holds which station”, those should be modeled as naval role / station / warfare commander semantics, rather than generalizing air two-aircraft formation terms into a common template.

## 5. Recommendations for Documentation and Code Collaboration

For upcoming module work, the Navy side recommends proceeding in the following order:

1. First, fix joint fields and DTO skeletons in `common`.
2. Then, have the Navy profile clarify which organizational levels and role calibers these fields correspond to in the naval runtime.
3. Finally, add tight-loop station / screen / support / recovery semantics in the dedicated `naval` documentation.

This avoids prematurely writing air-first formation and recovery assumptions into the `common` layer.

## 6. Ownership Implications for Runtime/Standards Bridge

This profile requires the bridge document to:

- `services/navy.md` is responsible for explaining which common attachment points the Navy profile wants the core to retain.
- It is not responsible for defining specific execution command fields for naval platforms.
- It should not directly treat existing air `route / landing / wingman` semantics as the default template for the Navy.

For documentation placement regarding future module boundaries, it can be preliminarily understood as follows:

- `joint/common core`:
  - `task_group_id`
  - `supported/supporting relation`
  - `recovery_site_id`
  - `coordination_mode`
- `services/navy`:
  - `officer_in_tactical_command`
  - `warfare_role_code`
  - tactical ownership at `task group / task unit` level
- Future `naval/` dedicated layer:
  - ship / formation mission semantics
  - shipboard recovery, replenishment, station-keeping, maritime formation geometry
  - naval execution command / reporting specialization

Therefore, the primary work for the runtime/standards bridge in the Navy direction should be to leave the core skeleton in the joint layer, hang the naval organization and control calibers in the profile layer, and not continue expanding air-specific command vocabulary into a “universal core”.
