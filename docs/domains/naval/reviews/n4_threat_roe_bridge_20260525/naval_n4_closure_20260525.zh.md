# 海军 N4 闭合

状态：`2026-05-27`，作为开火前 N4 bridge 与 active-entry gate 已闭合；维护态
contact-report、station-hold 和离站位恢复入口均已进入专门的海军动作/观测面和
单策略槽位 cooperative runtime。

语言：

- 英文规范版：
  [naval_n4_closure_20260525.md](naval_n4_closure_20260525.md)
- 中文伴随版：`naval_n4_closure_20260525.zh.md`

输入：

- [N4 集成验收](naval_n4_integration_acceptance_20260525.zh.md)
- [N4 RL 任务面预检](naval_n4_rl_task_surface_preflight_20260525.zh.md)
- [海军 active 训练条目](../../../../../examples/config/training/active/README.zh.md)
- [海军当前进展追踪](../naval_progress_snapshot_20260527.zh.md)

## 决策

当前海军工作线的 N4 bridge 已闭合。

闭合意味着：

- `ddg51_take1_screen_threat_roe_v1` 是已接受的开火前场景；
- `naval_screen_threat_roe_geometry` 是场景级 N4 contract；
- threat/ROE、交战授权和 assigned-target provenance 已存在于 maintained tasking surface；
- 已接受的 N4-compatible RL task id 已有维护中的 active smoke/probe 入口，
  包括稳定的离站位恢复 gate；
- 这些入口使用 `naval_station3`、`naval_screen_station_v1` 和已接受的单策略槽位
  cooperative roster 路径；
- `tools/eval/naval_station_policy_eval.py` 为 N4 active 入口提供维护中的 cooperative
  零动作基线 gate；
- N5 武器交战与 N6 毁伤结果的边界仍然明确且可测试。

闭合不意味着：

- 已存在 learned naval policy；
- 已存在完整海军训练 curriculum 或 learned-policy acceptance package；
- 通用 multi-agent naval training 已提升；
- weapon release、hit/intercept、damage 或 kill outcome 可作为 N4 任务目标。

## 域结构

N4 建立在现有 N1-N3 naval screen/contact 基础之上。

| 层 | N4 闭合姿态 |
| --- | --- |
| 平台与环境 | DDG/T-AKE/红方水面接触和 maritime state 保持为固定公开平台基线 |
| 运动与站位 | N3 screen geometry 仍是机动 gate；N4 不新增舰队机动 doctrine |
| 传感器与报告链 | contact source、shared track 与 report continuity 仍是必要支撑证据 |
| C2 与 ROE | `roe_state`、交战授权、assigned target 和 assigned-target provenance 是 N4 新增部分 |
| 武器释放 | 明确排除在 N4 之外；任何 release 都属于后续 N5 package |
| 毁伤与终止 | 明确排除在 N4 之外；任何 damage outcome 都属于 N6+ |
| RL 入口 | active smoke/probe gate 使用专门的 N4 海军动作/观测面和一个 DDG 策略槽位，但不是 learned-policy 证据 |

## 闭合矩阵

| Gate | Artifact | 闭合状态 |
| --- | --- | --- |
| Scenario | `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json` | N4 开火前场景已接受 |
| Contract | `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json` | threat/ROE screen geometry contract 已接受 |
| Integration | `naval_n4_integration_acceptance_20260525.md` | command-chain/runtime 证据已接受 |
| RL preflight | `naval_n4_rl_task_surface_preflight_20260525.md` | observation/action/reward/termination/eval surface 已冻结 |
| Active entries | `examples/config/training/active/naval/*.json` | contact-report、station-hold 和离站位恢复 smoke/probe 条目已存在，并使用 cooperative 单策略槽位 execution |
| Baseline eval | `tools/eval/naval_station_policy_eval.py` | 零动作 N4 cooperative 基线检查 roster、必要海军奖励项，以及禁止出现的空军 / 武器 / 毁伤项 |
| Regression gate | `tests/training/test_naval_training_entry_contracts.py` 与 `tests/training/test_naval_training_entry_contracts.py` | N4 metadata、scenario、docs 和 non-claims 被测试守住 |

## Active Entry 范围

已闭合的 active entries：

- `naval_contact_report_threat_roe_v1`
- `naval_screen_station_hold_threat_aware_v1`
- `naval_screen_station_recovery_threat_aware_v1`

这些都是 smoke/probe gates。它们使用专门的 no-release `naval_station3` 站位指令动作面、
`naval_screen_station_v1` 策略观测面，以及已接受的单策略槽位 cooperative runtime。
在后续 package 定义完整 curriculum、learned-policy acceptance 和更广 cooperative
policy 语义前，它们必须继续标记为 `entry_and_gate_only`。

恢复入口使用 `ddg51_take1_screen_threat_roe_offstation_recovery_v1`，DDG 初始位于
名义屏护站位内侧 `1800 m`，并开启站位恢复进度奖励。它闭合的是固定原始任务奖励参考下的
维护态脚本恢复 gate，不是已学会恢复的 policy。

active-entry 的场景路径现在会在训练启动和维护态 N4 eval 工具中强制检查。带有
`naval_entry.scenario_path` 的配置必须和声明场景一起启动或评估，因此普通站位保持和
离站位恢复 gate 不能在 runtime 被静默互换。
声明的 `naval_entry.contract_path` 也必须指向内部 `scenario` 字段匹配同一场景的
contract。
active-entry 测试现在会直接执行去重后的声明 contract，因此 config、scenario、
contract 这条链同时受到声明检查和实时 contract 执行保护。
训练 bootstrap 和维护态 N4 eval 工具也会拒绝任何解析后不是 `naval_station3` 加
`naval_screen_station_v1` 的 `naval_entry` 配置，防止 active naval 入口静默退回
空军或通用 policy surface。

## N5 打开 Gate

N5 仍然阻塞。打开 `naval_limited_engagement_v1` 需要独立 package，包含：

- launch request 和 launch/reject event contract；
- valid-track、ROE、range、arc、cooldown 和 inventory 前置条件；
- 明确拒绝原因；
- RL action masking；
- 单次受控 release 的非毁伤证明；
- 不依赖 hit probability、intercept success 或 damage outcome。

## 验证

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_training_entry_contracts.py tests/training/test_naval_training_entry_contracts.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_training_bootstrap_contracts.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/eval/test_evaluation_cli_contracts.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/eval/naval_station_policy_eval.py --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json --steps 1200

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/eval/naval_station_policy_eval.py --mode offstation_probe --scenario scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json --train_config examples/config/training/active/naval/naval_screen_station_recovery_threat_aware_smoke_v1.json --steps 300

git diff --check -- docs/domains/naval examples/config/training/active/naval tests/training/test_naval_training_entry_contracts.py tests/training/test_naval_training_entry_contracts.py
```

## 下一步

后续海军 package 不应重新打开 N4。它应当二选一：

- 把 N4 active entries 从 baseline eval gate 扩展为完整 curriculum 和 learned-policy
  acceptance package；
- 或用上面的 gates 打开独立 N5 limited-engagement package。
