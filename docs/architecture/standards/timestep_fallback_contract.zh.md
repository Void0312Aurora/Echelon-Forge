# 时间步长 fallback 与校验契约

Language:
- English canonical contract: `timestep_fallback_contract.md`。
- Chinese companion document。
Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/timestep_fallback_contract.md`
Owner: `architecture/runtime-contracts`
Last verified: `2026-10-10`

## 范围

本契约说明仿真和任务入口在每系统时间步为零、负数、非有限或不受支持时的行为。fallback 是直接 Flecs world、初始化和暂停阶段的兼容路径，不会改变 `SimulationKernel::step()` 或 `WorldBatch` 正常传入的正时间步。

策略按消费者分别定义。fallback 不代表正常 step 中引擎固定时钟存在多个活动 cadence，也不表示要把所有系统的时间步全局替换为同一个值。

## 策略清单

| 表面 | 无效或不受支持的输入 | 维护中的响应 | 可达路径 / 所有者 |
| --- | --- | --- | --- |
| `SimulationKernel::set_time_step` | 非有限或 `<= 0` | 抛出 `std::invalid_argument`；保留有限正值 | 公共 kernel 配置；`src/core/engine/simulation_kernel.cpp` |
| Kernel 默认值 | setup 未提供值 | `SimulationKernel::kDefaultTimeStepS`（`1/60 s`） | kernel 构造/reset；`src/core/engine/simulation_kernel.h` |
| WorldBatch setup | DTO `0` | 将旧的“缺省”哨兵映射为 kernel 默认值（`1/60 s`） | `src/core/engine/world_batch_setup_helper.h`；负数/非有限 DTO 被拒绝 |
| 共享物理积分器 | 零、负数或非有限 | 通过 `resolve_integrator_dt` 使用 `physics_runtime::kIntegratorFallbackDtS`（`0.05 s`） | Leapfrog、转动、地面接触及 air state/actuator/propulsion/control；直接 Flecs 调用或暂停阶段 |
| Aircraft/naval 实体 tick | 零、负数或非有限 | 通过 `resolve_entity_dt` 使用 `physics_runtime::kEntityFallbackDtS`（`1/60 s`） | Aircraft damage、naval damage、ship motion、submarine motion；直接系统调用 |
| 任务跑道外 grace 换算 | 非有限或 `<= 1e-6 s` | 通过 `resolve_termination_dt` 使用 `mission_runtime::kTerminationFallbackDtS`（`0.05 s`） | 将秒数 grace 转换为 step 数；不替换 kernel 时钟 |

共享物理 fallback 同样用于 `actuator_first_order_step` 和 `first_order_step`。有限正值行为保持不变；无效值现在采用与注册系统相同的有限正值判定。

## 可达性与边界

- 正常 `SimulationKernel::step()` 提供已校验的正固定步长。fallback 可由直接 Flecs 测试、初始化/暂停执行，以及用无效 iterator delta 调用注册系统的兼容调用者触发。
- 任务 `time_step_s` 是 termination 计算输入。fallback 只保护秒数到 step 数的换算，episode 时钟仍由调用方负责。
- WorldBatch 的零哨兵是传输规则，并不允许调用 `SimulationKernel::set_time_step(0)`。
- 本标准不授权修改系统模型常数、动作 cadence、传感器 cadence 或武器制导 cadence；此类修改需要单独契约和正时间步回归证据。

## 必须保留的测试

`src/tests/test_timestep_contract.cpp` 锁定：

- 共享物理策略对有限正值的保留，以及对零、负数、非有限值的 fallback；
- air actuator 和 propulsion 一阶响应的 fallback 行为；
- aircraft damage、naval motion/damage 使用的 `1/60 s` 实体 fallback；
- 任务跑道外 grace 对零、负数、`NaN`、无穷输入的处理，以及一个正时间步对照。

现有 kernel、ground-contact 和 WorldBatch 测试继续负责 kernel 拒绝、共享接触/积分行为和 DTO 零值映射。
