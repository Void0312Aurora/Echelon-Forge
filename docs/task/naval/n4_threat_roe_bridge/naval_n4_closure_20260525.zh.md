# 海军 N4 闭合

状态：`2026-05-25`，作为开火前 N4 bridge 与 active-entry gate 已闭合。

语言：

- 英文规范版：
  [naval_n4_closure_20260525.md](naval_n4_closure_20260525.md)
- 中文伴随版：`naval_n4_closure_20260525.zh.md`

输入：

- [N4 集成验收](naval_n4_integration_acceptance_20260525.zh.md)
- [N4 RL 任务面预检](naval_n4_rl_task_surface_preflight_20260525.zh.md)
- [海军 active 训练条目](../../../../examples/config/training/active/naval/README.zh.md)
- [海军当前进展追踪](../naval_current_progress_20260524.zh.md)

## 决策

当前海军工作线的 N4 bridge 已闭合。

闭合意味着：

- `ddg51_take1_screen_threat_roe_v1` 是已接受的开火前场景；
- `naval_screen_threat_roe_geometry` 是场景级 N4 contract；
- threat/ROE、交战授权和 assigned-target provenance 已存在于 maintained tasking surface；
- 两个已接受的 N4-compatible RL task id 已有维护中的 active smoke/probe 入口；
- N5 武器交战与 N6 毁伤结果的边界仍然明确且可测试。

闭合不意味着：

- 已存在 learned naval policy；
- 已存在专门的海军 observation/action/reward/eval package；
- cooperative naval training 已提升；
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
| RL 入口 | active smoke/probe gate 已存在，但不是 learned-policy 证据 |

## 闭合矩阵

| Gate | Artifact | 闭合状态 |
| --- | --- | --- |
| Scenario | `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json` | N4 开火前场景已接受 |
| Contract | `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json` | threat/ROE screen geometry contract 已接受 |
| Integration | `naval_n4_integration_acceptance_20260525.md` | command-chain/runtime 证据已接受 |
| RL preflight | `naval_n4_rl_task_surface_preflight_20260525.md` | observation/action/reward/termination/eval surface 已冻结 |
| Active entries | `examples/config/training/active/naval/*.json` | 两个 smoke/probe 条目已存在，并使用 maintained world-batch execution |
| Regression gate | `tests/training/test_naval_active_training_entries.py` 与 `tests/training/test_naval_n4_closure_gate.py` | N4 metadata、scenario、docs 和 non-claims 被测试守住 |

## Active Entry 范围

已闭合的 active entries：

- `naval_contact_report_threat_roe_v1`
- `naval_screen_station_hold_threat_aware_v1`

二者都是 smoke/probe gates。它们使用临时 no-release action surface，因为当前
execution action APIs 尚不是海军专用。在后续 package 定义专门海军 observations、
actions、rewards、curriculum 和 evaluation 前，它们必须继续标记为
`entry_and_gate_only`。

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
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json

git diff --check -- docs/task/naval examples/config/training/active/naval tests/training/test_naval_n4_closure_gate.py tests/training/test_naval_active_training_entries.py
```

## 下一步

后续海军 package 不应重新打开 N4。它应当二选一：

- 在 N4 active entries 后实现专门的海军 observation/action/reward/eval package；
- 或用上面的 gates 打开独立 N5 limited-engagement package。
