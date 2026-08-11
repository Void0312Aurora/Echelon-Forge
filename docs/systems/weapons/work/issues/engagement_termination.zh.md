# 任务终止与行为逻辑前瞻

Language:
- English canonical: [engagement_termination.md](engagement_termination.md)
- Chinese companion: `engagement_termination.zh.md`

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/weapons/work/issues/engagement_termination.md`
Owner: `systems/weapons`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

本文件记录“交战终止条件”和“行为逻辑”的规划方向，避免出现长时间
镜像追逐或无意义机动。

## 当前运行时覆盖范围
- 当前核心安全/快速失败终止逻辑位于
  `src/core/mission/runtime/termination_runtime.*`。
- 现有运行时已覆盖：
  - 有限状态无效 / NaN 防护终止
  - 基于生命值的坠毁终止
  - 深失速、低空倒飞、极端俯仰等 fail-fast 终止
  - 起落架折损与偏离跑道终止
  - `success` / `failure` / `timeout` 等最终原因归一化
- 场景加载与任务指令归一化当前位于 `gym_envs/scenario_loader/` 包，
  主要入口是 `core.py` 与 `loading.py`。

## 建议扩展的交战级终止条件
以下项目仍属于规划目标，不是当前已交付的运行时开关。

1) 脱战距离
- 增加面向 scenario 的阈值，例如 `disengage_range_m` +
  `disengage_hold_s`。
- 超出距离阈值且持续一段时间，终止或切换到返航行为。

2) 弹药耗尽
- 增加类似 `ammo_depletion_ends` 的规则，并可附加“空中无弹体”约束。
- 双方弹药均耗尽且空中无弹体，终止。
- 若单方耗尽，可切换到防御/撤退策略。

3) 能量过低
- 增加面向 scenario 的阈值，例如 `min_specific_energy_j_kg` +
  `energy_hold_s`。
- 以比能（J/kg）或速度阈值判定。
- 建议记录持续时间以避免瞬时抖动。

4) 感知丢失
- 目标长时间失踪（无探测/跟踪），触发脱战。

5) 任务目标完成
- 达成击毁/命中/任务杀伤即终止。

## 行为逻辑建议
- “交战”与“脱战”是两个状态，具备明确切换条件。
- 脱战后可采用：
  - 固定航向逃逸
  - 能量恢复（速度/高度提升）
  - 返航/盘旋待命

## 进一步落地建议
- 建议将交战级终止与现有 safety runtime 分层维护，避免两类规则混在一起。
- 在 scenario 中支持 per-side/per-entity 的终止规则。
- 日志记录终止原因与触发时刻，便于回放分析。
