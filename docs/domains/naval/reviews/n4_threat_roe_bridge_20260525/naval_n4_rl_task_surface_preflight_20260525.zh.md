# 海军 N4 RL 任务面预检

状态：`2026-05-25`，作为仅文档的 preflight surface，pass / 已接受。

语言：

- 英文规范版：
  [naval_n4_rl_task_surface_preflight_20260525.md](naval_n4_rl_task_surface_preflight_20260525.md)
- 中文伴随版：`naval_n4_rl_task_surface_preflight_20260525.zh.md`

输入：

- [N4 威胁 / ROE 桥接任务簇](naval_n4_threat_roe_bridge_cluster_20260524.zh.md)
- [N4 威胁 / ROE 分发队列](naval_n4_threat_roe_dispatch_queue_20260524.zh.md)
- [N4 集成验收](naval_n4_integration_acceptance_20260525.zh.md)
- [海军当前进展追踪](../naval_progress_snapshot_20260527.zh.md)

## 决策

屏护/接触 MVP 之后的第一个海军 RL curriculum 应留在已接受的 `N3 -> N4`
桥接范围内。它可以把 N4 威胁/ROE 状态作为可观察决策上下文，但不能加入
weapon-release action，也不能声明已经有 learned engagement policy。

建议顺序：

1. `naval_contact_report_threat_roe_v1`：报告并分类逼近水面接触，同时保持有效
   threat/ROE provenance。
2. `naval_screen_station_hold_threat_aware_v1`：在 policy 可观察威胁和 ROE 状态的
   同时保持 DDG/T-AKE 屏护几何稳定。
3. `naval_limited_engagement_v1`：推迟到 N5 launch/reject gate 被接受之后。

本 preflight 只冻结任务面。它不创建 trainer config、代码 reward、policy
checkpoint 或评估 dashboard。

## 真实性边界

| 边界 | 包含 | 排除 |
| --- | --- | --- |
| `N1-N3` 屏护/接触 | 本舰站位保持、HVU 保护、接触报告、共享航迹连续性 | 舰队级 C2 和多舰战术 |
| `N4` 威胁/ROE | 威胁状态、ROE 状态、交战授权、assigned-target provenance、航迹来源质量 | 发射事件成功、命中/拦截结果、毁伤结果 |
| `N5+` 交战/毁伤 | 只读范围外检测，用于安全终止 | weapon-release action、damage reward、kill-based termination |

任务可以观察 `authorization_to_fire`，但 N4 curriculum 的 RL action 不得开火。
如果后续环境暴露武器控制，N4 任务必须 mask 掉这些动作，或把它们作为范围外转换
终止。

## Observation 面

最低 observation 分组：

| 分组 | 字段 |
| --- | --- |
| 屏护几何 | DDG-HVU 距离、站位半径误差、站位方位误差、相对 HVU 方位、本舰速度、本舰航向 |
| 接触几何 | 接触距离、方位、闭合率、本舰/共享航迹 age、接触来源、来源置信度或质量 |
| N4 状态 | `threat_state`、`roe_state`、`authorization_to_fire`、交战授权 holder/grantor ids |
| 目标来源 | `assigned_target_id`、`assigned_target_track_id`、`assigned_target_source_id`、`assigned_target_snapshot_time_s`、assigned-target age |
| 报告链 | 最新报告 age、报告/航迹存在标志、command-chain active 标志、facade/world-batch packet provenance |
| 安全标志 | HVU 盲区暴露、stale-track、unauthorized-fire event、N5/N6 transition |

归一化规则：

- id 字段应投影为存在性、相等性或稳定小编码特征，除非后续模型明确支持 entity-id embedding；
- 航迹和目标 age 应裁剪到合同窗口；
- 来源和状态枚举应使用 maintained command/tasking surface 的稳定数值编码；
- 未知或缺失 provenance 应是显式特征值，不能静默折叠成零置信度的有效状态。

## Action 面

允许的 action 家族：

- 保持当前屏护站位；
- 在已接受的 N3 限制内调整期望站位半径或方位；
- 在舰船运动边界内调整速度或航向命令；
- 报告、分类或请求确认接触；
- 确认或请求 ROE 状态更新；
- 维持 assigned-target 确认，但不从静态 metadata 创造新目标。

禁止的 action 家族：

- 武器释放；
- 命中、kill 或毁伤声明；
- 直接编辑库存；
- 绕过报告或航迹 provenance 来设置威胁状态；
- 在没有可审计场景条件时覆盖 ROE 状态。

## Reward 面

Reward 候选：

- 保持在屏护站位窗口内给正奖励；
- 及时接触报告和共享航迹连续性给正奖励；
- 威胁升级由新鲜航迹 provenance 支撑时给正奖励；
- ROE/authority 一致性稳定时给小正奖励；
- 错误威胁升级给惩罚；
- 使用陈旧航迹做目标分配给惩罚；
- HVU 暴露或丢失站位给惩罚；
- 未授权开火尝试给强惩罚或立即失败。

N4 reward 不能使用命中概率、拦截成功、毁伤量或 kill state。

## Termination 面

成功候选：

- 接触在有效报告、威胁和 ROE 处置后离开威胁窗口；
- episode 到达计划 horizon，站位几何仍在 N3 窗口内，且没有 N5/N6 转换；
- assigned-target provenance 在最终决策窗口中保持有效。

失败候选：

- HVU 暴露超过已接受的 N3 容差；
- threat/ROE 状态无法由有效航迹 provenance 支撑；
- 目标分配只从静态 metadata 出现；
- 尝试或记录了未授权开火；
- 任务升级到 N5 前出现必需的武器释放、命中、毁伤或 kill 状态；
- 超时且没有接触报告或威胁状态收敛。

## 评估 Gate

实现 trainer 前，应增加确定性 gate：

- observation schema 包含所有必需 N4 分组；
- action mask 在 N4 任务中排除武器释放；
- reward 不引用 damage 或 kill state；
- seeded scenario rollout 保持 N3 screen/contact 合同；
- `threat_state` 升级时，assigned-target provenance 不得缺失；
- stale track age 被惩罚或拒绝；
- 未授权开火是失败信号，不是成功路径。

建议后续验证命令：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/leader/test_tasking_profile_contracts.py tests/leader/test_command_field_projection_contracts.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "naval_owner_slice or task_order_naval or command_chain or mission_command"
```

## 验收

本 preflight 被接受，因为它：

- 命名了前两个 N4 兼容 RL 任务候选；
- 定义了 observation、action、reward、termination 和 evaluation surface；
- 消费已接受的 N4 威胁/ROE 字段；
- 把武器释放、毁伤和 learned-policy 声明保持在范围外。

海军 RL 线已经可以进入后续实现包设计，但还不能声明已经有训练完成的 policy。

## 残留

- 只有在 owner 批准后，才创建具体 trainer/eval config entrypoint。
- 启动 policy loop 前应增加 observation-schema tests。
- `naval_limited_engagement_v1` 继续被 N5 launch/reject gate 阻塞。
