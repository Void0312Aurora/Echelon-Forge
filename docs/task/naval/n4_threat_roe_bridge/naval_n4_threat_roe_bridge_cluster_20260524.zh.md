# 海军 N4 威胁 / ROE 桥接任务簇

状态：`2026-05-24`，用于 DDG/T-AKE 屏护与接触 MVP 之后第一个海军场景扩展的
规划任务簇。owner 批准后已打开分发队列：
[N4 分发队列](naval_n4_threat_roe_dispatch_queue_20260524.zh.md)。

任务簇：`N4-0 Planning Surface`

Model / reasoning：`gpt-5.4`，medium

轮次上限：本规划面最多一轮实现。如果本轮无法闭合，应返回 `partial` 或
`blocked`，并在新增旁路文档前重新划分范围。

## 决策

下一个海军场景建议为 `ddg51_take1_screen_threat_roe_v1`。

这是一个 `N3 -> N4` 桥接场景。它应在当前 DDG/T-AKE 屏护与接触报告基线上，
加入威胁分类、ROE 状态和可审计的目标分配来源。它不应要求开火、命中评估、
毁伤传播或战斗终止。

建议发布顺序：

1. `threat_roe_v1`：威胁评估与 ROE 状态，不强制开火。
2. `limited_engagement_v1`：N4 守门通过后，只做一次受控武器释放。
3. `damage_outcome_v1`：只有在 N5 交战证据稳定后，才把毁伤和终止作为场景目标。

## 真实性边界

| 梯度 | 场景能力 | 发布姿态 | 允许证明 | 禁止证明 |
| --- | --- | --- | --- | --- |
| `N1-N3` | 现有屏护/接触 MVP | 已接受基线 | 舰船运动、站位保持、接触/报告、共享航迹、单 DDG/HVU 屏护几何 | 完整舰队 C2、火控真实性、毁伤结果 |
| `N4` | 受威胁机动与 ROE | 下一个桥接场景 | 威胁状态、ROE 状态、目标分配来源、传感器质量影响决策状态 | 把武器发射作为必需目标、命中/拦截证明、毁伤/kill 证明 |
| `N5` | 有限武器交战 | 仅后续 | 发射/拒绝事件、有效航迹、射程/射界/冷却/库存守门 | 把毁伤结果作为主要证明 |
| `N6` | 毁伤与终止 | 延后 | 与结果和奖励绑定的 mission/mobility/sensor kill proxy | 任何 `threat_roe_v1` 证明 |

关键边界：`threat_roe_v1` 可以让更宽 runtime 中的开火成为可能，但场景不得把
成功开火或毁伤作为验收证据。未授权或无支撑的开火应视为失败决策路径，而不是
N5 已就绪的证据。

## 场景候选

候选：

- `ddg51_take1_screen_threat_roe_v1`

最低场景形状：

- 蓝方 `DDG-51` 屏护蓝方 `T-AKE-1`；
- 红方水面接触从 HVU 盲区守门外逼近；
- DDG 获得并共享航迹；
- HVU 收到共享航迹和报告；
- 威胁状态只能从带来源/证明的有效航迹升级；
- ROE 状态可观察且可审计；
- 屏护几何仍保持在已接受的 N3 站位窗口内；
- 场景在武器释放前终止，或把任何释放明确记录为范围外转换。

预期 N4 断言：

- 没有有效航迹身份或航迹来源时，接触不能成为 assigned threat；
- ROE 状态应由场景条件导出，而不是写死为静态 metadata 标签；
- task surface 应区分 `monitor`、`threatened`、`authorized` 或等价的开火前状态；
- N4 observation 保留足够 RL 预检状态，但不声明已训练 policy。

## 有限任务簇列表

| 流 | Owner | Model / reasoning | 目标 | 写入范围 | 非目标 | 验证 | 闭合门 | 并行 / 依赖 | 轮次上限 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `N4-0 Planning Surface` | main thread | `gpt-5.4`，medium | 记录有限 N4 桥接计划和分发约束。 | `docs/task/naval/n4_threat_roe_bridge/**`，`docs/task/naval/README*.md` | 场景、测试、runtime 代码、binding、dispatch queue | `git diff --check -- docs/task/naval` | README 和任务簇文档记录场景决策、真实性边界、簇、验证、闭合门和残留项 | 当前簇；无依赖 | 1 轮 | 已实现 |
| `N4-A Scenario / Contract Boundary` | future worker | `gpt-5.4`，high | 增加 N4 威胁/ROE 场景 fixture 和场景级合同。 | `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json`；`tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json`；分发时命名的聚焦 loader/contract 测试路径 | 武器释放、毁伤、RL reward、runtime 重构 | 新 spec 的 scenario contract runner；既有海军 screen 合同 | 新场景可加载，保持 N3 守门，并暴露 N4 威胁/ROE 断言且不声明 N5/N6 | 依赖 `N4-0`；可先于 `N4-B`；下游簇依赖其边界被接受 | 2 轮 | pass / 已接受 |
| `N4-B Threat / ROE Semantics` | future worker | `gpt-5.4`，high | 实现或绑定场景所需 maintained 威胁状态、ROE 状态和目标分配来源。 | 开工前需要更窄分发包；预期文件族为 naval tasking/profile、mission command 和聚焦测试 | 武器效果、毁伤模型、宽范围 command-chain 重写 | 聚焦 runtime/leader 测试，加既有 naval mission-command 测试 | 无授权不开火；assigned target 来自有效航迹；状态通过 maintained contract 暴露 | 依赖 `N4-A`；仅在写入范围不重叠后可与 `N4-C` 并行 | 2 轮 | pass / 已接受 |
| `N4-C Runtime / Facade Evidence` | future worker | `gpt-5.4`，high | 证明 N4 字段通过 maintained facade/world-batch surface 运输，而不是回落到 raw whole-shell 路径。 | 开工前需要更窄分发包；预期文件族为 world-batch command-chain cache、vec-env 测试和 facade guards | 新场景几何、reward 设计、武器行为 | world-batch naval command-chain 测试；若触及则跑 facade/architecture guards | N4 字段在 batch sync 后仍通过 maintained assignment/export 存活 | 依赖 `N4-A`；与 `N4-B` 并行前必须检查写入范围 | 2 轮 | pass / 已接受 |
| `N4-D RL Task Surface Preflight` | future worker | `gpt-5.4`，medium | 用 N4 状态草拟后续 `naval_contact_report` 或 `naval_screen_station_hold` curriculum 的 observation/action/reward/termination。 | 本子项目下的 docs，或后续明确命名的 RL task doc；除非重划范围，否则不写 runtime 代码 | learned policy 声明、trainer launch、基于实验的 reward tuning | 文档 diff；实现后才补 leader-env smoke | RL surface 命名 N4 信号和终止规则，同时拒绝 N5/N6 声明 | 依赖 `N4-A`，实现前应消费 `N4-B` 语义 | 1 轮 | 暂停 / 未分发 |
| `N4-E Integration / Acceptance` | main thread 或 integration worker | `gpt-5.4`，high | 汇总证据、同步 README/current-progress 状态，并决定是否打开 N5 limited engagement。 | 分发时明确命名的 `docs/task/naval/**` acceptance/status 文件 | 实现改动、临时追加功能 | 已完成 worker 记录的完整命令集；`git diff --check -- docs/task/naval` | 前序簇均返回完整 packet；残留项和下一阶段守门已记录 | 串行，位于 `N4-A` 到 `N4-D` 之后 | 1 轮 | 暂停 / 未分发 |

## 分发规则

实现分发现在通过
[N4 分发队列](naval_n4_threat_roe_dispatch_queue_20260524.zh.md) 进行。每个
worker packet 必须映射到上表中的一个流，并遵循权威
[子代理使用政策](../../../standards/governance/subagent_usage_policy.zh.md)。

要求的 worker 结果形状：

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

额外约束：

- 不要把同一个场景合同或规范性 threat/ROE 表拆给多个并发 worker；
- `N4-E Integration / Acceptance` 在实现簇返回完整 packet 前保持串行；
- 若某个簇超过轮次上限，先重新基线该簇，再分配更多 follow-up；
- 若 runtime 工作需要计划写入范围之外的路径，停止并先收窄分发包。

## RL 预检面

Observation 候选：

- 本舰到 HVU 的站位误差；
- 本舰速度/航向和相对接触方位；
- 接触距离、方位、闭合率、航迹来源和置信度；
- HVU 盲区暴露标志；
- 威胁状态、ROE 状态、assigned-target id/provenance；
- 最新报告和 command-chain 状态。

Action 候选：

- 保持当前屏护站位；
- 在 N3 限制内调整站位偏移或速度命令；
- 报告或分类接触；
- 请求或确认 ROE 状态；
- 在 `threat_roe_v1` 中明确没有 weapon-release action。

Reward 候选：

- 维持屏护几何；
- 在保留共享航迹/报告行为的同时保护 HVU；
- 奖励及时且有依据的威胁状态转换；
- 惩罚误升级、使用陈旧航迹、丢失站位或未授权开火尝试。

Termination 候选：

- 接触在正确处置后离开威胁窗口；
- HVU 暴露超过已接受的 N3 容差；
- threat/ROE 状态无法由有效航迹来源支撑；
- 超时；
- 在桥接场景明确升级前，遇到任何必需 N5/N6 行为。

## 验证计划

本任务簇的文档验证：

```bash
git diff --check -- docs/task/naval
```

`N4-A` 之后预期的实现验证：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json
```

若触及 runtime/facade 代码，预期回归面：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_screen_scenario.py tests/leader/test_naval_profile_semantics.py tests/leader/test_naval_contract_fields.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "naval or task_order or command_chain"
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "naval_owner_slice or task_order_naval or command_chain"
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/mission/test_mission_command_naval_fields_roundtrip.py tests/runtime/mission/test_naval_mission_command_mapping.py tests/runtime/mission/test_ship_mission_command_authority.py
```

## 验收标准

N4 桥接未满足以下条件前不得接受：

- 场景和合同证明 N3 基线行为仍成立；
- 威胁状态拥有有效航迹来源和 provenance；
- ROE 状态可在 maintained contract 或 facade projection 中观察；
- target assignment 不能只从静态 metadata 中出现；
- 未授权开火被拒绝、忽略或记录为范围外；
- 文档继续把场景标注为 `N4`，而不是 `N5` 或 `N6`；
- RL 材料保持为 preflight surface，除非后续训练/评估包存在并通过。

## 残留图

立即后续：

- 在本规划面接受后实现 `ddg51_take1_screen_threat_roe_v1`；
- 代码分发前定义精确的 threat 和 ROE 状态名称。

后续：

- `limited_engagement_v1` 只能在 N4 threat/ROE gate 稳定后打开。

延后：

- 命中/拦截证据；
- 毁伤传播和毁伤绑定终止；
- 超出现有 MVP surface 的舰队 C2、ASW、舰载机和 UNREP 真实性。
