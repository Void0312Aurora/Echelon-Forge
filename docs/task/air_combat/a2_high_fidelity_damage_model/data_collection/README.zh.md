# A2 数据收集入口

状态：`2026-05-28` 数据收集与准入整理中。本文档只组织公开来源候选，不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

本目录承接 A2 高保真空战杀伤模型的外部公开数据收集工作。所有资料必须先以 source ledger 形式记录，经过 scope、来源层级、可公开性、交叉验证和 residual 风险审查后，才允许进入后续 `external_calibration_dataset` 或 `validated_physics_surrogate` 候选包。

## 准入规则

- [公开数据来源准入标准](../../../../standards/foundation/public_data_source_admission.zh.md)
- [A2 数据来源准入规则 - 2026-05-28](source_admission_rules_20260528.zh.md)

## 并行收集包

| 包 | 目标 | 当前状态 | 预期产物 |
|---|---|---|---|
| `f16c_block50_target_geometry` | F-16C Block 50 公开目标几何、组件位置和材料/装甲缺口 | recovered | `README.zh.md`、`source_ledger.zh.md` |
| `aim120c_warhead_fuze` | AIM-120C-class 公开战斗部/引信候选来源和通用 blast-fragmentation 方法入口 | recovered | `README.zh.md`、`source_ledger.zh.md` |
| `mechanism_model_public_methods` | 公开爆轰、破片、穿透、连续杆机制模型来源 | recovered | `README.zh.md`、`source_ledger.zh.md` |
| `component_fragility_vulnerability` | 公开组件脆弱性、失效概率、杀伤评估方法来源和拒绝清单 | recovered | `README.zh.md`、`source_ledger.zh.md` |
| `guidance_miss_distance_public_methods` | PN/APN、miss-distance、终端规避、seeker/noise 公开方法来源 | recovered | `README.zh.md`、`source_ledger.zh.md` |
| `f16c_material_fuel_fire_systems` | F-16C Block 50 材料、燃油、火灾、结构后果和系统依赖公开方法来源 | recovered | `README.zh.md`、`source_ledger.zh.md` |
| `vps_blast_fragmentation_methods` | 首个 blast-fragmentation mechanism-load surrogate 的公开方法和 benchmark 候选 | recovered | `README.zh.md`、`source_ledger.zh.md`、`benchmark_candidate_matrix.zh.md` |
| `component_fragility_benchmark_methods` | 组件失效/脆弱性 benchmark、schema mapping 和验证方法来源 | recovered | `README.zh.md`、`source_ledger.zh.md`、`schema_mapping_notes.zh.md` |
| `guidance_evasion_benchmark_methods` | guidance、miss-distance、terminal evasion、seeker/filter benchmark 方法续收集 | recovered | `README.zh.md`、`source_ledger.zh.md`、`benchmark_matrix.zh.md` |

## Gate 映射

- [A2 数据候选到 Evidence Gate 映射 - 2026-05-28](gate_mapping_20260528.zh.md)
- [A2 数据收集回收与准入审计 - 2026-05-28](recovery_admission_audit_20260528.zh.md)

## 回收判定

每个包回收时必须给出：

- `candidate`：可进入 A2 source ledger 的公开来源；
- `sanity_check_only`：只能用于量级交叉验证的来源；
- `rejected`：因 scope 不匹配、来源不稳定、权利不清、质量风险或敏感性而拒绝的来源；
- `residual`：即使采纳候选来源后仍无法关闭的真实性缺口。

当前所有收集包默认 `non-authoritative`。在缺少完整 validation manifest、验证报告和 residual closeout 前，不得把任何来源写成 calibrated vulnerability/Pk 或 deterministic fuze 权威。
