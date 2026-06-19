# MLF-9 Pk / 统计趋势任务簇

状态：`2026-06-19` finite task-cluster plan，对应
[MLF-9 Pk / 统计趋势](README.zh.md)。

## 边界决策

MLF-9 可以消费已验收、可回放的 MLF-5 到 MLF-8 仿真事实，并产出 synthetic
statistical trend report。它不能声明现实 Pk、具体弹种杀伤率、具体目标杀伤率、
校准权威、reward 权威、实体删除或碎片物理。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF9-P0` | main thread | n/a | 创建持久子项目表面和父级 A2 链接。 | `docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_pk_statistical_trends/**`；父级 A2 README 文件 | runtime 实现；Pk 数值声明 | `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model`；local Markdown link inspection | README、任务簇、派发队列、状态和 archive 占位存在且已链接 | First；serial | 1 | pass |
| `MLF9-P1` | main thread or read-only diagnostics worker | high | 盘点 MLF-5 到 MLF-8 可回放输入和当前 diagnostics 导出。 | 仅 MLF-9 inventory/status docs | runtime physics edits；inventory 前做 metric 决策 | read-only scan；docs diff check | accepted input fields、missing joins 和 safe implementation write sets 已命名 | After P0；可按来源区域只读并行 | 1 + 1 repair | pass |
| `MLF9-P2` | main thread | high | 定义 metric contract，并对齐该契约所需的 diagnostics row surface。 | MLF-9 contract docs；`tools/diagnostics/**`；聚焦 diagnostics tests | 真实 Pk 校准；公开来源拟合；runtime damage physics | contract inspection；py-compile；focused diagnostics tests | 契约可实现且不暗示现实概率，已验收 MLF-5..8 stages 可在 row surface 中观察 | After P1；serial | 2 | initial pass |
| `MLF9-P3` | implementation worker | high | 从受控 replay rows 或 fixtures 实现确定性趋势提取。 | `tools/diagnostics/**` 或 test-only fixture helpers；聚焦测试 | reward shaping；entity deletion；修改上游 MLF-5..8 facts | 聚焦 pytest/C++ tests；`git diff --check` | 受控 fixture 报告可复现且有边界 | After P2；与 P4 串行 | 2 | initial pass |
| `MLF9-P4` | integration worker | medium | 以 retained artifact 或 diagnostics output 暴露报告，且不泄漏到 consumer。 | MLF-9 docs；diagnostics report paths；可选 probe surface | training success claim；reward authority；calibration promotion | 聚焦 diagnostics tests；report shape inspection | 报告写清 sample source、denominator、trend labels 和 non-claims | After P3 | 2 | initial pass |
| `MLF9-P5` | main thread | medium | 执行聚焦验证和 smoke。 | MLF-9 validation/status docs；若失败暴露范围内缺口可更新测试 | 与 MLF-9 无关的 broad suite cleanup | 聚焦测试；相关 smoke；docs diff check | 验证结果已记录，residuals 已命名 | After P4 | 1 + 1 repair | pass |
| `MLF9-P6` | main thread | n/a | 验收、hold 或重划 MLF-9，并同步索引 / archive。 | MLF-9 README/status/acceptance/archive；若 accepted 则父级 A2 README/archive registry | 证据缺失时关闭；过度声明 Pk | docs link/path inspection；`git diff --check` | 状态和父级索引与证据一致 | Last；serial | 1 | pass |

## 派发规则

- 每个 worker packet 必须只对应上表中的一个 cluster。
- 不修改已归档 MLF evidence packages；除非只是修断链。
- `MLF9-P2`、`MLF9-P5` 和 `MLF9-P6` 保持串行。
- 若某个 cluster 超过 round cap，先停下重划范围，再追加新 wave。
- 遵循
  [Subagent 使用规范](../../../../../standards/governance/subagent_usage_policy.zh.md)。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 验证计划

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model
python3 -m py_compile tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_rows.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_snapshot.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/schema.py \
  tools/diagnostics/lethality_chain_contract.py \
  tools/diagnostics/mlf9_statistical_trends.py \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py
PYTHONPATH=build-workshop:. pytest -q \
  tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_summary.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py::DiagnosticsProcessProbeSnapshotTests::test_run_probe_payload_and_chain_csv_include_lethality_chain_rows \
  tests/training/test_fire_timing_fault_localization_contracts.py \
  tests/tools/test_mlf9_statistical_trends.py
```

## 验收标准

- MLF-9 报告对受控输入是确定性的。
- 每个趋势都写清样本来源、分母、后果分桶和不确定性标签。
- 测试阻止 trend report 变成 reward、deletion 或 calibration authority。
- 真实 Pk、具体弹种杀伤率和具体目标真值继续拒绝。

## 残余地图

Immediate:

- 已验收的 MLF-9 simulation-trend/report 切片不需要额外实现。

Follow-on:

- 只有用户要求 archive MLF-9 时再同步 physical archive 和 archive registry。

Deferred:

- MLF-10 校准门、公开来源结果准入、特定武器 / 目标校准。
