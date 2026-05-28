# Validation Report 模板

状态：非权威 candidate 模板，当前没有验证运行结论。本文档预留 `validated_physics_surrogate` 所需的验证 manifest、benchmark、metrics 和 acceptance criteria；在字段未填满、结果未复核、残差未关闭前，不能声称已校准，不能授予 Pk 或 deterministic-fuze authority。

候选 scope 固定为：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。

## 验证 Manifest 草案

| 字段 | 值 |
|---|---|
| `schema_version` | `a2.vulnerability_surrogate_validation.v1` |
| `validation_status` | `not_run` |
| `validation_artifact_sha256` | `<待生成；当前为空则不可授权>` |
| `validated_surrogate_model_ref` | `<待填>` |
| `validation_benchmark_ref` | `<待填>` |
| `validation_metrics_ref` | `<待填>` |
| `validation_acceptance_criteria_ref` | `<待填>` |
| `validation_scope.target_type` | `F-16C_Block50` |
| `validation_scope.weapon_family` | `blast_fragmentation` |
| `validation_scope.weapon_class` | `AIM-120C-class` |
| `validation_scope.aspect_bucket` | `beam` |
| `validation_scope.closure_bucket` | `high` |
| `validation_scope.miss_distance_bucket` | `near_miss_0_35m` |

`validation_status=not_run` 是刻意的候选状态，不满足 runtime gate。只有未来完整报告将状态改为 `validated` 或 `passed`，且所有引用和 checksum 非空、scope 完全匹配、review 记录可追溯时，才允许进入下一轮 authority 评审。

## Benchmark 计划

| `benchmark_id` | benchmark 来源 | 覆盖内容 | 独立于模型输入 | 当前状态 | residual |
|---|---|---|---|---|---|
| `BM-001` | `<SRC-...>` | `<effect/component/mechanism-load>` | `<yes/no/unknown>` | `<pending>` | `<RES-...>` |
| `BM-002` | `<SRC-...>` | `<待填>` | `<待填>` | `<pending>` | `<RES-...>` |

benchmark 必须与 surrogate 训练、拟合或参数选择来源分离。若 benchmark 只是同一求解器的重复运行，需要明确说明它不能独立支撑验证结论。

## 指标与验收门槛

| `metric_id` | 指标 | 适用输出 | 统计口径 | 验收门槛 | 当前结果 | authority 影响 |
|---|---|---|---|---|---|---|
| `MET-001` | effect-scale residual | `effect_scale` | `<MAE/RMSE/quantile>` | `<待定义>` | `not_run` | 不授权 |
| `MET-002` | component probability residual | `component_failure_probability` | `<Brier/calibration curve/log loss>` | `<待定义>` | `not_run` | 不授权 |
| `MET-003` | mechanism-load interval coverage | `min_*` / `max_*` row 门槛 | `<coverage/violation rate>` | `<待定义>` | `not_run` | 不授权 |
| `MET-004` | uncertainty calibration | `<置信区间/分位数>` | `<coverage>` | `<待定义>` | `not_run` | 不授权 |
| `MET-005` | scope leakage check | scope axes | `<manual + automated>` | `0 out-of-scope claims` | `not_run` | 不授权 |

验收门槛不得由同一候选结果事后反推。未定义验收门槛时，即使数值结果存在，也不能声明验证通过。

## 测试矩阵

| `case_id` | target | weapon family | aspect | closure | miss-distance bucket | 机制载荷 | 预期检查 | 当前状态 |
|---|---|---|---|---|---|---|---|---|
| `VAL-001` | `F-16C_Block50` | `blast_fragmentation` | `beam` | `high` | `near_miss_0_35m` | `<fragment + blast>` | `<effect residual>` | `not_run` |
| `VAL-002` | `F-16C_Block50` | `blast_fragmentation` | `beam` | `high` | `near_miss_0_35m` | `<component load rows>` | `<component probability residual>` | `not_run` |
| `VAL-003` | `F-16C_Block50` | `blast_fragmentation` | `beam` | `high` | `near_miss_0_35m` | `<uncertainty>` | `<coverage>` | `not_run` |

## 结果摘要

当前结果：无。所有表格项均为待填候选项，不构成验证结论。

| 输出 | 结论 | 证据引用 | 是否可授权 |
|---|---|---|---|
| `effect_scale` | `not_validated` | `<待填>` | 否 |
| `component_failure_probability` | `not_validated` | `<待填>` | 否 |
| `pk_authority` | `not_in_scope` | 无 | 否 |
| `deterministic_fuze_authority` | `deferred/out_of_scope` | 无 | 否 |

## 审阅与发布记录

| `review_id` | 审阅人 / 角色 | 日期 | 结论 | 必须整改项 |
|---|---|---|---|---|
| `REV-001` | `<待填>` | `<YYYY-MM-DD>` | `<reject/candidate/pass>` | `<RES-...>` |

## 当前判定

本报告模板当前判定为：`candidate / non-authoritative / not_run`。不得据此创建 authoritative descriptor，不得把 calibration 状态标为完成，不得放行 Pk 或 deterministic fuze。
