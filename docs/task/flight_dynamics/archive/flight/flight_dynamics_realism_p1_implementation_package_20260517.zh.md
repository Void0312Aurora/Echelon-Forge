# 飞行动力学真实化 P1 实施包

状态：`2026-05-17` 草案版。

关联输入：

- [飞行动力学现实性分析与空战前置门槛](flight_dynamics_realism_analysis_20260516.zh.md)
- [飞行动力学真实化 P0 实施包](flight_dynamics_realism_p0_implementation_package_20260516.zh.md)
- [真实化任务总表](../program/realism_program_taskboard_20260516.zh.md)
- [P0 守门测试](../../../../tests/runtime/air_combat/test_flight_dynamics_p0_runtime_guards.py)

文档目的：

- 在 `P0` 已落最小骨架后，把飞行动力学方向收敛成一个可以直接排期开工的 `P1` 包。
- 明确 `P1` 不等于“直接做更复杂公式”，而是先把 `P0` 遗留的集成面收尾，再进入更深的真实性语义。
- 给出建议文件范围、最小测试清单、数据源落地方式和验收口径。

---

## 1. P1 总目标

`P1` 的目标不是“做到机型级高保真”，而是把当前已经存在的飞行动力学骨架变成：

1. 可以被数据库驱动、而不是只能靠代码默认值运行。
2. 可以被仪表、油耗、观测、测试一致读取，而不是各系统各自解释。
3. 可以开始承载更真实的 `Mach / compressibility / propulsion transient / stall semantics`，而不是继续停留在“趋势勉强可用”的状态。

因此，`P1` 分成两层：

1. `P1 前置集成收尾`
2. `P1 深化真实化`

其中第一层是第二层的前置条件，不建议跳过。

---

## 2. P1 分层与优先级

### 2.1 必须先做：P1 前置集成收尾

这一层的目标是把 `P0` 骨架真正接入主线，而不是继续停留在“代码里有字段、运行时默认可用，但数据库和接口还没接通”的状态。

必须先做的原因：

- 当前 `AeroTuning / EngineTuning / StallState` 还没有正式走 `unit_definition -> loader -> factory` 路径。
- 当前推进状态和失速状态还没有形成对 `instrument / logistics / observation / reward` 的统一事实来源。
- 当前 `propulsion_system` 还是 helper 语义，还没有成为正式注册的系统边界。
- 当前本地 `ef_py` / `SimulationKernel` 生命周期在 runtime test 中仍暴露出进程退出 `SIGABRT` 问题，测试基础设施还不够稳。

### 2.2 后续推进：P1 深化真实化

这一层才进入更真实的物理语义：

- 更完整的 `Mach / compressibility` 调度
- 更真实的发动机瞬态与加力段语义
- 更真实的失速/后失速语义
- 机型参数化和数据表

不建议在第一层未收口时直接展开，否则会出现：

- 参数能写但无法通过数据库挂接
- 仪表与油耗读的仍然不是同一套状态
- 测试只能围绕私有默认路径写，无法形成稳定验收口径

---

## 3. P1 前置集成收尾

### 3.1 目标

这一层只解决“P0 骨架如何正式接入主线”的问题。

达成标准：

1. `AeroTuning / EngineTuning / StallState` 能从数据库读入并挂到实体。
2. `ForceSystem / LogisticsSystem / InstrumentSystem / Observation` 对推进状态与失速状态的解释一致。
3. `propulsion` 的运行时更新边界清晰，不再由 `ForceSystem` 独占全部推进逻辑。
4. runtime tests 不再依赖规避式子进程退出技巧才能稳定运行。

### 3.2 必须先做项

#### A. Tuning 配置路径正式打通

建议文件范围：

- `/home/void0312/Workshop/CMO/src/content/unit_definition.h`
- `/home/void0312/Workshop/CMO/src/content/unit_definition_loader.cpp`
- `/home/void0312/Workshop/CMO/src/models/core/default_unit_factory.h`
- `/home/void0312/Workshop/CMO/src/components/physics/flight_dynamics_tuning.h`

需要完成的事：

1. 在 `Airframe / Engine / UnitDefinition` 中加入可选真实化字段。
2. 明确 `engine_ref` 与 `airframe` 字段对 `EngineTuning / AeroTuning` 的映射关系。
3. Factory 在 spawn 时挂载：
   - `AeroTuning`
   - `EngineTuning`
   - `StallState`
4. 保留向后兼容：
   - 没有新字段时仍能回退到当前默认路径

验收口径：

- 同一机型在“无 tuning 配置”和“有 tuning 配置”下都能成功 spawn。
- 配置缺失时不崩溃，且保留当前 `P0` 默认行为。

#### B. Propulsion 状态成为正式共享事实来源

建议文件范围：

- `/home/void0312/Workshop/CMO/src/systems/physics/propulsion_system.h`
- `/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_systems.cpp`
- `/home/void0312/Workshop/CMO/src/systems/physics/force_system.h`
- `/home/void0312/Workshop/CMO/src/systems/systems/logistics_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/instrument_system.h`

需要完成的事：

1. 明确 `propulsion_system` 是否作为独立系统正式注册。
2. 若正式注册：
   - `PropulsionSystem` 负责 `throttle -> propulsion state`
   - `ForceSystem` 只消费 `current_thrust_n`
3. `LogisticsSystem` 改为读：
   - `current_thrust_n`
   - `current_tsfc`
   - `afterburner_active`
4. `InstrumentSystem` 改为读实际推进状态，而不是重新猜测油耗与 RPM。

验收口径：

- 推力、燃油流量、发动机转速三者对同一油门阶跃响应方向一致。
- `AB on/off` 在推力、油耗、RPM 上都有一致可观测体现。

#### C. Observation / Runtime Test 一致性补齐

建议文件范围：

- `/home/void0312/Workshop/CMO/src/systems/physics/instrument_system.h`
- `/home/void0312/Workshop/CMO/src/interfaces/python/bindings_core.cpp`
- `/home/void0312/Workshop/CMO/src/core/mission/runtime/execution_observation_runtime.cpp`
- `/home/void0312/Workshop/CMO/tests/runtime/air_combat/test_flight_dynamics_realism_guards.py`
- `/home/void0312/Workshop/CMO/tests/runtime/air_combat/test_flight_dynamics_p0_runtime_guards.py`

需要完成的事：

1. 决定哪些 `P1` 运行时量需要观测：
   - `alpha_dot`
   - `stall_progress`
   - `pitch_break_active`
   - `throttle_state`
   - `ab_state`
2. 明确它们是否只进入调试/仪表，还是进入训练观测。
3. 排查并修复当前 `ef_py` / `SimulationKernel` 在 runtime test 中的进程退出异常。
4. 让 `P0` 新测试回到普通进程内运行，不再依赖 `os._exit(0)` 规避 teardown。

验收口径：

- 运行时测试可在同一 pytest 进程稳定执行。
- 仪表、Python binding、reward/observation 读取的字段语义一致。

### 3.3 可后置项

下面这些属于前置收尾的延伸，但不必阻塞第一批开工：

1. `StallState` 是否进入 agent observation。
2. `current_tsfc` 是否直接进入训练观测。
3. `propulsion_system` 是否彻底从 `force_system` 代码中抽离全部 helper。

---

## 4. P1 深化真实化

### 4.1 目标

在前置集成收尾完成后，`P1` 深化层要把当前“趋势正确但语义还粗”的部分推进到下一档：

1. 压缩性与阻力上升不再只是粗分段补偿。
2. 发动机瞬态与加力段不再只是单一一阶滞后。
3. 失速与恢复不再只是 `smoothstep + pitch-break surrogate`。
4. 至少形成首批机型可配置参数表，而不是只有全局默认值。

### 4.2 必须先做项

#### A. Mach / Compressibility 调度深化

建议文件范围：

- `/home/void0312/Workshop/CMO/src/components/physics/flight_dynamics_tuning.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/aero_state_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/aerodynamics_system.h`
- 如需要：
  `/home/void0312/Workshop/CMO/src/models/environment/default_environment_model.cpp`

建议内容：

1. 从当前一维 scale 深化为更清晰的分项调度：
   - `Cl_alpha(M)`
   - `Cd0(M)`
   - `k_induced(M)`
   - `Cm_alpha(M)`
   - `alpha_stall(M)`
2. 把“跨声速阻力 rise”从单个 `cd0_add_vs_mach` 扩成更明确的 `drag rise schedule`。
3. 明确是否引入分段：
   - 亚声速
   - 跨声速
   - 超声速

验收口径：

- `M 0.8 -> 1.2` 阻力显著上升。
- 高空声速、Mach 计算与环境模型保持一致。
- 同一 IAS 下高 Mach/高空工况不会继续表现得像低速线性气动。

#### B. 发动机瞬态 / AB 语义深化

建议文件范围：

- `/home/void0312/Workshop/CMO/src/components/physics/flight_dynamics_tuning.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/propulsion_system.h`
- `/home/void0312/Workshop/CMO/src/systems/systems/logistics_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/instrument_system.h`

建议内容：

1. 干推与加力分开建模，不只是一条 `ab_state`。
2. 明确：
   - idle -> mil
   - mil -> AB light
   - AB stage / partial AB
   - throttle chop / spool down
3. 把 `theta` 温度项从字段预留推进到实际使用。
4. 如数据允许，增加简单 `installed thrust vs altitude/mach` 表。

验收口径：

- 慢车到军推、军推到加力的响应时间常数不同。
- 油耗增长与 `AB` 状态一致，不再只是开关式倍增。
- 高 Mach 下 ram 收益存在上限，必要时进入衰减。

#### C. 失速 / 后失速语义深化

建议文件范围：

- `/home/void0312/Workshop/CMO/src/components/physics/flight_dynamics_tuning.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/aerodynamics_system.h`
- `/home/void0312/Workshop/CMO/src/models/air/default_control_model.cpp`
- 可选：
  `/home/void0312/Workshop/CMO/src/systems/physics/control_system.h`

建议内容：

1. 在 `stall_progress` 之外补最小语义：
   - onset
   - developed stall
   - recovery
2. 引入最小 hysteresis，而不是 entry/recovery 共用同一条静态曲线。
3. 将 `alpha_dot` 对 `Cm` 的影响从简单附加项推进到更明确的 `Cm_alpha_dot` surrogate。
4. 明确“FBW 保护导致难以进入深失速”是设计目标还是当前失真。

验收口径：

- 高 AoA 进入与改出在 `AoA / pitch / VVI / g` 上存在可复现但不完全对称的轨迹。
- recovery 时“先减 AoA，再恢复能量/姿态”的语义更加清晰。
- 不再把“高俯仰受保护爬升”误当成“后失速真实性”。

### 4.3 可以后置的深化项

以下可明确放到 `P1` 后半段或 `P2`：

1. 完整 `Cl/Cd/Cm/Cn(alpha, beta, M)` 二维/三维查表。
2. `wing rock / spin entry / departure`。
3. 全量操纵面导数与控制分配。
4. 惯量随外挂投放、燃油迁移联动。
5. 湍流、阵风、风切变。

---

## 5. 建议文件范围

### 5.1 P1 前置集成收尾

建议优先文件：

- `/home/void0312/Workshop/CMO/src/content/unit_definition.h`
- `/home/void0312/Workshop/CMO/src/content/unit_definition_loader.cpp`
- `/home/void0312/Workshop/CMO/src/models/core/default_unit_factory.h`
- `/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_systems.cpp`
- `/home/void0312/Workshop/CMO/src/systems/physics/propulsion_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/force_system.h`
- `/home/void0312/Workshop/CMO/src/systems/systems/logistics_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/instrument_system.h`
- `/home/void0312/Workshop/CMO/src/interfaces/python/bindings_core.cpp`

### 5.2 P1 深化真实化

建议优先文件：

- `/home/void0312/Workshop/CMO/src/components/physics/flight_dynamics_tuning.h`
- `/home/void0312/Workshop/CMO/src/components/physics/dynamics.h`
- `/home/void0312/Workshop/CMO/src/components/physics/forces.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/aero_state_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/aerodynamics_system.h`
- `/home/void0312/Workshop/CMO/src/systems/physics/propulsion_system.h`
- `/home/void0312/Workshop/CMO/src/models/air/default_control_model.cpp`

---

## 6. 最小测试清单

### 6.1 P1 前置集成收尾测试

必须先有：

1. `loader_factory_mounts_flight_dynamics_tuning`
   - 验证 `AeroTuning / EngineTuning / StallState` 能从数据库进入实体。
2. `propulsion_state_drives_force_logistics_instrument_consistently`
   - 验证推力、油耗、RPM 对同一阶跃命令一致。
3. `python_runtime_guards_no_abort_on_kernel_teardown`
   - 验证 runtime tests 不再需要子进程或 `os._exit(0)`。

### 6.2 P1 深化真实化测试

建议至少有：

1. `mach_drag_rise_trend`
   - `M 0.8~1.2` 阻力 rise 明确可见。
2. `level_accel_vs_altitude_and_mach`
   - 不同高度/Mach 的平飞加速能力趋势合理。
3. `engine_spool_and_ab_transition`
   - idle/mil/AB 三段响应不同。
4. `high_aoa_entry_recovery_hysteresis`
   - entry/recovery 不再完全同路径。
5. `default_fallback_still_safe_without_tuning`
   - 缺少新字段时仍不破坏现有路径。

---

## 7. 数据源落地方式

### 7.1 一手资料优先

建议优先使用：

1. `U.S. Standard Atmosphere 1976`
   - 用于 `rho / T / a / Mach` 和高空 fallback
2. `FAA Airplane Flying Handbook`
   - 用于 stall/recovery 趋势与验收语义
3. NASA/NACA 公开高 AoA、压缩性、稳定性导数资料
   - 只在题名、PDF、相关章表可确认时上升为参数依据

### 7.2 二手工程资料

建议用途：

1. `JSBSim`
   - 用于发动机状态机结构、FDM 字段组织、趋势 sanity
2. `AeroBench`
   - 用于 F-16 风格状态组织、测试场景、回归 sanity

### 7.3 社区/非官方资料

可以使用，但建议只做初值或 sanity：

1. `BMS / DCS / forum extracted tables`
2. `CMANO / Harpoon / 玩家整理数据库`
3. 非官方手册摘录

原则：

- 有来源链接、有机型上下文、有单位说明时才入库。
- 无法确认出处的数值，不直接进入默认 tuning，只能进入候选参考表。

### 7.4 数据落地形式

建议新增或扩展：

1. `aircraft/modules/engines/*.json`
   - 放发动机时间常数、AB 阈值、TSFC、installed thrust schedule
2. `aircraft/modules/airframes/*.json`
   - 放 `Cl/Cd/Cm` 一维分段、stall 调度、pitch-break 参数
3. `docs/task/flight_dynamics/<direction>/*.md`
   - 在各方向子项目目录内保留“数据源 -> 参数字段”的引用表和标定说明

---

## 8. 验收口径

### 8.1 P1 前置集成收尾验收

通过标准：

1. 新 tuning 字段可通过数据库驱动实体。
2. `propulsion` 状态成为推力、油耗、仪表的一致来源。
3. runtime test 基础设施不再有已知 teardown abort。

### 8.2 P1 深化真实化验收

通过标准：

1. `Mach / drag rise / high-altitude speed of sound` 趋势可重复验证。
2. 发动机瞬态有可观测阶段差异，不再是单一近似。
3. 高 AoA 进入/恢复语义比 `P0` 更接近“先减 AoA，再恢复”的真实流程。
4. 至少 1 个机型可通过外部参考数据驱动出一套显式 tuning，而不是只吃默认值。

---

## 9. 对 P0 文档措辞的顺手修正

建议在后续引用 `P0` 结果时统一使用下面口径：

1. 不把 `P0` 描述成“已经实现失速/后失速真实性”。
   - 更准确的说法是：
     `P0 已建立 high-AoA observability、最小 stall progression 和 pitch-break surrogate`
2. 不把 `NASA TP-1538` 直接写成 `P0` 数值字段的确定依据。
   - 更准确的说法是：
     `目前仅可作为高 AoA / post-stall 现象候选参考，待补精确题名与章表后再升格`
3. 不把当前 `P0` 高 AoA 行为表述成“已具备深失速真实性”。
   - 更准确的说法是：
     `当前更接近受 FBW/控制律保护的高俯仰高 AoA 趋势，而非完整后失速语义`

---

## 10. 推荐实施顺序

建议按下面顺序推进 `P1`：

1. 先完成 `loader / factory / system registration / instrument / logistics` 收尾。
2. 再修 runtime test 与 `ef_py` 生命周期问题。
3. 之后推进 `Mach / drag rise / propulsion transient` 深化。
4. 最后再进入 `stall / post-stall / hysteresis / per-aircraft tables`。

这个顺序的核心理由是：

- 先把“数据如何进来、状态如何共享、测试如何稳定”弄对，
- 再把“公式做得更真”推进下去，
- 可以显著减少返工和口径漂移。
