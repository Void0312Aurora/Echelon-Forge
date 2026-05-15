# Joint 指挥关系与建模基线

本文档定义项目中所有军种共用的最小联合层模板。

## 1. 官方现实基础

根据 Joint Chiefs 官方资料，美军联合层的共通基础不在于“所有军种使用同一条战术指挥树”，
而在于：

- 共通的 command relationship
- 共通的 authority delegation
- 共通的 reporting / status framework

项目建模时必须先把这一层独立出来。

主要官方依据：

- [Joint Chiefs Service Publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C, Joint Reporting Structure](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)

## 2. Joint 层必须统一的对象

### 2.1 Command Relationship

项目应将下列关系作为联合层共通字段，而不是军种自定义字段：

- `COCOM`
- `OPCON`
- `TACON`
- `support`
- `ADCON`
- `coordinating authority`
- `DIRLAUTH`

说明：

- 这是统一的授权语言。
- 空军、陆军、海军的差异主要体现在“谁在什么情况下持有哪些关系”，而不是词汇本身不同。

### 2.2 Task Organization

联合层只定义：

- `command_node`
- `tactical_unit`
- `platform_unit`

以及：

- `parent_node_id`
- `supported_node_id`
- `supporting_node_id`
- `authority_scope_code`
- `task_group_id`

而不直接定义：

- `element`
- `brigade`
- `task force`

这些应交由军种 profile 解释。

### 2.3 Intent / Order / Report

所有域共通的数据流建议固定为：

`Commander Intent / Task Order -> Tactical Intent -> Execution Command -> Status / Report`

联合层只定义通用接口，不定义域特定执行参数。

## 3. 关注点分离原则

### 3.1 Joint 层负责什么

- 关系与权限
- 谁向谁下任务
- 谁向谁汇报
- 哪一级是 tight-loop tactical unit

### 3.2 Joint 层不负责什么

- 跑道进近
- 航母编队站位几何
- 陆战火力支撑楔形展开
- 具体平台执行动作

这些都属于 service profile 或 platform/task layer。

## 4. 对项目的数据模型约束

如果后续要支持空、海、陆，核心结构体不应优先写：

- `wingman_slot_id`
- `recovery_runway_id`
- `task_cap`

而应优先写：

- `task_family`
- `service_profile`
- `tactical_unit_type`
- `role_code`
- `relative_slot_code`
- `coordination_mode`
- `recovery_site_id`

说明：

- `runway` 是 air profile 的 `recovery_site`
- `CAP` 是 air profile 下 `patrol` 家族的一种
- `wingman` 是 air profile 下 `subordinate role` 的一种

## 5. 对项目架构的直接结论

后续项目标准化文档与代码设计应按三层组织：

1. `joint/common core`
2. `service profile`
3. `platform/task specialization`

这比“先写 air，再希望 sea/land 也能复用”更符合真实世界，也更符合工程上的关注点分离。
