# A2 数据来源准入规则 - 2026-05-28

状态：`A2 specialization / non-authoritative`。本文档把仓库 foundation 层 [公开数据来源准入标准](../../../../../research/standards/public_data_source_admission.zh.md) 映射到 A2 高保真空战杀伤模型。它只定义收集和准入规则，不授予任何运行时 authority。

## 上级标准

A2 数据收集必须先遵守标准化准入规则：

- [公开数据来源准入标准](../../../../../research/standards/public_data_source_admission.zh.md)
- [Public Data Source Admission Standard](../../../../../research/standards/public_data_source_admission.md)

本文件只补充 A2 特有的 target / weapon / aspect / closure / miss-distance / mechanism-load / component-failure / fuze authority 轴。若本文件和标准文档在来源层级、ledger 必填字段、拒绝来源或 authority 默认关闭原则上冲突，以标准文档为准。

空战毁伤领域通常无法获得官方或权威校准数据。A2 允许第三方、社区和开源资料进入候选池；它们必须被标记为 `third_party_candidate`、`community_sanity_check`、`open_source_config_candidate` 或等价非权威状态，并记录合理性评估、交叉验证和 residual。非官方不等于不可用，但未验证的第三方/社区资料也不能被写成 calibrated runtime authority。

## 来源层级

A2 继续沿用标准层的来源层级：

| 层级 | 可接受来源 | A2 用途 | 限制 |
|---|---|---|---|
| `Tier A / 官方-标准` | 标准、官方公开文档、公开教材、公开论文、公开验证方法 | 方法模型、validation criteria、可复现 benchmark 设计 | 仍需 scope 匹配和可复现记录 |
| `Tier B / 公开工程材料` | 厂商公开资料、国会/审计公开文件、军贸宣传册、公开课程材料、可追溯第三方工程资料 | 目标/武器/传感器量级、几何和组件布局候选、非权威参数候选 | 不能直接当型号级真值，必须标注工程近似和第三方性质 |
| `Tier C / sanity check` | 民间数据库、开源仿真配置、可追溯社区数据集、论坛汇编、百科式二手资料 | 量级交叉验证、初始假设 sanity check、候选假设生成 | 不能单独授予 calibrated authority；必须记录合理性评估和不可支持的结论 |
| `rejected` | 受限、不可再分发、来源不稳定、provenance 缺失、明显夸张或 scope 不匹配来源 | 只记录拒绝原因 | 不能进入 descriptor / row |

## 每条来源必须记录

除标准层要求的 source ledger 字段外，A2 ledger 必须显式标注与空战杀伤相关的 scope 轴：

- `source_id`；
- 来源类别和层级；
- 稳定 `source_ref`，例如 DOI、URL、报告编号、归档引用或可复现代码版本；
- 发布方或来源持有人；
- 可公开性、许可证或再分发限制；
- provenance 摘要，说明数据从何而来、如何处理、保留边界是什么；
- scope 匹配：target、weapon family、aspect、closure、miss-distance、组件/机制角色是否完全匹配；
- 交叉验证状态：是否有 Tier A/B 交叉，或只能 Tier C sanity check；
- 合理性评估：单位、数量级、内部一致性、与公开工程常识/相邻来源的冲突，以及是否可能来自游戏平衡或未授权资料；
- ingest 状态：`pending`、`acquired`、`rejected`、`superseded`；
- authority 状态：默认 `non-authoritative`；
- residual：采纳后仍未关闭的真实性缺口。

## A2 Evidence Gate 映射

| A2 角色 | 允许候选来源 | 可进入的包 | 不能直接声明 |
|---|---|---|---|
| `target_geometry` | Tier A/B 几何资料，多源交叉后的公开量级 | source ledger、target geometry notes | 完整结构模型、遮挡真值、组件装甲真值 |
| `warhead_model` | 公开武器尺寸/质量/战斗部类别，公开爆轰/破片模型 | warhead/fuze source ledger、surrogate model card | AIM-120C classified warhead truth |
| `mechanism_load` | 公开 scaled-distance、破片、穿透、连续杆方法 | validated surrogate candidate | calibrated component load without validation |
| `component_fragility` | 公开脆弱性/杀伤评估方法或非型号化公开数据 | component fragility ledger | 型号级组件失效概率 |
| `benchmark_dataset` | 公开数据集、第三方/社区数据、公开求解批次、可复现实验配置 | validation report | Pk authority without scope match |
| `validation_criteria` | 公开标准、论文指标、项目 residual gate | validation report | deterministic fuze admission |
| `reproducibility` | 代码版本、配置、checksum、随机种子、容器/环境 | validation manifest | 数据真实性本身 |

## Descriptor 准入规则

A2 vulnerability descriptor 只有两类 `source_kind` 可进入 runtime authority gate：

- `external_calibration_dataset`；
- 带完整 `validation_manifest` 且 scope 匹配的 `validated_physics_surrogate`。

所有 descriptor 必须满足：

- `schema_version = a2.vulnerability_evidence.v1`；
- `source_ref` 非空；
- `provenance` 非空；
- target / weapon / aspect / closure / miss-distance 证据轴完整；
- `calibration_status = calibrated`；
- rows 若要被消费，必须带 `row_id`、`source_ref`、`provenance`；
- `deterministic_fuze_authority` 在 vulnerability descriptor 中为 reserved/deferred，不能由该 descriptor 放行。

## 禁止项

- 不使用受限、专有、不可再分发或疑似敏感来源正文填充仓库；
- 不把临时实验目录、生成数据或本地 workspace 路径当长期 provenance；
- 不把单一宣传值直接写成 calibrated row；
- 不把民间数据库、第三方数据或论坛汇编单独作为 authority；允许其作为已标记候选或 sanity check；
- 不把 schema fixture、synthetic scaffold 或 engineering surrogate 当真实 Pk；
- 不在没有 fuze/kill-chain admission manifest 前放行 deterministic fuze。
