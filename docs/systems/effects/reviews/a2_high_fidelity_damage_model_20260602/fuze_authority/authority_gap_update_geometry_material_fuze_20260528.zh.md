# Fuze Authority Geometry-Material-Fuze Gap Update

状态：`2026-05-28 / authority gap update / not_admitted / non-authoritative`  
责任范围：把本轮 F-16C target geometry、material/fuel/fire、AIM-120C warhead/fuze 和材料/冲击/破片标准可达性复核映射到 fuze authority gap。  
准入边界：本文不授予 `deterministic_fuze_authority`，不修改 runtime，不允许公开 fact sheet、材料标准或 blast/fragment 方法直接成为 Pk、引信确定性、组件失效概率或 AAM/F-16 校准权威。

## 本轮证据到 fuze gate 的映射

| direction | 本轮可确认 | 最高用途 | 对 fuze authority 的影响 |
|---|---|---|---|
| `target_geometry` | F-16 official source URLs pinned; GE F110 PDFs reachable and hashed; `.mil` geometry pages not locally reachable. | `reference/sanity candidate` | 仍不能成为 contact surface、radar/laser signature、component geometry 或 target vulnerability authority。 |
| `material_fuel_fire_dependency` | FAA fuel/fire AC PDFs, NIST/NASA pages, NIJ/OJP material standards reachable; several hashes recorded. | `method_reference` / `validation_criteria_reference` | 可帮助设计 future dependency checks, but cannot prove F-16 fire cascade, material response or component kill. |
| `warhead_model` | govinfo AIM-120C-7 notice reachable and hashed; RTX reachable; official `.mil` AMRAAM pages not locally reachable. | `public terminology/reference candidate` | TDD / target detection / burst-point terms can name fields, but no trigger model or C-specific warhead/fuze parameters. |
| `blast_fragment_material_methods` | WBDG UFC and UN IATG PDFs reachable and hashed; DLA MIL-STD-662 and DDESB pages unresolved locally; NIJ/OJP standards reachable. | `method_reference` / `benchmark_design_reference` | Methods still need surrogate manifest, scope match, validation artifact and residual closeout before any runtime use. |

## URL / artifact status relevant to P4

| gate dependency | candidate refs | artifact/hash state | usable for admission? | why not |
|---|---|---|---|---|
| target geometry model | USAF/Shaw/NAVAIR F-16 pages; GE F110 PDFs | `.mil` pages `local_dns_failed`; GE hashes recorded. | no | Fact sheets and engine datasheets do not define hitbox surface accuracy, target local coordinates, material layers or signature model. |
| target material/fire dependency | FAA ACs, NIST SP 984 page, NASA NTRS damaged-aircraft page, NIJ standards | FAA/OJP hashes recorded; NIST/NASA HTML reachable. | no | Generic civil/generic methods only; no F-16 Block 50 topology, thresholds, fire growth or component failure probabilities. |
| AIM-120 public fuze terminology | govinfo FR `2011-27552`; official AMRAAM fact sheets | govinfo hash recorded; `.mil` pages local DNS failed. | no | Public terms identify sensitive subsystem classes but provide no threshold, delay, reliability, signal-processing or safe-arm evidence. |
| blast/fragment method refs | WBDG UFC, UN IATG, DDESB pending, MIL-STD-662 pending, NIJ standards | WBDG/UN/NIJ hashes recorded; DLA/DDESB unresolved. | no | Methods are not C-specific warhead/fuze truth and require validated surrogate admission. |

## Fuze type gap remains open

| fuze type | what public sources can help with | still-blocking gate |
|---|---|---|
| `radar_proximity` | AMRAAM active-radar/TDD terminology; future target-signature schema naming. | No target RCS/aspect calibration, receiver/threshold evidence, false/missed trigger criteria, delay/reliability evidence or replay admission. |
| `laser_proximity` | Generic geometry/material standards may help future test design. | No calibrated reflectance/projected-area evidence, laser threshold, environment scope, false/missed trigger criteria or replay admission. |
| `contact` / `impact` | NIJ/MIL-STD-662-style methods may inform ballistic test vocabulary only after official pin. | No F-16 contact surface accuracy, material stack, impact normal/angle/velocity evidence, arming/dud logic, timestep tunneling validation or replay admission. |
| `timed` | None of the new sources close timed-setting evidence. | No setting source, drift/accuracy, arming/safe separation, no-target policy or replay admission. |

## Required future artifacts before any admission

| artifact | required status | current status |
|---|---|---|
| `a2.fuze_authority.v1` manifest | admitted, scope-narrowed, dependency refs fixed | missing / draft only |
| target geometry dependency bundle | versioned, hashable, surface accuracy and signature scope declared | missing; current sources are fact-sheet candidates |
| warhead/fuze evidence bundle | trigger thresholds, delay, reliability, false/missed criteria with source_ref/provenance | missing; current sources only public terms and family context |
| validated physics surrogate | model/config/version, method refs, benchmark refs, artifact sha256, validation metrics and residual closeout | missing; current method refs are candidate-only |
| replay/admission matrix result | executed, event hashes, failed-case closeout, scope hash | missing |
| revocation policy record | tied to code/data/backend/time-step dependencies | draft only |

## 当前判定

`deterministic_fuze_authority = not_admitted / deferred`。本轮 source pins improve auditability, not authority. Runtime consumers must continue to fail closed for deterministic fuze, Pk, component failure probability, effect scale, and any AIM-120C/F-16 calibrated damage behavior.
