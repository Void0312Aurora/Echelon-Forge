<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g1_contract_skeleton/g1_profile_dto_preflight_20260521.md. Review before treating this file as authoritative. -->

# G1 Profile 与 DTO 预检

状态：`2026-05-21` G1 实现发布评审预检完成。

输入：

- [地面子代理调度队列](../ground_subagent_dispatch_queue_20260521.md)
- [G1 自述文件](README.md)
- [G1 profile 与 DTO 契约集群](g1_profile_dto_contract_cluster_20260521.md)
- [地面标准概述](../../../standards/ground/README.md)
- [地面最小任务结构](../../../standards/ground/minimal_task_structure.md)
- [美国陆军 profile](../../../standards/services/army.md)
- [子代理使用策略](../../../standards/governance/subagent_usage_policy.md)

## 建议

- 建议：`implementation-ready`
- DTO-shell 建议：`G1 中不需要`
- 范围建议：保持 G1 `仅限 Python profile`

未发现阻止使用狭窄 G1 的源缺口，该 G1 仅添加别名解析、地面 profile shell 和通用核心启动器默认值。如果有人试图将切片扩大到地面 `MissionCommand`、运行时执行行为、场景加载器行为、Python 绑定或新的 C++ DTO 字段所有权，G1 应立即停止。

## 源清单

### Python 解析器与 profile 选择界面

| 文件 | 锚点 | 预检发现 |
|------|--------|-------------------|
| `python/rl/tasking/bridge.py` | `_normalized_profile_name` 第 11-32 行 | 目前仅识别 `air` 和 `naval`。`Army`、`army`、`ground` 和 `land` 尚不可识别。 |
| `python/rl/tasking/bridge.py` | `resolve_tasking_profile` 第 43-53 行 | 解析器仅返回 `_air` 或 `_naval`。未来的 G1 地面别名工作应在此处进行。 |
| `python/rl/tasking/bridge.py` | `tasking_profile_for_loader` 第 56-80 行 | 现有优先级对于 G1 已正确：显式的 `tasking_profile` 优先，然后是 `service_profile` 推断。地面实现应严格遵循此优先级。 |
| `python/rl/tasking/common_core_profile.py` | `_profile_name_from_context` 第 23-59 行 | 通用核心默认值也仅推断 `naval`，否则回退到 `air`。地面支持也必须在此处添加，而不仅仅在 `bridge.py`。 |
| `python/rl/tasking/common_core_profile.py` | `_profile_module_for_context` 第 62-66 行 | 目前只能选择 `_naval_profile` 或 `_air_profile`。必须在此处连接地面 profile 选择。 |
| `python/rl/tasking/common_core_profile.py` | `normalize_task_order_spec` 第 187-188 行 | 分派到所选的 profile 模块。地面规范化可以插入此现有模式。 |
| `python/rl/tasking/common_core_profile.py` | `infer_coordination_mode` 第 195-210 行 | 已委托给所选的 profile 模块，因此地面特定的 `Support` 处理可以保持 Python 本地。 |
| `python/rl/tasking/common_core_profile.py` | `apply_task_order_common_core_defaults` 第 359-436 行 | 已存在用于 `service_profile`、`task_family`、`tactical_unit_type`、`command_relationship`、`authority_scope`、`coordination_mode` 和支持 ID 的共享回填路径。 |
| `python/rl/tasking/common_core_profile.py` | `apply_leader_intent_common_core_defaults` 第 439-545 行 | 现有传播路径可将地面默认值从 `TaskOrder` 传递到 `LeaderIntent`，无需 DTO 更改。 |
| `python/rl/tasking/common_core_profile.py` | `apply_pilot_report_common_core_defaults` 第 548-630 行 | 现有传播路径可将地面默认值从 `TaskOrder` 传递到 `PilotReport`，无需 DTO 更改。 |

### 可镜像的现有适配器/profile 模式

| 文件 | 锚点 | 预检发现 |
|------|--------|-------------------|
| `python/rl/tasking/air_adapter.py` | 模块导出第 3-48 行 | 适配器模块是通用核心辅助程序加上一个 profile 模块的薄导出层。 |
| `python/rl/tasking/naval_adapter.py` | 模块导出第 3-45 行 | 地面可以遵循相同的薄适配器模式，而无需更改桥接契约形状。 |
| `python/rl/profile/naval_profile.py` | `infer_naval_task_family` 第 97-120 行 | 领域特定的任务族回退目前保留在 Python profile 代码中。 |
| `python/rl/profile/naval_profile.py` | `infer_coordination_mode` 第 123-159 行 | 领域特定的协调默认值目前也是 Python 本地的。 |
| `python/rl/profile/naval_profile.py` | `normalize_task_order_spec` 第 196-260 行 | 按 profile 规范化的模式已存在。地面应重用此结构。 |
| `python/rl/profile/air_profile.py` | `infer_coordination_mode` 第 153-178 行 | 空中使用通用协调回退，基于共享枚举表面；地面可以执行相同操作。 |

### 与 G1 DTO 决策相关的 DTO 和绑定表面

| 文件 | 锚点 | 预检发现 |
|------|--------|-------------------|
| `src/components/tasking/common/core_tasking_enums.h` | 第 3-66 行 | 共享枚举已公开 `ServiceProfile::Army`、通用 `TacticalUnitType`、`CommandRelationship::Support` 和 `CoordinationMode::Support`。G1 默认值不需要地面特定枚举。 |
| `src/components/tasking/common/task_order_core.h` | 第 7-28 行 | `TaskOrderCore` 已拥有 G0 所需的所有第一波地面字段：service、task family、tactical unit type、parent/support ID、command relationship、authority scope、coordination mode。 |
| `src/components/tasking/common/leader_intent_core.h` | 第 7-27 行 | `LeaderIntentCore` 已携带默认传播所需的公共字段。 |
| `src/components/tasking/common/pilot_report_core.h` | 第 8-25 行 | `PilotReportCore` 已携带默认传播所需的公共字段。 |
| `src/components/tasking/task_order.h` | 第 3-11 行 | 聚合形状仍为 `common + air + naval`；尚不存在地面切片。 |
| `src/components/tasking/leader_intent.h` | 第 3-11 行 | 与 `TaskOrder` 相同的聚合分层模式。 |
| `src/components/tasking/pilot_report.h` | 第 3-7 行 | 与 `TaskOrder` 相同的聚合分层模式。 |
| `src/components/tasking/naval/task_order_naval.h` | 第 7-10 行 | 仅存在海军专用头文件，因为海军拥有额外的 DTO 字段。G1 地面尚不拥有任何等效的额外字段。 |
| `src/interfaces/python/bindings_command.cpp` | `ServiceProfile` 第 100-105 行 | Python 绑定已公开 `ServiceProfile.Army`。 |
| `src/interfaces/python/bindings_command.cpp` | `TaskOrder` 绑定第 319-379 行 | G1 所需的通用核心任务字段已绑定。 |
| `src/interfaces/python/bindings_command.cpp` | `LeaderIntent` 绑定第 381-429 行 | G1 所需的通用核心指挥意图字段已绑定。 |

### 要保留的现有测试锚点

| 文件 | 锚点 | 预检发现 |
|------|--------|-------------------|
| `tests/leader/test_tasking_profile_contracts.py` | `test_normalize_task_order_spec_backfills_common_core` 第 77-95 行 | 空中任务的现有共享默认行为必须保持不变。 |
| `tests/leader/test_tasking_profile_contracts.py` | `test_bridge_resolves_naval_profile` 第 22-24 行 | 地面别名工作不得退化海军解析。 |
| `tests/leader/test_tasking_profile_contracts.py` | `test_normalize_task_order_spec_uses_naval_defaults` 第 26-41 行 | 地面工作不得泄漏到海军默认映射中。 |
| `tests/runtime/mission/test_naval_mission_command_mapping.py` | `test_tasking_profile_for_loader_prefers_explicit_profile_over_service_profile` 第 32-44 行 | 添加地面别名后，显式的 `tasking_profile` 优先级必须保持不變。 |
| `tests/runtime/mission/test_naval_mission_command_mapping.py` | `test_tasking_profile_for_loader_infers_naval_from_service_profile_when_tasking_profile_missing` 第 45-56 行 | 添加陆军推断后，海军的服务 profile 推断模式必须仍然有效。 |
| `tests/leader/test_command_field_projection_contracts.py` | 第 13-93 行 | 领域特定的 DTO 添加目前需要绑定和内核往返覆盖。这证明了在没有自有字段的情况下添加空的地面 DTO shell 是不可取的。 |

## 提议的未来实现编写范围

### 要编辑的文件

- `python/rl/tasking/bridge.py`
- `python/rl/tasking/common_core_profile.py`
- `python/rl/tasking/ground_adapter.py` 新文件
- `python/rl/profile/ground_profile.py` 新文件
- `tests/leader/` 下的针对性测试

### G1 中保持不变的文件

- `src/components/tasking/**`
- `src/components/command/**`
- `src/interfaces/python/bindings_command.cpp`
- `tests/runtime/mission/**`，除非用作验证的现有只读回归测试
- 运行时、移动、传感器、武器、伤害、外观和场景加载器代码

### 狭窄的实现目标

未来 G1 应仅：

1. 教 Python 解析器和通用核心辅助层识别 `army`、`ground` 和 `land`。
2. 添加一个薄的 `ground_adapter` 模块，公开与现有空中/海军适配器相同的可调用名称。
3. 添加一个 `ground_profile` 模块，负责规范化启动任务顺序，并在现有通用核心 DTO 字段之上提供地面特定的默认推断。
4. 添加针对性的地面语义测试。

未来 G1 不应：

- 发明新的地面 DTO 字段
- 添加地面特定的 C++ 头文件
- 添加 Python 绑定
- 定义维护中的地面 `MissionCommand` 执行词汇表
- 修改场景导入或运行时行为

## 别名规范化计划

### 接受的输入

解析器级别接受的输入应为：

- 字符串 `army`
- 字符串 `ground`
- 字符串 `land`
- 字符串化的枚举 `ServiceProfile.Army`
- 枚举值 `ef_py.ServiceProfile.Army`

### 规范化结果

上述所有接受的输入应规范化为维护中的任务配置文件名 `ground`。

### 解析器规则

1. 扩展 `python/rl/tasking/bridge.py::_normalized_profile_name`，使 `Army`/`army`/`ground`/`land` 返回 `ground`。
2. 扩展 `python/rl/tasking/common_core_profile.py::_profile_name_from_context`，具有相同的识别集。
3. 保留 `tasking_profile_for_loader` 中的现有优先级：显式的 `tasking_profile` 仍优先于任何 `service_profile`。
4. 仅在未找到显式的 `tasking_profile` 时，才从 `service_profile = Army` 推断 `ground`。
5. 仅将 `army` 和 `land` 作为接受的输入别名。未来规范化的输出和 profile 模块命名应保持为 `ground`。

## 启动任务默认映射表

当前的共享 `TaskFamily` 枚举没有 `Maneuver` 或通用 `Support` 条目，因此 G1 应使用最近的现有通用族，并将确切的地面含义保留在 `task_name`、地面 profile 模块和接受的别名 `ground` 中。

| 任务名称 | `service_profile` | `task_family` 回退 | `tactical_unit_type` | `command_relationship` | `authority_scope` | `coordination_mode` | ID 规则 |
|-----------|-------------------|------------------------|----------------------|------------------------|-------------------|---------------------|----------|
| `TASK_MOVE` | `Army` | `Transit` | `TacticalUnit` | `TACON` | `Tactical` | `Independent` | `parent_node_id` 是指挥所有者回退；`supported_node_id` 和 `supporting_node_id` 保持可选 |
| `TASK_OCCUPY` | `Army` | `Defend` | `TacticalUnit` | `TACON` | `Tactical` | `Independent` | `parent_node_id` 是指挥所有者回退；支持 ID 保持可选 |
| `TASK_SUPPORT` | `Army` | `Defend` | `TacticalUnit` | `Support` | `Tactical` | `Support` | 当已知关系时，`supporting_node_id` 和 `supported_node_id` 携带该关系；`parent_node_id` 仍作为回退所有者 |

备注：

- `TacticalUnit` 是冻结的排级第一切片最近的维护中的通用核心单元类别。
- `TASK_SUPPORT` 应使用现有的共享支持关系字段，而不是海军专用的 DTO 扩展。
- 如果主线程希望 `TASK_OCCUPY` 或 `TASK_SUPPORT` 使用不同于 `Defend` 的 `task_family` 回退，那是策略选择，而非代码阻塞。当前源码表面可在不新增 DTO 的情况下支持任一选择。

## DTO-Shell 建议

建议：`G1 中不需要`

证据：

- G0 地面基线仅需 `TaskOrderCore`、`LeaderIntentCore` 和 `PilotReportCore` 中已有的通用核心字段。
- `ServiceProfile::Army` 已存在且已绑定。
- 当前唯一的领域特定任务 DTO 切片是海军的，其额外字段由专用头文件、绑定和内核往返测试支持。地面目前尚无任何等效字段集。
- 此时添加空的 `src/components/tasking/ground/**` 或 `src/components/command/ground/**` 头文件会扩大 C++ 和绑定边界，而不会增加行为、覆盖价值或冻结字段所有权。

后续工作的升级触发点：

- 如果后续阶段引入地面专有的 DTO 字段，且无法放入当前通用核心，则应在同一阶段添加 C++ 外壳、绑定和往返测试。这在 G1 中不合理。

## 聚焦验证计划

### 实现期间运行的只读验证

```bash
git diff --check
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/runtime/mission/test_naval_mission_command_mapping.py
```

### 后续 G1 实现中应添加的聚焦测试

新增一个聚焦文件，建议命名为 `tests/leader/test_tasking_profile_contracts.py`，覆盖以下内容：

1. `resolve_tasking_profile("army" | "ground" | "land")` 返回地面适配器。
2. `resolve_tasking_profile(ef_py.ServiceProfile.Army)` 返回地面适配器。
3. `tasking_profile_for_loader` 仍然优先使用显式 `tasking_profile` 而非 `service_profile = Army`。
4. 当 `tasking_profile` 缺失时，`tasking_profile_for_loader` 能从 `service_profile = Army` 推断出地面。
5. `normalize_task_order_spec` 将 `TASK_MOVE`、`TASK_OCCUPY` 和 `TASK_SUPPORT` 映射到上表。
6. `apply_task_order_common_core_defaults`、`apply_leader_intent_common_core_defaults` 和 `apply_pilot_report_common_core_defaults` 保留地面语义和 ID。

G1 中不强制要求的测试：

- 任务运行时执行行为
- 场景加载器固件覆盖
- 新 DTO 字段的内核往返测试

这些属于后续 G2/G3/G4 阶段，除非范围明确扩大。

## 空中/海军行为的兼容性风险

1. `bridge.py` 和 `common_core_profile.py` 各有自己的配置文件名称推断。地面支持必须同时落地到这两处，否则解析器和默认传播将不一致。
2. 现有显式配置文件优先级必须保持不变。地面推断不得覆盖显式的 `air` 或 `naval` 任务配置文件。
3. `service_profile_default()` 仍返回 `AirForce`，因此地面默认值必须通过地面配置文件路径注入，而不是更改全局共享默认值。
4. G1 应避免任何新的 `MissionCommand` 地面语义。该表面尚未冻结，扩大它可能带来超出 G1 范围的空中/海军回归。

## 遗留问题与发布决策

### G2/G3 遗留问题

- G2 在 G1 落地后仍需第一个固件路径和任务规范示例。
- G3 仍负责第一个可接受的地面执行表面和任何真实的地面 `MissionCommand` 行为。
- 如果通用枚举表面增长，`task_family` 回退标签的精确值可以在以后重新考虑，而无需现在强制进行 G1 DTO 更改。

### 阻塞检查

未发现狭窄 G1 版本的阻塞因素。

只有当请求的实现范围超出以下范围时，才应停止发布：

- Python 解析器/配置文件工作
- 通用核心默认映射
- 聚焦的领导者/配置文件测试

## Worker 返回包

流：`G1-A`

状态：`preflight-only`

修改的文件：

- `docs/task/ground/g1_contract_skeleton/g1_profile_dto_preflight_20260521.md`

运行过的命令：

- `sed -n '1,220p' docs/standards/governance/subagent_usage_policy.md`
- `sed -n '1,240p' docs/task/ground/ground_subagent_dispatch_queue_20260521.md`
- `sed -n '1,220p' docs/task/ground/g1_contract_skeleton/README.md`
- `sed -n '1,260p' docs/task/ground/g1_contract_skeleton/g1_profile_dto_contract_cluster_20260521.md`
- `sed -n '1,260p' docs/standards/ground/README.md`
- `sed -n '1,260p' docs/standards/ground/minimal_task_structure.md`
- `sed -n '1,260p' docs/standards/services/army.md`
- `rg -n "tasking_profile|common_core_profile|naval_profile|ground_profile|adapter|TASK_MOVE|TASK_OCCUPY|TASK_SUPPORT|specialization|army|ground|land" python src tests`
- `nl -ba python/rl/tasking/bridge.py | sed -n '1,240p'`
- `nl -ba python/rl/tasking/common_core_profile.py | sed -n '1,220p'`
- `nl -ba python/rl/tasking/common_core_profile.py | sed -n '220,660p'`
- `nl -ba python/rl/tasking/air_adapter.py | sed -n '1,220p'`
- `nl -ba python/rl/tasking/naval_adapter.py | sed -n '1,220p'`
- `nl -ba python/rl/profile/naval_profile.py | sed -n '1,260p'`
- `nl -ba python/rl/profile/air_profile.py | sed -n '100,260p'`
- `nl -ba python/rl/profile/air_profile.py | sed -n '520,620p'`
- `nl -ba tests/leader/test_tasking_profile_contracts.py | sed -n '1,220p'`
- `nl -ba tests/leader/test_tasking_profile_contracts.py | sed -n '1,220p'`
- `rg -n "struct TaskOrder|struct LeaderIntent|struct PilotReport|class TaskOrder|TaskOrder\\b|LeaderIntent\\b|PilotReport\\b|ServiceProfile|TaskFamily|TacticalUnitType|CoordinationMode" src/interfaces src/components src/core`
- `nl -ba src/components/tasking/README.md | sed -n '1,220p'`
- `find src/components -maxdepth 3 \\( -path '*/tasking/*' -o -path '*/command/*' \\) | sort`
- `nl -ba src/interfaces/python/bindings_command.cpp | sed -n '300,520p'`
- `nl -ba src/components/tasking/common/core_tasking_enums.h | sed -n '1,220p'`
- `nl -ba python/rl/profile/common_core_defaults.py | sed -n '1,260p'`
- `nl -ba src/components/tasking/task_order.h | sed -n '1,120p'`
- `nl -ba src/components/tasking/leader_intent.h | sed -n '1,120p'`
- `nl -ba src/components/tasking/pilot_report.h | sed -n '1,120p'`
- `nl -ba src/components/tasking/naval/task_order_naval.h | sed -n '1,160p'`
- `nl -ba src/components/tasking/naval/leader_intent_naval.h | sed -n '1,160p'`
- `nl -ba src/components/tasking/naval/pilot_report_naval.h | sed -n '1,160p'`
- `nl -ba tests/runtime/mission/test_naval_mission_command_mapping.py | sed -n '1,240p'`
- `nl -ba python/rl/tasking/__init__.py | sed -n '1,220p'`
- `nl -ba python/rl/profile/__init__.py | sed -n '1,200p'`
- `find docs/task/ground/g1_contract_skeleton -maxdepth 1 -type f | sort`
- `git status --short`
- `nl -ba tests/leader/test_command_field_projection_contracts.py | sed -n '1,220p'`
- `nl -ba src/components/tasking/common/task_order_core.h | sed -n '1,220p'`
- `nl -ba src/components/tasking/common/leader_intent_core.h | sed -n '1,220p'`
- `nl -ba src/components/tasking/common/pilot_report_core.h | sed -n '1,220p'`
- `rg -n "TaskFamily\\.(Transit|Patrol|Escort|Intercept|Attack|Defend|Recover|Withdraw)|task_family.*(Transit|Patrol|Escort|Intercept|Attack|Defend|Recover|Withdraw)" python tests src`
- `rg -n "TASK_MOVE|TASK_OCCUPY|TASK_SUPPORT|Maneuver|Support" docs python tests src`
- `nl -ba docs/task/ground/g2_content_test_seed/g2_content_fixture_test_cluster_20260521.md | sed -n '1,200p'`

证据：

- 地面别名解析目前在两处 Python 解析器路径中均缺失。
- 现有通用核心 DTO 字段足以满足第一波地面起始默认值。
- 当前 C++ 任务分层仅在领域拥有额外字段时才证明领域特定头文件的合理性。
- 现有的海军测试提供了 G1 必须保留的关键兼容性护栏。

遗留问题：

- G2 固件和测试等待已接受的 G1 实现。
- G3 仍负责第一个真实的地面执行表面。

集成说明：

- 主线程集成应将此说明视为 G1 预飞推荐，用于实现发布审查。

关闭影响：

- 此预飞解除了狭窄 G1 实现请求的阻塞。

G1 实现推荐：

- `implementation-ready`

G1 阻塞因素：

- 无（对于狭窄的 Python 配置文件切片而言）
- 如果范围扩展到运行时语义、场景加载器更改、Python 绑定或 C++ 地面 DTO 所有权，则阻塞
