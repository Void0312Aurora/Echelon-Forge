# A2 validated_physics_surrogate 候选包总说明

状态：`2026-06-01 / G2 candidate package accepted_non_authoritative`。本文档定义第一份
`validated_physics_surrogate` 候选包的整理范围、交付物和禁用边界；它不是 vulnerability
evidence descriptor，不是校准数据，不应被默认运行时加载，也不授予 Pk 或
deterministic-fuze authority。

候选包 ID：`a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0`

G2 收尾口径：本候选包已作为 `A2 blastfrag candidate evidence package acceptance`
的非权威候选包通过当前验收。该结论只说明 retained artifacts、source admission、
candidate bundle、runtime-aligned exercise 和 fail-closed residual 状态可审阅、可复现；
不允许把本包写成 release-grade descriptor、stock runtime authority、Pk 或 deterministic
fuze closeout。

当前默认数据路线是 research / candidate profile：底层数据可以来自公开、第三方、社区或
derived estimate，但必须可替换、可扩展、可追溯，并保留 source tier、uncertainty、
confidence 和 residual。详见
[../../research_candidate_data_policy_20260601.zh.md](../../research_candidate_data_policy_20260601.zh.md)。

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

- [source_ledger.zh.md](source_ledger.zh.md)：本候选包的 package-level 来源台账，聚合 target geometry、warhead/fuze、mechanism-load、fragility benchmark 和 standards 控制文档，不授予 authority。
- [surrogate_model_card.zh.md](surrogate_model_card.zh.md)：本候选包当前 runtime-aligned engineering surrogate 的实际 model card，记录输入、输出、假设、限制和 evidence gate 关系。
- [validation_report_draft.zh.md](validation_report_draft.zh.md)：本候选包当前的验证报告草案，固化 benchmark、metrics、审阅和 `not_run` / non-authoritative 边界。
- [validation_manifest_draft_blastfrag_20260528.zh.md](validation_manifest_draft_blastfrag_20260528.zh.md)：把 blast-fragmentation 公开方法收集包映射到首个 `not_run` validation manifest 草案。
- [validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md)：本候选包当前冻结的 validation metrics 与 acceptance criteria artifact。它只服务于 Stage B `effect_scale` 候选评审，不放行 stock authority，也不把 Stage C `component_failure_probability` 混入同一轮验收。
- [validation_metrics_and_acceptance_criteria_stage_c_component_probability_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_c_component_probability_20260530.zh.md)：本候选包当前冻结的 Stage C component-specific probability candidate metrics 与 acceptance criteria artifact。它把 Stage C 的最小 candidate hygiene 门槛冻结下来，但仍不是 fragility validation result。
- [validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md](validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md)：本候选包当前冻结的 scope / bucket / independence manifest。它把 `beam / high / near_miss_0_35m` 的候选边界和 benchmark/input separation 写清楚，但不等于这些边界已经通过执行验证。
- [validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md](validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md)：本候选包当前第一版 scope boundary probe 结果表。它证明边界 probe 已可执行，但仍保持 candidate / non-authoritative。
- [validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md](validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md)：本候选包当前第一版 fixed-seed Stage B benchmark snapshot。它把 frozen hard gates 对应的当前候选结果表固化下来，但仍不是独立 validation result。
- [validation_benchmark_snapshot_stage_c_component_probability_20260530.zh.md](validation_benchmark_snapshot_stage_c_component_probability_20260530.zh.md)：本候选包当前第一版 Stage C component-specific probability snapshot。它把当前 runtime-aligned Stage C candidate surface 固化成 author-side artifact，但仍不是独立 validation result，也不是 stock authority。
- [validation_result_pack_stage_c_component_probability_20260530.zh.md](validation_result_pack_stage_c_component_probability_20260530.zh.md)：本候选包当前第一版 Stage C component-specific probability result pack。它把 runtime-aligned authority exercise 和 Stage C snapshot 汇总成统一候选结果包，但仍不是独立 fragility validation result。
- [validation_retained_artifact_pack_stage_c_component_probability_20260530.zh.md](validation_retained_artifact_pack_stage_c_component_probability_20260530.zh.md)：本候选包当前第一版 Stage C retained artifact pack 说明。它把 runtime-aligned authority exercise、Stage C snapshot 和 result pack 固化到 repo 内 canonical JSON 目录，但仍只是 author-side candidate retained chain。
- [validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md](validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md)：本候选包当前第一版 Stage C review-readiness gate。它把“为什么已经进入 author-side candidate review、但仍不能放行 component probability authority”机器化固定下来。
- [validation_provenance_and_identity_gate_20260530.zh.md](validation_provenance_and_identity_gate_20260530.zh.md)：本候选包当前第一版 shared provenance / surrogate identity gate。它把 `RES-001/002` 的共享阻塞面单独收口成 package-level artifact，供 Stage B 与 Stage C 共用。
- [validation_result_pack_stage_b_effect_scale_20260530.zh.md](validation_result_pack_stage_b_effect_scale_20260530.zh.md)：本候选包当前第一版统一 Stage B result pack。它把 scaffold、scope probe 和 Stage B snapshot 汇总为一个带 content hash 与 independence audit 的候选结果包，但仍不是独立 validation result。
- [validation_retained_artifact_pack_stage_b_effect_scale_20260530.zh.md](validation_retained_artifact_pack_stage_b_effect_scale_20260530.zh.md)：本候选包当前第一版 Stage B retained artifact pack 说明。它把 repo 内 canonical author-side retained JSON 入口固定下来，供 surrogate identity 与 release-readiness audit 引用，但仍不是 release-grade identity。
- [validation_release_readiness_gate_stage_b_effect_scale_20260530.zh.md](validation_release_readiness_gate_stage_b_effect_scale_20260530.zh.md)：本候选包当前第一版 Stage B release readiness gate。它明确指出当前为什么仍 blocked，而不是让 author-side hard-gate pass 被误读成 ready to release。
- [validation_review_readiness_record_stage_b_effect_scale_20260530.zh.md](validation_review_readiness_record_stage_b_effect_scale_20260530.zh.md)：本候选包当前 author-side review readiness 记录。它汇总可供审阅的 artifacts、当前允许的结论和仍必须保持 open 的 residual。
- [artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md](artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md)：本候选包当前 Stage B 真正引用或拒绝的 artifact pin 清单。它明确哪些是 acquired candidate、哪些只是 sanity/pending/rejected。
- [surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md](surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md)：本候选包当前 Stage B surrogate 的 author-side 身份快照。它固定代码、输入、命令和当前 retained artifact pack 锚点，但不构成 release-grade validation identity。
- [target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md](target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md)：本候选包当前 Stage B 使用的目标几何假设表。它明确哪些几何只够支撑 beam witness bookkeeping，哪些 claim 仍被禁止。
- [warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md](warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md)：本候选包当前 Stage B 使用的战斗部 scope / sensitivity 假设表。它明确 family label、repo toy proxy、third-party sanity 和 rejected data 的边界。
- [residual_register.zh.md](residual_register.zh.md)：候选残差与阻塞项登记表；当前已按 research profile 收口为 `research_closed_authority_retained`，future authority 阻塞继续保留。
- `tools/maintenance/a2_blastfrag_validation_scaffold.py`：首个可执行的 non-authoritative blast-fragmentation validation scaffold。它输出 fixed-seed toy benchmark、mechanism-load vector，以及与 `a2.vulnerability_evidence.v1` 对齐的 non-authoritative row draft；该 row draft 只保留 gate 字段，不创建 runtime descriptor，不授予 `effect_scale`、`component_failure_probability`、`Pk` 或 `deterministic_fuze` authority。
- 上述 scaffold 当前已覆盖 `BFM-BM-001..006` 的可执行脚手架层：其中 `BFM-BM-002` 提供非型号化的 Mott/Gurney fragment mass/velocity/energy toy benchmark，`BFM-BM-004` 提供 penetration-margin / domain-rejection toy benchmark，二者都只服务于 candidate validation planning，不构成运行时 authority。
- `tools/maintenance/a2_blastfrag_stage_b_effect_scale_snapshot.py`：把 Stage B `effect_scale` frozen hard gates 对应的当前 fixed-seed scaffold 结果固化成 machine-readable snapshot，用于 review 和 residual 审计；它不会创建 runtime descriptor，也不会绕过独立 review。
- `tests/architecture/damage_model/test_candidate_artifact_contracts.py`：固定上述 Stage B snapshot 的 artifact 形状、hard-gate pass 记录和 non-authoritative 边界。
- `tools/maintenance/a2_blastfrag_stage_c_component_probability_result_pack.py`：把 runtime-aligned authority exercise 与 Stage C snapshot 汇总成统一的 candidate result pack，并固定 content hash 与 independence audit 语义；它不会把 author-side component probability 结果包提升成 authority。
- `tests/architecture/damage_model/test_component_probability_artifacts.py`：固定 Stage C snapshot 与 result pack 的 artifact 形状、component provenance / gate-band 检查和 non-authoritative 边界。
- `tools/maintenance/a2_blastfrag_stage_c_component_probability_retained_artifact_pack.py`：把 runtime-aligned authority exercise、Stage C snapshot 与 Stage C result pack 固化到 repo 内 canonical retained JSON 目录，并明确 test-local / candidate / non-authoritative 起源边界；它不会把 retained chain 提升成 authority。
- `tests/architecture/damage_model/test_component_probability_artifacts.py`：固定上述 Stage C retained pack 的 manifest 形状、artifact inventory 和 non-authoritative 边界。
- `tools/maintenance/a2_blastfrag_stage_c_component_probability_review_readiness_gate.py`：把 Stage C component-specific probability 当前为什么仍 blocked 机器化固定下来，并同时记录 upstream Stage B 依赖仍未收口；它不会把 author-side review gate 提升成 authority。
- `tests/architecture/damage_model/test_component_fragility_validation.py`：固定上述 Stage C review gate 的 artifact 形状、阻塞 residual 集和 non-authoritative 边界。
- `tools/maintenance/a2_blastfrag_package_provenance_identity_gate.py`：把 package-level provenance / surrogate identity 阻塞面收口成共享 gate，并显式承接 `RES-001/002` 的 author-side closeout surface；它不会把 retained chain 或 pin manifest 提升成 release-grade authority。
- `tests/architecture/damage_model/test_release_authority_guardrails.py`：固定上述 shared provenance / identity gate 的 artifact 形状、阻塞 residual 和 non-authoritative 边界。
- `tools/maintenance/a2_blastfrag_stage_c_component_probability_snapshot.py`：把当前 runtime-aligned Stage C component-specific probability candidate surface 固化成 machine-readable snapshot，用于把 test-local 演练推进到 package-level author-side artifact；它不会授予 stock authority，也不会关闭 fragility residual。
- `tests/architecture/damage_model/test_component_probability_artifacts.py`：固定上述 Stage C snapshot 的 artifact 形状、component provenance 检查和 non-authoritative 边界。
- `tools/maintenance/a2_blastfrag_stage_b_validation_result_pack.py`：把 scaffold、scope probe 和 Stage B snapshot 汇总为统一的 candidate result pack，并固定 content hash 与 independence audit 语义；它不会把 author-side 结果包提升成 authority。
- `tests/architecture/damage_model/test_candidate_artifact_contracts.py`：固定上述 result pack 的 artifact 形状、hash surface、scope audit 和 non-authoritative 边界。
- `tools/maintenance/a2_blastfrag_stage_b_retained_artifact_pack.py`：把当前 scaffold、scope probe、Stage B snapshot 和 result pack 固化到 repo 内 canonical retained JSON 目录，并提供 retained manifest 读取入口；它只保留 author-side candidate evidence，不授予 authority。
- `tests/architecture/damage_model/test_candidate_artifact_contracts.py`：固定上述 retained pack 的 manifest 形状、artifact inventory 和 non-authoritative 边界。
- `tools/maintenance/a2_blastfrag_stage_b_release_readiness_gate.py`：把当前 Stage B 候选包的 satisfied conditions 和 blocking conditions 固化成 release-readiness gate；它的职责是报告 blocked，而不是放行 authority。
- `tests/architecture/damage_model/test_release_authority_guardrails.py`：固定上述 readiness gate 的 blocked 决策、blocker surface 和 non-authoritative 边界。
- `tools/maintenance/a2_blastfrag_runtime_aligned_authority_pack.py`：把 Stage B / Stage C 的 runtime-aligned authority exercise 抽成独立 maintenance 工具。它先采样 stock `blast_fragmentation` 近失事件，再导出 baseline event summary、baseline component rows，以及仅限 `test_local_authority_exercise_only` 的 effect-scale / component-probability descriptor candidate；它不是 stock 数据库写入工具，不授予默认 authority。
- `tests/architecture/damage_model/test_candidate_artifact_contracts.py`：固定上述 authority exercise pack 的 package 边界、可复现性与 CLI 输出形状，防止 test-local 演练被误叙述成正式 candidate authority。
- `tools/maintenance/a2_candidate_vps_bundle.py`：把本目录文档、validation scaffold 和 runtime-aligned authority exercise 汇总成一个 package-level candidate bundle JSON，用于审阅、验收和后续 authority 评审；该 bundle 默认保持 `candidate_non_authoritative`。
- `tests/architecture/damage_model/test_candidate_artifact_contracts.py`：固定 candidate bundle 的边界、文档完备性、research / authority residual 分类和 CLI 输出形状，防止候选包再次退回模板状态。
- 当前 candidate bundle 还会汇总 acceptance criteria artifact 的状态、primary release scope 和 required benchmarks，防止 “criteria 已冻结” 与 “authority 已放行” 被混为一谈。
- 当前 candidate bundle 还会汇总 scope / independence manifest 的状态、boundary probes 和 out-of-scope labels，防止 “scope 已命名” 与 “scope 已验证” 被混为一谈。
- 当前 candidate bundle 还会汇总 scope boundary probe 的执行摘要，防止 “有 manifest” 与 “probe 已经跑过” 被混为一谈。
- 当前 candidate bundle 还会汇总 Stage B fixed-seed benchmark snapshot 与 author-side review readiness，防止 “当前 snapshot 通过 hard gates” 与 “independent validation 已完成” 被混为一谈。
- 当前 candidate bundle 还会汇总统一的 Stage B result pack，防止 “有几份 author-side snapshot” 与 “已经有 release-grade validation artifact pack” 被混为一谈。
- 当前 candidate bundle 还会汇总 Stage B retained artifact pack，防止 “有 repo 内 retained JSON” 与 “release-grade identity chain 已关闭” 被混为一谈。
- 当前 candidate bundle 还会汇总 Stage B release readiness gate，防止 “current author-side package is reviewable” 与 “current package is releasable” 被混为一谈。
- 当前 candidate bundle 还会汇总 Stage C candidate metrics、snapshot 和 result pack，但它们仍作为单独的 author-side Stage C 轨维护，防止在 Stage B release gate 尚 blocked 时把 component probability 提前混入同一轮 authority closeout。
- `tests/runtime/air_combat/weapon_guidance_realism/vulnerability_scaffold.py`：runtime 回归守卫。它伪造 aircraft JSON 指向上述 non-authoritative row draft，证明该草案即使被加载到 `EffectsEvent.vulnerability_evidence_*` 审计面，也仍保持 `evidence_dataset_valid=false` 且不会放行 `effect_scale_authority`、`component_failure_probability_authority`、`Pk` 或 `deterministic_fuze`。
- 同一回归文件还包含一个 test-local Stage B 演练：它先从 stock `blast_fragmentation` 近失事件采样 runtime mechanism-load，再构造一个 scope 对齐、manifest 完整、仅放行 `effect_scale_authority` 的 `validated_physics_surrogate` descriptor，证明 A2 候选包已经具备“从 scaffold 元数据到 row-backed effect-scale authority”的最小正向数据路径。该闭环仍只存在于测试临时数据库中，不修改默认 `examples/config/database` authority 状态。
- 同一回归文件现已补入 test-local Stage C 演练：运行时 broad near-miss 投影会为 `blast_fragmentation` 的被选中 hitbox 补一个 projected component 候选，因此该演练能够在原 `beam / high / near_miss` 子轴上，为 `right_aileron_actuator` 放行 component-specific `component_failure_probability_authority`，同时保留其他 projected components 的 synthetic probability。该闭环同样只存在于测试临时数据库中，不修改默认 `examples/config/database` authority 状态。

相关 data-collection 更新：

- [VPS validation gap update](../../data_collection/vps_blast_fragmentation_methods/validation_gap_update_20260528.zh.md)：记录 BFM-BM-001..006 的 `benchmark_design_reference` 充分性、artifact/hash/threshold 缺口和 rejected source guard。

相关 validation gate：

- [BFM-BM-006 Source Trace Manifest Gate](../../validation/bfm_bm_006_source_trace_manifest_gate_20260528.zh.md)：记录当前已实现的 source trace / rights / authority 行政准入门禁。

推荐命令：

```bash
python3 tools/maintenance/a2_blastfrag_validation_scaffold.py
python3 tools/maintenance/a2_blastfrag_validation_scaffold.py --output /tmp/a2_blastfrag_scaffold.json
python3 tools/maintenance/a2_blastfrag_scope_boundary_probe.py
python3 tools/maintenance/a2_blastfrag_scope_boundary_probe.py --output /tmp/a2_scope_boundary_probe.json
python3 tools/maintenance/a2_blastfrag_stage_b_effect_scale_snapshot.py
python3 tools/maintenance/a2_blastfrag_stage_b_effect_scale_snapshot.py --output /tmp/a2_stage_b_effect_scale_snapshot.json
python3 tools/maintenance/a2_blastfrag_stage_c_component_probability_snapshot.py
python3 tools/maintenance/a2_blastfrag_stage_c_component_probability_result_pack.py
python3 tools/maintenance/a2_blastfrag_stage_b_validation_result_pack.py
python3 tools/maintenance/a2_blastfrag_stage_b_validation_result_pack.py --output /tmp/a2_stage_b_validation_result_pack.json
python3 tools/maintenance/a2_blastfrag_stage_b_retained_artifact_pack.py
python3 tools/maintenance/a2_blastfrag_stage_b_release_readiness_gate.py
python3 tools/maintenance/a2_blastfrag_stage_b_release_readiness_gate.py --output /tmp/a2_stage_b_release_readiness_gate.json
python3 tools/maintenance/a2_blastfrag_runtime_aligned_authority_pack.py
python3 tools/maintenance/a2_blastfrag_runtime_aligned_authority_pack.py --output /tmp/a2_blastfrag_runtime_aligned_authority_pack.json
python3 tools/maintenance/a2_candidate_vps_bundle.py
python3 tools/maintenance/a2_candidate_vps_bundle.py --output /tmp/a2_candidate_vps_bundle.json
python3 -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
python3 -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
python3 -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
python3 -m pytest -q tests/architecture/damage_model/test_component_probability_artifacts.py
python3 -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
python3 -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
python3 -m pytest -q tests/architecture/damage_model/test_release_authority_guardrails.py
python3 -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
python3 -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
python3 -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k scaffold
```

## 使用规则

1. source ledger 只能记录来源和保留指针；来源存在本身不构成校准或授权。
2. model card 可以描述候选 surrogate 的物理假设和输出形状，但不得写成已通过验证。
3. validation report 在没有完整 benchmark、metrics、criteria、sha256 和审阅记录前，必须保持未通过状态。
4. residual register 中任何 authority-retained 阻塞项未关闭时，不得生成可被运行时消费的 authoritative descriptor。
5. 生成实验输出或大体量数据时，按 `reference_artifacts.md` 的保留边界记录稳定入口、摘要和外部保留位置，不把易清理的工作区输出当作 canonical source of truth。

## 参考

- [A2 Vulnerability Evidence Schema v1](../../vulnerability_evidence_schema_v1.zh.md)
- [Reference Artifacts](../../../../../reference_artifacts.md)
