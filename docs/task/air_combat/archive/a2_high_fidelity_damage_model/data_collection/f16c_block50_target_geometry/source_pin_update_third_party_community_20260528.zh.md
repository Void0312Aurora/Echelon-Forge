# F-16C Block 50 第三方 / 社区 / 开源几何候选 Source Pin Update

状态：`2026-05-28 / third-party-community-source-pin / non-authoritative`  
适用 ledger：[source_ledger.zh.md](source_ledger.zh.md)  
责任范围：F-16 / F-16C / F-16C Block 50 的第三方、社区和开源资料候选，用于目标外形、可见组件布局和低精度 hitbox scaffold 的来源审计。  
写入边界：本文只记录候选、拒绝和 residual；不创建 runtime descriptor，不授予 F-16C Block 50 runtime geometry authority，不写组件失效概率、Pk、effect scale、装甲或材料权威。

## 准入边界复核

本文继续遵守：

- [公开数据来源准入标准](../../../../../standards/foundation/public_data_source_admission.zh.md)
- [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)
- [A2 数据候选到 Evidence Gate 映射](../gate_mapping_20260528.zh.md)

第三方、社区和开源资料不因“非官方”自动拒绝；但必须显式保留 `third_party_candidate`、`community_sanity_check`、`open_source_config_candidate` 或 `non-authoritative_estimate` 标签。本文没有采纳 F-16 technical order、flight manual、maintenance manual、IPB / parts catalog、结构维修手册、未授权镜像、游戏 damage boxes、付费或来源不清 CAD、论坛附件、网盘资料或疑似泄露材料。

## 访问状态摘要

访问核对时间：`2026-05-28 Asia/Shanghai`。

| source group | 本轮访问状态 | 备注 |
|---|---|---|
| FAS F-16 page | `200 text/html` via `curl -L --max-time 20` | 可达；作为第三方公开技术摘要候选。 |
| Air & Space Forces Magazine F-16 profile | `200 text/html` via `curl -L --max-time 20` | 可达；HTML metadata 显示 2025 page/update context。 |
| F-16.net Block 50/52 page | `200 text/html` via `curl -L --max-time 20` | 可达；社区/专题站。 |
| Aerospaceweb F-16 page | `200 text/html` via `curl -L --max-time 20` | 可达；generic F-16/C-D 资料页。 |
| Wikimedia Commons F-16 three-view / photo pages | `local_timeout` in this environment | 既有 ledger 保留 Commons file page；本轮不下载或派生坐标。 |
| JSBSim `aircraft/f16` | `git clone --depth 1` succeeded | pinned commit `3e1a5cfa5c9a1243db8893cd00932f8f68e1a692`; F-16 file header identifies F-16A Block 32. |
| FlightGear `NikolaiVChr/f16` | `git clone --depth 1` succeeded | pinned commit `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5`; README lists F-16CJ Block 50/52 variants. |
| Airframer F-16 supplier guide | `200 text/html` via `curl -L --max-time 20` | Public page, but `noarchive, noai` metadata; use link-only as search lead. |
| GlobalSecurity F-16 page | `local_timeout` | Not admitted this round because content and rights were not reviewed locally. |

## 候选 / 拒绝记录

| `source_id` | source role / `source_ref` | admission / tags | 访问状态 / 权利边界 | 合理性评估 | 交叉验证 | residual / 不能支持的结论 |
|---|---|---|---|---|---|---|
| `F16-TG-3P-001` | `third_party_public_technical_summary`；[FAS F-16 Fighting Falcon](https://man.fas.org/dod-101/sys/ac/f-16.htm) | `Tier B / public-engineering-ish`; `third_party_candidate`, `non-authoritative_estimate` | `200 text/html`；FAS third-party webpage，权利归发布方；ledger 只链接和摘要，不复制正文。 | 资料有可识别发布方，包含 F-16 发展、构型、Block 50/52、发动机/雷达/可见结构等公开叙述；年份较旧，部分描述可能已过时。 | 外形尺寸和重量只能与 USAF/Shaw/NAVAIR ledger 互证；Block 50/52 engine/radar 叙述只能与 Shaw fact sheet、GE F110、GD radome 等互证后作为线索。 | 不能支持真实内部结构、组件边界、油箱分隔、材料分区、线束/管线、装甲、组件概率、damage threshold 或 F-16C Block 50 runtime geometry authority。 |
| `F16-TG-3P-002` | `third_party_platform_profile`；[Air & Space Forces Magazine F-16 profile](https://www.airandspaceforces.com/weapons/f-16/) | `Tier B / identifiable publisher`; `third_party_candidate`, `non-authoritative_estimate` | `200 text/html`；Air & Space Forces Magazine / Air & Space Forces Association 发布；页面版权归发布方，link-only。 | 可作为可追溯平台资料页，适合发现当前公开关键词、照片和平台级 specs 交叉点；不是工程资料。 | 只与 USAF/Shaw/NAVAIR/Lockheed/GE 等 Tier A/B 来源交叉后使用。 | 不能单独支持型号级尺寸真值、组件舱位、Block 50 runtime hitboxes、材料/油箱/火灾系统、Pk 或脆弱性。 |
| `F16-TG-3P-003` | `variant_specific_community_reference`；[F-16.net F-16C/D Block 50/52](https://www.f-16.net/f-16_versions_article9.html) | `Tier C / sanity-check`; `community_sanity_check`, `non-authoritative_estimate` | `200 text/html`；社区/专题站，权利归站点和贡献者；不复制数据库内容。 | 对 Block 50/52、F-16CJ、engine/radar/pod/mission-system 关键词较有用；但为社区整理，版本、来源链和混合批次风险高。 | GE F110、Shaw fact sheet、GD radome、USAF SLEP 和官方资料能互证的字段才可作为候选；与官方不一致时以官方/厂商源为准。 | 不能支持真实 Block 50 内部布局、radar aperture 尺寸、engine install boundary、油箱/线束/管线、组件概率或 runtime geometry authority。 |
| `F16-TG-3P-004` | `third_party_generic_specs_and_visuals`；[Aerospaceweb F-16 page](https://aerospaceweb.org/aircraft/fighter/f16/) | `Tier C / sanity-check`; `third_party_candidate`, `community_sanity_check` | `200 text/html`；第三方航空资料页；link-only。 | 可用于 generic F-16/F-16C-D 尺寸、图片和 schematic 的目视 sanity；不具备 Block 50 provenance。 | 只在 USAF/Shaw/NAVAIR 尺寸锚定后用于检查 nose/cockpit/wing/tail/engine 的外部顺序。 | 不能支持高精度外形、截面、遮挡、内部组件、材料、装甲或组件概率。 |
| `F16-TG-3P-005` | `community_three_view_visual_reference`；[Wikimedia Commons F-16 three-view file page](https://commons.wikimedia.org/wiki/File:General_Dynamics_F-16_Fighting_Falcon_3-view_line_drawing.svg) | `Tier C / sanity-check`; `community_sanity_check`, `non-authoritative_estimate` | `local_timeout` in this environment；Commons 文件页许可需以后续可达状态核对并保留 attribution；本轮不下载、不派生坐标。 | 三视图适合目视检查低精度 scaffold 的主轴、翼面、尾翼、座舱和机鼻顺序；不是工程图。 | 必须先用 USAF/Shaw/NAVAIR 官方尺寸定标；只能做 visual sanity。 | 不能推导内部组件位置、翼梁、油箱、截面、材料、装甲、hit probability 或 runtime geometry authority。 |
| `F16-TG-3P-006` | `open_source_fdm_config_candidate`；[JSBSim `aircraft/f16`](https://github.com/JSBSim-Team/jsbsim/tree/master/aircraft/f16), commit `3e1a5cfa5c9a1243db8893cd00932f8f68e1a692` | `Tier C / open-source-config`; `open_source_config_candidate`, `community_sanity_check`, `non-authoritative_estimate` | `git clone --depth 1` succeeded；repo `COPYING` is LGPL 2.1; `f16.xml` file header declares GPL and an F-16A Block 32 model; preserve upstream license if any derived code/data is ever used. | Valuable as a parseable open FDM/config example with metrics, eye point, pilot pointmass, engine and fuel tank objects; scope is explicitly F-16A Block 32 and includes public-data disclaimer. | Metrics and rough coordinate conventions can be compared against USAF/Shaw dimensions and existing internal scaffold; fuel/engine objects can only inspire schema sanity checks. | Not F-16C Block 50; engine/config choices differ; cannot support real hitbox geometry, internal tank segmentation, component sizes, materials, vulnerability, damage thresholds or runtime authority. |
| `F16-TG-3P-007` | `open_source_visual_sim_aircraft_candidate`；[FlightGear `NikolaiVChr/f16`](https://github.com/NikolaiVChr/f16), commit `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5` | `Tier C / open-source-community-sim`; `open_source_config_candidate`, `community_sanity_check` | `git clone --depth 1` succeeded；repository `LICENSE` is GPL v2; README states FlightGear F-16 variants including F-16CJ Block 50/52 and notes livery/payload caveats. | Useful as a traceable open-source visual/config corpus for obvious external features, variant naming and cockpit/payload sanity; also high risk of simulator assumptions and fictional content. | Only fields independently supported by official/厂商 sources may be echoed as candidate; visual checks should remain qualitative. | Cannot support real F-16C Block 50 internal geometry, mesh-derived hitboxes, component failure logic, material/fuel layout, damage boxes, aircraft vulnerability or runtime geometry authority. |
| `F16-TG-3P-008` | `third_party_supplier_search_lead`；[Airframer F-16 Fighting Falcon supplier guide](https://www.airframer.com/aircraft_detail.html?model=F-16_Fighting_Falcon) | `Tier C / search-lead`; `third_party_candidate`, `non-authoritative_estimate` | `200 text/html`；public page but has `noarchive, noai` metadata; link-only, no scraping or reproduction. | Can suggest supplier/system names for future official-source searches; not a geometry or component-layout source. | Any supplier/system inference must be validated against official/厂商 pages or public reports. | Cannot support geometry, component location, system dependency, material, line routing, ownership-sensitive details, runtime rows or authority. |
| `F16-TG-3P-REJ-001` | `not_acquired_third_party_page`；GlobalSecurity F-16 URL candidate | `rejected_this_round`; `no_authority` | `local_timeout`; content and rights not reviewed. | Potentially useful as third-party summary, but this round has no stable reviewed content. | None. | Not used for any conclusion; can be retried only with stable access, rights and field-level residual review. |
| `F16-TG-3P-REJ-002` | `mirrored_structure_article`；AircraftInformation / mirrored Joe Baugher F-16 structure page; original `joebaugher.com` returned `403` locally | `rejected`; `rights_unclear`, `mirror_not_authoritative` | Mirror page reachable, original source not locally accessible; mirror explicitly appears copied by HTTrack, rights/provenance not acceptable for ingest. | The mirror contains detailed structure/material claims, which makes provenance and rights especially important. | None admitted; do not backfill from the mirror. | Cannot support material percentages, wing spar/rib counts, canopy thickness, structure stations, internal layout, hitboxes or authority. |
| `F16-TG-3P-REJ-003` | `game_or_commercial_sim_damage_boxes`；DCS / War Thunder / CMANO / commercial sim configs and damage boxes | `rejected`; `game_balance_risk`, `rights_unclear`, `no_authority` | Not collected. | Gameplay or commercial sim parameters are not auditable evidence and may be balance-tuned. | None. | Cannot support hitbox scaffold, vulnerability, component probability, materials, Pk or runtime data. |
| `F16-TG-3P-REJ-004` | `unlicensed_or_paid_cad_mesh`；GrabCAD / Sketchfab / forum attachments / paid meshes /网盘模型 without clear license and provenance | `rejected`; `rights_unclear`, `provenance_gap`, `no_authority` | Not collected; no model stored. | Even visually plausible meshes may be artistic, game-derived, copyrighted or based on restricted material. | None. | Cannot support high-fidelity shape, mesh-derived coordinates, components, material or runtime geometry. |

## 用途判定

| 用途 | 当前最高可用来源 | 判定 |
|---|---|---|
| 低精度外形 hitbox scaffold | `F16-TG-3P-001/002/004/005` plus existing official ledger `F16-TG-SRC-001/002/003` | `candidate only`。可检查 length/span/height 量级和 nose/cockpit/wing/tail/aft-engine 顺序。 |
| 组件布局 sanity | `F16-TG-3P-003/006/007` plus GE/GD/Shaw official or厂商 sources | `weak sanity only`。可生成 engine/radar/cockpit/wing/tail 候选区域假设，不得声称内部边界。 |
| 可追溯开源 config / model | `F16-TG-3P-006/007` | `open_source_config_candidate`。可用于 parser/schema toy cases、坐标系 sanity 和视觉对照；不能导入为真实 F-16C geometry。 |
| 第三方技术页和资料站 | `F16-TG-3P-001/002/003/004/008` | `search lead / sanity`。适合发现关键词和交叉验证线索。 |
| F-16C Block 50 runtime geometry authority | none | `unsupported`。所有第三方/社区/开源来源均保持 `non-authoritative`。 |

## 当前仍缺口

- 无公开可再分发的 F-16C Block 50 工程三维几何、真实内部结构或组件边界。
- 无可采纳的 Block 50 油箱分隔、线束/管线、航电舱、液压/飞控作动器布局。
- 无材料分区、装甲、防护层、radome 厚度或座舱透明件权威数据。
- 无组件失效概率、threshold scale、Pk、damage boxes 或 effect-scale 校准数据。
- 无 artifact checksum / validation manifest / row-level runtime authorization。

结论：本文件只扩展第三方、社区和开源候选池。可用于低精度 scaffold 和 sanity-check 假设生成；不能支持真实内部结构、装甲、油箱分隔、线束/管线、组件概率或 F-16C Block 50 runtime geometry authority。
