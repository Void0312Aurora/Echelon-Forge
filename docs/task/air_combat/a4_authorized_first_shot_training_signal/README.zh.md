# A4 授权首发训练信号

状态：`2026-06-03`，作为已 accepted 的 A3 C2/ROE 层之后的 active follow-on；
reward-side、routing 与 post-routing learned evidence 已记录。由于 deterministic policy
仍不 fire，A4 继续 held。

语言：

- 英文规范页：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- 父级空战任务：[../README.zh.md](../README.zh.md)
- A3 C2/ROE 发射纪律层：
  [../a3_c2_roe_release_discipline/README.zh.md](../a3_c2_roe_release_discipline/README.zh.md)
- M1 动作接口拆分：
  [../../model/m1_action_interface_split/README.zh.md](../../model/m1_action_interface_split/README.zh.md)
- M1 时间窗证据：
  [../../model/m1_temporal_window_hmoe/README.zh.md](../../model/m1_temporal_window_hmoe/README.zh.md)
- 子项目创建标准：
  [../../../agent/rules/subproject_creation_standard.zh.md](../../../agent/rules/subproject_creation_standard.zh.md)

## Purpose

A3 已经让 C2/ROE 发射纪律可观察、可测试，但修复后的 learned-policy 证据仍显示：
deterministic policy 不开火。本子项目处理下一步有边界修复：先让授权首发变得可训练，
再讨论 M2 或更大的 sequence-native policy 工作。

目标行为很窄：在 S1 C2/ROE single-shot-then-assess probe 中，策略应学会
radar / TMS / master-arm / weapon-select / fire 这条链，并形成一次授权首发。
这不是导弹物理、Pk、引信、真实 BVR 战术或完整 C2 层级 release。

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A3 C2/ROE 合同 | accepted | A3 README 和 focused tests 已暴露授权、shot budget、pending assessment 与 release buckets。 | 不证明 learned weapon employment 已经学会。 |
| reactive/temporal 证据 | held | `2026-06-03` 32k 对照：temporal stochastic 清零违规发射，但 deterministic 仍不发射。 | temporal memory 单独不能作为修复验收。 |
| reward surface | partial | A4 reward probe 增加 episode 内一次性授权武器链 shaping 和更强违规惩罚。 | reward-only tuning 没让 deterministic fire。 |
| learned evidence | partial | `2026-06-03` A4 32k temporal probe：deterministic 0 fire/release；stochastic 11 release、3 授权、8 违规。 | 不验收策略；它把下一刀收窄到 pulse/routing mechanics。 |
| policy routing | pass | `2026-06-03` routing probe 为 `air_combat_c2_roe_v1` 增加 combat-weapons HMoE family，并测试 stats surface。 | 尚不证明 learned authorized release。 |
| post-routing learned evidence | held after evidence | `2026-06-03` retained routed temporal 32k probe 中 deterministic 仍为 0 fire/release；stochastic 产生 15 次 attempt、9 次 release、3 次授权 release、6 次 violation release 和 2 次 damage report。 | 保留 route 小幅改善 stochastic 发射纪律，但 A4 不验收。 |
| binary diagnostics / opportunity trial | held after evidence | `2026-06-03` binary diagnostics 显示 authorized-window `fire_weapon` probability 约 `0.22%`，max logit 约 `-6.11`；临时 fire-opportunity penalty 完成 32k 后 deterministic 仍不 fire，stochastic 发射纪律退化。 | 单纯 reward magnitude / urgency tuning 不作为下一步 active default。 |

## Scope

In scope:

- 增加有边界的 reward terms，让授权首发链条在训练中可达。
- 保持 C2/ROE single-shot budget 和发射后 pending-assessment 惩罚有效。
- 增加 focused reward/config tests 和短训证据。
- 分析 HMoE routing 是否需要 air-combat / weapons-employment route。

Out of scope:

- 把环境侧静默吞掉 fire 动作作为主要修复。
- 导弹物理、弹药 runtime、毁伤 authority、Pk authority 或引信 authority 修改。
- M2 release、causal transformer 实现、自博弈、`2v2` 或真实 BVR shot doctrine。

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 将 A4 冻结为训练信号工作。 | A3 accepted 但 deterministic policy 不发射。 | README 和 task clusters 写明范围与非目标。 | active |
| `P1 Reward Signal` | 增加授权武器链 shaping。 | 既有 A3 reward surface 和测试。 | focused tests 证明新 terms 受授权与 single-shot 状态约束。 | pass |
| `P2 Config Probe` | 在维护中的 S1 C2/ROE probe 打开 shaping。 | P1 reward keys 存在。 | active-entry tests 证明场景/config surface 携带 knobs。 | pass |
| `P3 Learned Evidence` | 运行有边界短训/probe。 | P1/P2 测试通过。 | 记录 deterministic/stochastic fire 和 release 变化。 | partial |
| `P4 Routing Review` | 判断 policy routing 是否需要 weapons family。 | P3 证据完成。 | 文档化或实现 routing 建议并配测试。 | pass |
| `P5 Binary Diagnostics` | 暴露 binary logits/probabilities，并测试一次有边界 reward urgency trial。 | P4 route evidence held。 | diagnostics 和 rejected trial 已记录。 | pass, held outcome |
| `P6 Closure` | 同步父级文档与残余。 | P5 完成。 | 更新 M1/M2 决策且不做越界声明。 | planned |

## Task Clusters

- 任务簇计划：
  [a4_authorized_first_shot_training_signal_task_clusters_20260603.zh.md](a4_authorized_first_shot_training_signal_task_clusters_20260603.zh.md)

## Outputs And Evidence

当前输出：

- A4 子项目范围与任务簇 packet。
- 面向授权武器链准备和授权 fire/no-release 的可配置 A3/A4 reward terms。
  正向准备项按 episode 一次性发放。
- focused runtime 和 active-entry tests。
- reward-side evidence：
  [a4_authorized_first_shot_reward_probe_20260603.zh.md](a4_authorized_first_shot_reward_probe_20260603.zh.md)
- routing evidence：
  [a4_authorized_first_shot_routing_probe_20260603.zh.md](a4_authorized_first_shot_routing_probe_20260603.zh.md)
- post-routing learned-policy evidence：
  [a4_authorized_first_shot_post_routing_probe_20260603.zh.md](a4_authorized_first_shot_post_routing_probe_20260603.zh.md)
- binary diagnostics 与被拒绝的 opportunity-penalty evidence：
  [a4_authorized_first_shot_binary_diagnostics_20260603.zh.md](a4_authorized_first_shot_binary_diagnostics_20260603.zh.md)

## Acceptance Gate

本子项目只能在以下条件满足后标记为 accepted：

- 维护中的 S1 C2/ROE probe 在 deterministic learned policy 下形成授权首发，或残余被
  明确归因到 policy routing / optimization，而不是单纯 reward 稀疏。
- reward breakdown tests 证明新 shaping 不能绕过 hold-fire、unauthorized、
  shot-budget 或 pending-assessment 约束。
- 父级 A3/M1/M2 文档明确这只是训练证据，不释放 M2、导弹 authority 或真实战术声明。

## Residuals And Next Steps

- HMoE 现在已经为 `air_combat_c2_roe_v1` 增加显式 air-combat weapons-employment route。
- post-routing learned-policy evidence 已记录但 held：deterministic 仍不 fire，
  stochastic 在首枚授权发射后仍会重复发射。
- binary-logit/probability diagnostics 已保留：deterministic `fire_weapon`
  在授权窗口内仍约为 `0.22%` probability / `-6.11` max logit。
- 有边界的 authorized fire-opportunity penalty trial 已拒绝作为 active default；
  它让 reward 更负，但没有推动 deterministic fire，且恶化 stochastic release discipline。
- 下一项残余已提升为 A5：
  [../a5_constrained_event_action_model/README.zh.md](../a5_constrained_event_action_model/README.zh.md)。
  A5 将 `fire_weapon` 作为受约束事件动作处理，而不是继续追加 reward-only pulse target。
- 在 A5 而非 A4 reward/routing repair 单独证明 deterministic 授权首发稳定前，M2 继续 held。

## Archive

当 A4 有 current-status 或 closeout 记录后，过期证据和带日期校准记录应移入
`archive/README.md`。
