# A3 C2/ROE 发射纪律

状态：`2026-06-02` planning。本子项目定义空战 C2、ROE 与发射纪律约束层；
在这层明确前，不再把同一目标多枚导弹问题直接归因为策略记忆失败。

语言：

- 英文规范页：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- 父级空战任务：[../README.zh.md](../README.zh.md)
- A1 分阶段 `1v1` 课程：
  [../a1_1v1_realism_gradient/README.zh.md](../a1_1v1_realism_gradient/README.zh.md)
- M1 观测窗口证据：
  [../../model/m1_temporal_window_hmoe/README.zh.md](../../model/m1_temporal_window_hmoe/README.zh.md)
- M1 动作接口拆分：
  [../../model/m1_action_interface_split/README.zh.md](../../model/m1_action_interface_split/README.zh.md)
- 子项目创建标准：
  [../../../agent/rules/subproject_creation_standard.zh.md](../../../agent/rules/subproject_creation_standard.zh.md)
- 公开来源准入：
  [../../../standards/foundation/public_data_source_admission.zh.md](../../../standards/foundation/public_data_source_admission.zh.md)
- 真实性与 authority 边界：
  [../../../standards/foundation/realism_authority_boundary.zh.md](../../../standards/foundation/realism_authority_boundary.zh.md)
- 公开来源扫描：
  [c2_roe_public_source_scan_20260602.zh.md](c2_roe_public_source_scan_20260602.zh.md)
- 代码表面扫描：
  [c2_roe_code_surface_scan_20260602.zh.md](c2_roe_code_surface_scan_20260602.zh.md)

## Purpose

当前 Stage-1 `1v1` 训练线中，蓝方可能对同一目标连续发射多枚导弹，却没有明确
战术理由。M1 已证明短历史观测是可用的 runtime 基础设施，但它本身并不定义何时
允许开火、何时允许第二发、何时必须等待评估，或何时必须停火。

A3 要补的是这层缺失的指挥约束。它把公开 C2/ROE 概念收敛为有边界的仿真合同：
武器控制状态、目标身份、交战命令、开火授权和 shot policy 应成为可观测、可测试、
可训练的事实。目标不是复刻保密战术，而是让 S1/M1 能把重复发射区分为：
授权齐射、授权再攻击、过早第二发，或 ROE 违规。

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| 公开 C2/ROE 术语 | planning | 公开来源扫描记录 WCS、engage/hold/cease/abort、bandit/hostile 和授权链边界。 | 公开来源只支持术语和状态机设计，不支持真实 BVR 战术或导弹发射纪律。 |
| 现有 runtime 命令字段 | 可用但空战策略未充分消费 | `mission_command` 已有 `authorization_to_fire`、`roe_state`、授权 holder/grantor、分配目标和目标快照字段。 | 这些字段还不是完整的空战发射纪律合同。 |
| 空战 S1 场景 | 存在缺口 | 当前 S1 `mission_command` 直接 `authorization_to_fire=true`，active 训练配置仍使用 `mission_obs_mode=basic`。 | `basic` 不向策略暴露 ROE、授权、目标分配或 shot policy。 |
| 海军 ROE 先例 | 可借鉴 | `naval_screen_station_v1` 已暴露 `roe_state`、`authorization_to_fire` 和目标字段，并有 ROE hold/authorization 奖励项。 | 海军 screen 逻辑只能指导 wiring 形态，不能定义空战战术。 |
| M1 证据 | 作为 held 输入 | Hybrid temporal shaped Stage-1 稳定运行，但仍出现重复发射。 | 这不能证明记忆无效；它说明 command/ROE 面仍未定义充分。 |

## Scope

In scope:

- 定义空战 C2/ROE 状态合同，用于训练和诊断。
- 将 target assignment / commit 与 engagement / fire authorization 分离。
- 暴露空战 mission observation 字段：授权、WCS、目标身份、分配目标、shot policy
  和 pending assessment。
- 定义 hold、未授权开火、授权首发、过早第二发、授权齐射、授权再攻击、
  cease/abort 覆盖命令的奖励和诊断语义。
- 在重开 M2 release 前，增加 S1 C2/ROE probe 场景和配置。
- 在 A3 合同可观测后，重新解释 M1 重复发射指标。

Out of scope:

- 保密或平台专用 ROE、真实 BVR timeline、真实 shot doctrine 或真实齐射战术。
- 通用 C2 仿真、多机指挥层级或完整数据链模型。
- 导弹物理、毁伤 authority、Pk authority、引信 authority 或弹药 runtime 修改。
- sequence-native PPO、recurrent memory、M2 release、自博弈或 `2v2` 战术。
- 把环境侧静默吞掉发射动作作为主要修复方式。

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结公开来源和 authority 边界。 | 用户要求补充 C2/ROE 约束。 | 来源扫描记录可安全事实和不可声明内容。 | active |
| `P1 Code Surface` | 盘点现有命令、观测、奖励、场景和诊断路径。 | 当前已有空战与海军 ROE 相关代码。 | 切入点地图写明文件、字段、测试和残余。 | active |
| `P2 Contract` | 定义空战 C2/ROE schema 与状态转换。 | P0/P1 事实接受。 | `air_combat_c2_roe_v1` 字段和值域文档化。 | planned |
| `P3 Implementation` | 接入观测、奖励、诊断和场景/config probe。 | P2 合同稳定。 | focused tests 通过，S1 C2/ROE probe 可运行。 | planned |
| `P4 Evidence` | 在 A3 约束下对比 reactive/temporal 行为。 | P3 probe 入口存在。 | 重复发射指标能拆分授权与违规情况。 | planned |
| `P5 Closure` | 同步文档、残余和 M1/M2 决策。 | P4 证据记录完成。 | A3 被 accepted、held 或带残余缩窄。 | planned |

## Task Clusters

- 任务簇计划：
  [a3_c2_roe_release_discipline_task_clusters_20260602.zh.md](a3_c2_roe_release_discipline_task_clusters_20260602.zh.md)
- 英文规范页：
  [a3_c2_roe_release_discipline_task_clusters_20260602.md](a3_c2_roe_release_discipline_task_clusters_20260602.md)

## Outputs And Evidence

计划输出：

- C2/ROE 术语的公开来源与不可声明内容扫描。
- 当前 mission-command、观测、release gating、reward、场景、配置和 process probe
  切入点的代码表面扫描。
- 空战 C2/ROE mission observation 合同。
- mission observation 字段、场景 round-trip、奖励项和训练入口 bootstrap 的 focused tests。
- 位于维护路径下的 S1 C2/ROE probe 场景/config 对。
- 过程探针指标：总发射、无效发射、未授权发射、过早第二发、授权齐射、再攻击发射。
- M1 证据更新：判断 C2/ROE 可观测后，重复发射是否仍是记忆问题。

## Acceptance Gate

本子项目只能在以下条件满足后标记为 accepted：

- 来源扫描已链接，所有现实作战表述都保持公开、保守、非保密。
- 空战 C2/ROE schema 进入策略观测，不依赖只有 reward 才知道的隐藏状态。
- S1 C2/ROE probe 能区分 hold、授权单发、授权齐射和过早第二发。
- 测试覆盖 mission-observation shape/fields、命令字段 round-trip、奖励/诊断项和
  active training entry bootstrap。
- M1/M2 文档明确区分“记忆证据”和“缺少 command/ROE 约束”。

## Residuals And Next Steps

- self-defense override 在首个 S1 命令合同 accepted 前保持 held。
- 长机/僚机授权委派在单机 C2/ROE 语义稳定前保持 held。
- 数据链、外部传感器和 friend/no-fire-zone 逻辑是未来扩展，不是 A3 验收条件。
- 若 A3 约束可观测后仍出现重复未授权开火，再把剩余问题交回 M1/M2 作为策略记忆
  或序列模型问题。

## Archive

当 current-status 或 closeout 文档替代带日期计划后，过期 A3 计划和 worker packet
应移入 `archive/README.md`。
