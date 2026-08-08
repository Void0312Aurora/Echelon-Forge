# 系统模块化 Issue 计划

Language:
- English canonical: [modularization_plan.md](modularization_plan.md)
- Chinese companion: `modularization_plan.zh.md`

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/architecture/work/issues/modularization_plan.md`
Owner: `architecture/system-modularization`
Last verified: `2026-08-08`

状态：依据当前源码布局形成的 owner-local draft issue plan；不是 runtime contract，
也不是 implementation work package。

## 授权边界

本文档不授权代码移动、创建目录、创建或删除接口、修改构建、修改 runtime 行为，
也不授权启动实现任务。任何获准变更都必须具备单独评审的 work package，其中明确
scope、依赖影响、测试、兼容行为和验收证据。

## 权威与证据顺序

本 issue 从属于当前
[严格仿真系统架构基线](../../standards/simulation_system_architecture_design.zh.md)。
该基线定义规范性 architecture laws、分层所有权、domain extension 准入和验证门禁。
迁移期间，[架构计划索引](../../../plan/archive/owner_migration_20260808/architecture/README.zh.md)仍是权威入口，
[Architecture owner README](../../README.zh.md)也记录了这一点。

当本 issue 与其他来源冲突时，按以下顺序裁决：

1. 严格架构基线负责规范性架构规则；
2. 当前源码与可执行测试负责已实现事实；
3. 本 draft 只记录候选缺口和可能的执行顺序。

本 issue 不修订严格基线，也不把任何候选路线提升为 maintained architecture。
候选项要转化为实现工作，必须在
[simulation architecture](../../../task/simulation_architecture/archive/phase3c_closeout_20260808/README.zh.md)
下形成单独授权的任务。

## 目的与范围

本 issue 所回答的问题比旧页面更窄：

`当前模块还存在哪些所有权和依赖缺口，使其尚未完全符合严格架构基线？`

它覆盖：

- 已核验的 `src/*/domains/<domain>/` 所有权根；
- 已存在的可替换模型接口及其当前 composition point；
- 缺失的 Ground system owner；
- 评估后续移动时使用的依赖规则。

它不定义第二套架构基线、新插件系统或新的全领域 runtime stack。

## 已核验的当前 Domain Roots

| 根目录 | 当前 domain owner | 已核验职责 | 当前限制 |
| --- | --- | --- | --- |
| [`src/components/domains/`](../../../../src/components/domains/README.zh.md) | `air`、`naval`、`ground` | Domain-owned ECS data、command/tasking 扩展、platform data 与窄 combat/status slice。 | Ground 是 static G0/G1 command/tasking 和 placeholder component 表面，不是完整 land runtime。 |
| [`src/systems/domains/`](../../../../src/systems/domains/README.zh.md) | `air`、`naval` | 已释放的 air flight behavior 与 naval motion/operations per-tick domain system。 | `src/systems/domains/ground/` owner 不存在。 |
| [`src/models/domains/`](../../../../src/models/domains/README.zh.md) | `air`、`naval`、`ground` | Domain model 实现、adapter，以及由共享 default 消费的显式 placeholder route。 | Ground 只有 effects placeholder route，没有维护中的 movement、sensing、fires、damage 或 terrain model。 |

共享和过渡 roots 仍是真实实现表面：

- `src/components/{combat,command,tasking}` 保存共享 carrier 与 compatibility
  aggregation；
- `src/systems/{combat,physics,systems}` 保存共享或尚未迁移的 system owner；
- `src/models/{core,systems,weapons}` 保存 default unit factory、sensor、effects、
  guidance 与相关共享实现。

某个 domain 目录存在，只能证明具名 owner slice 已存在；它不能证明各域成熟度相同，
不能释放缺失的 system owner，也不授权移动共享代码。

## 已存在的可替换接口

旧计划把下列接口错误地描述为未来工作。三者都已存在于 `src/core/interfaces/`，
具有当前实现，并可通过 `SimulationKernel` setter 替换。

| 接口 | 当前合同与实现 | 剩余问题 |
| --- | --- | --- |
| [`IUnitFactory`](../../../../src/core/interfaces/unit_factory.h) | 解析 `UnitDefinition` 并生成 Flecs entity。[`DefaultUnitFactory`](../../../../src/models/core/default_unit_factory.h) 由 `SimulationKernel` 构造，同时提供 `set_unit_factory(...)`。 | 当前 API 以名称/Flecs 为中心。严格基线中的 capability-composition 目标属于后续收敛问题，不是“接口尚未创建”的任务。 |
| [`IEffectsModel`](../../../../src/core/interfaces/effects_model.h) | 定义 `on_proximity_hit(...)`。[`default_effects_model.cpp`](../../../../src/models/weapons/default_effects_model.cpp) 实现该接口并路由 domain consequence，同时提供 `set_effects_model(...)`。 | Naval 与 Ground domain route 有意保持有限；Ground route 只保留 placeholder/finalization 行为，不构成 ground damage runtime。 |
| [`ISensorModel`](../../../../src/core/interfaces/sensor_model.h) | 定义 `scan(...)`。[`default_sensor_model.cpp`](../../../../src/models/systems/default_sensor_model.cpp) 实现该接口并包含 Naval maritime adapter，同时提供 `set_sensor_model(...)`。 | 尚未准入 Ground sensing system/model family；新实现必须提供严格基线要求的 domain-extension 证据。 |

`UnitDefinition` 也已经存在于
[`src/content/unit_definition.h`](../../../../src/content/unit_definition.h)。
因此，后续工作必须细化或组合既有合同，不能再宣称首次引入这些接口。

## Ground System 缺口

当前 Ground 表面有意保持不完整：

- [`src/components/domains/ground/`](../../../../src/components/domains/ground/README.zh.md)
  持有 static command/tasking 字段与 placeholder combat data；
- [`src/models/domains/ground/default_effects_ground_domain.h`](../../../../src/models/domains/ground/default_effects_ground_domain.h)
  是显式 placeholder route；
- [`src/systems/combat/damage_system_ground.h`](../../../../src/systems/combat/damage_system_ground.h)
  是 no-op include/register shell，并明确不声明维护中的 Ground damage 行为；
- `src/systems/domains/ground/` 不存在。

所以，本 issue 不得把 Ground movement、sensing、fires、damage、terrain control 或
完整 land-domain tick loop 写成已实现事实。在准入任何 Ground system owner 前，
单独 work package 必须按照严格基线明确 stage coverage、components、消费和产出的
packets、read/write sets、clock 与 latency policy、facade visibility、兼容行为，
以及 parity/regression tests。

## 依赖规则

本节箭头含义统一为 `consumer -> provider`。不存在一条有效的
`core -> systems -> interfaces` 单链；这种写法混淆了 composition ownership 与
低层依赖方向。

候选模块化必须保持以下 owner 规则：

1. `components`、`runtime/contracts` 与 `content` 提供 data contract，不拥有
   per-tick behavior、facade API 或 binding。
2. `core/interfaces` 定义可替换抽象。它可以消费当前合同所需的数据类型，但不得
   依赖具体 default model 实现。
3. `models -> core/interfaces + components/content/contracts`：models 实现可替换
   behavior，不注册 ECS system，也不拥有 lifecycle。
4. `systems -> components + approved model interfaces/refs`：systems 调度 ECS
   mutation，不得依赖 external binding、training glue、`runtime/facade`，也不得把
   sibling domain 当作捷径。
5. `core/engine -> systems + core/interfaces + data contracts`：engine 拥有 world
   lifecycle 与 composition。当前它还会构造 default model；这是明确的现有耦合，
   不是 models 应归属于 engine 层的证据。
6. `runtime/facade -> core/engine + runtime/contracts`，external
   `interfaces -> runtime/facade + contracts`。外部 adapter 只转换格式，不得直接
   修改 raw ECS state，也不得成为隐藏的 runtime owner。

任何拟议移动都必须同时说明它移除了什么依赖、引入了什么新的合法依赖。只移动文件，
却不改变 owner 或 include direction，不算架构闭合。

## 候选 Work Packages

下列项目均未获授权；排序只表示前置关系，不表示承诺实施。

### 候选 A：固定既有 Composition Contracts

- 盘点三项既有接口、default 实现、kernel 构造路径、setter 和测试；
- 找出 composition edge 仍保留的 concrete-model 直接 include；
- 只有在不改变行为且能减少已测得 boundary violation 时，才提出有界的
  composition 变更。

### 候选 B：Ground System 准入设计

- 裁决首个真实 Ground runtime slice 是 movement、sensing、fires、damage 还是
  terrain；
- 定义单一 stage-local contract 及其证据，而不是先创建空的
  `src/systems/domains/ground/` 树；
- 在该 slice 通过准入门禁前，现有 no-op damage shell 与 effects placeholder
  始终显式保持 non-authoritative。

### 候选 C：过渡 Root 清理

- 分配 domain owner 前先盘点共享文件；
- 保留 domain roots 之外的 common contract；
- 只迁移已经证明具备单一 domain owner 的 behavior，并在同一授权 slice 中更新
  build、include 与 architecture tests。

### 候选 D：Capability-Composition 收敛

- 将既有 `IUnitFactory` / `UnitDefinition` 路径与严格基线中的
  `CapabilityBundle` / `spawn_platform(...)` 目标对齐；
- 修改公开表面前先定义 `spawn_unit(type_name)` 的兼容行为；
- 不把示意性目标当成已经接受的 ABI。

## 准入与停止规则

候选项只有在 work package 提供下列内容后才能提升：

- 精确文件所有权与依赖变更；
- 当前和目标 include/build graph；
- 涉及 runtime 时的 stage、packet、clock 和 facade 影响；
- 兼容与回滚行为；
- 聚焦 architecture tests 及相关 runtime/build 证据。

如果提案只是创建空目录、重命名既有接口、复制严格基线，或在缺乏跨域合同的情况下
把 domain 术语移入 shared core，则应停止。

## 非目标

- plugin marketplace 或动态加载框架；
- ECS 替换或 distributed-runtime 重设计；
- 从 DTO 或 placeholder 推导 Ground runtime 已成熟；
- 在本 issue 内重设计严格架构基线；
- 授权实现上述任何候选项。

## 相关证据

- [严格仿真系统架构基线](../../standards/simulation_system_architecture_design.zh.md)
- [架构计划索引](../../../plan/archive/owner_migration_20260808/architecture/README.zh.md)
- [Architecture owner README](../../README.zh.md)
- [Simulation architecture task owner](../../../task/simulation_architecture/archive/phase3c_closeout_20260808/README.zh.md)
- [`SimulationKernel` composition](../../../../src/core/engine/simulation_kernel.cpp)
- [Domain-separation architecture tests](../../../../tests/architecture/structural_boundaries/test_domain_separation_boundaries.py)
