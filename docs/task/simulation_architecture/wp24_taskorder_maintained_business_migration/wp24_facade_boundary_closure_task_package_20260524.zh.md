# WP24 Facade Boundary Closure Task Package

状态：`2026-05-24`，经过并行 subagent 只读核验后确认打开的整改任务包。
本任务包把 TaskOrder maintained business migration 从“TaskOrder 全壳公共面清理”
推进到 facade / information-boundary 的完整收口。

英文主文：
[wp24_facade_boundary_closure_task_package_20260524.md](wp24_facade_boundary_closure_task_package_20260524.md)

## 1. 核验结论

在打开本任务包前，已经分发四个只读 subagent 核验。结论不是 optional backlog，
而是确认存在的边界泄漏整改队列。

| 问题 | 结论 | 证据 | 必须响应 |
| --- | --- | --- | --- |
| `ObservationBatchPacket` 混合 agent observation 与 command-side payload。 | 属实，P1。 | `ObservationBatchPacket` 暴露 `mission_commands`、`leader_intents`、`pilot_reports`；packet 只有一个 `AgentObservation` provenance。 | 拆分 observation export 与 command/tasking export，并守住 packet shape。 |
| 场景加载绕过 facade-owned boundary。 | 经校准后属实，P1。 | `batch_apply.py` 接受 raw-runtime-shaped `batch_runtime`；maintained `WorldBatchVecEnv` 当前传入 adapter，但 adapter 仍保留 raw runtime fallback。`UniversalEnv` 直接创建 `SimulationKernel`。 | 把 scenario setup 收到 maintained facade/adapter contract 后面，并隔离 raw fallback。 |
| Facade/contract 仍是双重表示主机。 | 部分属实。 | TaskOrder public whole-shell API 已经退休；但 `MissionCommand`、`LeaderIntent`、`PilotReport` 仍是没有 maintained contract 等价物的 compatibility transport shell。 | 增加 maintained command/tasking contract，或者把这些 shell 明确隔离为 compatibility-only。 |
| `agent_shim.py` 默认 `COMPATIBILITY_ADAPTER`。 | 经校准后属实，P2。 | 默认值是 fail-closed metadata，不是直接 runtime 执行；但 maintained caller 仍可能意外继承 compatibility provenance。 | maintained business path 必须显式传入 maintained provenance，并加 guard。 |

## 2. 强制工作线

### WP24-I: Observation And Command Export Split

`ObservationBatchPacket` 必须变成纯 observation export envelope。Command/tasking
payload 必须迁移到独立的 maintained export envelope 或专门的 command/tasking
read contract。

必须修改：

- 从 `ObservationBatchPacket` 移除 command/tasking 一等字段：
  `mission_commands`、`leader_intents`、`pilot_reports`，以及如果继续作为
  command/tasking read payload 存在的 maintained `task_order_contracts`。
- 替换默认导出全部字段的 vector overload，避免静默请求 command-side state。
- 为合法 command read-side use 增加 maintained command/tasking packet 或 contract。
- 增加 architecture guard，禁止 command/tasking shell 字段回到
  `ObservationBatchPacket`。

验收标准：

- Agent observation consumer 不能通过 observation packet 读取 command-side state。
- Command/tasking read 必须携带自己的 maintained provenance，或者明确
  compatibility quarantine label。
- Python bindings 不再在 `ObservationBatchPacket` 上暴露 command/tasking shell 字段。

### WP24-J: Scenario Setup Facade Ownership

场景加载必须停止接受 raw-runtime-shaped production input。

必须修改：

- 把 `batch_apply.py` 的 `batch_runtime` 参数形状替换为 maintained facade/adapter
  setup target。
- 拆分 `world_setup_compat.py`：maintained setup request construction 与显式命名的
  compatibility fallback 分开。
- facade coverage 完成后，从 maintained `RuntimeFacadeAdapter` 路径移除 raw runtime
  fallback。
- 把 `UniversalEnv` 从直接持有 `ef_py.SimulationKernel()` 迁移到 single-world
  facade/adapter path。
- 给 `python/scenario/runtime` 与 `gym_envs/universal_env.py` 增加 architecture
  guard，禁止生产场景路径在没有显式 compatibility quarantine 的情况下实例化或消费
  raw runtime。

验收标准：

- 正常 training/runtime path 使用 facade-owned setup API。
- 剩余 `SimulationKernel` 或 raw `WorldBatchRuntime` 使用只能存在于 tests、
  diagnostics 或明确命名的 compatibility module。
- `train.py` 默认不能进入 raw-runtime production env。

### WP24-K: Maintained Contracts For Command-Chain Payloads

`MissionCommand`、`LeaderIntent`、`PilotReport` 不能继续作为 maintained facade
surface 上含混的 whole-shell payload。

必须修改：

- 为 `MissionCommand`、`LeaderIntent`、`PilotReport` 的业务 slice 创建 maintained
  batch contract，或者把现有 assignment 重命名并 gate 成 compatibility-only。
- 更新 runtime/facade/bindings：maintained business flow 暴露 maintained contract；
  compatibility shell 只能通过显式 quarantine name 暴露。
- Command-chain 测试必须通过 maintained contract 证明字段保真，不能再通过
  whole-shell observation export 证明。
- 增加与 TaskOrder deletion standard 对齐的 guard 覆盖。

验收标准：

- 没有 maintained consumer 能把 `MissionCommand`、`LeaderIntent`、`PilotReport`
  shell transport 声称为 maintained truth。
- Maintained command-chain flow 对必要业务字段有 typed contract roundtrip。
- Compatibility shell 被命名、局部化，并且在 quarantine 外 fail closed。

### WP24-L: Maintained Provenance Defaults At Call Sites

`agent_shim.py` 可以保留 compatibility default 作为 fail-closed 行为，但 maintained
business path 不允许隐式继承这个默认值。

必须修改：

- 审计 maintained caller 对 `single_agent_role()` 和 `roster_slot_role()` 的使用。
- 要求 maintained caller 显式传入 `OBS_FACADE_OBSERVATION_PACKET` 或 maintained
  `DecisionBelief` provenance。
- 增加测试证明默认 compatibility provenance 会在 maintained business entry point
  被拒绝。

验收标准：

- shim 默认值仍是安全的 compatibility metadata。
- Maintained path 必须显式选择 maintained provenance，不能意外使用 compatibility
  default。
- Law 14 read-side guard 持续拒绝 relabeled raw 或 compatibility input。

## 3. 分发队列

下一轮 implementation wave 可以并行，但不能拆成松散 optional ideas。

| 工作线 | 所有权范围 | 起点文件 | 产出 |
| --- | --- | --- | --- |
| WP24-I | Facade DTO 与 Python binding packet split。 | `src/runtime/facade/runtime_facade_types.h`、`src/runtime/facade/runtime_facade.cpp`、`src/interfaces/python/bindings_runtime.cpp`、DTO tests。 | 纯 observation packet 与 command/tasking export replacement。 |
| WP24-J | Scenario setup facade ownership。 | `python/scenario/runtime/batch_apply.py`、`python/scenario/runtime/world_setup_compat.py`、`python/rl/runtime/world_batch/adapter.py`、`gym_envs/universal_env.py`、`train.py`。 | Maintained setup target 与 raw-runtime quarantine。 |
| WP24-K | Command-chain maintained contracts。 | `src/runtime/contracts/world_batch_contracts.h`、runtime/facade APIs、command-chain tests。 | Maintained MissionCommand/LeaderIntent/PilotReport contracts 或显式 quarantine APIs。 |
| WP24-L | Python provenance call-site hardening。 | `python/rl/runtime/agent_shim.py`、runtime Python callers、Law 14 tests。 | Maintained call site 显式 provenance。 |

## 4. 验证门

本任务包的 focused validation 必须包含：

```bash
git diff --check
python -m py_compile python/scenario/runtime/batch_apply.py python/scenario/runtime/world_setup_compat.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py python/rl/runtime/agent_shim.py gym_envs/universal_env.py train.py
cmake --build build-workshop --target ef_py -j4
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/test_agent_shim.py
PYTHONPATH=build-workshop python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_policy_belief_boundaries.py tests/architecture/test_wp12_law14_read_side_enforcement.py tests/architecture/test_wp22_dto_domain_shell_guard.py
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "observation or batch_runtime or task_order or command_chain"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py -k "observation or batch_runtime or task_order or command_chain"
```

只有当 guard 证明 raw-runtime 与 compatibility shell path 不能默认回流到 maintained
production flow 时，本任务包才可以关闭。

## 5. 实施记录

### WP24-K

已完成 command-chain maintained route 的 runtime-contract 层：

- 新增 slice-based `MissionCommandMaintainedBatchContract`、
  `LeaderIntentMaintainedBatchContract`、`PilotReportMaintainedBatchContract`；
- 新增对应 `World*MaintainedAssignment` transport struct，只承载 maintained
  contract，不承载 whole-shell payload；
- 保留 `WorldMissionCommandAssignment`、`WorldLeaderIntentAssignment`、
  `WorldPilotReportAssignment` 为明确的 compatibility-shell transport；
- 为三类 payload 增加 `WorldBatchRuntime` maintained batch read/write 方法；
  在 ECS storage split 排期前，runtime 内部仍投影到 compatibility storage。

后续仍需要 WP24-I / 主线程把这些 runtime 方法接到 facade 和 Python bindings，
Python/facade caller 才能直接使用。
