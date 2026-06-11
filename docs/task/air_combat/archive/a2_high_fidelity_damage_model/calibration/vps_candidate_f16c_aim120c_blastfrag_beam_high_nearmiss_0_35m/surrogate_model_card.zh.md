# Surrogate Model Card

状态：`candidate / non-authoritative / runtime-aligned engineering surrogate`。  
本文档描述当前候选 physics surrogate 的实际组成、输入、输出和限制。它不声称模型已校准，不允许被用作 `Pk`、`deterministic fuze`、`effect_scale` 或 `component_failure_probability` authority。

候选 scope 固定为：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。

## 模型元数据

| 字段 | 值 |
|---|---|
| `model_ref` | `candidate://a2/runtime-aligned-vps/f16c-aim120c-blastfrag-beam-high-nearmiss-0_35m-v0` |
| `model_version` | `v0_candidate_runtime_aligned` |
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `model_owner` | `CMO A2 workspace` |
| `code_ref` | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts validation-scaffold` / `runtime-authority-exercise`, [default_effects_model.cpp](../../../../../../src/models/weapons/default_effects_model.cpp) |
| `run_manifest_ref` | [surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md](surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md) |
| `code_version_ref` | [surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md](surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md) |
| `input_snapshot_ref` | [surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md](surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md) |
| `candidate_bundle_ref` | [validation_report_draft.zh.md](validation_report_draft.zh.md) |
| `random_seed_policy` | `fixed-seed for scaffold and runtime-aligned exercise; not yet multi-seed validated` |
| `current_validation_status` | `not_validated` |

## 允许描述的用途

- 为后续 `a2.vulnerability_surrogate_validation.v1` 验证报告提供模型说明。
- 在候选范围内描述当前已经能导出的 mechanism-load vector、effect-scale row gate 和 component-specific probability row gate。
- 帮助 reviewer 判断当前 runtime-aligned 演练与 future stock authority 之间还差哪些 residual。

## 明确非用途

- 不作为 `AircraftVulnerabilityProfile` 的 calibrated evidence。
- 不作为默认可被 runtime 加载并放权的 vulnerability evidence descriptor。
- 不输出或授权 `Pk` 曲线。
- 不替代 live fuze trigger、fuze reliability、target signature 或 kill-chain 验证。
- 不放行 deterministic fuze；当前 `deterministic_fuze_authority` 必须保持 `false`。

## 输入定义

| 输入 | 单位 / 类型 | 来源 | 必填 | 备注 |
|---|---|---|---|---|
| target geometry | `repo-authored hitbox/component table` | `SRC-PKG-001` | 是 | 当前锚定 `F-16C_Block50`；只证明代表性组件和局部几何路径存在 |
| detonation geometry | `body-frame local point + miss-distance bucket` | `SRC-PKG-003`, `SRC-PKG-005` | 是 | 当前固定 `beam` 与 `near_miss_0_35m` 候选子轴 |
| closure state | `bucket + runtime closure proxy` | `SRC-PKG-003`, `SRC-PKG-005` | 是 | 当前只覆盖 `high`；边界仍在 `RES-008` |
| warhead class | `AIM-120C-class / blast_fragmentation` | `SRC-PKG-002` | 是 | 只允许 family-level 假设，不暗示真实 C 型战斗部已知 |
| material / component assumptions | `engineering thresholds + public-method residuals` | `SRC-PKG-001`, `SRC-PKG-004` | 是 | 所有 fragility 与 dependency 仍需受 residual 管束 |
| solver / surrogate parameters | `fixed-seed scaffold + runtime-aligned event sampling` | `SRC-PKG-005` | 是 | 当前可复现但未完成独立 benchmark/uncertainty coverage |

## 输出定义

| 输出 | 目标 schema 对应 | 当前状态 | 授权状态 |
|---|---|---|---|
| candidate `effect_scale` | vulnerability evidence row 可选字段 | `test-local runtime exercise available; stock authority not granted` | `non-authoritative outside test-local exercise` |
| candidate `component_failure_probability` | vulnerability evidence row 可选字段 | `test-local runtime exercise available for right_aileron_actuator` | `non-authoritative outside test-local exercise` |
| mechanism-load intervals | row `min_*` / `max_*` 适用门槛 | `available as scaffold/runtime-aligned gate candidates` | `non-authoritative` |
| uncertainty summary | validation report 指标输入 | `not_run` | `non-authoritative` |
| Pk | 不在本 model card 授权 | `not_output` | `false` |
| deterministic fuze decision | 不在本 model card 授权 | `not_output` | `false` |

## 物理和工程假设

| `assumption_id` | 假设 | 来源 | 影响 | residual |
|---|---|---|---|---|
| `ASM-001` | `blast` / `fragmentation` / `blast_fragmentation` 的 near-miss 先按 hitbox 投影，再为 broad near-miss 选一个最佳 projected component 候选进入 component rows | `SRC-PKG-005` | 决定当前 effect-scale 和 component-probability row 的 runtime-aligned 入口形状 | `RES-005`, `RES-006`, `RES-007` |
| `ASM-002` | event-level `vulnerability_effect_scale` 使用聚合 mechanism-load gate，而 component probability 使用 projected component mechanism-load gate | `SRC-PKG-005` | 保持 global effect-scale 与 component-specific probability 分层，不把二者混成同一 authority | `RES-006`, `RES-009` |
| `ASM-003` | target geometry、component layout、dependency graph 与 threshold scale 当前仍主要是 engineering scaffold，而非官方 vulnerability 数据库 | `SRC-PKG-001`, `SRC-PKG-004` | 限制了 component fragility 与 platform consequence 的外推范围 | `RES-003`, `RES-009` |
| `ASM-004` | candidate surrogate 目前只覆盖 `beam / high / near_miss_0_35m` 子域，不自动外推到其他 aspect/closure/miss-distance bucket | `SRC-PKG-003`, `SRC-PKG-006` | 限制了当前一切 row-backed authority 演练的声明边界 | `RES-007`, `RES-008` |

当前 Stage B 相关补充约束见：

- [target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md](target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md)
- [warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md](warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md)

## 与 A2 evidence gate 的关系

未来如需把本候选包整理为 descriptor，必须先由验证报告证明以下字段完整、稳定且 scope 匹配：

| schema 字段 | 当前候选值 |
|---|---|
| `source_kind` | future intent 为 `validated_physics_surrogate`；当前不创建 stock authoritative descriptor |
| `source_ref` | [source_ledger.zh.md](source_ledger.zh.md) + future candidate bundle artifact |
| `validation_artifact_ref` | current draft only; 单独不授权 |
| `calibration_status` | `unvalidated` |
| `validation_manifest.schema_version` | `a2.vulnerability_surrogate_validation.v1` |
| `validation_manifest.validation_status` | `not_run`，不是 `validated` 或 `passed` |
| `validation_manifest.validation_scope` | 必须逐项等于本候选 scope |
| `pk_authority` | `false` |
| `deterministic_fuze_authority` | `false` |

## 已知限制

- 模型是否能代表真实 `AIM-120C-class blast_fragmentation` 效应尚未验证。
- F-16C Block 50 组件几何、材料、遮挡和 fragility 仍受 `RES-003` 与 `RES-009` 约束，不能被工程直觉补成权威。
- `near_miss_0_35m` 与 `beam/high` 的覆盖还没有完成 bucket 内 benchmark；单一 runtime-aligned 事件不能代表整个桶。
- 当前随机性与模型误差尚未做 multi-seed / uncertainty coverage 报告。
- 所有限制在 [residual_register.zh.md](residual_register.zh.md) 中保持 open，直到有独立审计记录关闭。
