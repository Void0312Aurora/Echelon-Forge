# Source Ledger

状态：`candidate / non-authoritative / package-level aggregation`。  
本文档把本候选包真正依赖的公开来源组、内部生成工具和拒绝边界收束到同一处，供后续 `validated_physics_surrogate` 评审使用。它不是 runtime descriptor，不是校准证据，不授予 `Pk`、`deterministic_fuze`、`effect_scale` 或 `component_failure_probability` authority。

候选 scope 固定为：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。

## Package 补充引用

- artifact/pin 清单： [artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md](artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md)
- surrogate 身份清单： [surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md](surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md)
- target geometry 假设： [target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md](target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md)
- warhead scope 假设： [warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md](warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md)

## 使用边界

- 这里只记录稳定 `source_ref`、聚合 provenance、权利和 scope 匹配，不复制受限正文、表格或数据。
- package-level 行只证明“本候选包依赖了哪些已登记来源组”，不意味着这些来源已经关闭 residual。
- 任何 `third_party_candidate`、`community_sanity_check`、`open_source_config_candidate` 只允许停留在候选或 sanity-check 层，不能直接变成 runtime authority。
- `validation_artifact_ref`、benchmark 计划、runtime 演练工具和 test-local descriptor 只是候选链条的一部分，不能单独授权。

## 来源台账

| `source_id` | 来源类别 | `source_ref` | 稳定定位 / checksum | 证据角色 | scope 匹配 | 可公开性 / 权利 | ingest 状态 | authority 状态 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| `SRC-PKG-001` | package source ledger | [f16c_block50_target_geometry/source_ledger.zh.md](../../data_collection/f16c_block50_target_geometry/source_ledger.zh.md)；关键来源组：`F16-TG-SRC-001/002/004/005/012` | 以仓库文档路径为稳定入口；外部 checksum 仍在各子账本后续补齐 | `target_geometry`、`material_gap`、`component_layout` | `partial`：支持 F-16C 外形、发动机/radar family 和代表性组件存在性，不支持真实装甲或内部舱段真值 | public / cite-only / repo-authored scaffold mix | `acquired_as_candidate_group` | `non-authoritative` | 支撑候选包的目标几何与组件布局假设；`RES-003` 保持 open |
| `SRC-PKG-002` | package source ledger | [aim120c_warhead_fuze/source_ledger.zh.md](../../data_collection/aim120c_warhead_fuze/source_ledger.zh.md)；关键来源组：`AIM120-WF-002/006/007`、`PHYS-BF-001/002/006/013/014/015` | 以仓库文档路径为稳定入口；DENIX / DTIC artifact hash 仍 pending | `warhead_model`、`fuze_evidence`、`mechanism_load` | `partial`：支持 AMRAAM 系列 envelope、blast-fragmentation family 和公开术语，不支持 AIM-120C 真实战斗部/引信门限 | public / cite-only / pending official artifact mix | `acquired_as_candidate_group` | `non-authoritative` | 支撑 family-level blast-fragmentation 候选，不关闭 `RES-004`、`RES-014` |
| `SRC-PKG-003` | package source ledger | [vps_blast_fragmentation_methods/source_ledger.zh.md](../../data_collection/vps_blast_fragmentation_methods/source_ledger.zh.md)；关键来源组：`VPS-BFM-001/002/006/010/011/013/014/015` | 以仓库文档路径为稳定入口；待补 official artifact sha256 的条目维持 pending | `mechanism_load`、`validation_criteria`、`reproducibility` | `partial`：支持公开 blast/fragment/penetration/sampling 方法，不支持型号级真值 | public / cite-only / pending official artifact mix | `acquired_as_candidate_group` | `non-authoritative` | 是当前候选 VPS 的方法骨架；`RES-005`、`RES-006`、`RES-007`、`RES-010`、`RES-011`、`RES-012` 保持 open |
| `SRC-PKG-004` | package source ledger | [component_fragility_benchmark_methods/source_ledger.zh.md](../../data_collection/component_fragility_benchmark_methods/source_ledger.zh.md)；关键来源组：`CFBM-FOI-001`、`CFBM-LFTE-001/002/003`、`CFBM-MSVV-001/002`、`CFBM-PAPER-001/002/003/004` | 以仓库文档路径为稳定入口；部分 NASA/ASSIST hash 待补 | `component_fragility`、`validation_criteria`、`redundancy_dependency_validation` | `partial`：支持 component kill criteria、M&S credibility 和 dependency/redundancy 逻辑，不支持 F-16C 真实组件概率 | public / cite-only / open-access mix | `acquired_as_candidate_group` | `non-authoritative` | 为未来 `component_failure_probability_authority` 提供方法语境，但 `RES-009` 仍 open |
| `SRC-PKG-005` | reproducibility / internal tooling | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts validation-scaffold` / `runtime-authority-exercise` | 仓库稳定路径；由测试固定输出形状和固定种子复现 | `benchmark_dataset`、`reproducibility` | `full` for current candidate packaging surface，`partial` for physics truth | repo-authored engineering tooling | `acquired_as_internal_candidate_tooling` | `non-authoritative` | 只生成 non-authoritative scaffold 与 test-local authority exercise，不能上卷成 stock authority |
| `SRC-PKG-006` | public policy / source-admission controls | [source_admission_rules_20260528.zh.md](../../data_collection/source_admission_rules_20260528.zh.md)、[vulnerability_evidence_schema_v1.zh.md](../../vulnerability_evidence_schema_v1.zh.md)、[gradient_realism_principles.zh.md](../../../../../standards/foundation/gradient_realism_principles.zh.md) | 仓库文档路径稳定 | `validation_criteria`、`residual_register` | `full` for authority boundary, `not_numeric` | repo-authored standards docs | `acquired_as_control_docs` | `non-authoritative` | 固定“可以说到哪一层”，防止局部 row-backed authority 上卷成 full `G6` 或 `Pk` |

## 证据角色枚举

| 角色 | 说明 | 当前可授权 |
|---|---|---|
| `target_geometry` | F-16C Block 50 外形、组件位置、遮挡或暴露面积来源 | 否 |
| `warhead_model` | AIM-120C-class blast-fragmentation family envelope 和公开术语来源 | 否 |
| `mechanism_load` | 破片能量、面密度、穿透裕度、blast scaled distance 等公开方法来源 | 否 |
| `component_fragility` | component kill criteria、dependency/redundancy、后果逻辑来源 | 否 |
| `benchmark_dataset` | 候选 benchmark 生成工具与 future public benchmark route | 否 |
| `validation_criteria` | scope gate、admission rule、M&S credibility 和 benchmark acceptance 口径 | 否 |
| `reproducibility` | 固定种子、代码路径、artifact shape 和后续 checksum 规划 | 否 |

## 来源验收检查

| 检查项 | 状态 | 备注 |
|---|---|---|
| `source_ref` 非空且稳定 | `pass` | package-level 行均指向仓库内稳定文档或工具入口 |
| provenance 能说明数据来源、处理链和保留边界 | `pass` | 每行都明确了其角色与 residual |
| 与候选 scope 的匹配轴逐项记录 | `pass` | 明确区分 `full`、`partial` 和 `not_numeric` |
| 权利和再分发限制明确 | `partial-pass` | group-level 已说明；子账本中的 external artifact checksum 仍有 pending 项 |
| benchmark 与 model-input 来源分离 | `partial-pass` | 已在组层面分离 method/source 与 candidate tooling；独立 benchmark residual 仍 open |
| checksum / manifest / 版本号可复现 | `partial-pass` | repo 工具可复现；部分 external artifact 尚未固定 sha256 |
| 不把 `validation_artifact_ref` 单独当作授权依据 | `pass` | candidate tooling 与 draft manifest 均保持 non-authoritative |

## 拒绝 / 排除记录

| `rejection_id` | 来源 | 排除原因 | 影响的 residual | 备注 |
|---|---|---|---|---|
| `REJ-PKG-001` | 任何 FOUO/CUI/ITAR/EAR、不可再分发、未授权镜像或泄漏的 aircraft / missile / fuze / vulnerability 材料 | rights/provenance blocked | `RES-001`, `RES-004`, `RES-014` | 仅保留拒绝类别，不入 candidate bundle |
| `REJ-PKG-002` | CMO/CMANO、DCS、War Thunder、论坛表格、民间 missile DB 单点值 | `third_party_candidate` 不能直接进 runtime row | `RES-004`, `RES-009`, `RES-013`, `RES-014` | 最多做 community sanity check，不得写 authority row |
| `REJ-PKG-003` | `UFC 3-340-01` 与其他被官方限制公开分发的 conventional-weapons 文档 | official restricted distribution | `RES-001`, `RES-006` | 只保留官方拒绝说明，不使用非官方镜像 |
