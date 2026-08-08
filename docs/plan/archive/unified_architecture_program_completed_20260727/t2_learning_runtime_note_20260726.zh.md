# T2 学习运行时一致性说明

语言：
- 英文正本：[t2_learning_runtime_note_20260726.md](t2_learning_runtime_note_20260726.md)
- 中文伴随：`t2_learning_runtime_note_20260726.zh.md`

文档种类：`reference`
生命周期：`maintained`
正本：`docs/plan/archive/unified_architecture_program_completed_20260727/t2_learning_runtime_note_20260726.md`
所有者：`unified architecture program workline`
最后核验：`2026-07-26`
基线提交：`0aa76a00`

状态：T2 收尾交付物（修订候选 (e)）。本文是一次只读的一致性普查。零代码变更，
零行为变更。

## 0. 方法与范围

基线的 Learning 面于 I29 落地为
[仿真系统架构设计](../../../architecture/standards/simulation_system_architecture_design.zh.md)
第 17 节，其中定义了三份契约。因此修订候选 (e) 已被接受*进入基线*；计划 README
的 T2 行仍欠的是本文档——对维护中的 Python 学习运行时给出针对这三份契约的一致性
裁定。

普查范围：`python/rl/runtime/world_batch/**`、`python/rl/policy_algo/**`、
`python/training/**`、`python/rl/tasking/**`、`python/rl/runtime/agent_shim.py`。
只读；每条裁定均标注 `file:line`。

非目标（依计划 README）：本文档不修订基线（修订须走架构工作线的治理流程）、
不提出代码修复、也不为其他轨道排期工作。缺口只被*路由*，而非解决。

## 1. 三份契约

引自基线第 17 节（`:837-850`）：

1. **Env-as-View 契约。** RL environment "是仿真 facade 之上的一个 view
   adapter，不是权威 runtime owner。它消费 observation packet，通过 facade
   contract 注入 action，并 mirror episode state。它不得拥有权威仿真 truth 或
   episode phase。"
2. **Rollout collection 契约。** Rollout 数据 "在 facade 声明的 barrier 处采集。
   采集节奏是一个 policy clock domain。Rollout provenance 必须记录 observation
   snapshot version 与 action effective time。"
3. **Policy bridge 契约。** policy "是挂接在 AgentRole 上的可替换 decision
   model"，且 bridge "必须声明自己的 information-state source、observation
   version 要求与 action interface"。

## 2. 契约 1 — Env-as-View：符合（有限定）

environment 通过 facade 读取 truth，而非自己拥有 truth。每次批量读取都经过
adapter 的 observation packet，而不是一个被存住的 world：

- `python/rl/runtime/world_batch/vec_env.py:380-392` —
  `_read_truth_and_inst_batch` 调用
  `self._runtime_adapter.read_observation_packet(...)`，并从返回 packet 的字段
  派生 `truth_list` / `inst_list`。Truth 是*每批重读*的，不是被持有的。
- `python/rl/runtime/world_batch/adapter.py:312-316` — adapter 构造
  `ef_py.RuntimeFacade(self._world_count)`，bindings 缺失时抛错。这是唯一维护中
  的跨界构造路径（与 G1 一致；见 T0 SCAL 普查的旁路盘点）。

逐 world 的 `handle.last_truth` / `handle.last_inst` 字段（`vec_env.py:508-509`，
读取于 `:459`）是**最近一个 packet 的缓存**，不是权威：它们由 packet 内容赋值，
且每次读取都被重新填充。`_command_chain_entity_active`（`:457-465`）把缺失的
`last_truth` 当作宽容默认值而非权威状态来处理——这是 mirror 的行为，不是 owner
的行为。

episode-phase 子句（"它不得拥有权威仿真 truth 或 episode phase"，基线
`:840-841`）需要比 truth 子句更仔细的裁定。在默认路径上，Python 拥有 episode
stepping 状态：两个 execution episode controller 开关都默认关闭
（`vec_env.py:147-148`），step 计数在 Python 侧推进（`handle.steps += 1`，
`vec_env.py:675`），`terminated` / `truncated` 由 Python 侧 loader 求值计算，
而非从任何 facade episode 面读出（调用 `_compute_loader_step_outcome` 的默认
分支，`vec_env.py:728-739`；`done` 于 `:821`）。episode 状态只有在 opt-in
controller 路径上才流经 facade 的 episode 面（`vec_env.py:723-727`），而且即便
在那里，权威方向也是 Python 到 facade：
`_sync_execution_episode_controller_runtime_state` 经由
`handle.loader.build_execution_episode_state()` 把 facade 面*从* loader 灌注
（`python/rl/runtime/world_batch/_execution_episode_mixin.py:181-191`，途经
`python/rl/runtime/world_batch/adapter.py:886-887`）。

裁定：在本基线上，loader 求值面是 episode phase 的*过渡期所有者*，opt-in 的
execution episode controller 是通往契约所描述的、由 facade 拥有的 episode 面的
收敛路径。这一过渡期所有权是已声明、有开关门控的，而非隐藏权威（参照
`EpisodeLifecycleContract`，基线 `:432`，其禁止推进*私有*权威状态机）；mainline
切换是 T2 范围之外的学习运行时后续工作。

裁定结论：**符合，有限定**。truth 所有权子句按上文引证完全满足。episode-phase
子句只在上述限定意义下满足：默认路径上 Python 拥有 episode stepping 状态，
"mirror episode state" 目前描述的是 opt-in controller 路径——而该路径本身是把
loader 状态 mirror 进 facade，并非反向——这一子句要等 episode-controller
mainline 切换落地后才完全可核验。

## 3. 契约 2 — Rollout collection：不符合

该契约三个子句中有两个未满足，且失败是结构性的，不是偶发的。

**Barrier 有暴露，但未在采集点被声明。** `barrier_trace` 存在于 adapter 的
window 结果上（`python/rl/runtime/world_batch/adapter.py:58`，填充于 `:469`），
所以 facade 确实暴露了 barrier 信息。但没有任何 rollout 采集代码消费它。

**Rollout provenance 既不记录 snapshot version，也不记录 action effective
time。** 在 `python/rl/policy_algo/**` 与 `python/training/**` 中搜索
`snapshot_version` 与 `effective_time` 均为**零命中**。rollout buffer
（`python/rl/policy_algo/device_dict_rollout_buffer.py:19`）扩展自 SB3 的
`DictRolloutBuffer`，其文档化用途是设备放置效率（`:20-25`）——完全不携带任何
provenance 字段。

这是契约自身的显式要求（"Rollout provenance **必须**记录 observation snapshot
version 与 action effective time"），所以这是不符合，而非部分符合。

注意对 T10 的直接依赖：证据脊柱普查记录 `packet.snapshot_version` 仍派生自
`next_snapshot_version(index)`（`index + 1`，每次导出重置），因此即便 rollout
采集今天就记录 snapshot version，记录到的值也不是 run 全局单调的。VA-2 生产者
本身在本基线上已经存在——`RuntimeFacade::allocate_run_snapshot_version` 于 I54
落地（`src/runtime/facade/runtime_facade.h:172`），并由 adapter 在
`use_facade_evidence_producers` 开关之后以 opt-in 方式消费
（`python/rl/runtime/world_batch/adapter.py:400-402`）——所以仍被 T10 门控的是
把该生产者接入默认导出路径，而不是创建生产者，也不只是加一个字段。

裁定结论：**不符合**。缺口 G2-1 与 G2-2 见下。

## 4. 契约 3 — Policy bridge：部分符合

bridge 的声明比学习运行时里任何其他表面都多，其词汇已经是正确的形状：

- **Information-state source：已声明。** `agent_shim.py:141-148` 发出
  `information_state_layer`、`source_label`、`maintained_status`、
  `observation_packet_ids` 与 `source_observation_versions`。
- **Observation version 要求：已声明。** `source_observation_versions` 是一等
  tuple 字段（`agent_shim.py:557`，规范化于 `:572-573`），
  `consumed_snapshot_version` 为其供值（`:140`）。
- **挂接到 role 的 decision model：已声明。** `decision_model_ref` 是结构化
  mapping（`agent_shim.py:222`，防御性拷贝于 `:231`，导出于 `:248` 与 `:275`，
  构造于 `:303` 与 `:335`），携带 `kind` 与 `id`。这与 T9 在
  `python/tasking_contracts/agency_registry.py` 中的
  `AUTHORITY_ROLES[*].decision_model_ref` 词汇一致。

缺口在于这些声明是**自我断言的字符串，未被 G4 注册表门控**。`agent_shim` 在
`python/architecture/information_layer.py` 中完全没有出现——grep 零命中——所以
其 `information_state_layer` 取值不受 G4 词汇白名单约束，也不被管辖十三个已注册
消费者的声明门禁校验（`MAINTAINED_INFORMATION_LAYER_CONSUMERS`：九个
view-converged 加四个 declared-deferred，
`python/architecture/information_layer.py:84-129`；已声明的 view owner
`gym_envs.observation_view` 是单独的常量，不是消费者）。policy bridge 用一套
G4 门禁不检查的词汇声明自己的认知层。

裁定结论：**部分符合**——三个子句全部有声明；没有一个被强制。缺口 G3-1 见下。

## 5. 缺口登记与轨道路由

| 缺口 | 契约 | 陈述 | 路由至 |
| --- | --- | --- | --- |
| G2-1 | Rollout collection | Rollout provenance 未记录 observation snapshot version。需要有 run 全局单调的版本可记录，因此依赖 T10 的 VA-2 生产者被接入导出路径。 | **T10**（证据脊柱），随后一个 T2/learning 后续切片 |
| G2-2 | Rollout collection | Rollout provenance 未记录 action effective time。采集面中不存在任何 `effective_time` 字段。 | **T10** 负责词汇；学习运行时切片负责管线 |
| G2-3 | Rollout collection | `barrier_trace` 由 adapter 暴露但没有任何 rollout 采集器消费，因此 "在 facade 声明的 barrier 处采集" 是未被核验，而非为假。 | 学习运行时后续；无跨轨道阻塞 |
| G3-1 | Policy bridge | `agent_shim` 的 `information_state_layer` 是自我断言且不在 G4 注册表中，声明未被门控。 | **T8**（把 G4 注册表/门禁扩展到 policy bridge） |
| G3-2 | Policy bridge | `decision_model_ref` 复制了 T9 的注册表词汇但未把注册表引用为 owner，两者可能漂移。 | **T9**，但注意 T9 的语义收敛在 doctrine 权威落定前处于搁置 |

这些缺口没有一个能在 T2 内部关闭。T2 自身的剩余范围由本文档清偿。

## 6. 基线与代码不一致之处

一处实质分歧，作为本次普查最有用的产出予以标记。

**第 17 节把 "model checkpointing" 划给 Learning 面**（`:854-855`），并把
curriculum、evaluation protocol 与 experiment composition 划给 Experiment 面
（`:852-854`）。但 checkpoint *兼容性*当前是通过 `ObservationViewSpec` 裁定的
——这个 DTO 由 I60 扩展了 `view_id` / `information_layer_produced` /
`information_layer_consumed` / `semantic_stage`，并从 runtime facade 导出。因此
checkpoint 兼容性表面由 facade 的 observation-view 词汇（T8 的领地）拥有，而不
是由 Learning 面拥有。

这不是任何一处的缺陷——这是一个未指派的接缝。建议架构工作线裁定：checkpoint
兼容性是消费 facade 声明的 view spec 的 Learning 面关切，还是 Learning 面只做
读取的 facade 关切。路由至**架构工作线**，此处不解决。

第二处较小的错配：第 17 节说采集节奏 "是一个 policy clock domain"，但多速率
clock domain 仍处于已注册但被 exact-runtime WP4/WP5 搁置的状态
（`kClockDomainAdvisoryOnly` 仍为 `true`，
`src/runtime/contracts/stage_node_manifest_registry.h:13`）。所以该子句当前不可
证伪——只有一个有效速率。记录为背景，不记录为缺口。

## 7. 核验

Docs-only 迭代；不触碰任何构建或行为表面。

- 文档链接审计：在双语簇注册表刷新前后各跑一次；registry-match 门禁在刷新前
  预期为红，这一模式在此前每次普查落地时都有记录。
- CI smoke 套件。
- `git diff --check`。

非本迭代造成的既有红：`tests/runtime/mission/test_mission_command_roe_fields.py`
中四个 subtest 失败，源于一个过期的共享 `ef_py` 二进制（其 equivalence 函数早于
shared-core 合并）；三个 `damage_model` 路径分隔符红，归并行的 T6 清障包所有；
以及缺少 `_deps` 源的构建树中的 flecs/spdlog 收集错误（I65 已定根因为
build-snapshot 完整性问题，非 lineage 红）。

## 8. 相关权威文档

- [统一架构计划](README.zh.md)（T2 轨道行；本文档关闭其 (e) 交付物）
- [仿真系统架构设计](../../../architecture/standards/simulation_system_architecture_design.zh.md)第 17 节（本文档据以度量的基线契约）
- [T8 G4 真值泄漏清单](../../../architecture/reference/t8_g4_truth_leak_inventory.zh.md)（G3-1 的去处）
- [T10 证据脊柱普查](t10_evidence_spine_census_20260721.zh.md)（G2-1/G2-2 的依赖）
- [Agency 权限普查](../../../systems/command-tasking/reference/agency_authority_census_20260721.zh.md)（G3-2 的 `decision_model_ref` 词汇）
- [C++ 精确运行时重构计划](../../../architecture/work/issues/exact_runtime/cpp_exact_runtime_refactor_plan.zh.md)（第 6 节所记被搁置的 clock-domain 背景）
