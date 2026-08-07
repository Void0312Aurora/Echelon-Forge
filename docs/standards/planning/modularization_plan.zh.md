# 模块化规划

Language:
- English canonical: `planning/modularization_plan.md`
- Chinese companion: [modularization_plan.zh.md](modularization_plan.zh.md)

状态：`2026-06-10`，带当前布局说明的活跃规划文档，不是当前 runtime 合同。

本文档仍然有效，但现在必须放在新的 standards tree 下阅读：

- [标准概览](../README.md)
- [联合指挥与建模基线](../../domains/joint/standards/command_and_modeling_baseline.zh.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md)
- [军种画像总览](../../domains/joint/service_profiles/README.md)

这页文档的职责，是回答“后续如果继续拆分代码库，应怎样模块化”，而不是描述当前 runtime 已经如何稳定工作。

关于当前现状的权威口径，仍应以维护中的工作流与标准文档为准。

## 目的

模块化规划回答的是一个面向未来的问题：

`如果项目继续把稳定核心、可替换模型和领域特化分开，代码库应如何拆分？`

因此，下文中的目录映射与接口设计都应被理解为目标结构，而不是证明“这些模块今天已经完整存在”。

## 当前已实现的域根目录

仓库现在已经有真实的 domain owner roots。这让本规划页继续有效，但也改变了阅读方式：
当前 roots 是 ownership direction 的证据，不证明每个域都具备同等 runtime 成熟度。

当前已实现 roots：

- `src/components/domains/`
  - 当前 owner：`air/`、`naval/`、`ground/`
  - 职责：域自有 ECS component、command/tasking 扩展、平台 DTO，以及窄 combat/status 切片
  - 边界：共享 shell 仍在 `src/components/{combat,command,tasking}`；新增域专属
    component slice 应进入 `src/components/domains/<domain>/`
- `src/systems/domains/`
  - 当前 owner：`air/`、`naval/`
  - 职责：域自有 runtime system registration 与 per-tick behavior
  - 边界：这里尚未释放 `ground/` runtime system owner；ground movement、sensing、
    fires、damage 与 terrain-control runtime 在对应接口和验收门槛存在前保持 held
- `src/models/domains/`
  - 当前 owner：`air/`、`naval/`、`ground/`
  - 职责：域自有可替换模型实现、adapter，以及供共享模型消费的显式 placeholder route
  - 边界：ground model ownership 只限于 unit-factory capability evidence 与显式
    effects placeholder routing，不代表完整 land-domain runtime maturity

新增域只有在具备真实 component、system 或 model owner 时，才应扩展这些
`domains/<domain>/` roots。不要把空 production owner root、demo domain 或教学壳当作
standards evidence。

旧的共享或过渡 roots 仍然有效：

- `src/components/combat`、`src/components/command` 与 `src/components/tasking`
  仍是共享 component shell。
- `src/systems/combat`、`src/systems/physics` 与 `src/systems/systems` 仍是共享或过渡
  runtime 区域。
- `src/models/weapons` 与 `src/models/systems` 仍是共享 model 区域；当域 adapter
  存在时，它们会路由到相应域 adapter。

这意味着：下方 target map 对未来 cleanup 仍有用，但当前代码库已经把
`src/*/domains/<domain>/` 作为域自有 specialization 的优先位置。

## 目标

- 将稳定核心与可替换模型分开
- 让单位定义、传感器模型与效果逻辑能够在不重写引擎基础层的前提下演进
- 只在可变性真正有价值的地方做模块化，避免无收益复杂化

## 原则

- 单向依赖：`core -> systems -> interfaces`，不引入有意的反向边
- 数据定义与执行逻辑分开
- 可替换模块放在小而明确的接口之后
- 先保留领域中立核心，再把军种与平台特化向下收束，而不是向上泄漏

这些内容是规划原则，不是说仓库今天已经在所有位置都完全满足它们。

## 目标模块映射

### `core/`

- 用途：仿真生命周期、时间步进、实体生命周期、世界访问
- 目标所有权：`SimulationKernel`、reset/step 流程、实体注册、确定性时间
- 目标依赖方向：只依赖 `components/`

### `components/`

- 用途：纯数据组件
- 目标所有权：`Transform`、`Velocity`、`Sensor`、`Health`、`Score`、
  `Weapon` 等数据载体
- 目标依赖方向：不依赖更高层
- 当前 domain 约定：域专属 slice 放在 `src/components/domains/<domain>/`；
  共享 component shell 保留在 domain roots 之外

### `systems/`

- 用途：控制、移动、传感器扫描、制导、伤害等执行系统
- 目标所有权：系统注册与更新逻辑
- 目标依赖方向：依赖 `core/` 与 `components/`
- 当前 domain 约定：已释放的 domain runtime owner 放在
  `src/systems/domains/<domain>/`；缺少某个域 root 表示 runtime ownership 仍 held，
  不表示该 runtime 归其他域所有

### `interfaces/`

- 用途：Python 绑定、Web 表面、CLI 工具等外部接口
- 目标所有权：仅负责绑定与数据转换
- 目标依赖方向：依赖 `core/`

### `content/`

- 用途：单位、武器、传感器、场景的数据驱动定义
- 目标所有权：`UnitDefinition`、`WeaponDefinition`、`SensorDefinition`、
  `ScenarioConfig`
- 目标依赖方向：仅数据

### `standards/`

- 用途：建模、分层与所有权的文档真源
- 目标所有权：joint/common core、service profiles、workflow bridge 文档、
  specialization 文档
- 目标依赖方向：无

### `models/`

- 用途：可替换的行为模型实现
- 目标所有权：接口背后的 effects、sensor、guidance 等具体模型
- 目标依赖方向：通常依赖 `components/`，在必须访问世界状态时可有限依赖 `core/`
- 当前 domain 约定：域自有 model adapter 与实现放在 `src/models/domains/<domain>/`；
  共享 model route 可继续留在 `src/models/{weapons,systems}`，并在需要时分发到域 adapter

## 目标可替换接口

下列接口当前仍应视为规划目标，只有未来代码真正落地后，才应被视为已存在稳定接口。

### `IUnitFactory`

- 职责：根据 `UnitDefinition` 生成实体
- 输入：`UnitDefinition` 与初始状态
- 输出：附带适当组件束的实体

### `IEffectsModel`

- 职责：解析命中、伤害与得分效果
- 输入：攻击者、目标与事件上下文
- 输出：血量、分数或摧毁事件等状态增量

### `ISensorModel`

- 职责：根据环境状态生成探测结果
- 输入：传感器拥有者与环境快照
- 输出：符合维护中约定的 detection lists

## 示例组件束目标

这些组件束仍只是意图示例，用来说明工厂输出形状：

- `AirUnitBundle`：`Transform`、`Velocity`、`FlightModel`、`Sensor`、
  `Health`、`Score`
- `MissileBundle`：`Transform`、`Velocity`、`Missile`、导引头 `Sensor`、
  `Health`
- `FacilityBundle`：`Transform`、`Health`、可选 `Sensor`

它们用于表达工厂输出方向，并不意味着已经存在最终 ABI。

## 分阶段迁移计划

### 阶段 1：文档与边界

- 记录约定与所有权边界
- 在本规划文档中固定目标模块映射

### 阶段 2：单位定义与工厂

- 在 `content/` 下引入 `UnitDefinition` 风格的数据定义
- 在 `models/` 中建立基本工厂路径
- 把生成逻辑从硬编码构造逐步迁向委托式生成

### 阶段 3：效果模型

- 引入 `IEffectsModel` 风格接口
- 把伤害与杀伤逻辑移到接口之后

### 阶段 4：传感器模型

- 引入 `ISensorModel` 风格接口
- 把探测计算移到模型边界之后，由系统负责调度扫描

### 阶段 5：可选细化

- 增加场景配置内容层
- 增加不同保真度模型与按场景选择机制

## 所有权与约束

未来模块化应继续遵守以下约束：

- core 模块避免直接依赖具体模型头文件
- systems 不应依赖外部接口层
- 外部接口负责数据翻译，而不是变成隐藏的 runtime 所有者
- `docs/standards/` 中的文档所有权应与代码所有权边界保持一致

## 当前非目标

- 完整插件市场或动态加载系统
- ECS 替换或分布式架构重写
- 深层渲染或可视化重构

## 与标准树的对齐

未来模块化应遵循当前维护中的标准树：

- `joint/common core` 保持在军种特定语义之上
- service profiles 负责解释组织与控制口径
- 平台/任务语义继续留在 specialized modules 与 adapters 中
- workflow bridge 的所有权继续区别于 pure runtime kernels

这意味着，未来代码不应把空中或海上特有术语推入全局核心模块，尤其当一个概念本质上只是：

- 通用指挥关系
- 通用任务组织锚点
- 军种特定的战术编组

## 相关文档

- [标准概览](../README.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md)
- [文档对齐映射](../overview/document_alignment_map.md)
