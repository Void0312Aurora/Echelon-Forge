# Surrogate Model Card 模板

状态：非权威 candidate 模板。本文档用于描述候选 physics surrogate 的模型边界和验证前提；它不声称模型已校准，不允许被用作 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

候选 scope 固定为：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。

## 模型元数据

| 字段 | 值 |
|---|---|
| `model_ref` | `<待填：稳定模型/代码/配置版本引用>` |
| `model_version` | `<待填>` |
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `model_owner` | `<待填>` |
| `code_ref` | `<待填：commit/container/archive>` |
| `run_manifest_ref` | `<待填>` |
| `random_seed_policy` | `<待填：固定/多种子/不适用>` |
| `current_validation_status` | `not_validated` |

## 允许描述的用途

- 为后续 `a2.vulnerability_surrogate_validation.v1` 验证报告准备模型说明。
- 在候选范围内描述可能输出的 mechanism-load、effect-scale 或 component-failure probability 候选量。
- 帮助 reviewer 判断模型输入、假设、局限、复现条件和 residual 风险。

## 明确非用途

- 不作为 `AircraftVulnerabilityProfile` 的 calibrated evidence。
- 不作为可被 runtime 加载的 vulnerability evidence descriptor。
- 不输出或授权 Pk 曲线。
- 不替代 live fuze trigger、fuze reliability、target signature 或 kill-chain 验证。
- 不放行 deterministic fuze；当前 deterministic-fuze authority 必须保持 `false`。

## 输入定义

| 输入 | 单位 / 类型 | 来源 | 必填 | 备注 |
|---|---|---|---|---|
| target geometry | `<mesh/hitbox/component table>` | `<SRC-...>` | 是 | 必须限定 `F-16C_Block50`，不能泛化到其他 F-16 变体 |
| detonation geometry | `<body-frame vector / miss distance>` | `<SRC-...>` | 是 | 必须覆盖 `beam` 与 `near_miss_0_35m` |
| closure state | `<m/s 或 bucket>` | `<SRC-...>` | 是 | 必须记录 `high` 的定义和边界 |
| warhead class | `AIM-120C-class/blast_fragmentation` | `<SRC-...>` | 是 | 不得暗示具体受限弹药参数已知 |
| material / component assumptions | `<table>` | `<SRC-...>` | 是 | 所有假设必须可追溯 |
| solver / surrogate parameters | `<配置引用>` | `<SRC-...>` | 是 | 需要版本、checksum、单位 |

## 输出定义

| 输出 | 目标 schema 对应 | 当前状态 | 授权状态 |
|---|---|---|---|
| candidate `effect_scale` | vulnerability evidence row 可选字段 | `<待验证>` | `non-authoritative` |
| candidate `component_failure_probability` | vulnerability evidence row 可选字段 | `<待验证>` | `non-authoritative` |
| mechanism-load intervals | row `min_*` / `max_*` 适用门槛 | `<待验证>` | `non-authoritative` |
| uncertainty summary | validation report 指标输入 | `<待填>` | `non-authoritative` |
| Pk | 不在本 model card 授权 | 不输出 | `false` |
| deterministic fuze decision | 不在本 model card 授权 | 不输出 | `false` |

## 物理和工程假设

| `assumption_id` | 假设 | 来源 | 影响 | residual |
|---|---|---|---|---|
| `ASM-001` | `<待填>` | `<SRC-...>` | `<mechanism/effect/component>` | `<RES-...>` |
| `ASM-002` | `<待填>` | `<SRC-...>` | `<待填>` | `<RES-...>` |

## 与 A2 evidence gate 的关系

未来如需把本候选包整理为 descriptor，必须先由验证报告证明以下字段完整、稳定且 scope 匹配：

| schema 字段 | 当前候选值 |
|---|---|
| `source_kind` | 不设置为 runtime descriptor；候选意图为未来 `validated_physics_surrogate` |
| `source_ref` | `<待填，当前不可授权>` |
| `validation_artifact_ref` | `<待填，单独不授权>` |
| `calibration_status` | `unvalidated` |
| `validation_manifest.schema_version` | `a2.vulnerability_surrogate_validation.v1` |
| `validation_manifest.validation_status` | `not_run`，不是 `validated` 或 `passed` |
| `validation_manifest.validation_scope` | 必须逐项等于本候选 scope |
| `pk_authority` | `false` |
| `deterministic_fuze_authority` | `false` |

## 已知限制

- 模型是否能代表真实 AIM-120C-class blast-fragmentation 效应尚未验证。
- F-16C Block 50 组件几何、材料和遮挡关系必须由 source ledger 支撑；缺失项不能由工程直觉补成权威。
- `near_miss_0_35m` 与 `beam/high` 的覆盖需要独立 benchmark；单一算例不能代表整个桶。
- 模型输出若存在随机采样，必须报告种子策略、置信区间和残差分布。
- 所有限制在 [residual_register.zh.md](residual_register.zh.md) 中保持 open，直到有审计记录关闭。
