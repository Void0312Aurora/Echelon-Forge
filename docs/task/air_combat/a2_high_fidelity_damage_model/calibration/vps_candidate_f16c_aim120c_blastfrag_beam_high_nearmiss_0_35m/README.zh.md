# A2 validated_physics_surrogate 候选包总说明

状态：`2026-05-28` 非权威 candidate 文档脚手架。本文档只定义第一份 `validated_physics_surrogate` 候选包的整理范围、交付物和禁用边界；它不是 vulnerability evidence descriptor，不是校准数据，不应被运行时加载，也不授予 Pk 或 deterministic-fuze authority。

候选包 ID：`a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0`

## 候选 Scope

| 轴 | 值 |
|---|---|
| `target_type` | `F-16C_Block50` |
| weapon class | `AIM-120C-class` |
| `weapon_family` | `blast_fragmentation` |
| `aspect_bucket` | `beam` |
| `closure_bucket` | `high` |
| `miss_distance_bucket` | `near_miss_0_35m` |
| candidate source line | `validated_physics_surrogate` 候选；当前不满足 authority gate |
| validation schema target | `a2.vulnerability_surrogate_validation.v1` 的未来验证产物 |

`near_miss_0_35m` 是候选证据桶名，不代表当前仓库已有 0-0.35 m 近失验证结果。任何超出上表的目标、武器族、姿态、闭合速度或 miss-distance 桶，都必须另建候选包。

## 当前 Authority 边界

本候选包必须保持以下姿态，直到另有完整、可审计的验证产物和独立评审：

| 字段 | 当前值 |
|---|---|
| `calibration_status` | `unvalidated` |
| `effect_scale_authority` | `false` |
| `component_failure_probability_authority` | `false` |
| `pk_authority` | `false` |
| `deterministic_fuze_authority` | `false` |
| runtime descriptor status | 不创建、不加载、不消费 |

即使后续模型被整理为 `validated_physics_surrogate` 来源，仍必须满足 `vulnerability_evidence_schema_v1.zh.md` 中的 descriptor gate、完整 `validation_manifest`、scope 逐项匹配、非空 `source_ref` / `provenance`、验证 artifact 摘要和验收指标要求，才允许讨论 effect-scale 或 component-failure probability 的有限授权。Pk 与 deterministic fuze 不由本候选包放行。

## 本目录交付物

- [source_ledger_template.zh.md](source_ledger_template.zh.md)：来源台账模板，记录可追溯引用、保留边界、许可证和 scope 覆盖，不授予 authority。
- [surrogate_model_card_template.zh.md](surrogate_model_card_template.zh.md)：surrogate model card 模板，记录模型版本、输入输出、假设、限制和非用途。
- [validation_report_template.zh.md](validation_report_template.zh.md)：验证报告模板，预留 `a2.vulnerability_surrogate_validation.v1` manifest 字段和指标表，但默认 `not_run` / non-authoritative。
- [validation_manifest_draft_blastfrag_20260528.zh.md](validation_manifest_draft_blastfrag_20260528.zh.md)：把 blast-fragmentation 公开方法收集包映射到首个 `not_run` validation manifest 草案。
- [residual_register.zh.md](residual_register.zh.md)：候选残差与阻塞项登记表，初始条目全部保持 open。

相关 data-collection 更新：

- [VPS validation gap update](../../data_collection/vps_blast_fragmentation_methods/validation_gap_update_20260528.zh.md)：记录 BFM-BM-001..006 的 `benchmark_design_reference` 充分性、artifact/hash/threshold 缺口和 rejected source guard。

相关 validation gate：

- [BFM-BM-006 Source Trace Manifest Gate](../../validation/bfm_bm_006_source_trace_manifest_gate_20260528.zh.md)：记录当前已实现的 source trace / rights / authority 行政准入门禁。

## 使用规则

1. source ledger 只能记录来源和保留指针；来源存在本身不构成校准或授权。
2. model card 可以描述候选 surrogate 的物理假设和输出形状，但不得写成已通过验证。
3. validation report 在没有完整 benchmark、metrics、criteria、sha256 和审阅记录前，必须保持未通过状态。
4. residual register 中任何阻塞项未关闭时，不得生成可被运行时消费的 authoritative descriptor。
5. 生成实验输出或大体量数据时，按 `reference_artifacts.md` 的保留边界记录稳定入口、摘要和外部保留位置，不把易清理的工作区输出当作 canonical source of truth。

## 参考

- [A2 Vulnerability Evidence Schema v1](../../vulnerability_evidence_schema_v1.zh.md)
- [Reference Artifacts](../../../../../reference_artifacts.md)
