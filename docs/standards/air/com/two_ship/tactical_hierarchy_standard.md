# 双机阶段战术层级标准 (Tactical Hierarchy Standard for Two-Ship Stage)

> ARCHIVED NOTE (2026-03-23): 该文档属于第一版 air-specific 双机标准草案，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)。

本文档定义双机阶段的**战术层级**、**控制权限**和**真实性边界**。

## 1. 现实基础

### 1.1 不把行政编制直接映射为运行时控制层

现实中的“中队 / 大队 / 旅 / 联队”首先是行政、保障、出动和资源组织单元，不等于 sortie 级的逐步战术控制层。

因此在仿真与 RL 中必须区分：

- 行政层：编制、值班、出动、补充、轮换
- 战术层：双机、四机、任务包、GCI/AWACS 指挥

双机阶段只把战术层进入运行时闭环。

### 1.2 双机是最小真实战术单元

本项目第一多机阶段采用：

- `Element = 2 aircraft`

这对应现实中最常见的最小战术协同单元：

- 1 架 lead
- 1 架 wingman

双机单元可以完成：

- scramble / departure
- join-up / rejoin
- route / cap transit
- support / mutual cover
- rtb / recover

### 1.3 四机不是“中队”，而是下一阶段的任务包内战术编组

四机阶段定义为：

- `Package = 2 Elements = 4 aircraft`

其语义是一次 mission package 内的战术编组，而不是行政意义上的“中队”。

## 2. 双机阶段运行时层级

### 2.1 层级定义

双机阶段采用以下层级：

1. `C2 / GCI / AWACS`
2. `Element Lead`
3. `Wingman`
4. `Execution Layer`

### 2.2 各层职责

#### C2 / GCI / AWACS

职责：
- 发布 sortie 级任务
- 指定 CAP / intercept / RTB / recover 目标
- 改变任务优先级和进入/退出条件

不负责：
- 直接写舵面
- 直接写终端进近细节
- 对 wingman 逐步下飞行动作

#### Element Lead

职责：
- 接收 element 级 `TaskOrder`
- 决定双机的战术姿态与阶段
- 给 wingman 分配 slot、join / rejoin、support、split / abort 指令
- 维护 element 内的队形纪律与任务推进

不负责：
- 直接输出 wingman 的杆舵
- 取代 wingman 的执行层闭环

#### Wingman

职责：
- 在 element lead 约束下执行跟随、集合、保持、展开、重组
- 必要时执行自主安全动作
- 向 lead / C2 回报失队、无法保持、油量告警等状态

不负责：
- 独立重写整个 mission thread
- 与 lead 竞争 task authority

#### Execution Layer

职责：
- 把 `MissionCommand` 变成可飞的 `PilotAction`
- 保证飞控、包线和 terminal 稳定性

## 3. 双机阶段的真实指挥权限

### 3.1 正确的权限分配

正确权限链：

`C2 -> Element Lead -> Wingman`

对应含义：
- C2 对整个双机单元下任务
- lead 对 element 内部下协同意图
- wingman 执行编队与支持动作

### 3.2 错误的权限分配

双机阶段必须避免：

- `C2 -> aircraft_1`
- `C2 -> aircraft_2`
- 两架飞机各自独立接收完整 sortie 任务线程

原因：
- 这会把双机协同退化为两个平行的单机任务
- 不符合现实中的 lead-wingman 权责结构
- 会让 RL 奖励和归因高度混乱

## 4. 运行时对象建议

双机阶段建议引入三个逻辑层对象：

### 4.1 AircraftUnit

对应单架飞机实体。

最小属性：
- `aircraft_id`
- `element_id`
- `role_id`
- `lead_aircraft_id`
- `wingman_index`

### 4.2 ElementUnit

对应一个双机战术单元。

最小属性：
- `element_id`
- `lead_aircraft_id`
- `member_aircraft_ids`
- `formation_template_id`
- `element_task_id`

### 4.3 PackageUnit

四机阶段才进入运行时。

双机阶段只要求预留标识，不要求激活完整控制器。

## 5. 双机阶段与四机阶段的关系

### 5.1 双机阶段

运行时主对象：
- `ElementUnit`

控制链：
- `C2 -> Element Lead -> Wingman`

### 5.2 四机阶段

运行时主对象：
- `PackageUnit`
- `ElementUnit`

控制链：
- `C2 -> Package Lead -> Element Lead -> Wingman`

因此，四机阶段不是简单“把双机复制两份”，而是必须增加一个新的 package lead 层。

## 6. 本阶段的标准结论

双机阶段采用如下强制约束：

- 最小战术单元是 `2 aircraft element`
- 运行时任务接收者优先是 `element`，不是单机
- wingman 不独立承担完整 sortie task authority
- 四机编组保留为下一阶段的 `package`
- 行政编制暂不进入运行时控制链
