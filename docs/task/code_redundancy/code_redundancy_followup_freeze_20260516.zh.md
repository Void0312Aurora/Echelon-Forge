# 代码冗余优化后续冻结计划

状态：`2026-05-16` 冻结执行版；`2026-05-16` WP-A / WP-B / WP-C 已全部收口
关联文档：

- [代码冗余与重复逻辑审计报告](/home/void0312/Workshop/CMO/docs/task/code_redundancy/code_redundancy_duplication_audit_20260516.zh.md)
- [Common / Air / Naval 模块拆分冻结计划](/home/void0312/Workshop/CMO/docs/task/common_air_naval/common_air_naval_modular_split_plan_20260515.zh.md)

文档定位：

- 本文档用于收敛 `2026-05-16` 审计之后**仍待完成**、且适合继续推进的非 `scenario_loader` 主线优化项。
- 本文档只冻结一条窄范围的“兼容层样板压缩 + 低风险共享抽取 + 最小测试补强”路线。
- 本文档不授权继续扩张到 `gym_envs/scenario_loader/*` 拆分主线，也不授权以“顺手整理”为名推进新的大文件拆分。

验证口径：涉及 Python / nanobind / runtime 的实现时，默认使用本地构建产物与仓库虚拟环境进行验收，即：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python -m pytest
```

如果只做局部 C++ helper / 文档调整，允许使用聚焦测试集合做阶段验收；但凡触及 `ef_py` 绑定可见面，必须补一次 `cmake --build build-workshop --target ef_py -j4`。

## 一、当前基线

根据审计文档与已完成实现，以下条目已在当前主线中完成第一轮或实质收口：

1. `3.1` `MassProperties` 重复注册已删除。
2. `3.3` `command_link_system.h` 三类 pending delivery 逻辑已模板化。
3. `3.4` Python 侧 `TaskOrder / LeaderIntent / PilotReport` clone 已改为反射驱动，并有字段一致性校验。
4. `4.1` `MovementCommand` 兼容链已完成三批低风险样板收口：
   - throttle / brake fallback helper
   - legacy movement / lagged / pending movement helper
   - action / pending action / pending mission helper
5. `5.6` `EGI -> InstrumentState` 已完成“导航状态面 -> 仪表投影面”边界收口。
6. `5.7` 地面航迹计算已统一到 `Math::ground_track_deg_from_velocity()`。
7. `5.8` 主运行时姿态旋转公共化已完成，武器效果模型中的简化近似暂保留。
8. `5.12` mission obs taxonomy 已改为基础字段 + 增量字段组合，并有直接测试覆盖。
9. `5.13` `env_config.py` merge helper 已抽取完成，并补齐 optional merge 直接单测。
10. `5.4` scripted controllers 已完成最小共享骨架收口：
   - 新增 `python/rl/control/base_scripted_controller.py`
   - 三个 controller 共享 `action_dim/dt`、`obs -> np.ndarray` 解包、零动作构造与角度 wrap helper
   - 公开类名与构造签名保持不变，聚焦 controller contract 已回归通过
11. `3.2` / `5.10` 已完成第一批边界补强：
   - `MassUpdate` 现已显式以 `Mass` 为运行时分解质量权威，并同步 `MassProperties.empty_mass_kg/current_total_mass_kg`
   - 新增最小 debug 读回口与聚焦回归，固定质量组件同步关系
   - 补充 `MissionCommand / PilotAction / CommPacket` 绑定 surface 直接测试，收紧 nanobind 第三维护面风险

因此，后续不再继续围绕上述已完成项扩写新范围；它们只作为当前基线记录保留。

## 二、剩余事项分桶

### 2.1 本冻结版允许继续推进

当前状态：本冻结版内授权推进的条目已全部完成本轮收口，当前**不再保留继续实现中的活动条目**。

已完成收口的授权条目：

1. `4.1` `MovementCommand` 兼容链剩余低风险样板与 consumer 收口。
2. `5.14` `simulation_kernel_command_api.cpp` entity validate / warn 样板收口。
3. `3.2` `Mass` / `MassProperties` 双轨质量组件边界分析与第一阶段最小实现。
4. `5.10` nanobind 第三维护面的状态澄清与测试补强。

### 2.2 本冻结版明确暂缓

以下条目不适合在当前阶段继续展开：

1. `4.2` `common_core_profile.py` bridge 与 profile 共性再抽象。
2. `4.3` `leader_env.py` 大文件职责拆分。
3. `4.4` `air_profile.py` / `naval_profile.py` 共基类抽象。
4. `5.5` `world_batch_vec_env.py` / `cooperative_world_batch_vec_env.py` 深度 infrastructure 合并。
5. `5.16` `training_callbacks.py` 与 `world_model/dreamer.py` 大文件拆分。

这些项要么风险显著高于当前收益，要么与海空并行开发边界耦合较深，必须另起冻结文档。

### 2.3 本冻结版禁止触碰

以下条目本轮**不授权实现**：

1. `5.3` `gym_envs/scenario_loader/core.py` 拆分。
2. `5.11` `gym_envs/scenario_loader/execution_runtime/shaping.py` 抽象收口。
3. `5.15` `execution_runtime/mainline.py` / `shadow.py` 双写整理。
4. 任何会影响 `gym_envs/scenario_loader/*` 正在进行中的并行整合工作的结构性重排。

原因：

- 用户已明确提示 `gym_env` 正在拆分；
- 当前仓库存在另一条并行整合分支；
- 若继续把审计优化扩展到该主线，极易形成重复施工和合并冲突。

## 三、总体策略

本冻结版采用“三阶段收口”策略：

1. 先继续压缩**兼容层样板**，尽量把高频初始化、entity 校验、helper 调度收敛到共享原语。
2. 再处理**轻量共骨架抽取**，只抽已经有聚焦 contract 的脚本控制器，不碰更重的 runtime/env 大文件。
3. 最后只做**边界澄清 + 最小测试补强**，不在本计划内启动新的大重构。

核心原则：

1. 代码实现优先于进一步分析，但每一步都必须有明确停止条件。
2. 每个阶段都必须能独立验收，任何跨阶段新范围必须另起文档。
3. 文档中列为“暂缓”或“禁止触碰”的内容，不得因为“顺手可以一起做”而带入实现。

## 四、冻结工作包

### WP-A：兼容链与命令 API 样板继续收口

目标：

- 完成 `4.1` 剩余低风险 consumer 的收敛判断。
- 优先处理 `5.14`，减少 `simulation_kernel_command_api.cpp` 中重复 entity 解析与 invalid guard 样板。
- 只在 helper 不改变 public API 的前提下进行抽取。

冻结范围：

- [src/core/engine/simulation_kernel_command_api.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_command_api.cpp)
- [src/components/command/legacy_command.h](/home/void0312/Workshop/CMO/src/components/command/legacy_command.h)
- [src/components/command/command_link.h](/home/void0312/Workshop/CMO/src/components/command/command_link.h)
- 必要时允许触及：
  - [src/systems/core/operation_system.h](/home/void0312/Workshop/CMO/src/systems/core/operation_system.h)
  - [src/systems/physics/control_system.h](/home/void0312/Workshop/CMO/src/systems/physics/control_system.h)

明确不做：

1. 不在本阶段把 `MovementCommand` 标记为 `[[deprecated]]`。
2. 不在本阶段删除 `MovementCommand` / `LaggedCommand` / `PendingMovementCommand` 兼容链。
3. 不把该 helper 向 observation / visual API 全面推广。

验收标准：

1. `cmake --build build-workshop --target ef_py -j4` 通过。
2. 以下聚焦回归保持通过：
   - `tests/runtime/test_mission_command_split_semantics.py`
   - `tests/runtime/test_mission_runtime.py`
   - `tests/world_batch/test_world_batch_runtime.py`
3. 审计文档 `4.1`、`5.14` 的状态同步更新。

当前执行记录：

1. 已完成第一批：`simulation_kernel_command_api.cpp` 的 invalid guard / world time / active-copy helper 化。
2. 已完成第二批：`operation_system.h` 中 `MovementCommand` / `LaggedCommand` 的 seed 初始化样板收口。
3. 已确认 `control_system.h` 当前不再继续抽象；它只保留调度/转发责任，不作为本阶段新的收口面。

停止条件：

- 一旦 helper 抽取需要改变 API 行为、entity 生命周期语义或跨文件大面积联动，即停止并转入后续候选，不在本阶段继续。

### WP-B：scripted controller 共骨架最小抽取

目标：

- 解决 `5.4` 中三个 scripted controller 的共享接口/输入解包重复。
- 提取最小 `BaseScriptedController` 或等价共享 helper，但保持现有 controller 名称与入口不变。

冻结范围：

- [python/rl/control/scripted_takeoff.py](/home/void0312/Workshop/CMO/python/rl/control/scripted_takeoff.py)
- [python/rl/control/scripted_stable_flight.py](/home/void0312/Workshop/CMO/python/rl/control/scripted_stable_flight.py)
- [python/rl/control/scripted_landing.py](/home/void0312/Workshop/CMO/python/rl/control/scripted_landing.py)
- 允许新增：
  - `python/rl/control/base_scripted_controller.py`
  - 或同目录下的轻量共享 helper 模块

明确不做：

1. 不重写控制律本身。
2. 不改变 contract runner 对三个公开 controller 类名的依赖方式。
3. 不把该阶段扩展为 `wrappers.py` / `leader_env.py` 的脚本基线重构。

验收标准：

1. 下列 contract / 测试保持通过：
   - `tests/contracts/unit/controllers/scripted_takeoff_takeoff2_throttle.json`
   - `tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json`
   - `tests/contracts/unit/controllers/scripted_landing_controller.json`
   - `tests/contracts/unit/controllers/scripted_stable_flight_rudder_sign.json`
2. 若新增共享 helper，三个 controller 的公开构造签名保持兼容。
3. 审计文档 `5.4` 状态更新为已完成或第一批收口。

当前执行记录：

1. 已新增 [python/rl/control/base_scripted_controller.py](/home/void0312/Workshop/CMO/python/rl/control/base_scripted_controller.py)，统一 `action_dim/dt` 保存、`obs` 数组解包、零动作构造与 `wrap_deg()`。
2. 已将 [scripted_takeoff.py](/home/void0312/Workshop/CMO/python/rl/control/scripted_takeoff.py)、[scripted_stable_flight.py](/home/void0312/Workshop/CMO/python/rl/control/scripted_stable_flight.py)、[scripted_landing.py](/home/void0312/Workshop/CMO/python/rl/control/scripted_landing.py) 切换为共享 helper，但未改动控制律主体，也未改动公开类名或构造签名。
3. 已补齐 [tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json](/home/void0312/Workshop/CMO/tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json) 缺失的 `type: "unit_regression"` 元数据，使其能被统一 contract runner 正常分发执行。
4. 已完成以下聚焦验证：
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/controllers/scripted_takeoff_takeoff2_throttle.json`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/controllers/scripted_landing_controller.json`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/controllers/scripted_stable_flight_rudder_sign.json`

停止条件：

- 只要抽取开始要求改动大量 env/wrapper 调用链，立即停止，保留为单目录内 helper 收口，不再向外扩展。

### WP-C：质量组件与绑定维护面边界冻结

目标：

- 对 `3.2` 与 `5.10` 只做“边界澄清 + 最小补强”，不做整仓重构。
- 明确 `Mass` / `MassProperties` 的第一阶段收口策略。
- 明确 nanobind 绑定作为维护面的合理边界，以及需要的最小测试保障。

冻结范围：

- [src/components/physics/dynamics.h](/home/void0312/Workshop/CMO/src/components/physics/dynamics.h)
- [src/components/systems/logistics.h](/home/void0312/Workshop/CMO/src/components/systems/logistics.h)
- [src/systems/systems/logistics_system.h](/home/void0312/Workshop/CMO/src/systems/systems/logistics_system.h)
- [src/interfaces/python/bindings_command.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/bindings_command.cpp)
- [tests/leader/test_two_ship_contract_fields.py](/home/void0312/Workshop/CMO/tests/leader/test_two_ship_contract_fields.py)
- 允许新增针对质量组件边界的最小回归测试

明确不做：

1. 不在本阶段废除 `Mass` 组件。
2. 不一次性把所有 consumer 改为只读 `MassProperties`。
3. 不生成新的自动绑定系统，不替换 nanobind 现有 `.def_rw(...)` 模式。

验收标准：

1. 如果有代码变更，必须补聚焦测试，证明 `Mass` / `MassProperties` 没有引入行为回归。
2. `bindings_command.cpp` 只允许做与维护面一致性有关的最小补强，不允许展开为全面自动化改造。
3. 审计文档 `3.2` 与 `5.10` 的状态和后续建议同步更新。

当前执行记录：

1. 已在 [src/systems/systems/logistics_system.h](/home/void0312/Workshop/CMO/src/systems/systems/logistics_system.h) 将 `MassUpdate` 收紧为“`Mass` 为运行时分解质量权威，`MassProperties` 仅镜像 `empty/total` 读数”的第一阶段边界：
   - `rigid_mass.fuel_mass_kg` 继续由 `FuelSystem` 驱动；
   - `MassProperties.empty_mass_kg` 与 `current_total_mass_kg` 改为显式镜像 `Mass` 的 `empty` 与 `get_total_kg()`；
   - 因此 `MassProperties.current_total_mass_kg` 不再漏掉 `stores_mass_kg`。
2. 已新增最小 debug 读回口：
   - [simulation_kernel.h](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel.h)
   - [simulation_kernel_observation_api.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_observation_api.cpp)
   - [bindings_core.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/bindings_core.cpp)
   用于测试期读取 `[mass_empty, mass_fuel, mass_stores, mass_total, props_empty, props_total]`，未扩展为通用组件暴露面。
3. 已新增聚焦测试：
   - [tests/runtime/test_mass_component_boundary.py](/home/void0312/Workshop/CMO/tests/runtime/test_mass_component_boundary.py)
   - [tests/runtime/test_bindings_command_surface.py](/home/void0312/Workshop/CMO/tests/runtime/test_bindings_command_surface.py)
4. 已完成以下验收：
   - `cmake --build build-workshop --target ef_py -j4`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest tests/runtime/test_mass_component_boundary.py -q`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest tests/runtime/test_bindings_command_surface.py -q`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest tests/leader/test_two_ship_contract_fields.py -q`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest tests/runtime/test_command_api_entity_guards.py tests/runtime/test_mission_command_split_semantics.py -q`

停止条件：

- 一旦发现需要跨 `aerodynamics / force / leapfrog / logistics` 多系统联动迁移，立即停止在“分析 + 冻结边界”层，不在本计划内继续代码实现。

## 五、阶段顺序

固定顺序如下：

1. `WP-A`：先继续压缩命令兼容链样板。
2. `WP-B`：再处理 scripted controller 最小共骨架。
3. `WP-C`：最后只做质量组件与绑定维护面的边界冻结或最小补强。

不允许跳序原因：

1. `WP-A` 与当前已完成的 helper 化主线直接衔接，回归面最可控。
2. `WP-B` 有现成 contract，可做稳定的小步抽取。
3. `WP-C` 风险最高，必须在前两批完全收口后再决定是实现还是仅更新边界文档。

## 六、冻结规则

1. 本文档之外的新条目，不得直接进入实现。
2. 凡是涉及 `gym_envs/scenario_loader/*` 的优化诉求，全部回退到并行主线，不得在本文档名义下推进。
3. 若某阶段出现“需要拆大文件才能继续”的情况，视为超出本冻结版范围，应停止并单独立项。
4. 文档更新必须与代码状态同步；不得保留“已做完但文档仍写待做”的状态。
5. 每完成一个工作包，都要在审计文档中记录“执行更新”，避免后续重复判断。

## 七、完成定义

本冻结版视为完成，需同时满足：

1. `WP-A`、`WP-B` 完成并通过各自聚焦验收。
2. `WP-C` 至少完成边界结论冻结；如果实施代码，则需完成对应测试。
3. 审计文档与本计划文档中的“剩余事项”列表同步收敛，不再出现已完成条目仍停留在“立即切入”列表中的情况。

**2026-05-16 完成确认**：

1. `WP-A`、`WP-B`、`WP-C` 均已完成，并已记录各自执行更新与聚焦验收结果。
2. 本文档 `2.1` 中不再保留活动中的实现条目。
3. 后续若继续推进该主题，应转入“下一份冻结文档”而不是在本文档上继续扩写。

## 八、后续候选（需另行冻结）

以下方向不属于本计划，但可能成为下一份冻结文档候选：

1. `leader_env.py` 命令编解码 / observation builder 拆分。
2. `world_batch_vec_env.py` / `cooperative_world_batch_vec_env.py` infrastructure mixin 化。
3. `common_core_profile.py` 与 `air/naval_profile.py` 的共性下沉。
4. `Mass` / `MassProperties` 的真正单权威组件迁移。
5. `scenario_loader` 主线拆分完成后的审计回补。

这些项必须在当前冻结版关闭后，再单独形成新的收敛文档。
