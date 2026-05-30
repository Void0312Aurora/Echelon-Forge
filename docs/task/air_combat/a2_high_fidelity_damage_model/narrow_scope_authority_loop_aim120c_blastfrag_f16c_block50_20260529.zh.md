# A2 窄域 Authority 闭环任务定义 - AIM-120C-class blast-fragmentation -> F-16C Block 50

状态：`2026-05-29 / task_definition / narrow_scope / authority_boundary_frozen`

本文档用于冻结 A2 杀伤模型下一阶段的窄域任务边界，目标是先闭合一个最小、可审计、可验收的 authority loop，避免继续把 scope 发散到多武器、多目标、多 kill-chain 权威同时推进。本文档只定义任务边界、准入和验收，不直接授予任何新的 runtime authority。

## 1. 本轮固定 scope

本轮只允许围绕下列 weapon-target 对推进：

| 轴 | 固定值 |
|---|---|
| `target_type` | `F-16C_Block50` |
| `weapon_class` | `AIM-120C-class` |
| `weapon_family` | `blast_fragmentation` |
| authority 目标层 | `effect_scale`、`component_failure_probability` |
| 明确不放行 | `pk`、`deterministic_fuze` |

补充说明：

- 本轮冻结的是 weapon-target 主 scope；如需进入首个可执行校准包，优先沿用现有候选子轴 `beam / high / near_miss_0_35m`，但那属于该主 scope 下的进一步收窄，而不是本轮向外扩面。
- 不在本轮同时扩到 `AIM-9X`、`R-77`、`Su-35`、`MQ-9`、`E-3`、`continuous_rod` 或其他 target/weapon family。

## 2. 为什么先选这个 weapon-target scope

选择 `AIM-120C-class blast-fragmentation -> F-16C_Block50` 的原因如下：

1. 现有准备度最高。仓库已经同时具备：
   - `F-16C_Block50` 的 authored 组件几何、overlay 和代表性 component consequence 路径；
   - `AIM-120C-class` 的公开来源台账、warhead/fuze residual 和 `blast_fragmentation` family 候选；
   - 首个窄子域 validation manifest 草案：`beam / high / near_miss_0_35m`。
2. authority 面最容易收口。当前代码和文档已经把 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority`、`deterministic_fuze_authority` 分开；这个 scope 适合先放行前两者，而不误触 kill-chain 终局 authority。
3. 符合梯度真实性原则。项目当前更接近“组件级机制载荷和后果闭环”而非“已校准 Pk / 已校准确定性引信”。选一个窄域 scope 能让真实性声明停留在证据支持的最高层，不把局部进展误写成全域高保真完成。
4. 公开数据条件下最可执行。AIM-120C C 型具体战斗部/引信真值缺口仍大，F-16C Block 50 的内部脆弱性真值也不完整，因此应先追求“可审计、可复现、可 gate 的局部 authority”，而不是跨域追求一次性闭合完整 Pk。
5. 最能抑制发散。若不先冻结 weapon-target 对，后续很容易把几何、引信、脆弱性、Pk、reward、训练 smoke 混成一个大任务，最后任何一层都无法清晰验收。

## 3. 当前要放行到哪一层

本轮 authority 闭环只允许推进到 vulnerability descriptor / row 对 `effect_scale` 与 `component_failure_probability` 的受控放行，且必须停在这一层。

### 3.1 允许优先推进的 authority

| authority 字段 | 本轮目标 | 放行条件 |
|---|---|---|
| `effect_scale_authority` | `priority_1` | 仅限 scope 匹配的 `external_calibration_dataset` 或带完整 `validation_manifest` 的 `validated_physics_surrogate`；descriptor 与 row 都要通过 schema/source/provenance/axis gate。 |
| `component_failure_probability_authority` | `priority_2` | 同上；可晚于 `effect_scale_authority` 放行，不要求同一轮同步闭合。component-specific row 必须带 `component_name/system/redundancy_group` provenance。 |

本轮“放行”指：

- 允许 narrow-scope descriptor/rows 在 gate 完整关闭后进入 runtime 消费路径；
- 允许 `EffectsEvent` / component mechanism rows 记录被消费 row 的 `dataset_id`、`row_id`、`source_ref`、`provenance`；
- 允许 effect scale 和组件条件失效概率从 synthetic/profile-scale 路径升级到 row-backed 路径；
- 不允许把这一步表述为真实 kill probability、真实引信、真实单发杀伤结论。

### 3.2 明确不放行的 authority

| authority 字段 | 当前结论 | 原因 |
|---|---|---|
| `pk_authority` | `false / deferred` | 本轮只做 mechanism-load 到 component consequence 的窄域 authority，不做 mission kill / platform loss 概率校准。 |
| `deterministic_fuze_authority` | `false / deferred` | 当前公开来源、replay/admission matrix、target signature、trigger threshold、delay/reliability 证据仍不足；vulnerability descriptor 也不允许放行确定性引信。 |

硬边界：

- 不得用 `effect_scale` 或 `component_failure_probability` 的放行结果，反向暗示 `pk_authority=true`；
- 不得因为某个 scope 内 row 已通过，就移除现有 RNG fuze gate；
- 不得把 terminal reward、combat win、`DamageReport.loss_state_to` 或 live smoke 结果当成 Pk 校准替代物。

## 4. 与 gradient realism 的关系

本轮任务是 A2 主线对梯度真实性原则的一次“收口”，不是一次“升级声明”。

具体约束如下：

1. 允许声明的最高进展：`AIM-120C-class blast_fragmentation -> F-16C_Block50` 这一窄域内，mechanism-load 到 component consequence 的 authority gate 开始具备受控放行路径。
2. 不允许声明的进展：
   - “A2 已完成高保真 kill chain”；
   - “AIM-120C 对 F-16C 的单发杀伤概率已可信”；
   - “deterministic fuze 已有公开证据支撑”；
   - “该窄域放行可自动外推到其他目标、其他 aspect、其他 closure、其他 missile family”。
3. 若本轮只闭合 `effect_scale_authority`，则真实性声明也只能停在 effect-scale 层；不能提前把 `component_failure_probability`、`Pk`、`kill assessment` 一并宣称完成。

换言之，本轮的正确产出不是“更像真的数值”，而是“更清楚地知道哪些数值已被授权、哪些还没有”。

## 5. 与 public data admission 的关系

本轮必须继续服从以下上级规则：

- [A2 数据来源准入规则](data_collection/source_admission_rules_20260528.zh.md)
- [A2 Vulnerability Evidence Schema v1](vulnerability_evidence_schema_v1.zh.md)
- [梯度真实性原则](../../../standards/foundation/gradient_realism_principles.zh.md)

对本窄域任务，公开数据准入规则落到三条：

1. 允许公开第三方、社区、开源资料进入候选池，但默认只能是 `non-authoritative`。
2. 能进入 runtime authority gate 的 descriptor `source_kind` 仍只有：
   - `external_calibration_dataset`
   - `validated_physics_surrogate`
3. 即使是上述两类，也必须具备完整 `schema_version`、`source_ref`、`provenance`、`calibration_status` 和 scope 轴匹配；缺一项都不能放行。

## 6. 第三方 / 社区候选的允许方式

第三方/社区来源允许参与本任务，但只允许以候选或 sanity-check 角色进入，必须显式保留 `non-authoritative` 标记和合理性评估。

### 6.1 允许的角色

| 来源类型 | 允许角色 | 必须附带 |
|---|---|---|
| Tier A / Tier B 公开官方、标准、工程资料 | `candidate`、`method_ref`、`validation_input_candidate` | `source_ref`、rights、scope 匹配、residual |
| Tier C 第三方/社区/开源资料 | `third_party_candidate`、`community_sanity_check`、`open_source_config_candidate` | 合理性评估、交叉验证状态、不可直接授予 authority 的说明 |

### 6.2 合理性评估最低要求

每条第三方/社区候选至少要回答：

- 单位和量级是否自洽；
- 是否与 Tier A/B 来源或相邻公开工程常识冲突；
- 是否可能来自游戏平衡值、论坛转述、未授权镜像或不可复现实验；
- 是否只能支持“看起来不离谱”，而不能支持“可进入 runtime row”；
- 采纳后还剩哪些 residual 没有关闭。

### 6.3 明确禁止

- 不得把 DCS、War Thunder、论坛表格、民间数据库的数值直接写成 descriptor row；
- 不得把 marketing 值、博物馆介绍页或二手网页单独写成 `effect_scale_authority` 或 `component_failure_probability_authority`；
- 不得从第三方/社区候选直接推导 `pk_authority` 或 `deterministic_fuze_authority`。

## 7. 验收标准

本任务的验收以“authority 闭环是否清晰、是否可审计、是否未越界”为主，不以“是否得到好看的杀伤率数值”为主。

### 7.1 最小验收

满足以下条件，才可认为本窄域任务闭环已建立：

1. scope 冻结清楚：文档、descriptor、validation manifest、residual register 对同一 `target_type / weapon_family / weapon_class` 一致，不混入其他平台或武器族。
2. narrow-scope 数据来源台账完整：每条候选都有 `source_ref`、发布方、rights、provenance、scope 匹配、authority 状态和 residual。
3. 若放行 `effect_scale_authority`：
   - descriptor 为 `calibrated`；
   - `source_kind` 合法；
   - `validation_manifest` 或 external calibration 证据完整；
   - 被消费 row 带 `row_id`、`source_ref`、`provenance`；
   - 事件面能反查 effect-scale 来源。
4. 若放行 `component_failure_probability_authority`：
   - 除第 3 条要求外，还要能说明组件适用轴；
   - component-specific row 优先级和 provenance 可审计；
   - 事件面能反查 probability row 来源和 dataset ref。
5. 验收文档或测试必须明确写出：
   - `pk_authority=false`
   - `deterministic_fuze_authority=false`
   - `non-authoritative` 候选未被误提升为 runtime authority。

### 7.2 增强验收

以下条件满足越多，说明该闭环越稳，但它们不自动等于 Pk/引信放行：

- 同一窄域下，effect-scale row 能按 mechanism-load 门槛稳定区分 blast / fragment / obliquity / miss-distance 子情况；
- component-failure row 能区分 global row 与 component-specific row，且不被低载荷误消费；
- 第三方/社区候选仅停留在 ledger 或 sanity-check 层，没有泄漏进 authority row；
- residual register 明确保留 AIM-120C 战斗部/引信真值缺口和 F-16C 内部脆弱性缺口。

## 8. 非目标

本轮明确不是以下任务：

- 不是全域 A2 高保真完成宣告；
- 不是 AIM-120 全家族或所有 F-16 变型的统一 authority 发布；
- 不是 `Pk`、`mission_kill_probability`、`single-shot kill` 校准；
- 不是 deterministic fuze、trigger threshold、delay/reliability 的公开证据闭合；
- 不是 live missile smoke 稳定“一发必杀”；
- 不是把 reward、terminal override、训练 shaping 或 legacy `health` 重新变成物理权威。

## 9. 残余风险

即使本轮按计划完成，仍应显式保留以下风险：

1. `validated_physics_surrogate` 可能只是“方法上合理”，不等于 AIM-120C C 型真值。
2. F-16C Block 50 的 component fragility 与系统内部拓扑仍主要来自公开方法和工程抽象，不是官方 vulnerability 数据库。
3. `beam / high / near_miss_0_35m` 之类的窄子域即使闭合，也不能自动外推到 head-on、tail-chase、direct-hit 或其他 miss-distance bucket。
4. 若 effect scale 已放行但 component failure probability 尚未放行，事件链仍停留在“载荷已授权、后果概率未授权”的中间态。
5. 若 component failure probability 已放行但 fuze / Pk 未放行，kill-chain 终局仍不能解释为可信单发杀伤概率。

## 10. 后续升级路径

建议按以下顺序升级，避免多层 authority 一起松动：

1. **阶段 A**：冻结本窄域 scope，补齐 source ledger、validation manifest、residual register 和 authority 声明。
2. **阶段 B**：先放行 `effect_scale_authority`，让 blast/fragment 机制载荷缩放进入 row-backed authority。
3. **阶段 C**：在同一窄域内再放行 `component_failure_probability_authority`，优先从 component-specific rows 开始。
4. **阶段 D**：只在同一 weapon-target 主 scope 内，逐步扩到更多 aspect / closure / miss-distance buckets。
5. **阶段 E**：待独立 fuze 证据链、replay/admission matrix、target signature 和 kill-chain 校准闭合后，再单独评估 `deterministic_fuze_authority` 与 `pk_authority`；二者不得借本轮结果自动继承。

## 11. 当前判定

当前主线应按以下句子统一口径：

> A2 下一阶段只为 `AIM-120C-class blast_fragmentation -> F-16C_Block50` 建立窄域 authority 闭环；优先放行 `effect_scale` 与 `component_failure_probability`，并明确保持 `pk` 与 `deterministic_fuze` 为 `false / deferred`。第三方和社区资料可以进入候选池，但必须保持 `non-authoritative` 标记和合理性评估，不能直接成为 runtime authority。
