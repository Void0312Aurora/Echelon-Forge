# 发射决策架构整理与重构计划

语言：
- 英文规范版：README.md
- 本文件为中文伴随版。

文档类型：plan
生命周期：draft
规范位置：docs/learning/work/issues/launch_decision_reorg/README.md
负责人：learning/policy-architecture
最后核验：2026-09-19
状态：暂存提案；未授权实现。

## 授权边界

这是一份有界的架构计划，不是实现工作包。它不授权移动代码、改动模型
参数、改变 rollout 语义、改变运行时合法性、批量改写活动配置，或发布新的
验收结论。

只有负责人接受本计划并在合适的 active 工作面建立独立工作包后，才可以开始
实现。该工作包必须列出精确文件范围、兼容行为、聚焦测试、验收证据和残留
问题负责人。本计划不会修改现有脏的治理工作树或其他无关工作树。

计划文档预算固定为两个文件：英文规范版和本中文伴随版；不另建 dispatch
队列、ledger 或验收报告。

## 事实基线

维护中的策略执行架构标准已经区分 observation、actor latent、action
distribution、policy-visible support、A5 运行时合法性、辅助 head 和诊断。
当前实现仍有以下整理缺口：

- HMoE residual 作用于完整 hybrid action 参数向量，event slice 可能在
  专用 event head 之前被战术分支改变。
- policies.py 的 event 组合逻辑可在 hybrid_event_head、stopping head 和
  window-classifier adapter 之间切换；同时启用时存在隐式优先级，而不是
  在配置层拒绝冲突。
- ppo_adaptive_kl.py 通过 first-event、credit、grouped-stopping、
  event-window 四个 mixin 组合大量扁平参数，sidecar、目标、优化器归属和
  前向耦合难以从一个契约核对。
- model_contracts.py 对 window-classifier 和 direct fire-boundary 有细化
  契约，但尚无覆盖所有 event owner、辅助证据、互斥配置和迁移规则的统一
  launch-decision 契约。
- 当前 direct-boundary 活动探针明确关闭 stopping/window adapter；这是兼容
  基线，不是代码已经阻止所有隐式切换的证明。
- A5 才是最终运行时权威。requested、accepted、release 和 auxiliary
  信号必须分开报告。

这些是架构归属发现，不等于当前策略已经或没有完成一次合法发射。学习发射
验收仍只使用维护标准中定义的窄门槛。

## 目标归属

提议的目标边界如下，待独立审查后才能进入实现：

| 表面 | 目标角色 | 对采样事件的允许影响 |
| --- | --- | --- |
| HMoE 战术分支 | 连续/动作族 residual | 不得无声明地拥有 event slice |
| opportunity/window | 机会证据 w_t | 只能经明确 typed adapter 进入 |
| stopping/trigger | 条件证据 h_t | 只能经同一显式 adapter 模式进入 |
| credit | 辅助值和诊断 | 默认不改变事件 |
| hybrid_event_head | 默认唯一的 learned executable owner | 直接产生 hold/fire logit residual |
| LaunchDecisionComposer（候选提取边界） | 解析 owner、证据组合和顺序 | 不允许隐藏优先级 |
| policy support mask | 采样前的 legal_t | 限制支持集，不代表 A5 接受 |
| A5 状态机 | 最终合法性和一次性消费 | 接受或拒绝 pulse |

第一阶段保留 hybrid_event_head 的参数名和状态字典形状，避免为了整理命名
引入新的 learned event owner。若旧 checkpoint 的 HMoE event residual 无法在
不变形状下隔离，必须把它明确记为兼容 adapter，并单独安排移除。

## 必须保持的不变量

1. 每个 policy instance 只有一个 learned executable event owner；stopping
   与 window 冲突必须在训练前报错。
2. HMoE event residual 要么排除 event slice，要么作为有名的兼容 adapter，
   记录其归属；不能继续作为隐藏副作用。
3. 证据、executable owner、policy mask、distribution、pulse 和 A5 接受
   的顺序必须可观测。
4. auxiliary-only head 不能作为 learned-firing 验收证据；adapter-coupled
   head 必须有 gradient、detach、确定性和随机行为测试。
5. optimizer group 和 dedicated update 必须指向同一个声明的 owner。
6. 旧 flag 和 checkpoint 要么显式映射并记录兼容模式，要么给出可操作错误；
   静默 precedence 不算兼容。
7. A5 的 mask、authority、readiness、ammo、FiredAssess 和重复抑制不能被
   重构削弱。
8. M3-S1/M3-S2 作为历史 metric/mechanism 名称可保留，但不能作为新的模块、
   head、配置字段或 active 文件名前缀。

## 有限任务簇

本计划不派发实现 worker。若批准后建立实现包，只能使用以下有限任务簇；每簇
最多两轮，超出则重新定界。C0/C1 串行，C2/C3/C4 只有在 C1 接受后且文件
范围不重叠时才能并行，C5 始终最后串行。

- C0 基线与权威冻结：核对当前图、活动 direct-boundary 配置、checkpoint、
  术语和验收字段；不改生产代码。门槛是负责人确认事实和非目标。
- C1 typed contract 与 owner 矩阵：定义唯一 owner、adapter 互斥、证据/
  gradient 语义、兼容模式和冲突错误；只改契约面。门槛是每个现有 flag
  都有默认值、归属、迁移和拒绝规则。
- C2 前向归属边界：在保留 direct-boundary 行为的前提下提取或显式化
  event composition；只改 policies.py 及必要的 HMoE event-slice helper。
  门槛是 owner trace、event-slice、log-prob、entropy 和旧 checkpoint 测试。
- C3 目标、rollout 与 optimizer 对齐：对齐 event-window、fire-boundary、
  stopping、credit、first-event sidecar 和优化器归属；不新增 label。门槛
  是梯度隔离、censoring/source 元数据和 metric 兼容测试。
- C4 配置与 checkpoint 迁移：把扁平 PPO/policy kwargs 显式翻译为 typed
  spec；不批量覆写 active config，不破坏 A5。门槛是代表性配置、冲突矩阵、
  序列化往返和 key/shape 比较。
- C5 验收与 closure：串行运行聚焦测试、架构/路径/worktree 审计，收齐
  worker packet 和独立审查，最后给出 Mergeable、Blocked 或 Closed。不得在
  closure 阶段偷偷扩大实现范围。

每个 delegated worker 必须返回 status、touched files、commands/outcomes、
remaining paths、behavior risks 和 integration notes。主线程保留最终范围、
验收和发布决定。

## 后续实现顺序与验证

批准后先冻结 C0，再以无行为变化的 C1 契约进入；随后让 C2 在兼容路径下比较
旧/新 logits、mask、log-prob、entropy 和 state-dict；C3/C4 只有在 owner trace
稳定后才能合并；最后 C5 才能处理弃用和文档 closure。

现有证据线仍必须保留：

    python -m pytest tests/policy/test_execution_policy_event_heads.py
    python -m pytest tests/policy/test_event_head_update_contracts.py
    python -m pytest tests/training/test_event_timing_training_config_contracts.py
    python -m pytest tests/runtime/air_combat/test_fire_action_release_gate.py

最终实现还应增加唯一 owner、冲突拒绝、HMoE event-slice、梯度/优化器归属、
旧配置和 checkpoint 往返、support mask、随机/确定性 distribution，以及
accepted/rejected fire_once 和重复抑制的测试。必须分别报告 requested、
accepted、release、authorized release、拒绝原因和 repeat suppression；kill、
damage、Pk 或 effects 不能替代发射验收。

## 审查状态

下一步是对本次计划 revision 做只读独立审查。审查 agent 不得编辑工作树，
必须检查本计划、维护标准、治理规范和引用的源码/测试面，并返回：

    status: pass | partial | blocked | failed
    touched files: none
    commands/outcomes:
    remaining paths:
    behavior risks:
    integration notes:

在负责人根据审查决定修订、建立实现包或继续暂存之前，本问题保持 draft，
没有任何实现授权。
