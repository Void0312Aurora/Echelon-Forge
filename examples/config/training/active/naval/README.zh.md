# 海军 N4 训练条目

此目录存放已接受 DDG/T-AKE `N4` 威胁/ROE bridge 的维护中 active
smoke/probe 条目。

## 范围

- 该线路的场景配对为：
  - [ddg51_take1_screen_threat_roe_v1.json](../../../../../scenarios/naval/ddg51_take1_screen_threat_roe_v1.json)
  - [ddg51_take1_screen_threat_roe_offstation_recovery_v1.json](../../../../../scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json)
- 合同配对为：
  - [naval_screen_threat_roe_geometry.json](../../../../../tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json)
  - [naval_screen_threat_roe_offstation_recovery.json](../../../../../tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json)
- 当前基线是入口/runtime gate，而不是已训练海军策略。
- 维护中的基线评估是
  [eval_naval_n4_baseline.py](../../../../../tools/eval/eval_naval_n4_baseline.py)
  提供的 cooperative 零动作 N4 gate。

这些条目有意停留在开火前 `N4` 边界。它们验证 scenario、config 和当前
execution runtime 可以被配对用于 RL 实验。它们不暴露武器释放动作，不使用毁伤或
击杀奖励，也不声称已经学会屏护或交战行为。

## 条目

- [naval_contact_report_threat_roe_smoke_v1.json](naval_contact_report_threat_roe_smoke_v1.json)
  - 最小 contact-report / threat-ROE smoke probe。
  - 使用已接受 N4 场景和 threat/ROE 合同作为 gate 来源。
  - 使用 `agent_layer=cooperative_execution`；DDG 是唯一策略槽位，非 agent 的
    T-AKE 支援舰仍保留在 scenario loader 的 roster 中。

- [naval_screen_station_hold_threat_aware_smoke_v1.json](naval_screen_station_hold_threat_aware_smoke_v1.json)
  - 最小 threat-aware screen-station smoke probe。
  - 使用相同 N4 场景，同时追踪第二个已接受 RL task id。
  - 使用 `agent_layer=cooperative_execution`；DDG 是唯一策略槽位，非 agent 的
    T-AKE 支援舰仍保留在 scenario loader 的 roster 中。

- [naval_screen_station_recovery_threat_aware_smoke_v1.json](naval_screen_station_recovery_threat_aware_smoke_v1.json)
  - 最小离站位恢复 smoke probe。
  - 使用维护态 off-station N4 场景，DDG 初始位于名义屏护站位内侧 `1800 m`。
  - 保持同一开火前 threat/ROE 边界和单 DDG 策略槽位，同时在场景中开启站位恢复进度奖励。

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

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_recovery_threat_aware_smoke_v1.json \
  --output_base experiments/naval \
  --run_name naval_screen_station_recovery_threat_aware_smoke_v1

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/eval/eval_naval_n4_baseline.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json \
  --steps 1200 \
  --json_out experiments/naval/naval_n4_zero_action_baseline.json

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/eval/eval_naval_n4_baseline.py \
  --mode offstation_probe \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_recovery_threat_aware_smoke_v1.json \
  --steps 300 \
  --json_out experiments/naval/naval_n4_offstation_recovery_probe.json
```

## 设计说明

- `naval_entry.scenario_path` 是执行契约，不只是文档字段：如果 `--scenario`
  没有解析到条目声明的场景，`train.py` 和维护态 N4 eval 工具都会拒绝启动。
  这可以防止恢复入口误跑普通站位保持场景，或普通入口误跑恢复场景。
- `naval_entry.contract_path` 也必须绑定同一个声明场景。若 contract 内部的
  `scenario` 字段指向另一个场景，bootstrap 会拒绝启动，从而保持
  scenario/config/contract 三者对齐。
- active action surface 是专门的 no-release 海军站位指令 probe：
  `action_mode=naval_station3`。它通过海军 task/command 链调整站位方位、
  站位半径和受限速度意图，同时保持舰艇 pilot-action carrier 为中性。
- active observation surface 是海军站位/接触模式：
  `mission_obs_mode=naval_screen_station_v1`。它暴露站位几何、接触可见性、
  支援轨迹/报告链状态、ROE 和指定目标来源，不再继承空军编队或起飞字段命名。
- 所有 active 入口都使用 `cooperative_execution` 的单策略槽位情况：DDG 接收策略动作，
  非 agent 的 T-AKE 保留为支援 roster，用于 reference / report-chain 上下文。
  这不是通用的多 agent 海军提升。
- 从这些 smoke/probe 条目继续提升，仍需要更清晰的 packet 所有权、更完整的
  action mask、reward shaping、更广的 cooperative 观测 schema 和 eval gates。
- baseline eval gate 不是已训练 policy 声明。它验证 N4 cooperative 零动作保持路径
  只有一个 DDG 策略槽位、保留非 agent 的 T-AKE 支援 roster、产生必要的海军站位 /
  接触 / 报告 / ROE 奖励项，并且不产生机场、武器、毁伤或击杀奖励项。
- 离站位 probe gate 也不是已训练 policy 声明。它验证脚本站位保持能在固定原始任务参考下
  从离站位初始状态恢复，并验证 `naval_station3` 站位改令不能把奖励参考点移动到本舰身上。
  维护态恢复入口把这条 gate 固化为稳定的场景 / 配置配对；有用的非零 policy 恢复仍需要
  单独 curriculum 和 learned-policy 验收。

## 验证

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_train_bootstrap.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/eval/test_eval_naval_n4_baseline.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/eval/eval_naval_n4_baseline.py --mode offstation_probe --scenario scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json --train_config examples/config/training/active/naval/naval_screen_station_recovery_threat_aware_smoke_v1.json --steps 300
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json
```
