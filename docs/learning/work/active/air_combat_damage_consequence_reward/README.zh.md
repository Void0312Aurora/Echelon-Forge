# A2 损伤后果奖励面

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/learning/work/active/air_combat_damage_consequence_reward/README.md`
Owner: `learning/air-combat-reward`
Last verified: `2026-08-08`

状态：`2026-06-11` active A2 follow-on / DCR-A-D 已验证；DCR-E probe 导出和
diagnostics-only bridge 已具备。受控 fixed-fire bridge 能报告 release/effects/damage timing，
但 DCR totals 仍为 0，因为当前 damage report 没有暴露 DCR 可读的后果字段。`DCR-E-R1`
已将下一步证据重定界为 controlled consequence fixture probe；DCR-E 仍为 partial。

语言：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- Learning owner：[../../../README.zh.md](../../../README.zh.md)
- A2 封存包：[../../archive/a2_high_fidelity_damage_model/README.zh.md](../../../../../README.zh.md)
- A8 损伤效果链：[../../archive/a8_damage_effect_chain/README.zh.md](../../../../systems/effects/reviews/damage_effect_chain_20260608/README.zh.md)
- Air execution owner：[../../../../domains/air/README.zh.md](../../../../domains/air/README.zh.md)
- 奖励 runtime 入口：[../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py](../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py)
- 聚焦奖励测试：[../../../../../tests/runtime/air_combat/test_air_combat_reward_surface.py](../../../../../tests/runtime/air_combat/test_air_combat_reward_surface.py)

## 目的

把空战训练反馈从只等 `kill` 或目标实体 inactive 扩展到“造成了什么后果”：任务系统下降、传感/数据链下降、机动能力下降、燃油泄漏、火灾扩大、失控下降、严重触地或坠毁。

该方向放在 A2 下，而不是新建 A9，因为它首先是毁伤模型保真度与后果解释的问题，其次才是训练 reward 设计问题。本 follow-on 只消费已有 runtime 后果作为训练信号，不重开已封存 A2 包，不声明验收，也不把 A8 的有边界效果链升级为 stock AIM-120C / MQ-9 杀伤权威。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| A2 高真实度毁伤模型 | archived / sealed | A2 archive 保留 research/candidate 证据 | 不释放 Pk、deterministic fuze 或 stock weapon-outcome authority |
| A8 损伤效果链 | accepted bounded slice | 起爆后可观察具体部件损伤和维护中系统响应 | 不增加直接坠毁规则、MQ-9 特例击杀规则或碎片/残留对象 |
| 当前训练反馈 | active extension | 非终局 damage report 已经能给一次性系统/能力/loss-state shaping；延迟火灾、燃油、触地、坠毁和飞机内部损伤后果正在作为有边界 follow-on 加入 | 不能把旧 `Health` 或单个 `kill` flag 当作完整杀伤链评价 |

## 范围

纳入：

- 先维护任务簇，再改 runtime。
- 增加可配置奖励项，读取已经可观察的损伤后果。
- 对延迟后果优先使用变化量/转移奖励，避免策略因为同一团火或同一次坠毁反复拿分。
- 将训练 synthetic reward calibration 与真实武器/目标 authority 分开。
- 通过单测、受控杀伤链 probe 和后续 Stage-2 训练指标保留最小 witness。

不纳入：

- 不创建 A9。
- 不重开已封存的 A2 archive 包。
- 不声明真实 Pk、真实引信、真实 AIM-120C 杀伤或 MQ-9 特例击杀。
- 不用“直接坠毁规则”替代损伤链。
- 不做训练提速；多 world 提速属于单独性能工作。
- 没有反复训练/评估证据前，不声明本子项目 accepted。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Idea Seed` | 固定问题位置和边界 | 当前讨论 | 本 README 存在并链接到 A2 指针 | pass |
| `P1 Boundary` | 定义可奖励后果、观测字段和禁止声明 | 用户要求回到奖励扩展 | 形成 task cluster 文档 | pass |
| `P2 Runtime Surface` | 增加有边界的后果奖励消费 | P1 边界成立 | 聚焦测试覆盖变化量/转移语义 | pass |
| `P3 Consequence Probe` | 为受控杀伤链 probe 和后续 Stage-2 训练消费者准备证据报告 | P2 测试通过 | Stage-2 opt-in 已存在，process probe 可分开发射项和后果项 | partial |
| `P4 Closure` | 记录 accepted slice 或 residual | P3 证据存在 | README/status 和父级指针一致 | planned |

## 任务簇

- 任务簇计划：
  [damage_consequence_reward_surface_task_clusters_20260609.md](damage_consequence_reward_surface_task_clusters_20260609.md)
- 当前派发队列：
  [damage_consequence_reward_surface_dispatch_queue_20260609.md](damage_consequence_reward_surface_dispatch_queue_20260609.md)

## 输出和证据

- 已有 active 任务簇计划。
- `gym_envs/scenario_loader/reward_runtime/air_combat.py` 已加入可选的后果变化量 shaping，读取飞机损伤和严重触地转移。
- `tests/runtime/air_combat/test_air_combat_reward_surface.py` 覆盖目标后果正奖励、自身受损惩罚、静态损伤不重复给分和安全触地拒绝。
- `scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json`
  已显式 opt-in 低权重 consequence shaping，仅作为 synthetic training feedback。
- `tools/diagnostics/air_combat_weapon_employment_process_probe.py` 现在可以按 target/self 前缀导出逐步和逐 episode 的 DCR reward totals。
- `tools/diagnostics/air_combat_weapon_employment_process_probe.py --diagnostic_dcr_bridge`
  现在只在 diagnostics probe 内叠加 DCR reward terms，并输出简洁的
  `controlled_consequence_bridge_records`；当前 fixed-fire record 仍为
  `damage_consequence_reward_total=0.0`。
- `2026-06-09` 使用
  `experiments_tmp/a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1/final_model.zip`
  做 2 episode x 512 step model-mode probe：模型保持雷达和主武器开关打开，但没有触发发射；
  release/effects/damage/DCR reward 均为 0，因此它不是后果证据。
- DCR-E-P2 只验收为 implementation bridge / blocker record，不作为 consequence evidence。
- DCR-E-R1 作为只读 re-scope evidence 验收。它建议把
  `DCR-E-P3 Controlled Consequence Fixture Probe` 作为现有 DCR-E cluster 内的下一实现包。

## 验收门

本 follow-on 只有在以下条件满足后才能标记为 accepted：

- 损伤后果字段能稳定观测，且不依赖旧 `Health` 作为主真值。
- 不同后果的 reward 权重不会鼓励明显虚假的仿真漏洞。
- training synthetic calibration 与真实武器/目标 authority 明确分离。
- A2/A8 已封存或已验收边界不被误写成更高权威。
- 受控 consequence-chain probe、replay artifact 或后续 Stage-2 run 能把新后果项和 launch/firing 项分开报告。

## 残余和下一步

- 第一刀：reward runtime 读取飞机损伤与触地 debug state，作为可配置变化量/转移 shaping。
- Stage-2 已用保守权重 opt-in，作为未来训练消费者；当前候选模型不会发射，因此不是杀伤链验证证据。
- 下一步证据：派发 `DCR-E-P3 Controlled Consequence Fixture Probe`，通过 diagnostics/probe
  surface 产生非零 DCR-readable aircraft/ground consequence snapshot。若 fixture 证据不能收口，
  再把从 damage-report projections 到 DCR terms 的 reward mapping 作为单独 semantic packet 保留。
- 后续：构建“连续后果观测诊断”表，把任务/机动/传感/生存能力、飞机内部损伤、燃油/火灾、触地生命周期和 inactive 变化放到同一张验收表中。

## Archive

被替代的规划记录只有在出现 replacement current-status 或 closeout surface 后，才移入本地 `archive/` 目录。
