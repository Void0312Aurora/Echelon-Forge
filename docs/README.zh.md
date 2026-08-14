# 文档索引

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/README.md`
Owner: `project documentation`
Last verified: `2026-08-12`

`docs/` 按内容所有权组织。文档类型在所属区域内表达；退役是生命周期终点，记录在
台账里，而不是以 archive 目录形式留在树内与当前权威竞争。

## 目标所有权根

| 区域 | 所有权 | 迁移状态 |
| --- | --- | --- |
| [project](project/README.zh.md) | 目标、成熟度、全局状态、路线图、项目决策 | 已启用；拥有迁移计划 |
| [architecture](architecture/README.zh.md) | 跨领域架构、runtime、contracts、后端、ADR | Standards、reference、reviews 与开放架构工作均已 owner-local 化 |
| [domains](domains/README.zh.md) | Air、Naval、Ground、Joint | Joint/service-profile、Air、Ground、Naval 标准均已路由到 owner |
| [systems](systems/README.zh.md) | Environment、physics、sensing、command/tasking、weapons、effects | Environment、command/tasking、effects、weapons 与 realism 路由均已 owner-local 化 |
| [learning](learning/README.zh.md) | RL、模型、训练、评估协议、实验 | Standards、active work、issues 与保留 reviews 均已 owner-local 化 |
| [operations](operations/README.zh.md) | How-to、当前 reference、可视化和集成操作 | Scenario、manual 与 visualization 路由已迁移 |
| [engineering](engineering/README.zh.md) | 贡献、构建、测试、工具、文档治理、自动化、发布 | Documentation、automation、release 与 testing 路由均已 owner-local 化 |
| [research](research/README.zh.md) | 问题、方法、结果、出版物、外部来源 | Source index 与 public-data admission standard 已迁移 |

[文档信息架构](project/documentation_architecture.zh.md)定义目标边界、迁移阶段和
切换门禁。

## 已退役的遗留容器

所有维护中的 `standards`、`plan` 与 `task` 源均已路由到内容 owner。当前分布式
权威映射见[文档对齐映射](engineering/documentation/reference/document_alignment_map.zh.md)。

`Archive/`、`evaluation/`、`manual/`、`plan/` 与 `task/` 容器只承担历史存储，已于
2026-08-13 退役。Git 历史即归档：每个被退役文件都列在
[退役文档台账](archive_ledger.md) 中，并附可继续取回内容的
`git show <commit>:<path>` 地址；机器可读形式为
`engineering/documentation/reference/retired_documents.json`。同批退役的 owner
本地归档列在[退役 systems 归档台账](systems/archive_ledger.md)。

不得在 `docs/` 下重新引入 `archive/`、`Archive/` 或 `temp/` 路径组件；一旦出现，
`tests/architecture/governance/test_archive_retirement.py` 会让构建失败。退役文档的
方式是删除文件并补一行台账；仍然有效的内容应改为路由到其 owner。

## 直接操作入口

- [引擎能力](operations/reference/engine_capabilities.zh.md)
- [代码层地图](operations/reference/src_layer_map.zh.md)
- [物理引擎清单](operations/reference/physics_engine_inventory.zh.md)
- [可视化指南](operations/howto/visualization_guide.zh.md)
- [自动化与 Agent 指引](engineering/automation/README.zh.md)
- [文档工程与实例](engineering/documentation/README.zh.md)
- [发布与依赖治理](engineering/release/README.zh.md)
- [测试工程](engineering/testing/README.zh.md)
- [保留制品来源](reference_artifacts.zh.md)
- [退役文档台账](archive_ledger.md)
- [测试系统入口](../tests/README.zh.md)

## 权威规则

1. 当前用户指令、代码、配置、场景、测试和 contracts 高于过期文字。
2. 维护 owner README 路由当前权威；dated packet 默认只是支撑证据。
3. 目录存在不等于能力已经成立。
4. plan、task、review、reference、standard 迁移后仍保留原文档类型；目录 owner
   不会扩大其证据边界。
5. 保留即退役：被取代的文档直接删除并登记到归档台账，不再以 `archive/` 路径
   留存。树内已没有需要审计的归档目录，旧 `docs/Archive/` 曾经阻挡
   `docs/archive/` 终点的大小写冲突也随之消失。

## 语言与权利

稳定入口、导航 README、standards、reference 和 how-to 采用英文规范页与中文
companion。work/evidence 面（`docs/**/work/**`）只维护英文规范版；仅当文档被明确
提升进入严格双语面时才增设中文 companion，因此中文导航页可以直接链接英文
work 文档。既有归档按冻结时的语言布局保持不动。仓库文档默认采用 Apache-2.0；
第三方来源另有声明时从其权利边界。参见 [LICENSE](../LICENSE) 和
[THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md)。
