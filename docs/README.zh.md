# 文档索引

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/README.md`
Owner: `project documentation`
Last verified: `2026-08-08`

`docs/` 按内容所有权组织。文档类型在所属区域内表达；archive 是生命周期终点，
不是与当前权威竞争的内容域。

## 目标所有权根

| 区域 | 所有权 | 迁移状态 |
| --- | --- | --- |
| [project](project/README.zh.md) | 目标、成熟度、全局状态、路线图、项目决策 | 已启用；拥有迁移计划 |
| [architecture](architecture/README.zh.md) | 跨领域架构、runtime、contracts、后端、ADR | Conventions/runtime standards、reviews 与 modularization issue 已迁移；旧 plan/task 权威仍待迁移 |
| [domains](domains/README.zh.md) | Air、Naval、Ground、Joint | Joint/service-profile、Air、Ground、Naval 标准均已路由到 owner |
| [systems](systems/README.zh.md) | Environment、physics、sensing、command/tasking、weapons、effects | System issue/review 路由与 gradient-realism standard 已启用 |
| [learning](learning/README.zh.md) | RL、模型、训练、评估协议、实验 | Policy architecture standard 及 policy/training issue 路由已启用 |
| [operations](operations/README.zh.md) | How-to、当前 reference、可视化和集成操作 | Scenario、manual 与 visualization 路由已迁移 |
| [engineering](engineering/README.zh.md) | 贡献、构建、测试、工具、文档治理、自动化、发布 | Documentation alignment、automation、release 与 review 路由已迁移 |
| [research](research/README.zh.md) | 问题、方法、结果、出版物、外部来源 | Source index 与 public-data admission standard 已迁移 |

[文档信息架构](project/documentation_architecture.zh.md)定义目标边界、迁移阶段和
切换门禁。

## 当前遗留路由

迁移期间，下列旧根仍包含维护源：

- 迁移后的跨域与领域规则位于各 owner-local `standards/` 和 `reference/`
  表面；当前分布式路由见[文档对齐映射](engineering/documentation/reference/document_alignment_map.zh.md)；
- [plan](plan/README.zh.md)：活跃/冻结方向和迁移计划；
- [task](task/README.zh.md)：有界实施工作和状态。

不得新增一级类别或继续扩张这些旧根。只有识别内容 owner 与当前权威后才能移动文档。

旧 `Archive/`、`evaluation/archive/` 与 `manual/archive/` 容器属于冻结历史存储，
不是维护路由，也不进入本次迁移的追踪范围。

## 直接操作入口

- [引擎能力](operations/reference/engine_capabilities.zh.md)
- [代码层地图](operations/reference/src_layer_map.zh.md)
- [物理引擎清单](operations/reference/physics_engine_inventory.zh.md)
- [可视化指南](operations/howto/visualization_guide.zh.md)
- [自动化与 Agent 指引](engineering/automation/README.zh.md)
- [文档工程与实例](engineering/documentation/README.zh.md)
- [发布与依赖治理](engineering/release/README.zh.md)
- [保留制品来源](reference_artifacts.zh.md)
- [测试系统入口](../tests/README.zh.md)

## 权威规则

1. 当前用户指令、代码、配置、场景、测试和 contracts 高于过期文字。
2. 维护 owner README 路由当前权威；dated packet 默认只是支撑证据。
3. 目录存在不等于能力已经成立。
4. plan、task、review、reference、standard 迁移后仍保留原文档类型；目录 owner
   不会扩大其证据边界。
5. 既有归档继续冻结并排除在维护源审计之外。未来逻辑终点
   `docs/archive/` 本阶段不落盘，因为它在 Windows 上与旧 `docs/Archive/`
   发生大小写冲突；解决该历史布局属于单独迁移。

## 语言与权利

稳定入口、standards、reference 和 how-to 采用英文规范页与中文 companion。
高频 work/evidence 除非被提升，可以只维护英文。仓库文档默认采用 Apache-2.0；
第三方来源另有声明时从其权利边界。参见 [LICENSE](../LICENSE) 和
[THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md)。
