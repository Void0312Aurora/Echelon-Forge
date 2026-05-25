# 海军 N4 集成验收

状态：`2026-05-25`，pre-fire N4 bridge pass / 已接受。

语言：

- 英文规范版：
  [naval_n4_integration_acceptance_20260525.md](naval_n4_integration_acceptance_20260525.md)
- 中文伴随版：`naval_n4_integration_acceptance_20260525.zh.md`

输入：

- [N4 威胁 / ROE 桥接任务簇](naval_n4_threat_roe_bridge_cluster_20260524.zh.md)
- [N4 威胁 / ROE 分发队列](naval_n4_threat_roe_dispatch_queue_20260524.zh.md)
- [N4 RL 任务面预检](naval_n4_rl_task_surface_preflight_20260525.zh.md)
- [海军当前进展追踪](../naval_current_progress_20260524.zh.md)

## 决策

N4 `ddg51_take1_screen_threat_roe_v1` 桥接被接受为开火前场景扩展。它证明了
威胁/ROE 状态、交战授权和 assigned-target provenance 已经通过当前 runtime 与
RL plumbing 所需的 maintained command-chain surface。

本验收不打开 N5 实现工作。后续 `limited_engagement_v1` 可以在 owner 批准后作为
新包规划，但在声明任何 weapon-release 任务前，必须补充 launch/reject、
range/arc/cooldown/inventory 和非毁伤验收 gate。

## 证据汇总

| 流 | 结果 | 已接受证据 |
| --- | --- | --- |
| `N4-A Scenario / Contract Boundary` | pass / 已接受 | `ddg51_take1_screen_threat_roe_v1` 场景和 `naval_screen_threat_roe_geometry` 合同存在；N3 screen/contact gate 继续有效；不要求武器、health 或 damage delta |
| `N4-B Threat / ROE Semantics` | pass / 已接受 | maintained 字段覆盖 `threat_state`、`roe_state`、交战授权、assigned target 和 assigned-target provenance，并通过 command JSON、bindings、naval profile 与 loader fallback |
| `N4-C Runtime / Facade Evidence` | pass / 已接受 | N4 mission-command 字段可通过 maintained world-batch/facade tasking export 和 Python runtime DTO surface 存活 |
| `N4-D RL Task Surface Preflight` | pass / 已接受 | observation/action/reward/termination/eval surface 已冻结，且不声明 weapon-release 或 learned-policy |

## 验收检查

| Gate | 结果 |
| --- | --- |
| N3 screen/contact 基线仍通过 | 通过保留 contact-report 和 closing-contact 合同接受 |
| 威胁状态有航迹/provenance 支撑 | 对 N4 bridge 字段和合同窗口接受 |
| ROE 状态可通过 maintained contract 观察 | 通过 mission-command shared core 和 tasking packet export 接受 |
| 目标分配不能只来自静态 metadata | 通过 assigned-target track/source/snapshot provenance 字段接受 |
| 未授权开火不是成功证据 | 在 N4 合同和 RL preflight 中作为范围外/失败姿态接受 |
| 场景保持 N4，而不是 N5/N6 | 已接受；launch、hit/intercept、damage 和 kill proof 继续延后 |
| RL 材料保持 preflight | 已接受；不声明 trainer、reward code 或 learned policy |

## 验证记录

N4 queue 已记录实现验证 packet。集成 owner 复用该证据，并为新的 D/E 闭合面增加
文档验证：

```bash
git diff --check -- docs/task/naval
```

队列中已接受的相关实现证据：

```bash
cmake --build build-workshop --target ef_py -j2
# passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py
# 33 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/facade/test_runtime_facade.py
# 30 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "naval or task_order or command_chain or mission_command"
# 7 passed, 22 deselected

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "naval_owner_slice or task_order_naval or command_chain or mission_command"
# 5 passed, 56 deselected
```

## N5 打开 Gate

N5 limited engagement 仍被阻塞，直到新包定义：

- launch request 和 launch/reject event 合同；
- valid-track、ROE、range、arc、cooldown 和 inventory 前置条件；
- 明确拒绝原因；
- 单次受控武器释放的非毁伤验收证明；
- RL 任务的 action masking 和失败语义；
- 不依赖命中概率、拦截成功或毁伤结果。

建议后续规划面：

- `naval_limited_engagement_v1`，仅在 owner 批准后作为 N5 包打开。

## 残留

- N4 威胁逻辑仍是 bridge-level decision surface，不是完整战术指挥官。
- RL 任务面已经设计，但本验收片段不实现 trainer config 或评估命令。
- N6 毁伤与终止继续延后。
- 舰队 C2、ASW、舰载机和 UNREP 真实性保持在 N4 bridge 范围外。
