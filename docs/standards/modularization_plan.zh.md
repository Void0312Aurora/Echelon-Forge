<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/modularization_plan.md. Review before treating this file as authoritative. -->

# 模块化计划

本文档仍然有效，但需在新的标准体系下阅读：

- [标准概览](README.md)
- [联合基线](joint/command_and_modeling_baseline.md)
- [服务画像](services/README.md)

本文档概述了一个最小化的、分阶段的计划，用于对项目进行模块化，以提高可维护性并实现单元模型、传感器和战斗逻辑的可替换性。

## 目标
- 将稳定的核心与可替换的模型分离。
- 允许在不更改引擎核心的情况下，替换单元定义、传感器模型和效果逻辑。
- 保持低复杂度：仅在需要可变性的地方进行模块化。

## 原则
- 单向依赖：核心 -> 系统 -> 接口（无反向边）。
- 数据定义与执行逻辑分离。
- 可替换的模块位于小型、明确的接口之后。
- 领域中立的核心优先；服务和平台的特化不应向上泄漏。

## 模块映射（目标）

### core/
- 用途：仿真生命周期、时间步进、实体生命周期、世界访问。
- 拥有：SimulationKernel、重置/步进、实体注册表、确定性时间。
- 依赖：仅 components/。

### components/
- 用途：纯数据组件（无逻辑）。
- 拥有：Transform、Velocity、Sensor、Health、Score、Weapon 等。
- 依赖：无。

### systems/
- 用途：系统执行（控制、移动、传感器扫描、制导、伤害）。
- 拥有：系统注册与更新逻辑。
- 依赖：core/、components/。

### interfaces/
- 用途：外部 API（Python、Web、CLI 工具）。
- 拥有：仅绑定与数据转换。
- 依赖：core/。

### content/
- 用途：用于单元、武器、传感器、场景的数据驱动定义。
- 拥有：UnitDefinition、WeaponDefinition、SensorDefinition、ScenarioConfig。
- 依赖：无（仅数据）。

### standards/
- 用途：建模基线及领域/服务画像。
- 拥有：联合/公共核心、服务画像、平台/任务专化文档。
- 依赖：无（文档来源）。

### models/
- 用途：可替换的行为模型（效果、传感器、制导）。
- 拥有：接口背后的具体实现。
- 依赖：components/（以及可能 core/ 用于世界访问）。

## 可替换接口（稳定）

### IUnitFactory
- 职责：从 UnitDefinition 生成实体。
- 输入：UnitDefinition、初始状态。
- 输出：带有组件束的实体。

### IEffectsModel
- 职责：处理命中、伤害和分数变化。
- 输入：攻击者、目标、事件上下文。
- 输出：状态增量（血量、分数、摧毁事件）。

### ISensorModel
- 职责：从环境状态产生探测结果。
- 输入：传感器拥有者、环境快照。
- 输出：ContactList（具有一致约定的探测结果）。

## 组件束
- AirUnitBundle：Transform、Velocity、FlightModel、Sensor、Health、Score。
- MissileBundle：Transform、Velocity、Missile、Sensor（导引头）、Health。
- FacilityBundle：Transform、Health、Sensor（可选）。

组件束由 IUnitFactory 根据 UnitDefinition 创建。

## 分阶段迁移计划

### 阶段 1：文档与边界
- 记录约定（角度、单位、传感器语义）。
- 定义目标模块映射（本文档）。

### 阶段 2：单元定义与工厂
- 在 content/ 下引入 UnitDefinition 数据结构。
- 在 models/ 中实现基本 UnitFactory 以生成组件束。
- 更新 SimulationKernel 中的 spawn_unit 方法，委托给 UnitFactory。

### 阶段 3：效果模型
- 引入 IEffectsModel 接口。
- 将伤害逻辑从 systems/damage_system.h 移至 EffectsModel 实现中（系统调用接口）。

### 阶段 4：传感器模型
- 引入 ISensorModel 接口。
- 将探测计算移至模型实现中；系统仅安排扫描。

### 阶段 5：可选优化
- 添加场景配置（content/）。
- 添加替代模型（低/中/高保真度）并按场景选择。

## 所有权与约束
- Core 不应直接包含模型头文件，应使用前向接口。
- Systems 不应依赖 interfaces/。
- Interfaces 不应通过核心 API 之外的方式修改内部状态。

## 非目标（目前）
- 完整的插件系统或动态加载。
- ECS 替换或分布式架构变更。
- 对渲染/可视化的深层重构。

## 标准对齐

从新的文档基线来看，未来的模块化应遵循：

- “联合/公共核心”保持在服务特定语义之上
- 服务画像解释组织与控制模式
- 平台/任务语义保留在领域特定模块和适配器中

这意味着，当概念本质上属于：
- 通用指挥关系
- 通用任务组织
- 服务特定的战术编组

时，未来的代码应避免将空中特定术语推入全局核心模块。
