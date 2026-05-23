# WP2 契约冻结

状态：`2026-05-19` 活跃冻结草案。

语言版本：

- 英文主文：[contract_freeze_wp2_20260519.md](contract_freeze_wp2_20260519.md)
- 中文辅文：`contract_freeze_wp2_20260519.zh.md`

输入：

- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [WP1 管线盘点](pipeline_inventory_wp1_20260519.zh.md)
- 围绕交战、facade、验证、策略与编排面的只读代码证据。

本文档冻结 `WP2` 的架构契约形状。它不实现新的 runtime 代码。它的职责是决定哪些 packet 族和 stage-node 边界属于维护中的契约，哪些既有路径只是兼容 adapter，以及后续工作包应实现或验证哪些决策。

## 一、冻结定位

仿真层、策略计算层、测试/编排层之间的架构框架已经闭合。`P0-P10` 是规范语义生命周期，真实执行是多率 temporal DAG。跨窗口反馈必须跨越 `StateStore`、`EventQueue` 或显式调度 barrier。

因此 WP2 冻结的是契约 ownership，而不是线性 executor。

必要规则：

1. 新的维护中工作必须面向 facade-shaped request/result API 或 `runtime/contracts` DTO。
2. `RuntimeFacade::runtime()`、raw `WorldBatchRuntime`、raw `SimulationKernel` 与 debug API 只能保留为兼容或诊断逃逸口。
3. `MissionCommand` 在更窄的 tasking、command、engagement packet 替代相关字段前，仍是兼容性聚合面。
4. 仿真事实由仿真层和 compiled mission runtime 拥有。策略与编排可以塑造 reward、选择 observation view 或请求 truncation，但不能成为仿真真值的隐藏 owner。
5. Stage-node contract 必须声明 `semantic_stage`、`read_set`、`write_set`、`clock_domain`、`latency_policy`、`sync_policy`、facade 可见性与确定性 event-ordering 要求。

## 二、契约族

| 契约族 | 当前证据 | 冻结决策 | 最小冻结字段 | Facade / 兼容路径 | 验证门槛 |
|--------|----------|----------|--------------|-------------------|----------|
| `TrackPacket` | `SystemTrack`、`TrackDatabase` 与 `AgentObservation.contacts` 已承载 fused track 数据。 | 维护中的 `P6/P10` 契约。Raw `ContactList` fallback 仅为兼容路径。 | `track_id`、entity correlation policy、source、classification、status、quality、confidence、usability、IFF、source time 或 update age、snapshot version。 | 通过 observation/facade packet 导出；不暴露 raw track database layout。 | Observation 测试应验证 fused-track 字段和 fallback 标记。 |
| `LaunchRequest` | Launch intent 目前分散在 `PilotAction`、`MissionCommand`、ROE gate 和 `fire_missile()` 参数中。 | 新 `P7` request contract。它拆分 fire-control intent 与 munition spawning。 | shooter ref、target entity 或 track ref、launcher station 或 mount、requested munition family、authority source、requested time、`merge_policy`、request id。 | 未来 facade request/result API；旧 `fire_missile()` 与 mission-command 字段是兼容 adapter。 | Facade-only engagement pilot 必须不经 raw runtime 提交 launch intent。 |
| `LaunchEvent` | Accepted/rejected launch outcome 隐含在 kernel launch return value、ammo/cooldown mutation 与 spawned munition id 中。 | 新 `P7` event contract。它是权威 launch result。 | request id、accepted/rejected、rejection reason、selected launcher、selected munition、ammo delta、cooldown delta、spawned munition id、event time、event id。 | 由仿真产生，并通过 facade diagnostics/event packet 导出。 | 航空和舰载 launch 测试应收敛到同一 event shape。 |
| `MunitionLifecyclePacket` | `Missile` 与 guidance system 已追踪 attacker、target、seeker、guidance cadence、launch time、track memory、fuel、burnout 与 fuze state。 | 维护中的 `P8` 生命周期 packet，外露最小外部状态。Guidance tuning 保持 component-internal。 | munition id、attacker ref、target ref 或 track ref、launch event id、active flag、seeker mode、guidance cadence、track memory state、fuel 或 burnout state、max flight time、fuze state、source time。 | Facade diagnostics/export；component state 不是公共 schema。 | 非 RL smoke 应在 launch event 后观察 lifecycle progression。 |
| `EffectsEvent` | Fuze 与 effects 行为存在于 damage system 和 weapon effects model。 | 新 event-driven `P9` effects contract。 | munition id、target ref、trigger type、hit/miss/proximity state、detonation 或 nearest approach time、quality/confidence、effect family。 | Simulation event queue 与 facade diagnostics。 | Engagement trace 必须解释 damage 为什么发生或未发生。 |
| `DamageReport` | `PlatformDamageState` 与 effects model 会更新 HP、system health、kill flag、fire、flooding、breach 与 loss state。 | 维护中的 `P9` report contract。Debug health read 仅为兼容路径。 | target ref、source event id、HP delta、system health delta、platform damage-state delta、mission/mobility/sensor/survivability kill flags、loss-state transition、destroyed flag、report time。 | Facade report/export packet；debug damage API 仅保留为测试 helper。 | Damage report 必须不经 raw `SimulationKernel` debug call 即可看见。 |
| `DiagnosticsTrace` | Observation export 已存在，但 launch/damage 解释尚未绑成一条 trace。 | 维护中的 trace index，WP2 不要求完整日志系统。 | trace id、track id、launch request id、launch event id、munition id、effects event id、damage report id、observation packet version。 | Facade diagnostics/export。 | 一条 trace 必须串起 launch、lifecycle、effect、damage 与 observation。 |
| `PlatformControlPacket` | `PilotAction`、control model 与 control system 已存在，但没有窄 facade-level `P4` packet。 | 新 `P4` contract 候选。WP2 冻结 ownership 与 timing，具体控制字段可在实现中细化。 | target entity、control source、effective time、validity window、direct-control family、normalized action vector 或 bound fields、hold policy id。 | `ActionIntentPacket` 在 `P3/P4` 由 facade/仿真翻译；既有 `PilotAction` 是兼容目标。 | 架构测试必须阻止 policy 代码 raw mutate control state。 |
| `ObservationViewSpec` / `ObservationPacket` | Facade 已有 typed observation request flags 和 packet vectors；Python 仍直接组装部分 view。 | 维护中的跨层契约。策略/测试拥有 view schema；仿真/facade 拥有 snapshot 与 packet builder。 | schema version、required fields、optional fields、include flags、source snapshot version、source time、normalization/encoding owner、compatibility rule。 | `ObservationBatchRequest` / `ObservationBatchPacket`；Python 直接组装在 adapter parity 被证明前为兼容路径。 | Checkpoint/schema 规则必须拒绝 major-incompatible view。 |
| `ActionIntentPacket` / `ActionHoldPolicy` | Execution action 与 leader action 已存在，但 cadence 与 Python mapping 不同。 | 维护中的 policy-to-simulation 契约。 | action source、target entity、action family、effective time、validity window、refresh cadence、expiry behavior、hold/interpolation/drop rule、`merge_policy`、credit-latency note。 | Facade 接收 intent，并翻译到 `P3/P4/P5` 消费点。 | Policy cadence 必须可测试，而不能假设与 physics 等 `dt`。 |
| `CoordinationIntentPacket` | Cooperative director、leader tasking 和 C2 路径在 simulation DAG 外产生 tasking/command intent。 | 维护中的跨层契约。C2 可消费 shared situation 和 report，但不能直接 author low-level mission command。 | source type、source id、roster、target refs、update clock、produced tasking fields、produced leader-intent fields、`merge_policy`、effective time。 | scripted、learned、human director 均通过 facade-compatible assignment path。 | 测试必须证明 coordination write 通过 facade/adapter path。 |
| `RewardSpec` / `RewardReport` | C++ episode controller 已返回 reward total、status vector、termination reason 与 JSON breakdown；Python 仍有 fallback shaping 路径。 | 分裂契约。仿真拥有 facts；策略/测试拥有 shaping 与实验组合。 | fact snapshot version、fact terms、shaping terms、reward total、breakdown JSON、每项 term 的 owner/source、computation latency。 | Facade execution step result 是维护中路径；Python reward fallback 是兼容路径。 | Reward report 必须标记 fact 与 shaping term。 |
| `TerminationSpec` / `EpisodeStatus` | Compiled episode flow 已返回 `terminated`、`truncated`、status vector 与 termination reason；adapter mirror Gymnasium state。 | 分裂契约。仿真拥有语义 termination；编排拥有测试/训练 truncation request。 | terminated、truncated、reason、reason source、status vector、source time、snapshot version、reset requested flag。 | Facade execution result 与 episode status mirror。 | Termination/truncation 测试必须归因 reason source。 |
| `EpisodeLifecycleContract` | Episode controller/state 已追踪 phase、mission command、waypoint、reward、termination 与 reset 相关状态。 | 维护中的生命周期 authority。Compiled/facade state 是权威；Gymnasium 与 batch API 只 mirror。 | agent id、step count、phase、waypoint index、mission command ref 或 JSON、last reward total、last termination reason、last reward breakdown、reset transition id。 | Facade execution result 与未来 episode export packet。 | Adapter 不得推进私有权威 phase machine。 |

## 三、Stage-Node 冻结

下表冻结第一版维护中 stage-node 词汇。它不是完整 scheduler 实现。

| 阶段 | 维护中 node contract | Read set | Write set | Clock / latency / sync policy | Event ordering |
|------|----------------------|----------|-----------|--------------------------------|----------------|
| `P0 ContentCompile` | Content 与 scenario 规范化。 | 静态 content、scenario file、backend capability request。 | Content id、compiled setup packet、默认 capability shard。 | Offline 或 setup-window only；无 per-tick mutation。 | WP2 中不是 event-driven。 |
| `P1 WorldSetup` | World、terrain、environment、seed、spawn 与 initial state setup。 | Compiled content、setup packet、seed、initial environment refs。 | Entity refs、world batch refs、initial `StateStore` snapshot。 | simulation window 前的 setup barrier。 | Setup event 排在 runtime event 前。 |
| `P2 TaskingIntent` | Mission、leader 与 coordination intent ingestion。 | Coordination intent、mission plan、roster、prior reports。 | Task orders、leader intents、mission-command compatibility fields。 | 低于 physics 的 cadence；external input 在 scheduling-window barrier 前注入。 | Intent event 使用 `(timestamp, priority, event_id)`。 |
| `P3 CommandDelivery` | Command link、latency、drop、pending queue 与 command materialization。 | Tasking/mission command shard、link state、authority state。 | Pending command queue、delivered command state、delivery reports。 | Event/latency driven；可在 next window delivery。 | Delivery event 使用确定性 timestamp 和 priority。 |
| `P4 PlatformControl` | Control-command 翻译与 hold policy consumption。 | Delivered commands、action intent、platform state、hold policy。 | Control inputs、actuator/control state、action validity reports。 | Control-rate clock；一个 policy output 可被多个 control tick 消费。 | Control conflict 按 request `merge_policy` 处理。 |
| `P5 PhysicsStep` | Kinematics、forces、contacts 与 integration。 | Control state、physical state、environment。 | 更新后的 physical state、contact candidates、供后续 node 读取的 capability-affecting state。 | Physics-rate clock，可含 substep；CPU exact path 是参考。 | Physics output 通过 state versioning commit。 |
| `P6 SenseTrackLink` | Sensor scan、fusion、datalink、EW 与 track snapshot。 | Physical state、sensor state、EW/link state、prior tracks。 | `TrackPacket`、shared situation、pilot reports、observation-ready track snapshot。 | Sensor 与 link clock 不同于 physics；snapshot 声明 source time 和 version。 | Track update 使用确定性 timestamp 和 source priority。 |
| `P7 FireControlLaunch` | Fire-control gating、launcher selection、envelope、ammo、cooldown 与 launch result。 | Track packet、authority state、platform weapon state、launch request。 | Launch event、ammo/cooldown state、spawned munition ref、rejection report。 | Event-driven 或 fire-control cadence；仅在 request barrier 后 same-window。 | Launch event 使用 `(timestamp, priority, event_id)`。 |
| `P8 MunitionLifecycle` | Guidance、seeker、datalink、fuze arming 与 lifecycle state。 | Launch event、munition state、target track、environment、datalink。 | Munition lifecycle packet、guidance state、fuze/effects trigger candidate。 | Guidance、seeker、fuze clock 可不同；默认 nested triggering，除非声明显式 merge policy。 | Lifecycle event 保留 launch-event ancestry。 |
| `P9 EffectsDamage` | Effects resolution、damage mutation、loss-state transition 与 report generation。 | Effects event、target state、protection/damage model state。 | Damage report、platform damage state、capability degradation、kill/loss events。 | Event-driven；反馈到后续 capability read 必须跨 state/event barrier。 | Damage 与 kill event 按 timestamp、priority、event id 排序。 |
| `P10 ObservationExport` | Snapshot export、facade packet construction、diagnostics trace 与 policy/test view。 | Committed state snapshot、reports、traces、observation view spec。 | Observation packet、diagnostics trace export、mirrored episode status。 | Facade-requested、episode-boundary、diagnostic 或 batch-collector cadence。 | Observation 声明 source snapshot version 与 export time。 |

## 四、跨层冻结

WP2 按如下方式冻结三个顶层层级的交互：

| 边界 | 仿真层拥有 | 策略计算层拥有 | 测试/编排层拥有 | 必要通道 |
|------|------------|----------------|-----------------|----------|
| Observation | 可查询 state shard、committed snapshot version、facade packet builder、diagnostics export。 | `ObservationViewSpec`、field subset、encoding、normalization、masking、stacking、schema version。 | Test view selection、assertion view、replay comparison view。 | `ObservationBatchRequest` / `ObservationBatchPacket` 或已记录 adapter parity。 |
| Action | Command/control ingestion point、validity enforcement、state mutation、deterministic application。 | `ActionIntentPacket`、action family、effective time、hold policy、merge policy。 | 测试用 scripted action injection、seed/replay scheduling。 | Facade action/step request，绝不 raw ECS mutation。 |
| Coordination | 一旦进入 simulation DAG，就拥有 tasking 与 command state。 | scripted、learned 或 human director output，表现为 `CoordinationIntentPacket`。 | Scenario-level coordination script 与 validation schedule。 | Scheduling-window barrier 前的 facade-compatible assignment path。 |
| Reward | Simulation facts、compiled mission products、damage/kill facts、semantic fact snapshots。 | Experiment shaping、curriculum term、consumer-specific reward composition。 | Benchmark reward config 与 reporting。 | 带 fact/shaping attribution 的 `RewardReport`。 |
| Termination | 仿真语义 `terminated` reason 与权威 phase。 | 仅拥有 policy-visible status mirror。 | `truncated` request、max-step 或 wall-clock policy、reset request。 | `EpisodeStatus` 与 facade execution result。 |
| Episode lifecycle | Phase、transition result、reset application、semantic reason。 | Rollout bookkeeping mirror。 | Reset/truncation scheduling 与 CI episode boundary。 | `EpisodeLifecycleContract`；adapter 不得拥有私有 truth。 |

Cross-layer producer 必须提供 merge policy。合法值保持为：

- `last_write_wins`
- `priority_override`
- `reject_on_conflict`
- `merge_by_field`
- `append_only`

External graph input 在 scheduling-window barrier 前注入。如果某条 action 或 coordination path 需要 next-window 语义，它必须把 `effective_time` 设到后续窗口，而不是依赖隐藏调用顺序。

## 五、兼容性分类

| Surface | 分类 | WP2 规则 |
|---------|------|----------|
| `RuntimeFacade::runtime()` | Diagnostics 与 legacy adapter 逃逸口。 | 新的维护中 engagement、policy 或 validation 路径不得依赖它。 |
| Direct `WorldBatchRuntime` Python exposure | 兼容路径。 | 只允许出现在显式 adapter 内。 |
| `MissionCommand` engagement fields | 兼容性聚合。 | 除非同步到更窄契约，否则不继续追加新的 `P7-P9` 语义。 |
| Raw `ContactList` observation fallback | 兼容 fallback。 | 维护中导出应优先使用 `TrackPacket` / fused-track semantics。 |
| Debug damage 与 raw health reads | Test helper / diagnostics。 | 维护中 damage 可见性应使用 `DamageReport`。 |
| Python reward 与 observation fallback assembly | 兼容 / 迁移支持。 | 维护中路径应收敛到 facade packet 与显式 view/reward spec。 |

## 六、验证门槛

只有当仓库已有足够测试或已记录 gate 来保护冻结契约形状时，WP2 才算完成。当前立即可用的本机 gate 是：

```powershell
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\architecture\test_runtime_facade_layering.py tests\architecture\test_cmake_target_readiness.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_pytest_suite.py --suite tests\smoke\ci_smoke_suite.json
```

如果需要从干净本机构建窗口开始：

```powershell
cmake -S . -B build-local-win -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-local-win --target ef_core ef_py -j2
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_pytest_suite.py --suite tests\smoke\ci_smoke_suite.json
```

本冻结之后需要排期的缺失验证：

1. 契约文档一致性测试，覆盖 `P0-P10` stage vocabulary、packet ownership、read/write sets、clock domains、event ordering 与 merge policy。
2. Facade-only engagement path 测试，覆盖 launch、munition lifecycle、effects、damage 与 observation export。
3. Stage-aligned local non-RL smoke test，显式验证架构词汇。
4. Diagnostics trace 测试，把 track、launch request/event、munition、effects、damage 与 observation packet version 绑定起来。

## 七、移交后续工作包

`WP3 Engagement Pilot` 应在本冻结之后实现第一条跨领域切片：

1. 读取 `TrackPacket`，
2. 提交 `LaunchRequest`，
3. 接收 `LaunchEvent`，
4. 观察 `MunitionLifecyclePacket`，
5. 接收 `EffectsEvent` 与 `DamageReport`，
6. 导出 `ObservationPacket` 与 `DiagnosticsTrace`。

该试点必须至少覆盖航空挂架发射与舰载挂载发射，且不得创建彼此独立的私有生命周期栈。

`WP2.5 Scheduler Semantics Freeze` [任务族](scheduler_semantics_wp25_20260519.zh.md)
应先冻结 event ordering、state versioning、barrier visibility、
clock-domain merge policy、replay contract 与 stage-node manifest，再开始
facade hardening。

`WP4 Facade Alignment` [任务族](facade_alignment_wp4_20260519.zh.md) 应新增或适配
request/result API，使该试点不经 raw runtime access 即可访问。

`WP5 Validation Harness` 应把上面的 gates 固化为维护中的测试与本机 Windows smoke 命令。

## 八、退出标准

WP2 退出条件：

1. 本文档中的契约族已经实现为维护中的 DTO，或被显式跟踪为实现任务。
2. 每个维护中的 `P0-P10` node 都已记录 ownership、read/write sets、clock domain、latency policy、sync policy 与 event-ordering rule。
3. 兼容路径被记录，并且不会成为新的 mainline dependency。
4. 策略与编排 producer 使用带 `merge_policy` 和 `effective_time` 的 facade-shaped request。
5. 本地验证不需要 RL 训练依赖。
