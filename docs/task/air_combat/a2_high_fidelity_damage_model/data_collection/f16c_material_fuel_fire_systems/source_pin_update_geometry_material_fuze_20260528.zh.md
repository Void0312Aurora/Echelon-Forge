# F-16C Material / Fuel / Fire Systems Geometry-Material-Fuze Source Pin Update

状态：`2026-05-28 / source reachability update / candidate-only / non-authoritative`  
责任范围：F-16C Block 50 材料、燃油、火灾、系统依赖和材料/冲击/破片测试标准的公开来源可达性复核。  
准入边界：本文只记录公开 method/reference/sanity 候选，不写运行时配置，不创建校准 row，不授予 F-16 material/fuel/fire authority。

## 复核摘要

| 主题 | 当前最高用途 | 结论 |
|---|---|---|
| FAA fuel/fire 方法源 | `method_reference` / `validation_criteria_reference` | AC 25.981-1D、AC 25.981-2A、AC 20-53B、AC 25.869-1A 当前可达并计算 hash；只能用于民机/通用飞机燃油火灾方法轴。 |
| NIST/NASA 方法源 | `method_reference` / `consequence_reference` | NIST SP 984 页面和 NASA NTRS 页面当前可达；未下载全部 artifact，hash 状态分开记录。 |
| 材料/冲击/破片标准 | `test_method_reference` | MIL-STD-662 QuickSearch 官方入口当前环境 DNS 失败，保持 `pending-official-confirmation`；NIJ/OJP 0108.01 PDF 可达并 hash。 |
| F-16C Block 50 系统真实数据 | `gap` | 仍无公开可用的材料分区、油箱分隔、管线/线束、fire detection/suppression layout、component fragility 或 Pk。 |

## URL / artifact pin 表

| pin_id | ledger source_id | source_ref | 发布方 / 持有人 | 访问状态 `2026-05-28 Asia/Shanghai` | 版本 / 日期 | 权利边界 | artifact / hash 状态 | 允许用途 | residual / 禁止用途 |
|---|---|---|---|---|---|---|---|---|---|
| `F16-GMF-MFFS-001` | `F16-MFFS-SRC-003` | `https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_25.981-1D.pdf` | Federal Aviation Administration | `200 application/pdf` via `curl -L -I --max-time 20`. | FAA `AC 25.981-1D`; exact issue date should be read from PDF if cited in later reports. | FAA public PDF; cite title/AC number; no long excerpts. | sha256 stream: `e9f1fe237c32b65e99bfbd8b0910ad2ed6688471d42313d875b0dd834b1dbf04`. | Fuel-tank ignition-source prevention method axis; validation checklist vocabulary. | Civil transport compliance; no F-16 ignition probability, tank layout, combat damage threshold or Pk. |
| `F16-GMF-MFFS-002` | `F16-MFFS-SRC-004` | `https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_25.981-2A.pdf` | Federal Aviation Administration | `200 application/pdf`. | FAA `AC 25.981-2A`; exact issue date should be read from PDF if cited in later reports. | FAA public PDF; cite AC number/title. | sha256 stream: `399c6022d9719bf8d33c0e226ce31f6ac93bc28d3a344945765d57aede3596e2`. | Fuel tank flammability / inerting method reference. | Does not prove F-16 has any FRM/OBIGGS/self-sealing feature or parameter. |
| `F16-GMF-MFFS-003` | `F16-MFFS-SRC-005` | `https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_20-53B.pdf` | Federal Aviation Administration | PDF downloaded for hash; HEAD status not separately retained in this note. | FAA `AC 20-53B`; exact issue date should be read from PDF before strong citation. | FAA public PDF; cite title/AC number. | sha256 stream: `74b671779fa106d6e5d5ba13f2bd8bc996c0cd477c30590327faf11686e68b77`. | Lightning/static/bonding/venting ignition-source method axis. | No F-16 bonding path, wiring route, tank vent geometry or ignition probability. |
| `F16-GMF-MFFS-004` | `F16-MFFS-SRC-009` | `https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_25_869-1A.pdf` | Federal Aviation Administration | PDF downloaded for hash; ledger also has FAA AC index URL. | FAA `AC 25.869-1A`; exact issue date should be read from PDF before strong citation. | FAA public PDF; cite title/AC number. | sha256 stream: `3eb0402b5f9f20e501a974162aafda313946596dd4dcf125a94962efb07b2db7`. | Generic fire-protection systems taxonomy and flammable-fluid dependency method. | No F-16 fire zones, sensors, bottles, nozzles, EWIS, hydraulic routing or system cascade probabilities. |
| `F16-GMF-MFFS-005` | `F16-MFFS-SRC-013` | `https://www.nist.gov/node/589031` redirected to NIST SP 984 publication page | National Institute of Standards and Technology | `200 text/html`; effective URL `https://www.nist.gov/publications/discharge-cf3i-cold-simulated-aircraft-engine-nacelle-nist-sp-984`. | NIST SP 984 publication page; PDF URL in ledger should be pinned separately if artifact is retained. | NIST official publication page; cite title/SP number. | `html_reachable / pdf_hash_not_recorded_this_round`. | Generic engine-nacelle fire suppression method and dependency axis. | Simulated nacelle is not F110/F-16; no bay geometry, sensor logic, bottle/nozzle parameters or suppression probability. |
| `F16-GMF-MFFS-006` | `F16-MFFS-SRC-017` | `https://ntrs.nasa.gov/citations/20080034656` | NASA NTRS | `200 text/html`. | NTRS citation `20080034656`; exact paper date and rights should be read from NTRS record for future reports. | NASA public record; rights per NTRS page. | `html_reachable / artifact_hash_not_recorded_this_round`. | Damaged-aircraft consequence modeling reference. | Transport-aircraft consequence only; no F-16 control law, combat hit-to-damage probability or fire growth. |
| `F16-GMF-MFFS-007` | method sidecar | `https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=35877` | Defense Logistics Agency / ASSIST QuickSearch | `local_dns_failed`; official catalog entry not locally verified. | Candidate MIL-STD-662 family entry; `MIL-STD-662F` version/date remains pending official confirmation. | Use only official DLA/ASSIST catalog; reject unofficial mirrors. | `no_artifact / no_hash`. | Pending source lead for V50 ballistic test method. | Not usable as source until official version/rights/artifact are pinned; no F-16 material or armor authority. |
| `F16-GMF-MFFS-008` | method sidecar | `https://www.ojp.gov/pdffiles1/nij/099859.pdf`; NIJ catalog page `https://nij.ojp.gov/library/publications/ballistic-resistant-protective-materials-nij-standard-010801` | National Institute of Justice / OJP | PDF `200 application/pdf`; NIJ page `200 text/html` via HEAD, Python urllib got `403`. | `NIJ Standard 0108.01`, Ballistic Resistant Protective Materials; legacy official public standard. | DOJ/OJP public PDF; cite standard title; avoid table copying. | sha256 stream: `2435615c87cd951d6ea5e5ee7a62472e00a79297cd01615a9db1396591e57cd3`. | Ballistic protective-material test method and validation-criteria reference. | Personnel/material standard, not aircraft vulnerability; no F-16 material map, thickness, fragment threshold or Pk. |
| `F16-GMF-MFFS-009` | method sidecar | `https://www.ojp.gov/pdffiles1/nij/307346.pdf`; NIJ 0101.07 topic page | National Institute of Justice / OJP | PDF `200 application/pdf`; NIJ topic page `200 text/html`. | `NIJ Standard 0101.07`, body armor ballistic resistance; modern NIJ method context. | DOJ/OJP public PDF; cite standard title. | sha256 stream: `c770bea230ba7810344dd1f2b7ac89c83f77ef3db3c56226b44465ba6d0ca5ea`. | Modern ballistic test method terminology reference only. | Body-armor scope; not F-16, not AAM fragment cloud, not component failure probability. |

## 字段级边界

| field / concept | candidate sources | 最高用途 | gap |
|---|---|---|---|
| `fuel_fire_mechanism_axes` | `F16-GMF-MFFS-001/002/003` | method/reference candidate | no F-16 tank segmentation, ullage, self-sealing, inerting or ignition probability. |
| `flammable_fluid_fire_axis` | `F16-GMF-MFFS-004/005` | dependency taxonomy / method candidate | no F-16 fire-zone, routing, detector, bottle, nozzle or suppression probability. |
| `damaged_aircraft_consequence` | `F16-GMF-MFFS-006` | consequence scenario design reference | transport-aircraft scope only; no fighter calibration. |
| `ballistic_material_test_method` | `F16-GMF-MFFS-007/008/009` | method/reference candidate | no aircraft material distribution, no AAM fragment lethality, no component fragility row. |

## 当前判定

`material_fuel_fire_dependency = method/reference candidate / non-authoritative`。没有来源通过 external calibration dataset 或 validated surrogate gate；任何 runtime consumer 必须继续把 F-16 material/fuel/fire authority 视为 gap。
