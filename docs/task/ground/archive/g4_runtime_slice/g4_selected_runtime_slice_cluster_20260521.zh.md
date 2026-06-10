<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g4_runtime_slice/g4_selected_runtime_slice_cluster_20260521.md. Review before treating this file as authoritative. -->

# G4 选定运行时切片集群

状态：`2026-05-22` 已实现并验证经归一化的 ground `TaskOrder ->
LeaderIntent -> PilotReport` status shell 所代表的 selected tasking-only
lifecycle-proof 切片。

输入：

- [G4 自述文件](README.md)
- [G3 执行面预检集群](../g3_execution_surface_design/g3_execution_surface_preflight_cluster_20260521.md)
- [子代理使用策略](../../../standards/governance/subagent_usage_policy.md)

## 目的

定义已释放的 G4 集群边界、worker packet 与验收标准，针对唯一批准的
地面运行时切片。

## 任务集群

### `G4-A` 生命周期 shell

- 将 ground tasking 路径从 `TaskOrder` 归一化为 `LeaderIntent` 再到
  `PilotReport`。
- 保持该切片仅为 status shell。
- 不加入 command-delivery、sensing、movement、terrain、fires 或 effects
  语义。

验收：

- 释放路径恰好是经归一化的
  `TaskOrder -> LeaderIntent -> PilotReport` lifecycle shell。
- 实现仍仅限于 G3 批准的写入范围。

### `G4-B` worker packet 与验证聚焦

- 保持 worker packet 简洁且可序列化以便调度。
- 明确写出能证明该释放切片的验证命令，而不扩张行为。
- 保留空中/海军兼容性检查所需的共享入口点。

验收：

- worker packet 说明范围、排除项、验证与残留。
- 验证命令明确且可从仓库根目录运行。

### `G4-C` 无私有路径证明

- 证明该切片使用的是维护中的共享入口点。
- 证明没有引入 ground-only runtime path、私有 import shortcut 或
  air-only fallback。

验收：

- 证明引用维护中的 `tasking_profile` bridge。
- 证明不依赖 route refs、recovery base/runway fields、landing/takeoff
  semantics、world-truth observation surfaces 或已 deferred 的 terrain/LOS/
  radio runtime。

### `G4-D` 残留映射与交接

- 记录此切片之外仍然 deferred 的表面。
- 将剩余工作作为 residual map 交接，而不是作为隐含验收。

验收：

- residual map 明确保持 `CommandPacket`、`ObservationPacket`、
  `TrackPacket`、`P3`、`P10`、movement、sensing、terrain、fires 与 broad
  `MissionCommand` 工作继续 deferred。
- 文档集明确列出触及的文件、运行的命令、兼容性结果与残留项。

## 写入范围

G3 已释放一个有边界的文件族规则。最终 worker 应尽量保持在最窄文件集内，以证明
shared entry-point lifecycle behavior：

- 仍承载经归一化 `TaskOrder -> LeaderIntent -> PilotReport` shell 的共享
  tasking-profile/runtime call sites
- focused ground lifecycle tests
- common-core / naval mission-profile behavior 的 narrow compatibility guards

发布前请勿编辑：

- 运动/物理系统
- 传感器/跟踪系统
- 火控、武器或伤害运行时
- 宽泛的外观 API 接口
- C++ DTO 或 binding surface，除非后续有已接受计划明确释放它们

## 建议的验证

已接受的基准期望：

```bash
git diff --check
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/runtime/mission/test_leader_tasking_runtime.py
python -m pytest -q tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/ground/task_order_ground_profile_defaults.json tests/contracts/unit/ground/task_order_ground_minimal_structures.json tests/contracts/unit/ground/task_order_ground_support_relationships.json
```

## 交接

返回：

- 触及的文件
- 运行的命令
- 维护入口点的证据
- 兼容性结果
- 残留映射

无私有路径证明要求：

- ground runtime selection 必须经过维护中的 `tasking_profile` bridge，而不是
  ground-only loop 或 air-only import shortcut
- 第一切片不得依赖 route refs、recovery base/runway fields、
  landing/takeoff semantics、world-truth observation surfaces，或已 deferred 的
  terrain/LOS/radio runtime

## 主线程验证结果

触及的实现文件：

- `python/rl/runtime/world_batch_vec_env.py`
- `python/rl/runtime/cooperative_world_batch_vec_env.py`
- `tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py`

已接受证据：

- 两个 batch env 都从 `python.rl.tasking.bridge` 导入
  `build_kernel_mission_command`，而不是从 air-first `leader_tasking` 模块导入。
- `tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py` 证明 explicit
  ground `tasking_profile` dispatch、Army `service_profile` inference、
  source-level no-private-path import checks，以及 air/naval compatibility
  resolution。
- 第一 G4 切片仍只导出 shared command-chain status shell：
  `TaskOrder`、`LeaderIntent` 与 `PilotReport`。

验证已通过：

```bash
git diff --check -- docs\task\ground python\rl\runtime tests\runtime\mission\test_ground_runtime_lifecycle_bridge.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\mission\test_ground_runtime_lifecycle_bridge.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\leader\test_tasking_profile_contracts.py tests\runtime\mission\test_leader_tasking_runtime.py
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_scenario_contract.py --spec tests\contracts\unit\ground\task_order_ground_profile_defaults.json tests\contracts\unit\ground\task_order_ground_minimal_structures.json tests\contracts\unit\ground\task_order_ground_support_relationships.json
```

仍然 deferred：

- `CommandPacket`、`ObservationPacket`、`TrackPacket`、formal `P3`、formal
  `P10`、movement、sensing、terrain、fires、effects、DTO/binding expansion 与
  broad `MissionCommand` growth。
