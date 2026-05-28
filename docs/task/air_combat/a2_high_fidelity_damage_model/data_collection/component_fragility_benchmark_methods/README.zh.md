# A2 组件失效 / 脆弱性公开 benchmark 方法来源

状态：`2026-05-28` 数据收集候选；docs-only；non-authoritative；不写入运行时数据；不提交。

本目录在已有 [component_fragility_vulnerability](../component_fragility_vulnerability/README.zh.md) 组件包基础上继续收集公开候选来源，重点是可公开引用的组件失效准则、LFT&E / FOI / NASA / FAA / NAP 方法、非受控验证指标和 benchmark 设计口径。它不收集、复现或派生受控武器-目标表，也不把公开论文示例转成 A2 calibrated probability rows。

## 已遵守的准入边界

- 依照 [source_admission_rules_20260528.zh.md](../source_admission_rules_20260528.zh.md)，每条来源默认 `non-authoritative`，必须记录 `source_ref`、发布方、权利、Tier、scope、交叉验证、不确定性和 admission/authority。
- 依照 [vulnerability_evidence_schema_v1.zh.md](../../vulnerability_evidence_schema_v1.zh.md)，当前目录不创建 `external_calibration_dataset` 或 `validated_physics_surrogate` descriptor。
- 当前目录不授予 `Pk`、`deterministic_fuze_authority`、`effect_scale_authority` 或 `component_failure_probability_authority`。
- 只有公开、可引用、provenance 可追溯的标准、官方报告、公开论文和公开教材题录可进入候选账本。
- JMEM / JWS / J-ACE / AJEM / COVART / FASTGEN / SLATE / Endgame Manager 等工具或数据只记录拒绝或 sanity-check 边界。

## 本目录与已有组件包的差异

已有组件包偏“组件脆弱性 / 杀伤评估来源池”。本目录偏“可复现 benchmark 与验证方法准则”：

| 关注点 | 本目录处理 |
|---|---|
| `component kill criteria` | 只收集公开方法、状态定义、fault-tree / redundancy / dependency 表达；不采集受控组件概率表。 |
| `failure probability surrogate benchmark` | 只记录公开材料/结构/几何/后果链可如何成为 surrogate benchmark；必须另有项目内 validation manifest 才能进入 runtime。 |
| `redundancy/dependency validation` | 用 FOI、公开 vulnerability 论文、FAA system safety、NASA damaged-aircraft consequence 支撑验证问题设计。 |
| `residual register` | 明确哪些真实性缺口不能被公开方法关闭，例如目标内部布局、武器破片场、组件 Pcd|h、LFT&E 原始数据。 |

## 最高价值候选来源

| source_id | 价值 | 可支持 | 当前限制 |
|---|---|---|---|
| `CFBM-FOI-001` | 公开报告直接讨论 component kill criteria、功能杀伤、fault tree 和 Pk/Pk/h 术语。 | `component kill criteria`、failure-state schema、dependency propagation benchmark。 | 文献综述不是校准数据；不能复制为 probability row。 |
| `CFBM-LFTE-001` / `CFBM-LFTE-002` / `CFBM-LFTE-003` | NAP、GAO 和 10 U.S.C. § 4172 LFT&E 为验证分层、full-up evidence、M&S 不能替代试验提供公开准则。 | validation acceptance criteria、evidence gate、residual policy。 | 不给组件概率或具体武器-目标数据。 |
| `CFBM-NASA-001` 到 `CFBM-NASA-004` | NASA damaged-aircraft / model credibility 资料适合构造后果链 benchmark 和 V&V 指标。 | damaged-aircraft consequence validation、surrogate credibility checklist。 | 多为 transport / GTM / model-credibility 方法，不验证空空武器效应。 |
| `CFBM-FAA-001` / `CFBM-FAA-002` | FAA 系统安全和 uncontained rotor debris 资料适合冗余、隔离、碎片路径 sanity。 | redundancy/dependency validation、residual register、civil fail-safe severity mapping。 | 民用适航概率等级不能迁移为战斗 component fragility。 |
| `CFBM-PAPER-001` 到 `CFBM-PAPER-005` | 公开论文覆盖 shotline、product-structure vulnerability、projectile/fragment impact、representative helicopter/aircraft 方法。 | geometry-to-component exposure、fault-tree、surrogate benchmark design。 | 示例平台和示例概率均不具备 A2 authority。 |

## 明确拒绝或仅限 sanity check

| 来源类型 | 判定 |
|---|---|
| JMEM / JWS / J-ACE / JAAM / AJEM 武器效能或 weaponeering 数据 | `rejected`：受控或不可公开再分发，不进入 descriptor / row。 |
| COVART / FASTGEN / SLATE / ACEL / Endgame Manager 内部模型、validation sets、工具输出 | `rejected`：工具名可作为公开术语线索，内部数据不可采。 |
| 游戏、商业仿真配置、论坛、民间武器 DB、百科式 Pk / damage scalar | `sanity_check_only` 或 `rejected`：不能授予任何 calibrated authority。 |
| FOUO / CUI / ITAR / EAR / leaked PDF / 非授权课件 / 承包商附件 / 非公开 LFT&E 原始数据 | `rejected`：不下载、不摘录、不派生。 |

## 与 schema 的使用方式

本目录来源最多只能帮助后续形成这些非运行时 artifact：

- `method_reference`：组件失效状态、hit-to-component、fault-tree、redundancy/dependency 的公开方法说明。
- `benchmark_design_reference`：公开 benchmark 的输入空间、误差指标、覆盖率、敏感性、uncertainty 记录。
- `validation_criteria_reference`：LFT&E、M&S credibility、NASA/FAA consequence validation 的验收口径。
- `residual_register_reference`：哪些数据仍缺，哪些不能从公开方法推断。

若后续要进入 `a2.vulnerability_evidence.v1` runtime descriptor，仍必须另行满足：

- `source_kind` 只能是 `external_calibration_dataset` 或带完整 `validation_manifest` 的 `validated_physics_surrogate`；
- `calibration_status = calibrated`；
- target / weapon / aspect / closure / miss-distance scope 逐项匹配；
- row 具备 `row_id`、`source_ref`、`provenance`、uncertainty 和机制载荷过滤条件；
- 所有 authority 字段必须由独立 gate 放行，不能由本目录文献引用自动放行。

## 文件

- [source_ledger.zh.md](source_ledger.zh.md)：逐条来源账本，含 source_ref、发布方、权利、Tier、scope、交叉验证、不确定性、admission/authority。
- [source_pin_update_20260528.zh.md](source_pin_update_20260528.zh.md)：2026-05-28 联网核对后的版本/权利/公开性 pin、角色汇总和 residual；不授予 runtime authority。
- [schema_mapping_notes.zh.md](schema_mapping_notes.zh.md)：把来源能支持的 schema / benchmark / residual 角色和禁止转换规则映射到 A2 evidence schema。

## 仍缺的外部数据

- 公开、可再分发、scope 匹配并含 uncertainty 的 aircraft component fragility calibration dataset。
- 公开的现代空空 blast-fragmentation warhead fragment mass / velocity / pattern / fuze burst-position 数据。
- F-16C Block 50 级别公开内部组件布局、冗余、线束/液压/电源依赖和战斗损伤试验数据。
- 可公开引用的 full-up 或 component-level LFT&E 原始试验矩阵、误差指标和 acceptance thresholds。
- 可把 NASA/FAA/FOI 方法闭合为 `validated_physics_surrogate` 的项目内 validation manifest、checksum、版本和误差报告。
