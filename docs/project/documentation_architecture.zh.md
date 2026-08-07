# 文档信息架构

语言：

- 英文规范页：[documentation_architecture.md](documentation_architecture.md)
- 中文配套页：`documentation_architecture.zh.md`

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/project/documentation_architecture.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-07`

## 目标

按照内容所有权统一维护文档。目录树不能继续在同一层混用主题领域、文档类型、
受众和生命周期。

目标维护根目录为：

1. `project/`：目标、成熟度、全局状态、路线图和项目级决策。
2. `architecture/`：跨领域架构、runtime、contracts、后端和 ADR。
3. `domains/`：`air`、`naval`、`ground`、`joint` 四个任务领域 owner。
4. `systems/`：environment、physics、sensing、command/tasking、weapons、effects。
5. `learning/`：RL、模型、训练、评估协议和实验。
6. `operations/`：操作/维护 how-to、当前 reference、可视化和集成。
7. `engineering/`：贡献、构建、测试、工具、文档治理、自动化、依赖和发布。
8. `research/`：研究问题、方法、结果、出版物和外部来源。

`archive/` 是唯一逻辑生命周期终点，不进入维护源审计。第一阶段不创建该小写
路径，因为它在 Windows 的大小写不敏感文件系统上与旧 `docs/Archive/` 冲突。
既有归档树继续冻结；解决该冲突属于单独的历史迁移，本文不授权重写归档文档。

## 域内结构

每个维护 owner 从双语 `README` 进入。只有存在维护内容时才建立以下可选表面：

- `standards/`：规范规则；
- `reference/`：已核验的当前事实；
- `work/active/`：已授权实施工作；
- `work/issues/`：未解决缺口；
- `reviews/`：当前审查与验收决定。

[文档结构实例](../engineering/documentation/structure_examples.zh.md)定义每种表面和
嵌套 owner 的可复用骨架。它们只指导形态，不为 owner 提供技术或规范内容。

文档类型和生命周期继续由显式元数据表达。任务完成后，将仍需维护的事实提升到
standard、reference 或 README；其余任务包归档，不得永久保持 active task 身份。

## 迁移阶段

- 第一阶段：建立所有权根；迁移 `manual → operations`、
  `agent → engineering/automation`、`book → research/sources`。
- 第二阶段（2026-08-07 完成）：取消维护中的 `forward`、`evaluation`、`log`
  表面，将计划和评审路由到内容 owner；既有 `evaluation/archive/` 保持冻结且不修改。
- 第三阶段（2026-08-07 启动）：按内容所有权拆分 `standards`、`plan`、`task`。
  首个切片将文档、自动化、依赖与发布治理迁入 `engineering/`；第二个切片将 Joint
  common-core README 与标准迁入 `domains/joint/`。所有剩余旧标准以及 plan/task 树
  留给后续 owner 切片。不得把旧树整体移动成新的全局桶。
- 第四阶段：切换全部维护入口并禁止继续写入旧根；只有旧根不再含维护源时才删除。

## 门禁

每一轮迁移都必须保持双语配对、通过维护链接审计、更新当前路由，并继续排除归档
源。仓库必须拒绝未登记的 docs 一级目录；大型领域迁移分别评审。

## 非目标

- 重组或重写既有归档。
- 为匹配文档路径而重命名代码领域。
- 预建空目录骨架。
- 把目录移动当作能力已验收的证据。
