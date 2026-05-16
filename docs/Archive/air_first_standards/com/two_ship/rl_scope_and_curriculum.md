# 双机阶段 RL 范围与课程计划 (RL Scope and Curriculum for Two-Ship Stage)

> ARCHIVED NOTE (2026-03-23): 该文档属于第一版 air-specific 双机标准草案，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/Workshop/CMO/docs/standards/README.md)。

本文档定义双机阶段的 RL 训练边界，目标是在保持真实性的前提下控制复杂度。

## 1. 为什么双机 RL 复杂度会陡增

双机协同相对单机训练，复杂度上升主要来自四类耦合：

### 1.1 角色耦合

lead 和 wingman 的动作不是独立的：

- lead 的战术决策会改变 wingman 的可行动作空间
- wingman 的位置误差会反过来影响 lead 的任务选择

### 1.2 观测耦合

双机协同必须加入：

- 队内相对几何
- 机间通信状态
- 编队模板约束
- 失队 / 重组状态

这比单机纯导航 / terminal 观测明显更复杂。

### 1.3 归因耦合

双机 reward 很容易失真：

- lead 选得对，但 wingman 没跟上
- wingman 跟得对，但 lead 机动太猛
- 两机都没撞机，但整个 element 脱队

若没有分层课程，reward credit assignment 会迅速恶化。

### 1.4 安全耦合

双机阶段新增的硬约束包括：

- 撞机风险
- 最小安全间隔
- 过大闭合率
- 遮挡与失视
- terminal 阶段的队形解散 / 回收规则

## 2. 双机阶段不该怎么训

本阶段明确不建议：

- 两架飞机同时从零开始联合训练
- C2、lead、wingman 三层一起端到端训练
- 直接进入双边自博弈
- 一开始就扩成四机

这些做法既不真实，也几乎必然造成训练不稳定。

## 3. 推荐训练顺序

### Phase 0: 全脚本双机基线

目标：
- 先验证双机场景、编队模板、奖励与终止条件是否合理

要求：
- lead 脚本
- wingman 脚本
- 不引入 RL

通过标准：
- 双机起飞
- 集合成功
- 保持编队进入 CAP / route
- 编队 RTB / recover

### Phase 1: Wingman-only RL

目标：
- 在脚本 lead 下训练僚机

输入：
- lead 的意图
- 队内相对状态
- 编队 slot 误差

输出：
- 僚机的协同命令选择或受限 `LeaderIntent`

此阶段不训练：
- C2
- lead 的战术决策

这样做最符合现实：
- wingman 首先学会“怎么跟、什么时候重组、什么时候报告 unable”

### Phase 2: Lead-only RL

目标：
- 在脚本 wingman 下训练 element lead

输入：
- 双机整体状态
- wingman 状态 / 队形质量
- 任务线程 / terminal 几何

输出：
- element 级意图
- wingman 协同模式
- 路线 / RTB / recover 时机

此阶段仍不训练：
- C2

### Phase 3: Lead + Wingman 交替训练

目标：
- 不是同时自由 co-train，而是交替冻结训练

推荐方式：
- 固定 lead，训 wingman
- 固定 wingman，训 lead
- 周期性交替

不建议：
- 第一版就完全同时更新

### Phase 4: 四机 package

只有在双机阶段稳定后才进入：

- `Package Lead`
- `Element Lead`
- `Wingman`

这一步不是双机阶段内容，只是接口上需要现在预留。

## 4. 现实优先的动作空间建议

### 4.1 Wingman

优先采用有限协同动作，而不是完全自由飞行三元组。

建议动作：

- `HOLD_SLOT`
- `REJOIN`
- `OFFSET_LEFT`
- `OFFSET_RIGHT`
- `TRAIL`
- `SUPPORT`
- `ABORT_FORM`

含义：
- wingman 学的是协同纪律，不是重写整个 sortie 导航

### 4.2 Lead

lead 仍然走“选阶段、选协同模式、选 route / recover 时机”这一路，不应退化为每步手拧 wingman 参数。

## 5. 奖励设计建议

双机阶段奖励必须分层：

### 5.1 Element 级奖励

- 全编队任务完成
- 编队完整返航
- CAP / route 阶段保持战术完整性

### 5.2 Lead 级奖励

- 任务推进合理
- 不把 wingman 拉爆闭合率或拉丢
- 回收时机正确

### 5.3 Wingman 级奖励

- slot 保持
- 安全间隔
- join / rejoin 成功
- 对 lead 指令的稳定跟随

## 6. 本阶段的工程结论

双机阶段必须遵守以下训练约束：

- 先做全脚本双机基线
- 先训 wingman-only 或 lead-only，不同时从零训练
- 不把 C2 纳入第一轮 RL
- 不直接进入四机与自博弈

这不是“为了省事”，而是为了让训练复杂度与真实性同时可控。
