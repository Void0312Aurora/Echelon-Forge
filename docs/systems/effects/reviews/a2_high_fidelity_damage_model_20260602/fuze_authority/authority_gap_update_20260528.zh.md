# Fuze Authority Gap Update

状态：`2026-05-28 / authority gap update / non-authoritative`  
关联包：[AIM-120C-class warhead/fuze source ledger](../data_collection/aim120c_warhead_fuze/source_ledger.zh.md)  
写入边界：本文只说明公开来源能支持的 reference / method / sanity 角色，以及 P4 deterministic fuze 仍缺的 gate；不授予任何 runtime authority。

## 当前公开来源只能支持什么

| evidence area | 可支持角色 | 主要公开来源 | 当前结论 |
|---|---|---|---|
| AMRAAM / AIM-120 family public envelope | `reference candidate` | `AIM120-WF-001/002/003/004` | 可帮助约束导弹全弹尺寸、重量量级和 public family context。 |
| warhead family label | `reference candidate` | `AIM120-WF-002` | 可支持 `blast_fragmentation` family-level 描述；不是 C 型破片云。 |
| early-series warhead mass sanity | `sanity_check_only` | `AIM120-WF-007` | 仅作 early AIM-120 exhibit 量级 sanity；不能外推到 AIM-120C。 |
| TDD / target detection / burst-point public terminology | `public terminology reference` | `AIM120-WF-006` plus official AMRAAM pages | 可命名证据字段和 residual；不能形成 trigger model。 |
| blast / fragmentation equations and benchmark design | `method_reference` / `benchmark_design_reference` | `PHYS-BF-*` after version and rights pin | 可指导 surrogate 结构；不提供 AIM-120C warhead/fuze truth。 |
| runtime event fields | `diagnostics / replay input` | current fuze runtime/event coverage docs | 可审计 miss distance、detonation time、signature proxy、contact diagnostics；不是 admission result。 |

## 各 fuze type 的 authority gap

| fuze type | 当前可支持 | 仍缺 authority gate |
|---|---|---|
| `radar_proximity` | official AMRAAM pages support active-radar context; Federal Register notice supports public TDD terminology; runtime records signature proxy fields. | target RCS/aspect evidence or validated surrogate, receiver/threshold evidence, false/missed trigger criteria, delay evidence, scope-matched validation artifact, replay admission result. |
| `laser_proximity` | runtime can record projected-hitbox style diagnostics; generic optical/geometry methods may guide future tests. | calibrated reflectance/projected signature evidence, laser gate threshold, environmental scope, false/missed trigger criteria, delay evidence, validation artifact, replay admission result. |
| `contact` / `impact` | runtime can distinguish hitbox contact diagnostics from old near-miss radius behavior. | authored surface accuracy standard, impact normal/angle/velocity evidence, arming/safe separation/dud logic, material/surface scope, timestep tunneling checks, validation artifact, replay admission result. |
| `timed` | runtime can schedule a delay and record detonation time diagnostics. | setting source, delay accuracy/drift evidence, arming and safe separation evidence, no-target/no-effect policy, validation artifact, replay admission result. |

## Gate 缺口对照

| gate | 当前状态 | blocking residual |
|---|---|---|
| independent schema / manifest | 草案存在。 | 没有 admitted manifest；schema 仍是计划文档。 |
| source gate | 公开来源已能支持术语、family context 和方法候选。 | 没有可授权的 fuze trigger threshold / delay / reliability source。 |
| validation gate | 只有未来 validation manifest 字段草案。 | 没有 scope-matched validation artifact、checksum、metrics、acceptance criteria 和 reviewer record。 |
| evidence gate | checklist 已列出各 fuze type 所需证据。 | radar/laser/contact/timed 的 required evidence 均未闭合。 |
| replay gate | replay/admission matrix 草案存在。 | 没有 executed replay matrix、event hashes、failed-case closeout 或 scope hash。 |
| dependency gate | AIM-120/F-16 数据收集包已列出 public candidates and gaps。 | target geometry、warhead, target signature, backend profile and time-step policy 尚无 admitted dependency bundle。 |
| revocation gate | revocation policy 方向已写在 schema draft。 | 没有已签核 admission，因此无可执行 revocation record。 |

## 与四个数据方向的关系

| direction | 当前最高可用性 | 不能跨越的边界 |
|---|---|---|
| `target_geometry` | F-16 外形盒和粗组件区 `reference/sanity candidate`。 | 不能成为 fuze contact surface 或 radar/laser signature authority。 |
| `material_fuel_fire_dependency` | FAA/NIST/NASA/GAO 等通用 `method/reference`。 | 不能成为 F-16 material/fire cascade authority。 |
| `warhead_model` | AIM-120 family envelope、blast-fragmentation family label、early-series mass sanity、generic blast/fragment methods。 | 不能成为 AIM-120C warhead footprint or fuze trigger authority。 |
| `fuze_authority` | checklist、manifest schema draft、replay matrix draft 和 residual register。 | 不能放行 deterministic fuze；不能移除 non-authoritative fallback。 |

## 当前判定

当前结论保持：`deterministic_fuze_authority = not_admitted / deferred`。

任何 runtime consumer 若需要 deterministic fuze admission，必须等待独立 fuze manifest、scope-matched evidence、validation artifact、executed replay matrix and residual review 全部完成。当前公开 source pins 只能作为后续申请的输入，不是授权结果。
