# G4-R-B Mechanism-Load Envelope Source Scan - 2026-06-01

状态：`2026-06-01 / G4-R-B-001-SOURCE-LEDGER-SCAN / pass / research_only / replaceable_data`。

本文是 `G4-R-B` 的第一波 research worker packet。它只把既有公开来源账本整理成
fragment / blast mechanism-load envelope 可用的研究输入，不新增运行时描述符，不写
calibration row，不引入新的原始数值。

## Worker Packet

| 字段 | 内容 |
|---|---|
| task id | `G4-R-B-001-SOURCE-LEDGER-SCAN` |
| owner | main-thread research source scan |
| touched files | 本文件 |
| 输入 | `data_collection/mechanism_model_public_methods/source_ledger.zh.md`；`data_collection/vps_blast_fragmentation_methods/source_ledger.zh.md`；`research_candidate_data_policy_20260601.zh.md` |
| status | `pass` |
| remaining paths | `G4-R-B-002-DERIVED-ENVELOPE-DRAFT` 可基于本文起草 derived envelope；`G4-R-B-003-VALIDATION-GUARD-AUDIT` 仍需在 draft 后执行 |

本文的输出只回答一个问题：哪些公开或可引用来源可以支持 research envelope 的字段形状、
量级约束、验证词汇和替换路径。

## 可用研究输入

| research row id | source ids | 可支持字段 | source tier / rights | scope | uncertainty / confidence | replacement rule |
|---|---|---|---|---|---|---|
| `G4RB-BLAST-METHOD-001` | `MECH-BLAST-001`；`VPS-BFM-001` | blast scaled distance、overpressure / impulse 方法族、单位与适用域检查 | Tier A；UN/IATG 公开 PDF；只引用和摘要 | 通用弹药 / TNT 等效 blast 方法，不匹配具体空空导弹或 F-16C 结构 | `medium` confidence for formula family；空爆、壳体遮挡、姿态、目标局部反射仍不确定 | 若获得 scope-near public test data、独立 benchmark manifest 或 reviewer-approved derived envelope，可替换当前方法入口 |
| `G4RB-BLAST-XCHECK-002` | `MECH-BLAST-002`；`VPS-BFM-002` | UFC / WBDG blast engineering cross-check、版本和单位审查 | Tier A；公开官方标准入口；不复制正文 | 结构抗爆设计领域，适合作为 blast 方法交叉验证 | `medium` confidence for method lineage；结构域到飞机近炸存在大幅 scope gap | 若固定更近似空爆/小战斗部公开验证来源，可降级本行到 background cross-check |
| `G4RB-BLAST-TOOL-003` | `MECH-BLAST-004`；`VPS-BFM-014` | BEC-O / DDESB public-tool route、blast curve lock、benchmark design reference | Tier A candidate；官方公开 artifact 已在既有账本记录 URL/hash；本文不保留工具输出 | blast public-tool comparison design，不是 release benchmark | `medium-low` confidence；canonical retention、allowed-output policy 和 selected output hashes 仍需独立处理 | 若 future retained benchmark packet 提供 hash-only selected outputs，可替换为具体 benchmark design row；否则保持 candidate-only |
| `G4RB-FRAG-MASS-004` | `MECH-FRAG-001`；`VPS-BFM-006` | Mott fragment mass distribution proxy、distribution-shape check | Tier A；公开 DOI/题录；正文版权受限，只引用题录和自写摘要 | 壳体破碎理论，不匹配预制破片、现代 missile warhead 或方向图 | `medium` confidence for theory shape；casing / explosive / material / scale 输入缺失 | 若获得公开 warhead-fragment test source 或 scoped surrogate validation，可替换 proxy 参数化路线 |
| `G4RB-FRAG-VELOCITY-005` | `MECH-FRAG-002`；`VPS-BFM-007` | Gurney initial velocity proxy、charge/casing ratio sensitivity note | Tier A pending；报告号/DOI route 已记录但 artifact/alias 仍需固定；IATG 可作方法导航 | 通用破片初速尺度，不匹配具体 AIM-120C-class fragment cloud | `medium-low` confidence；官方 artifact、rights、checksum、charge/casing assumption 缺失 | 若官方公开 artifact 固定或有同等公开教材/报告 route，可升级为 method reference；否则只作方法导航 |
| `G4RB-FRAG-DEBRIS-006` | `MECH-FRAG-004`；`VPS-BFM-015` | debris density、mass/range/bearing、velocity-analysis vocabulary、collection efficiency residual | Tier A candidate；DDESB TP-21 artifact route/hash 已在既有账本记录；不复制表格或 raw output | explosion-produced debris criteria，不是 missile-specific fragment pattern | `medium` confidence for vocabulary；具体选例、preimage、allowed-output 仍不进入本 research row | 若后续只提供 hash-only selected output anchor，可作为 validation vocabulary replacement；不得变成原始数值来源 |
| `G4RB-PEN-MARGIN-007` | `MECH-PEN-001`；`MECH-PEN-003`；`VPS-BFM-010`；`VPS-BFM-011`；`VPS-BFM-012` | penetration margin 公式形状、ballistic-limit / V50 validation vocabulary | Tier A / pending mix；NASA / DOI / ASSIST route；只引用方法形状 | impact / shielding / armor threshold analogy，不是 aircraft component probability | `low-medium` confidence；速度域、材料、靶板、入射角和组件失效差异大 | 若找到公开 conventional fragment penetration examples 且 rights 清楚，可替换本行；否则只能作为 thresholding scaffold |
| `G4RB-ROD-SHAPE-008` | `MECH-ROD-001`；`MECH-ROD-002`；`MECH-ROD-003` | continuous-rod cut margin 的机制形状、方向性窗口和切割概念 | Tier B / background；公开历史文章或对象页；只引用和摘要 | historical mechanism background，不匹配现代型号 | `low` confidence；不能外推杆数、速度、半径或有效区域 | 若本项目后续不模拟 continuous-rod proxy，可直接降级为 background-only；若加入 rod-cut proxy，必须另建 assumptions 表 |
| `G4RB-SAMPLING-009` | `VPS-BFM-013` | fragment direction sampling reproducibility、isotropy / convergence check | Tier A；公开 DOI；只引用算法思想 | 随机采样方法，不是物理方向图 | `medium-high` confidence for sampling method；真实 warhead pattern 仍未知 | 若找到公开 warhead pattern source，可替换 isotropic sampling；否则保持 surrogate sampling baseline |

## 拒绝或隔离输入

| id | 来源类型 | research 处理 |
|---|---|---|
| `G4RB-REJ-001` | UFC 3-340-01、TM 镜像、FOUO/CUI/export-controlled 或未授权材料 | 不下载、不摘录、不派生；只保留公开拒绝记录 |
| `G4RB-REJ-002` | 论坛、游戏配置、民间 missile DB、百科式 warhead / lethal radius / damage scalar | 只可作为搜索关键词或字段覆盖 sanity；不得进入 envelope row |
| `G4RB-REJ-003` | TP-21 / BEC-O raw tables、spreadsheet raw outputs、selected comparison values | 不进入本文；已有 retained/hash-only 材料只作为 replacement target 和边界上下文 |

## 给 `G4-R-B-002` 的分发输入

`G4-R-B-002-DERIVED-ENVELOPE-DRAFT` 可以基于上表起草下列非权威研究字段：

- `blast_scaled_distance_m_kg13`
- `blast_overpressure_kpa_proxy`
- `blast_impulse_kpa_ms_proxy`
- `fragment_mass_distribution_proxy`
- `fragment_velocity_proxy`
- `fragment_areal_density_proxy`
- `penetration_margin_proxy`
- `rod_cut_margin_shape`
- `surface_incidence_filter`

每个字段必须只给出 `qualitative`、`range placeholder`、`formula family` 或
`derived estimate slot`。若要写任何数值，必须同时写明 source ids、单位、assumption、
uncertainty、confidence 和 replacement rule。

## Research 边界

- 本文可支持 research envelope draft。
- 本文不支持工业级发布、stock/runtime 写入或型号级真值声明。
- 本文不复制任何受限来源正文、表格、图或原始输出。
- 本文不把 `TP-21`、`BEC-O`、Mott、Gurney、Kingery-Bulmash 或 NASA BLE 直接改写成
  AIM-120C / F-16C 专用数据。
