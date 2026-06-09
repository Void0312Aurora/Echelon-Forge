# WP7 后端能力物化验收审查

状态：`2026-05-19` 已作为文档与实现准备线验收。

语言版本：

- 英文主文：[wp7_backend_capability_materialization_acceptance_review_20260519.md](wp7_backend_capability_materialization_acceptance_review_20260519.md)
- 中文辅文：`wp7_backend_capability_materialization_acceptance_review_20260519.zh.md`

审查输入：

- [WP7 后端能力物化](../simulation_architecture/backend_capability_materialization_wp7_20260519.zh.md)
- [WP7-A registry materialization 笔记](../simulation_architecture/wp7_registry_materialization_notes_20260519.zh.md)
- [WP7-B runtime capability projection 笔记](../simulation_architecture/wp7_runtime_capability_projection_notes_20260519.zh.md)
- [WP7-C promotion evidence gates 笔记](../simulation_architecture/wp7_promotion_evidence_gates_notes_20260519.zh.md)
- [WP7-D multi-fidelity entry conditions 笔记](../simulation_architecture/wp7_multifidelity_entry_conditions_notes_20260519.zh.md)
- [WP7-E integration and index sync 任务簇](../simulation_architecture/wp7_integration_and_index_sync_cluster_20260519.zh.md)

## 1. 审查结论

WP7 Backend Capability Materialization 已作为文档与实现准备线验收。

本次验收不晋级任何后端能力。当前维护中 support 仍为：

```yaml
supports_gpu_visual: false
supports_gpu_observation: false
supports_gpu_flight_shaping: false
supports_device_observation_view: false
supports_resident_state: false
supports_exact_gpu_backend: false
supports_shadow_compare: false
```

唯一已验收的维护中基线仍是 `cpu_exact.reference`。既有 batch runtime、
compiled episode controller 与 compiled execution step 等 facade/runtime
surface 仍与 GPU、resident-state、shadow 或 multi-fidelity support claim 分开处理。

## 2. 已验收产物

WP7-A 作为 registry materialization 计划验收。它选择从属于 WP6 policy 的
hand-maintained YAML seed，并要求 schema check、source-document provenance、
显式 `maintained_status`、`projection_eligibility` 与 drift detection。本次验收不创建 seed 文件或 doc tests。

WP7-B 作为 runtime capability projection 计划验收。`RuntimeCapabilities`
必须从 `maintained_status`、`projection_eligibility`、profile `validation_gate`
与 budget `acceptance_gate` 投影维护中 support。deployment facts 只能解释
diagnostics 或 availability，不能晋级 support。

WP7-C 作为 promotion evidence gate 计划验收。exact GPU、resident-state 与
shadow candidate 在未来 promotion packet 同时验收 profile registry revision、
parity budget revision、ownership/sync policy、event/snapshot evidence、
mismatch/quarantine policy、replay evidence、facade/core layering evidence、
WP5 mapping 与 capability projection update 前，仍保持 false。

WP7-D 作为 multi-fidelity entry-condition 计划验收。fidelity profile label
是 request，不是 support claim。如果 request 不能绑定维护中的 backend metadata、
budget、model-family scope、validation gate 与 facade-visible evidence，则必须按 mismatch policy 拒绝、回退到维护中 baseline，或标记为 diagnostics-only。

WP7-E 作为发布交接验收。索引已经指向 WP7 materialization 线与本审查，同时保留
WP7 本身不升级 exact GPU、resident-state、shadow、device observation 或
multi-fidelity support 的规则。

## 3. 推迟的实现工作

以下工作仍为后续事项，本次验收不隐含其已完成：

1. 添加 hand-maintained WP7 registry seed 文件。
2. 添加 registry fields、provenance、parity-budget pairing、projection eligibility 与 drift detection 的 doc/schema tests。
3. 实现 runtime projection adapter，使其消费 normalized registry metadata，而不是 markdown table 或 deployment probe。
4. 为任何 exact GPU、resident-state、shadow、device observation 或 multi-fidelity claim 添加 promotion-specific review packet、registry revision、parity budget revision、evidence artifact 与 tests。
5. 只有满足 WP7-D entry gates 后，才实现 adaptive fidelity scheduling、ModelProvider binding 或 approximate/tolerance budget。

## 4. 验证

WP7-E 收尾所需验证：

```bash
git diff --check
rg -n "WP7|backend capability materialization|acceptance review|RuntimeCapabilities|maintained_status|projection_eligibility|multi-fidelity|promotion gate" docs/task/simulation_architecture docs/plan/architecture docs/task/review
python -m pytest tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py tests/architecture/runtime_facade/test_layering.py -q
```

审查预期：pytest 目标应继续证明当前 facade projection 与 GPU helper binding
不会晋级不受支持的后端能力。

## 5. 剩余风险

主要风险是后续实现漂移：helper、probe、request label 或 deployment fact 被误认为
support。WP7 的缓解方式是把 registry metadata、projection eligibility、
promotion gates 与 acceptance review 作为进入维护中 backend capability support 的唯一路径。
