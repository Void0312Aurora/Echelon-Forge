# A5 受约束事件动作模型

状态：`2026-06-08 closed / structural event-action line superseded by M3-S2
firing closure`。A5 保留 event-action surface 和 A5 weapon-arm action-frame fix
的历史证据，但它不再是当前发射阻塞项。当前有边界发射闭合权威记录是：
[../../model/archive/m3_s2_fire_timing_learnability_audit/README.zh.md](../../../model/archive/m3_s2_fire_timing_learnability_audit/README.zh.md)。

语言：

- 英文规范页：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- 父级空战任务：[../README.zh.md](../../README.zh.md)
- A3 C2/ROE 发射纪律：
  [../a3_c2_roe_release_discipline/README.zh.md](../a3_c2_roe_release_discipline/README.zh.md)
- A4 授权首发训练信号：
  [../a4_authorized_first_shot_training_signal/README.zh.md](../a4_authorized_first_shot_training_signal/README.zh.md)
- M1 动作接口拆分：
  [../../model/m1_action_interface_split/README.zh.md](../../../model/m1_action_interface_split/README.zh.md)
- 子项目创建标准：
  [../../../agent/rules/subproject_creation_standard.zh.md](../../../../agent/rules/subproject_creation_standard.zh.md)
- 本轮调研输入，作为非权威设计材料：
  [temp-01](../../../../temp/6/6·3/temp-01.md)、
  [temp-02](../../../../temp/6/6·3/temp-02.md) 和
  [temp-03](../../../../temp/6/6·3/temp-03.md)

## Purpose

A3 已经让 C2/ROE 发射纪律可观察、可测试。A4 随后证明，reward shaping、
combat-weapons HMoE route、binary diagnostics 和有边界 fire-opportunity penalty
仍不能让 deterministic policy fire。当前保留诊断转为结构性问题：
`fire_weapon` 仍过度接近逐帧 binary / threshold control，而导弹释放本质是受约束
first-event 决策。

本子项目定义并实现长期修正：受约束 semi-MDP event-action 架构。合法性由
C2/ROE/武器状态和 action mask 处理，策略只在有效交战窗口内学习 `hold` 与
`fire_once` 的取舍。

## 历史证据状态

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| 生命周期 | closed；superseded | M3-S2 后续依赖 A5 event-action surface 与 weapon-arm action-frame fix 验收有边界发射门。 | A5 的旧 deterministic no-fire 结果是历史证据，不是当前发射状态。 |
| A3 C2/ROE 约束 | accepted | A3 暴露 authorization、shot budget、pending assessment、salvo 与 reattack 字段。 | 它能分类和约束 release discipline，不证明 learned deterministic release。 |
| A4 reward/routing 修复 | held | A4 binary diagnostics 显示授权窗口内 `fire_weapon` 仍约 `0.22%` probability / `-6.11` max logit；opportunity penalty 已拒绝。 | reward magnitude 与 route selection 不足以作为根治手段。 |
| M1 hybrid action interface | accepted | `air_combat_hybrid_v1` 已拆分连续飞行轴、开关、选择器和 pulse 命令。 | fire pulse 仍需要事件支持、post-launch suppression 和 deterministic eval 语义。 |
| 外部设计材料 | design input | `docs/temp/6/6·3/temp-01..03.md` 一致指向 state machine + mask + event head。 | 这些材料不是 authority；A5 将其转成维护中的任务范围。 |
| Event-action architecture | pass as historical surface；closed | A5 contract、runtime state machine、policy event head、active S1 C2/ROE reward/config cleanup、diagnostics implementation 和短训 learned-policy evidence 已记录。 | A5 自身未关闭发射；M3-S2 后续关闭可执行发射门。 |

## Scope

范围内：

- 将 `engagement_state` 和 `fire_mask` 定义为 policy-visible event-action support，
  而不是 reward preference。
- 在 S1 C2/ROE 训练入口中，把 policy-facing `fire_weapon` threshold 语义替换为
  `MaskedCategorical([hold, fire_once])` 之类的事件 head。
- 硬实现 `AuthorizedReady + fire_once -> FiredAssess`，并在默认情况下 post-launch
  禁射，直到显式 `ReattackReady` 或其他授权后续状态出现。
- 让训练时随机探索和 deterministic evaluation 使用同一套事件动作结构。
- 保留 requested、accepted、rejected、authorized、violation、repeated 和 post-launch
  fire attempt 诊断。
- 决定首版实现采用 masked categorical、event Q-head，或先验收 masked categorical、
  后续再推进 Q/hazard 的分阶段路线。

范围外：

- 导弹物理、制导、Pk authority、deterministic fuze authority 或高保真毁伤 authority 修改。
- 真实 BVR doctrine、涉密 ROE 或真实战机 release authorization 声明。
- 在 A5 acceptance evidence 之前释放 M2 Causal Transformer、`2v2`、self-play 或
  sequence-native policy 实现。
- 将纯 reward tuning 或全局 pulse-prior relaxation 当作主修复。

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 将 A4 held 诊断和 temp 调研转成持久任务范围。 | A4 deterministic fire 仍为 0，reward/routing trial held。 | README、current status、acceptance、dispatch queue、archive 边界和任务簇存在。 | pass |
| `P1 Contract Audit` | 映射当前 action、observation、reward、policy、diagnostic 和 config surface。 | P0 完成。 | 精确实现写集和风险图存在。 | pass |
| `P2 Event Contract` | 定义 `engagement_state`、`fire_mask`、事件动作、状态转移和 deterministic eval 语义。 | P1 事实可用。 | contract 文档冻结 event support 与 reward 的分离；focused implementation tests 留在 P3/P4。 | pass |
| `P3 Runtime Integration` | 为 S1 C2/ROE 实现受约束状态机和 event action adapter。 | P2 contract accepted。 | runtime 从结构上拒绝多发并暴露 post-launch state。 | pass |
| `P4 Policy Integration` | 增加 event action distribution 或 event Q-head，并保持 PPO log-prob/eval 语义正确。 | P2/P3 稳定。 | policy tests 证明 mask、log-prob、entropy/stats 和 deterministic event behavior。 | pass |
| `P5 Scenario And Reward Cleanup` | 将 S1 C2/ROE active entries 转到 event-action 语义，并简化 reward 职责。 | P3/P4 可用。 | config tests 和 reward tests 证明约束不是靠 penalty 学出来的。 | pass |
| `P6 Validation` | 运行 focused tests 和 learned-policy probes。 | 实现路径通过 unit tests。 | deterministic policy 形成一次授权首发，或残余有证据归因。 | pass；historical residual |
| `P7 Closure` | 同步 A3/A4/M1/M2 和父级索引。 | P6 证据完成。 | A5 accepted 或 held，并带显式 residual map。 | closed；superseded by M3-S2 |

## Task Clusters

- 任务簇计划：
  [a5_constrained_event_action_model_task_clusters_20260603.zh.md](a5_constrained_event_action_model_task_clusters_20260603.zh.md)
- 当前状态：
  [a5_constrained_event_action_model_current_status_20260603.zh.md](a5_constrained_event_action_model_current_status_20260603.zh.md)
- 派发队列：
  [a5_constrained_event_action_model_dispatch_queue_20260603.zh.md](a5_constrained_event_action_model_dispatch_queue_20260603.zh.md)
- 验收门：
  [a5_constrained_event_action_model_acceptance_20260603.zh.md](a5_constrained_event_action_model_acceptance_20260603.zh.md)
- Surface audit：
  [a5_constrained_event_action_model_surface_audit_20260603.zh.md](a5_constrained_event_action_model_surface_audit_20260603.zh.md)
- Event action contract：
  [a5_constrained_event_action_model_event_contract_20260603.zh.md](a5_constrained_event_action_model_event_contract_20260603.zh.md)
- Implementation evidence：
  [a5_constrained_event_action_model_implementation_evidence_20260603.zh.md](a5_constrained_event_action_model_implementation_evidence_20260603.zh.md)
- 短训 learned-policy evidence：
  [a5_constrained_event_action_model_short_learned_probe_20260603.zh.md](a5_constrained_event_action_model_short_learned_probe_20260603.zh.md)

## Outputs And Evidence

预期输出：

- `engagement_state`、`fire_mask` 和 `hold/fire_once` 的 event-action contract：
  [a5_constrained_event_action_model_event_contract_20260603.zh.md](a5_constrained_event_action_model_event_contract_20260603.zh.md)
- 已验收的只读 surface audit：
  [a5_constrained_event_action_model_surface_audit_20260603.zh.md](a5_constrained_event_action_model_surface_audit_20260603.zh.md)
- runtime state-machine 和 action-mask tests。
- 覆盖随机采样与 deterministic evaluation 的 policy distribution 或 event Q-head tests。
- runtime/policy implementation evidence：
  [a5_constrained_event_action_model_implementation_evidence_20260603.zh.md](a5_constrained_event_action_model_implementation_evidence_20260603.zh.md)
- 更新后的 S1 C2/ROE training/eval config entries。
- 能证明 requested versus executed release 和 post-launch suppression 的 diagnostics。
- 对比 deterministic / stochastic 行为的 learned-policy evidence。当前 A5 短训证据已记录，
  但结论为 held。

## Acceptance Gate

这是历史 A5 验收门。A5 现在作为后续 M3-S2 发射闭合依赖的结构性 event-action
surface 关闭，而不是作为独立 learned-policy firing solution 验收。

本子项目只能在满足以下条件后标记为 accepted：

- accepted S1 C2/ROE training entry 中，`fire_weapon` 不再是 policy-facing 的逐帧连续阈值
  或无约束 Bernoulli。
- illegal fire 通过 action support 或 state-machine transition 不可用，而不是主要靠 reward
  penalty 压制。
- `fire_once` 作为事件被消费，并立即把交战流程转入 no-fire assessment state，除非存在显式
  reattack authorization。
- 训练时 stochastic exploration 和 deterministic evaluation 使用同一套 masked event action
  structure。
- focused tests 覆盖 mask behavior、post-launch suppression、repeated-fire rejection、
  policy log-prob/eval semantics 和 active config wiring。
- learned-policy evidence 证明 deterministic 授权首发，或者将剩余阻塞明确归入后续
  policy/optimization package，且不重新回到 reward-only tuning。当前证据属于后者：
  stochastic release discipline 已修复，deterministic release 仍 held。
- 文档仍拒绝导弹物理、Pk、引信、真实 BVR doctrine 和 M2 release 过度声明。

## 收口

- A5 原地关闭，作为历史结构性证据保留。
- 保留结论是：受约束 `hold/fire_once` 表面修正了发射请求形态，但 A5 单独没有让
  deterministic policy 请求它。
- 后续 A5 weapon-arm action-frame fix 已成为 M3-S2 发射闭合的一部分。未来发射回归应先查
  M3-S2 证据，不要默认重开 A5。
- 发射时机、稳健性和模型族问题属于后续 model follow-on。

## Archive

完整 A5 包已归档到 `docs/task/air_combat/archive/`。原任务路径现在只保留轻量指针
README。
