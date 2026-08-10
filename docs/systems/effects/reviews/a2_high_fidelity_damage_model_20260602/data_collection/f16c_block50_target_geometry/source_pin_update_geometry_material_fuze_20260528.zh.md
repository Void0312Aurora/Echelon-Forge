# F-16C Block 50 Geometry / Material / Fuze-linked Source Pin Update

状态：`2026-05-28 / source reachability update / candidate-only / non-authoritative`  
责任范围：F-16C Block 50 外形、尺寸、质量、总燃油量和与材料/引信链相邻的公开来源可达性复核。  
准入边界：遵守 [公开数据来源准入标准](../../../../../../research/standards/public_data_source_admission.zh.md) 和 [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)。本文不授予 runtime authority，不创建 row，不校准 Pk、deterministic fuze、组件失效概率、材料厚度或 F-16 内部系统布局。

## 复核摘要

| 主题 | 当前最高用途 | 结论 |
|---|---|---|
| F-16 外形/尺寸/重量 | `target_geometry reference candidate` | 官方 USAF/Shaw/NAVAIR URL 仍作为稳定 source_ref；当前环境对多个 `.mil` host DNS 解析失败，因此只记录为 `official-url-pinned / local-access-not-confirmed`。 |
| F110 发动机公开资料 | `component_layout / mass sanity candidate` | GE PDF 当前可达，已计算下载流 sha256；只支持 aft single-engine region 和 engine-family sanity，不支持安装边界或脆弱性。 |
| 燃油系统 | `mass/fuel quantity candidate` 与 material/fuel/fire 包的 `method_reference` | F-16 fact sheet 只支持总量量级；油箱分隔、管线、惰化、防火、自封细节仍是 gap。 |
| 材料/冲击/破片标准接口 | `method_reference` / `validation_criteria_reference` | MIL-STD-662F DLA QuickSearch 官方入口当前环境 DNS 失败；NIJ/OJP 0108.01 PDF 可达并 hash，仅作 ballistic material test method reference。 |

## URL / artifact pin 表

| pin_id | ledger source_id | source_ref | 发布方 / 持有人 | 访问状态 `2026-05-28 Asia/Shanghai` | 版本 / 日期 | 权利边界 | artifact / hash 状态 | 允许用途 | residual / 禁止用途 |
|---|---|---|---|---|---|---|---|---|---|
| `F16-GMF-TG-001` | `F16-TG-SRC-001` | `https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/` | U.S. Air Force | `local_dns_failed` via `curl -L -I --max-time 15`; official URL retained from ledger. | 网页 fact sheet；页面版本日期需后续人工或可达环境复核。 | 官方公开网页；只链接和摘要，不复制长正文。 | `hash_not_applicable_html_not_archived`。 | F-16 generic length / wingspan / height / empty/max weight / total fuel quantity sanity with cross-check. | 非 Block 50 专属；不支持内部组件、材料、油箱分隔、armor、Pk 或 fuze authority。 |
| `F16-GMF-TG-002` | `F16-TG-SRC-002`, `F16-MFFS-SRC-001` | `https://www.shaw.af.mil/About-Us/Fact-Sheets/Display/Article/663884/f-16c-fighting-falcon/` | U.S. Air Force / Shaw AFB | `local_dns_failed` via `curl -L -I --max-time 15`; official URL retained from ledger. | 网页 fact sheet；Block 50/52 scope anchor; exact page date not locally confirmed. | 官方公开网页；只链接和摘要。 | `hash_not_applicable_html_not_archived`。 | F-16C Block 50/52 context, engine/radar family sanity, public dimensions and fuel quantity cross-check. | Block 50/52 合并；不支持工程图、internal fuel routing、material/armor、component failure probability 或 fuze trigger surface。 |
| `F16-GMF-TG-003` | `F16-TG-SRC-003` | `https://www.navair.navy.mil/product/F-16-Fighting-Falcon-Viper` | Naval Air Systems Command | `local_dns_failed` via `curl -L -I --max-time 15`; official URL retained from ledger. | NAVAIR product page；exact page date not locally confirmed. | 官方公开网页；只链接。 | `hash_not_applicable_html_not_archived`。 | Generic F-16/Viper geometry and platform envelope cross-check. | Navy product/support context; not Block 50 internal geometry; no material, armor, line routing, Pk or fuze authority. |
| `F16-GMF-TG-004` | `F16-TG-SRC-004`, `F16-MFFS-SRC-002` | `https://www.geaerospace.com/sites/default/files/GE-F110-turbofan-engine-family-datasheet.pdf` | GE Aerospace | `200 application/pdf` via `curl -L -I --max-time 20`. | Public GE F110 family datasheet; exact revision date must be read from PDF before stronger citation. | 厂商公开 PDF；copyright retained by GE; no table copying. | sha256 stream: `34e1d547bbae208f708ca47d17078c755ab6fa551e49cc263cb34ce9ece4e99b`. | Engine-family and aft-engine-region sanity; cross-check Shaw F-16C engine family. | Does not define F-16 installation boundary, accessories, fuel/hydraulic routing, fire suppression, damage threshold or vulnerability. |
| `F16-GMF-TG-005` | `F16-TG-SRC-004`, `F16-MFFS-SRC-002` | `https://www.geaerospace.com/sites/default/files/datasheet-F110-GE-129.pdf` | GE Aerospace | `200 application/pdf` via `curl -L -I --max-time 20`. | Public F110-GE-129 datasheet; exact revision date must be read from PDF before stronger citation. | 厂商公开 PDF；copyright retained by GE; no table copying. | sha256 stream: `aacf7af82254f2eab5d41c5f626a1cb12c508588adedf78fc0f4ea98373280ea`. | F110-GE-129 model sanity for Block 50 candidate engine ref. | Does not authorize engine mass distribution, component fragility, fire cascade, hitbox or effect scale. |
| `F16-GMF-TG-006` | method sidecar | `https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=35877` for `MIL-STD-662` QuickSearch record | Defense Logistics Agency / ASSIST QuickSearch | `local_dns_failed`; MCP fetch also failed robots/DNS in this environment. | Candidate record for MIL-STD-662 family; F revision (`MIL-STD-662F`) date/version details remain `not_locally_confirmed` here. | Official standard catalog entry preferred; do not use unofficial mirrors. | `no_artifact_downloaded / no_hash`. | Search pin only for V50 / ballistic test method provenance. | Cannot be used until official record/PDF/version/right status is confirmed; no F-16 material, armor or fragment authority. |
| `F16-GMF-TG-007` | method sidecar | `https://www.ojp.gov/pdffiles1/nij/099859.pdf` and NIJ page `https://nij.ojp.gov/library/publications/ballistic-resistant-protective-materials-nij-standard-010801` | National Institute of Justice / OJP | PDF `200 application/pdf`; NIJ HTML page `200 text/html` by `curl -I`, Python urllib received `403` without browser headers. | `NIJ Standard 0108.01`, Ballistic Resistant Protective Materials; publication page should be treated as official catalog, PDF as legacy official artifact. | U.S. DOJ/OJP public PDF; cite standard and page; do not copy tables wholesale. | sha256 stream: `2435615c87cd951d6ea5e5ee7a62472e00a79297cd01615a9db1396591e57cd3`. | Generic ballistic protective-material test method reference / validation criteria candidate. | Human/armor material standard, not F-16 airframe; does not provide aircraft material map, fragment cloud, armor thickness, Pk or component failure probability. |

## 字段级边界

| field / concept | candidate sources | 最高用途 | gap |
|---|---|---|---|
| `airframe.length_m`, `wingspan_m`, `height_m` | `F16-GMF-TG-001/002/003` | public geometry envelope candidate after cross-check | no high-fidelity mesh, cross-section, occlusion, component boundary or contact-surface authority. |
| `empty_mass_kg`, `max_takeoff_mass`, `fuel_quantity_total` | `F16-GMF-TG-001/002` plus existing ledger cross-check | mass/fuel sanity candidate | no mission configuration, mass distribution, tank segmentation or fuel routing. |
| engine family / aft engine zone | `F16-GMF-TG-002/004/005` | component-layout sanity candidate | no F-16 installation geometry, fire-detection/suppression, line routing or vulnerability. |
| ballistic material method interface | `F16-GMF-TG-006/007` | method/reference candidate only | no F-16 material/armor truth and no authority to derive thresholds. |

## 当前判定

`target_geometry = candidate / non-authoritative`。以上来源只能支持公开量级、方法引用或后续 residual tracking；不得作为 deterministic fuze、Pk、component failure probability、effect scale、F-16 calibrated geometry/material authority。
