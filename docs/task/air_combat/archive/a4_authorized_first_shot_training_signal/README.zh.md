# A4 授权首发训练信号

状态：`2026-06-08 closed / historical firing-signal line superseded`。A4
保留 reward/routing 不能让模型学会发射的历史证据；当前发射闭合问题已经迁移并由
M3-S2 有边界发射门验收记录收口：
[../../model/archive/m3_s2_fire_timing_learnability_audit/README.zh.md](../../../model/archive/m3_s2_fire_timing_learnability_audit/README.zh.md)。

语言：

- 英文规范页：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- 父级空战任务：[../README.zh.md](../../README.zh.md)
- A3 C2/ROE 发射纪律层：
  [../a3_c2_roe_release_discipline/README.zh.md](../a3_c2_roe_release_discipline/README.zh.md)
- M1 动作接口拆分：
  [../../model/m1_action_interface_split/README.zh.md](../../../model/m1_action_interface_split/README.zh.md)
- M1 时间窗证据：
  [../../model/m1_temporal_window_hmoe/README.zh.md](../../../model/m1_temporal_window_hmoe/README.zh.md)
- 子项目创建标准：
  [../../../agent/rules/subproject_creation_standard.zh.md](../../../../agent/rules/subproject_creation_standard.zh.md)

## Purpose

A3 已经让 C2/ROE 发射纪律可观察、可测试，但修复后的 learned-policy 证据仍显示：
deterministic policy 不开火。本子项目处理下一步有边界修复：先让授权首发变得可训练，
再讨论 M2 或更大的 sequence-native policy 工作。

目标行为很窄：在 S1 C2/ROE single-shot-then-assess probe 中，策略应学会
radar / TMS / master-arm / weapon-select / fire 这条链，并形成一次授权首发。
这不是导弹物理、Pk、引信、真实 BVR 战术或完整 C2 层级 release。

## 历史证据状态

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| 生命周期 | closed；superseded | M3-S2 后续在 A5 weapon-arm action-frame fix 后验收有边界发射门。 | A4 不再是当前发射阻塞项。 |
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
| `P0 Boundary` | 将 A4 冻结为训练信号工作。 | A3 accepted 但 deterministic policy 不发射。 | README 和 task clusters 写明范围与非目标。 | pass |
| `P1 Reward Signal` | 增加授权武器链 shaping。 | 既有 A3 reward surface 和测试。 | focused tests 证明新 terms 受授权与 single-shot 状态约束。 | pass |
| `P2 Config Probe` | 在维护中的 S1 C2/ROE probe 打开 shaping。 | P1 reward keys 存在。 | active-entry tests 证明场景/config surface 携带 knobs。 | pass |
| `P3 Learned Evidence` | 运行有边界短训/probe。 | P1/P2 测试通过。 | 记录 deterministic/stochastic fire 和 release 变化。 | partial |
| `P4 Routing Review` | 判断 policy routing 是否需要 weapons family。 | P3 证据完成。 | 文档化或实现 routing 建议并配测试。 | pass |
| `P5 Binary Diagnostics` | 暴露 binary logits/probabilities，并测试一次有边界 reward urgency trial。 | P4 route evidence held。 | diagnostics 和 rejected trial 已记录。 | pass, held outcome |
| `P6 Closure` | 同步父级文档与残余。 | P5 完成。 | A4 作为历史负证据关闭，发射残余交给后续模型工作。 | closed；superseded by M3-S2 |

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

这是历史 A4 验收门。A4 现在是 closed，不是独立发射方案 accepted。

本子项目只能在以下条件满足后标记为 accepted：

- 维护中的 S1 C2/ROE probe 在 deterministic learned policy 下形成授权首发，或残余被
  明确归因到 policy routing / optimization，而不是单纯 reward 稀疏。
- reward breakdown tests 证明新 shaping 不能绕过 hold-fire、unauthorized、
  shot-budget 或 pending-assessment 约束。
- 父级 A3/M1/M2 文档明确这只是训练证据，不释放 M2、导弹 authority 或真实战术声明。

## 收口

- A4 原地关闭，作为历史负证据保留。
- 保留结论很简单：reward shaping、HMoE routing、binary diagnostics 和 opportunity
  penalty 都没有让模型学会发射。
- 当前发射问题不要默认回开 A4；有边界发射闭合的权威记录是 M3-S2。
- 发射时机、多场景稳健性、效果和杀伤链问题属于后续 model/A8 follow-on。

## Archive

完整 A4 包已归档到 `docs/task/air_combat/archive/`。原任务路径现在只保留轻量指针
README。
