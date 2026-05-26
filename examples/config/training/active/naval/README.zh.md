<!-- Machine-translated draft generated on 2026-05-25 from examples/config/training/active/naval/README.md. Review before treating this file as authoritative. -->

# 海军 N4 训练条目

此目录存放已接受 DDG/T-AKE `N4` 威胁/ROE bridge 的维护中 active
smoke/probe 条目。

## 范围

- 该线路的场景配对为：
  - [ddg51_take1_screen_threat_roe_v1.json](../../../../../scenarios/naval/ddg51_take1_screen_threat_roe_v1.json)
- 合同配对为：
  - [naval_screen_threat_roe_geometry.json](../../../../../tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json)
- 当前基线是入口/runtime gate，而不是已训练海军策略。

这些条目有意停留在开火前 `N4` 边界。它们验证 scenario、config 和
maintained world-batch execution path 可以被配对用于 RL 实验。它们不暴露武器
释放动作，不使用毁伤或击杀奖励，也不声称已经学会屏护或交战行为。

## 条目

- [naval_contact_report_threat_roe_smoke_v1.json](naval_contact_report_threat_roe_smoke_v1.json)
  - 最小 contact-report / threat-ROE smoke probe。
  - 使用已接受 N4 场景和 threat/ROE 合同作为 gate 来源。

- [naval_screen_station_hold_threat_aware_smoke_v1.json](naval_screen_station_hold_threat_aware_smoke_v1.json)
  - 最小 threat-aware screen-station smoke probe。
  - 使用相同 N4 场景，同时追踪第二个已接受 RL task id。

## 命令

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json \
  --train_config examples/config/training/active/naval/naval_contact_report_threat_roe_smoke_v1.json \
  --output_base experiments/naval \
  --run_name naval_contact_report_threat_roe_smoke_v1

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json \
  --output_base experiments/naval \
  --run_name naval_screen_station_hold_threat_aware_smoke_v1
```

## 设计说明

- active action surface 是专门的 no-release 海军站位指令 probe：
  `action_mode=naval_station3`。它通过海军 task/command 链调整站位方位、
  站位半径和受限速度意图，同时保持舰艇 pilot-action carrier 为中性。
- active observation surface 是海军站位/接触模式：
  `mission_obs_mode=naval_screen_station_v1`。它暴露站位几何、接触可见性、
  支援轨迹/报告链状态、ROE 和指定目标来源，不再继承空军编队或起飞字段命名。
- trainer 路径为 `agent_layer=execution` 且
  `runtime.world_batch_vec_env=true`，因此停留在 maintained world-batch runtime，
  不走隔离中的 raw-kernel compatibility path。
- 此处有意暂不使用 `cooperative_execution`。当前海军 roster 包含非 agent 支援舰，
  cooperative slot accounting 在提升为多槽位海军路径前需要单独 gate。
- 从这些 smoke/probe 条目继续提升，仍需要更清晰的 packet 所有权、更完整的
  action mask、reward shaping、cooperative slot 和 eval gates。

## 验证

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
```
