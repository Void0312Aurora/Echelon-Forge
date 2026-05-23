# WP18-C ScenarioLoader Adapter Split

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp18_scenario_loader_adapter_split_cluster_20260521.md](wp18_scenario_loader_adapter_split_cluster_20260521.md)
- 中文辅文：`wp18_scenario_loader_adapter_split_cluster_20260521.zh.md`

输入：

- [WP18 主计划](runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.zh.md)
- [WP18-A ownership fact ledger](wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md)
- [仿真系统架构设计](../../../plan/architecture/simulation_system_architecture_design.zh.md)

## 目标

停止把 `ScenarioLoader` 当成一个无差别 owner。WP18-C 需要拆分或预加 gate：
scenario/content adaptation 保持合法，而 maintained runtime state ownership 则继续向
C++/facade surfaces 迁移。

## 范围

范围内：

- 识别 `ScenarioLoader` 中属于 static scenario/content adaptation、frontend helper、
  runtime state mirror 或 maintained owner candidate 的职责；
- 引入窄 adapter boundary 或测试来约束这些分类；
- 迁移一个低风险 call site，或添加 guard 防止新的 authoritative runtime fields
  静默落入 `ScenarioLoader`。

范围外：

- 修改 C++ runtime reward/termination logic；
- 删除既有 scenario 使用的 loader APIs；
- 修改 public scenario schemas。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `C1` | Responsibility map | Loader fields/methods 按 scenario adapter、frontend helper、runtime mirror 或 owner candidate 分类。 |
| `C2` | Adapter/pre-gate seam | 存在窄 split 或 guard，防止新的 maintained runtime ownership 静默落入 loader。 |
| `C3` | Compatibility preservation | 既有 scenario 与 world-batch loader tests 仍通过。 |
| `C4` | Handoff to B/E | 应迁到 B 或 E 的 runtime-owned fields 以候选测试命名。 |

## 建议验证

```bash
git diff --check
python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py
python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "scenario_loader or route"
python -m pytest -q tests/runtime/naval/test_naval_screen_scenario.py -k "scenario"
```

## Handoff

返回 responsibility map、adapter/guard changes、touched files、commands run、
compatibility risks，以及后续应迁到 C++/facade ownership 的字段。
