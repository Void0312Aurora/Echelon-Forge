# ADR：兵力包与群组组合

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
