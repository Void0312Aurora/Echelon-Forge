# WP5-D Information And Belief Gates 笔记

状态：`2026-05-19` information/belief 聚焦 gate 已完成。

语言版本：

- 英文主文：[wp5_information_belief_notes_20260519.md](wp5_information_belief_notes_20260519.md)
- 中文辅文：`wp5_information_belief_notes_20260519.zh.md`

输入：

- [WP5-D information/belief 分发表](wp5_information_belief_cluster_20260519.zh.md)
- [WP5 validation harness](validation_harness_wp5_20260519.zh.md)
- [WP5 第一波验收审查](../review/wp5_first_wave_acceptance_review_20260519.zh.md)
- [WP5-A harness inventory 笔记](wp5_harness_inventory_notes_20260519.zh.md)
- [WP4-H agent shim 实现笔记](wp4_agent_shim_implementation_notes_20260519.md)
- `python/rl/runtime/agent_shim.py`
- `tests/runtime/test_agent_shim.py`

## 一、决策

WP5-D 采用 label-first 的 information/belief validation。已实现的 gate 是
`tests/runtime/test_agent_shim.py`，它验证被动 Python shim 词汇，不改变 policy
inference、runtime 行为、smoke suite 成员，也不移除 diagnostics/oracle helper。

WP5-D 不新增全仓库 direct `sim.*` ban。当前 Gym、scenario-loader、reward、
teacher、oracle、diagnostics 与 test path 仍存在合法的 compatibility 或 diagnostics
访问。未来若要禁用 direct `sim.*`，必须基于 allowlist，并等待 maintained policy
adapter label 稳定。

## 二、Shim Vocabulary Gate

`tests/runtime/test_agent_shim.py` 现在覆盖以下 label：

| Gate | 维护中含义 | WP5-D 处理 |
|------|------------|------------|
| `facade_observation_packet` | observation 来自 `ObservationBatchPacket`。 | 当 role 携带 consumed snapshot 和 observation packet id 等 facade source metadata 时，可标为 `maintained`。 |
| `agent_observation_compat` | observation 来自 legacy `get_agent_observation` 或 batch getter 输出。 | 保持 `compatibility_adapter`；迁移期可用，但不是最终 maintained policy truth。 |
| `raw_world_truth` | input 来自 raw runtime 或 simulation internals。 | 必须保持 `diagnostics_only`；不是 maintained policy input。 |
| `diagnostics_oracle` | input 来自 teacher、oracle、debug 或 privileged helper。 | 即使用作临时 `DecisionBelief` layer label，也必须保持 `diagnostics_only`。 |
| `AgentRole` 五元素 | role、authority scope、information-state source、decision-model reference、action interface。 | 今天可作为被动 metadata 测试；C++ DTO promotion 仍 deferred。 |
| `ActionIntentCompat` / `CoordinationIntentCompat` | 当前 action 与 command-chain payload 的 metadata wrapper。 | 今天可测试 source id、snapshot id、timing、role id、payload fields 与 maintained/compat label。 |

测试有意不强制禁止构造 diagnostics source 的 `AgentRole`。当前 shim 是被动标签；
真正 enforcement 应等 allowlist 与 DTO metadata 成熟后交给 maintained adapter。

## 三、Maintained-Path Allowlist 草案

未来 direct `sim.*` restriction 应从小型 maintained-path allowlist 开始：

| 候选 maintained path | 预期 information input | 后续 guard 形态 |
|----------------------|------------------------|----------------|
| `python/rl/runtime/agent_shim.py` | 被动 `ObservationProvenance`、`AgentRole`、action intent、coordination intent metadata。 | 不出现 direct `sim.*`；truth/oracle 必须显式 diagnostics-only label。 |
| `python/rl/runtime/world_batch_vec_env.py` 的主 `WorldBatchVecEnv` class | Facade/batch adapter 输出，加声明过的 compatibility access。 | 延续 architecture guard，把 raw runtime handle 限定在显式 adapter 内。 |
| `python/rl/runtime/leader_world_batch_runtime.py` 的 maintained facade-facing methods | Shared execution request/result 输出，而不是 raw world handle。 | 延续禁止 direct world handle reach-through 和 `RuntimeFacade.runtime()` 的 architecture guard。 |
| 未来包装 `ActionIntentCompat` 的 policy adapter module | 来自 facade packet 或声明过 compatibility source 的 `ObservationProvenance`。 | 除注册 compatibility bridge function 外，禁止 direct `sim.*`。 |
| 未来包装 `DecisionBelief` 的 belief adapter module | consumed observation packet ids 或 snapshot versions，加 model/inference source。 | 要求 label、source version，并对 oracle/truth-derived belief 标 diagnostics-only。 |

这是草案，不是实现。WP5-E 不应在 WP5-D/WP5-E 确认 maintained policy package 与
registered compatibility adapter 前加入 broad AST ban。

## 四、Compatibility 与 Diagnostics Exception List

以下模块或模块族在 caller 携带 maintained label 前应保持例外：

| Exception area | 当前原因 | enforcement 前要求 |
|----------------|----------|--------------------|
| `gym_envs/universal_env.py` 与 `gym_envs/universal_env_parts/*` | legacy single-world Gym path 使用 direct `sim.get_agent_observation`、`sim.get_instrument_state`、`sim.set_pilot_action`、`sim.step` 和 visual helper。 | facade-shaped observation/action adapter，带 provenance 与 action intent metadata。 |
| `gym_envs/scenario_loader/*` runtime helper | scenario loading、step evaluation、navigation、reward 与 behavior helper 会读取 direct simulation state 或写 mission/task command。 | 区分 maintained adapter state 与 compatibility/direct simulation state 的 label。 |
| `gym_envs/leader_env_parts/*` | leader environment bridge、decision runtime 与 execution runtime 仍在 compatibility flow 中读取 `env.unwrapped.sim` 或 `loader.sim`。 | 在 leader policy boundary 携带 AgentRole 与 observation provenance label。 |
| `python/rl/runtime/world_batch/adapter.py` | centralized compatibility adapter 有意持有 `RuntimeFacade.runtime()` / `WorldBatchRuntime` fallback。 | 保留为 registered compatibility adapter，不作为 maintained policy API 暴露。 |
| Domain、oracle、teacher、reward、diagnostics、test helper | 它们可能需要 privileged world truth 来审计行为或构造 fixture。 | 被 policy/belief-facing check 消费时必须标为 `diagnostics_only`。 |

## 五、Truth/Oracle Leakage Boundary

WP5-D 区分三类信息状态：

| Class | 是否允许作为 maintained policy input | 当前可测证据 |
|-------|--------------------------------------|--------------|
| `ObservationPacket` / `facade_observation_packet` | 可以，但 adapter 必须携带 source metadata。 | `ObservationProvenance` 可保存 `consumed_snapshot_version`、`observation_packet_id`、source layer 与 maintained status。 |
| `agent_observation_compat` | 不是最终 maintained truth；只允许作为迁移 compatibility。 | 测试保持 `compatibility_adapter` status，并与 maintained source label 分离。 |
| `raw_world_truth` / `diagnostics_oracle` | 不允许。它们是 diagnostics-only 或 oracle-derived。 | 测试断言 truth/oracle label 保持 diagnostics-only、显式 source layer 与 diagnostics note。 |

当前 shim 里的 `DecisionBelief` 只是 belief layer label，不是 typed public DTO。
truth-derived 或 oracle-derived belief 在未来 maintained belief contract 能声明 consumed
observation version 与 inference provenance 前，必须保持 `diagnostics_only`。

## 六、Typed DTO 前的 DecisionBelief 边界

今天可以测试：

1. belief-like input 可被标记为 `information_state_layer = "DecisionBelief"`。
2. oracle 或 teacher-derived belief label 保持 `diagnostics_only`。
3. maintained role 可记录 facade observation source、consumed snapshot、
   observation packet id、decision-model kind 与 decision-model id。
4. action / coordination intent wrapper 可记录 source id、input snapshot、
   effective time、validity、role id 与 maintained/compat status。

仍依赖 metadata 的内容：

1. typed `DecisionBelief` DTO shape 与 C++/Python binding promotion。
2. runtime-enforced consumed observation packet versions。
3. uncertainty/confidence、estimator source、memory source、doctrine source 与
   learned-state provenance field。
4. maintained policy execution path 拒绝 diagnostics-only belief input。
5. 将 `DecisionBelief` provenance 与 `ObservationBatchPacket` snapshot/barrier/
   source-time metadata 做交叉校验。

## 七、Smoke Candidate 建议

推荐 WP5-D 聚焦命令：

```bash
python -m pytest -q tests/runtime/test_agent_shim.py
```

推荐 WP5-E smoke candidate：

```bash
python -m pytest -q tests/runtime/test_agent_shim.py
```

该文件成本低，并为 maintained validation harness 提供一个明确的
information/belief leakage tier gate。WP5-E 可将它与 WP5-B architecture gates、
WP5-C trace/replay gates 组合，但暂不应把 broad direct `sim.*` ban 加入 smoke。

## 八、Deferred Gates

WP5-D 不解决以下事项：

- policy inference rewrite 或 Gym adapter migration；
- 移除 diagnostics、oracle、teacher 或 reward helper；
- runtime `ObservationViewSpec` 或 packet-level snapshot/barrier metadata；
- typed `DecisionBelief`、`RewardReport` 或 termination reason-source DTO；
- 直接编辑 `tests/smoke/ci_smoke_suite.json`；
- 没有 maintained-path allowlist 的全局 direct `sim.*` ban。
