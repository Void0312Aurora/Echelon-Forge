# F-16C Block 50 第三方 / 社区 / 开源材料-燃油-火灾-系统候选 Source Pin Update

状态：`2026-05-28 / third-party-community-source-pin / non-authoritative`  
适用 ledger：[source_ledger.zh.md](source_ledger.zh.md)  
责任范围：F-16 / F-16C / F-16C Block 50 的第三方、社区和开源资料候选，用于材料、燃油、火灾和系统依赖假设的来源审计。  
写入边界：本文只记录候选、拒绝和 residual；不创建 runtime descriptor，不授予 material/fuel/fire/system dependency authority，不写真实材料厚度、油箱分隔、管线/线束拓扑、防火/灭火布局、组件失效概率或 Pk。

## 准入边界复核

本文继续遵守：

- [公开数据来源准入标准](../../../../../standards/foundation/public_data_source_admission.zh.md)
- [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)
- [A2 数据候选到 Evidence Gate 映射](../gate_mapping_20260528.zh.md)

本目录已有 FAA/NIST/NASA/GAO/FOI 等公开方法源；第三方、社区和开源资料只能补充 search lead、sanity check、open-source parser/config 示例和非权威假设。本文没有采纳 F-16 technical order、flight manual、maintenance manual、structural repair manual、IPB / parts catalog、航电/武器接口手册、未授权镜像、游戏 damage boxes、付费 CAD、论坛附件、网盘资料或疑似泄露材料。

## 候选 / 拒绝记录

| `source_id` | source role / `source_ref` | admission / tags | 访问状态 / 权利边界 | 合理性评估 | 交叉验证 | residual / 不能支持的结论 |
|---|---|---|---|---|---|---|
| `F16-MFFS-3P-001` | `third_party_material_system_narrative`；[FAS F-16 Fighting Falcon](https://man.fas.org/dod-101/sys/ac/f-16.htm) | `Tier B / public-engineering-ish`; `third_party_candidate`, `non-authoritative_estimate` | `200 text/html` via `curl -L --max-time 20`；FAS third-party webpage，权利归发布方；只链接和摘要。 | 可作为 F-16 blended-body fuel volume、FBW/control-surface、canopy/visibility、engine/intake 等公开叙述线索；年份较旧且非官方。 | 只与 USAF/Shaw/GE/GD、FAA/NASA/NIST 和既有几何 ledger 交叉后形成弱假设。 | 不能支持真实材料比例、材料厚度、油箱分隔、line routing、fire suppression layout、component fragility、Pk 或 runtime authority。 |
| `F16-MFFS-3P-002` | `variant_specific_community_system_reference`；[F-16.net F-16C/D Block 50/52](https://www.f-16.net/f-16_versions_article9.html) | `Tier C / sanity-check`; `community_sanity_check`, `non-authoritative_estimate` | `200 text/html`；社区/专题站，权利归站点和贡献者；不复制数据库内容。 | 对 Block 50/52、F-16CJ、engine/radar、OBOGS、mission equipment 关键词有检索价值；但为社区整理，版本链和批次差异风险高。 | Engine/radar/Block 50/52 语境需与 Shaw fact sheet、GE F110、GD radome 和官方公开资料交叉；OBOGS/mission equipment 只能作为后续官方检索线索。 | 不能支持真实 oxygen/fuel/hydraulic/electrical routing、系统冗余、火灾探测/灭火布置、材料、油箱、概率或 Pk。 |
| `F16-MFFS-3P-003` | `open_source_fdm_fuel_config_candidate`；[JSBSim `aircraft/f16`](https://github.com/JSBSim-Team/jsbsim/tree/master/aircraft/f16), commit `3e1a5cfa5c9a1243db8893cd00932f8f68e1a692` | `Tier C / open-source-config`; `open_source_config_candidate`, `community_sanity_check`, `non-authoritative_estimate` | `git clone --depth 1` succeeded；repo `COPYING` is LGPL 2.1; `f16.xml` file header declares GPL and F-16A Block 32. | Parseable fuel/engine/pointmass/control example: `f16.xml` includes engine and fuel tank objects, pilot pointmass, metrics and coordinate conventions. Its own header warns it is public-data based and not manufacturer-related. | Can be compared with official dimensions and total fuel量级 only for schema/parser sanity; fuel objects are simulation states, not real tank compartments. | Not F-16C Block 50; cannot support real tank segmentation, fuel quantity distribution, dry bay, line routing, fire growth, material, component fragility or runtime data. |
| `F16-MFFS-3P-004` | `open_source_visual_sim_system_candidate`；[FlightGear `NikolaiVChr/f16`](https://github.com/NikolaiVChr/f16), commit `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5` | `Tier C / open-source-community-sim`; `open_source_config_candidate`, `community_sanity_check` | `git clone --depth 1` succeeded；repository `LICENSE` is GPL v2; README lists variants including F-16CJ Block 50/52 and warns livery/payload quality can vary. | Useful for visible cockpit/external stores/control naming and variant-search sanity; as a simulator aircraft it may include simplifications, fictional liveries and gameplay/visual assumptions. | Any system name must be revalidated against official/厂商 or Tier A/B method sources before use. | Cannot support real fuel/fire/material/system topology, component dependence, damage model, internal geometry, failure probabilities or Pk. |
| `F16-MFFS-3P-005` | `third_party_supplier_search_lead`；[Airframer F-16 Fighting Falcon supplier guide](https://www.airframer.com/aircraft_detail.html?model=F-16_Fighting_Falcon) | `Tier C / search-lead`; `third_party_candidate`, `non-authoritative_estimate` | `200 text/html`；public page has `noarchive, noai` metadata; link-only, no scraping/republication. | Can help identify candidate suppliers or subsystem names for future public-source searches; not a technical dependency model. | All supplier/system claims must be cross-checked against official press releases,厂商 pages, GAO/USAF public docs or open reports. | Cannot support component layout, material, line routing, dependency graph truth, failure probability, export-controlled interfaces or runtime authority. |
| `F16-MFFS-3P-006` | `third_party_platform_profile`；[Air & Space Forces Magazine F-16 profile](https://www.airandspaceforces.com/weapons/f-16/) | `Tier B / identifiable publisher`; `third_party_candidate`, `non-authoritative_estimate` | `200 text/html`；Air & Space Forces Magazine / Air & Space Forces Association 发布；link-only。 | Useful current platform context and photo/profile source; not an engineering material/fuel/fire source. | Can cross-check platform naming and public context with USAF/Shaw/NAVAIR; cannot override official source ledgers. | Cannot support fuel/fire mechanisms, materials, oil/hydraulic/electrical topology, Block 50 system truth, probabilities or authority. |
| `F16-MFFS-3P-007` | `third_party_generic_specs_and_visuals`；[Aerospaceweb F-16 page](https://aerospaceweb.org/aircraft/fighter/f16/) | `Tier C / sanity-check`; `third_party_candidate`, `community_sanity_check` | `200 text/html`；third-party aviation page; link-only. | Can be used as generic F-16 specs/visual sanity and keyword discovery; scope is not Block 50 material/fuel/fire. | Only use after USAF/Shaw/NAVAIR and FAA/NIST/NASA/GAO method sources establish the relevant axis. | Cannot support material map, tank layout, fire zones, line routing, dependency probabilities or Pk. |
| `F16-MFFS-3P-REJ-001` | `mirrored_structure_material_article`；AircraftInformation / mirrored Joe Baugher F-16 structure page; original `joebaugher.com` returned `403` locally | `rejected`; `rights_unclear`, `mirror_not_authoritative`, `no_authority` | Mirror reachable, original not locally accessible; mirror appears copied by HTTrack. | Contains detailed structure/material claims, which would require strong provenance and rights. This source does not meet that bar. | None admitted; do not use mirror values for cross-check. | Cannot support material percentages, canopy thickness, wing spars/ribs, fuel fraction, structural layout, material thickness, thresholds or authority. |
| `F16-MFFS-3P-REJ-002` | `not_acquired_third_party_page`；GlobalSecurity F-16 URL candidate | `rejected_this_round`; `no_authority` | `local_timeout`; content/rights not reviewed locally. | Potential third-party summary, but no stable reviewed content in this round. | None. | Not used for any conclusion; can be retried only with stable access, rights and residual review. |
| `F16-MFFS-3P-REJ-003` | `game_or_commercial_sim_damage_and_system_configs`；DCS / War Thunder / CMANO / commercial sim configs / damage boxes | `rejected`; `game_balance_risk`, `rights_unclear`, `no_authority` | Not collected. | Sim/game system and damage parameters may be balance-tuned, proprietary or unverifiable. | None. | Cannot support tank segmentation, fire propagation, component dependencies, hitboxes, vulnerability, probability, Pk or runtime data. |
| `F16-MFFS-3P-REJ-004` | `unlicensed_or_paid_cad_mesh`；GrabCAD / Sketchfab / forum attachments / paid meshes /网盘模型 without clear license and provenance | `rejected`; `rights_unclear`, `provenance_gap`, `no_authority` | Not collected; no model stored. | Visually plausible meshes do not establish material, fuel or systems provenance and may be derived from restricted or copyrighted inputs. | None. | Cannot support internal material/fuel/fire/system layout, geometry-derived component dependencies or authority. |
| `F16-MFFS-3P-REJ-005` | `restricted_manual_or_parts_source`；F-16 TO / maintenance / SRM / IPB / parts catalog / wiring / fuel / hydraulic / avionics manual mirrors | `rejected`; `restricted_or_rights_unclear`, `no_authority` | Not collected. | Even if web-accessible, these categories are high-risk for restricted/proprietary/export-controlled data. | None. | Cannot be summarized into parameters, component maps, routing, tank layout, material properties, fire system logic or runtime rows. |

## 假设生成边界

| 用途 | 可用候选 | 当前判定 |
|---|---|---|
| 材料/结构假设关键词 | `F16-MFFS-3P-001` only as third-party narrative, plus official GAO/USAF SLEP sources already in ledger | `search lead / weak sanity`。不得写真实材料比例、厚度或结构阈值。 |
| 燃油/engine state schema sanity | `F16-MFFS-3P-003` JSBSim open config | `open_source_config_candidate`。可用于 parser/toy schema and coordinate sanity；不能作为真实油箱分隔。 |
| Block 50/52 system keyword discovery | `F16-MFFS-3P-002/004/005` | `community/search lead`。适合生成 OBOGS、mission equipment、engine/radar 等后续官方检索词；不能给 topology。 |
| 外部可见组件/照片 sanity | `F16-MFFS-3P-004/006/007` | `visual sanity only`。只判断明显外部构型，不判断内部依赖。 |
| fire/fuel/material method authority | FAA/NIST/NASA/FOI sources in main ledger, not this third-party set | 第三方资料不提升 method authority；仍不得转成 F-16 runtime row。 |
| F-16C Block 50 material/fuel/fire/runtime authority | none | `unsupported`。 |

## 当前仍缺口

- 无 F-16C Block 50 真实材料分区、蒙皮/框梁/翼梁材料和厚度。
- 无油箱分隔、容量分配、壁材、自封、防火、惰化或 fuel routing 公开权威数据。
- 无燃油/液压/润滑管线、阀门、电气线束、电源总线、飞控线束或冗余拓扑。
- 无 engine bay / dry bay fire detection and suppression layout、探测器/瓶/喷嘴参数或灭火概率。
- 无 component fragility、fire growth、system cascade、mission kill、Pk 或校准数据集。
- 无 validated surrogate manifest、artifact checksum、scope-matched validation 或逐字段 runtime 授权。

结论：本文第三方、社区和开源候选只能用于关键词发现、低风险 sanity check 和非权威假设生成。它们不能支持真实内部结构、装甲、油箱分隔、线束/管线、组件概率、F-16C Block 50 material/fuel/fire authority 或 runtime geometry authority。
