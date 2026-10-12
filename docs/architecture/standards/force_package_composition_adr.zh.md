# ADR：兵力包与群组组合

语言：
- 英文规范页：[force_package_composition_adr.md](force_package_composition_adr.md)
- 中文配套页：`force_package_composition_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/force_package_composition_adr.md`
Owner: `architecture/joint-contracts`
Last verified: `2026-10-12`

**状态：** 待评审的资格验证设计；现有 scenario expansion 与 Joint/tasking 契约仍是权威。

定义可复用、带版本的 force-package authoring 投影，描述 unit assembly、角色、包含关系、
指挥关系和布局，并编译到现有 scenario entity 与 Joint/tasking 契约。通用编译器不成为第二套
ECS、命令或领域战术权威。

成员可引用平台蓝图组装或有限的嵌套 package，展开必须形成确定性 DAG；环、重复 scoped ID、
未解析 import 及冲突 side/role 约束在创建 entity 前拒绝。成员关系、任务权威、通信连接和动态
orders 分开处理；嵌套不会自动授予命令、无线电或信息权限。Air/Naval/Ground 的编队、舰载库存
和领域几何由各自 adapter 负责。现有 CSG compiler 通过显式 adapter 保留。

资格验证应覆盖 Air 编队、Naval 群组、Ground squad、嵌套 package 及失败样例；生产启用需经过
schema/identity、native Joint/tasking admission 和领域 owner 审查。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

编译结果及身份计算已保留实例作用域内的关系，校验嵌套角色能力，并保留 frame、anchor 与 provenance 引用。资格适配器要求显式提供 entity 与 assembly 映射，校验 group/entity/inventory 元数据，并只把新鲜且完整通过资格的快照交给现有 loader。named 和 mirror 两个 S0 fixture 的 native 坐标与 replay 帧保持一致；CSG 位置、geodesy 和 native materialization 仍由原 owner 负责。命令和库存迁移仍待验收；关系记录本身不会授予指挥权限。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。
