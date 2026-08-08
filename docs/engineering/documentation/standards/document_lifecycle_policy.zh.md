# 文档生命周期规范

语言：
- 英文规范页：[document_lifecycle_policy.md](document_lifecycle_policy.md)
- 中文配套页：`document_lifecycle_policy.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/standards/document_lifecycle_policy.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-08`

状态：`2026-08-08`，仓库文档分类、维护、审阅、生成和归档的权威规范。

## 目的

本规范要求每一份维护文档同时具有一个内容类型和一个生命周期状态，避免把当前
权威、历史记录、生成输出、配置输入和保留证据混放在同一导航面而不说明边界。

`maintained` 与 `archived` 是生命周期状态，不是与 reference、howto、review
并列的目录类型。因此，一份 reference 可以同时是 `kind: reference` 和
`lifecycle: maintained`，以后也可以改为 `lifecycle: archived`，而无需被误归为
另一种文档。

本规范治理 Git 跟踪的仓库文档。ignored、私有或仅本地工作区不属于发布面，除非
经过明确准入后进入跟踪树。

## 分类模型

### 文档类型

| Kind | 用途 | 通常位置 | 权威边界 |
| --- | --- | --- | --- |
| `standard` | 稳定术语、所有权、治理规则和强制约束 | 内容 owner 的 `standards/` 子树 | 在声明范围内具有规范性；不能覆盖当前代码或可执行证据所证明的实现事实。 |
| `plan` | 有界架构方向、顺序、迁移和验收设计 | 内容 owner 的 `work/issues/` 子树；全项目计划进入 `docs/project/` | 只授权明确冻结或显式 active 的范围。 |
| `task` | 当前实现工作、状态、残余和验收包 | 内容 owner 的 `work/active/` 子树 | 拥有范围化执行状态；不能重定义由适用 standards owner 拥有的跨项目术语。 |
| `reference` | 经核验的当前结构、API、能力或清单说明 | owner 的 `reference/` 子树或组件 README | 只对最后核验状态具有描述权威。 |
| `howto` | 可复现的操作员或维护者流程 | `docs/operations/howto/` 或 owner 本地 how-to 表面 | 只对注明的平台、前置条件和已核验命令路径有效。 |
| `review` | 独立发现、风险评估、验收决定或否决 | 内容 owner 的 `reviews/` 子树 | 记录判断；行动项必须转入 `work/active/` 或 `work/issues/`，review 本身不实现变更。 |
| `evidence` | 不可变的输入、测量、清单、图表或验收证明 | 紧邻 owner-local active work 或 review 的 `evidence/` 包 | 只支撑有界 claim；不是当前行为或政策权威。 |
| `generated` | 由明确的 tracked 输入可复现生成的输出 | owner-local `generated/` 目录 | 不可手工成为规范；producer 和输入才是权威。 |
| `config-index` | canonical scenario 或配置输入的人类可读索引 | 所属 reference 或配置表面 | 指向配置真值，不得复制 payload。 |

已退役的 `docs/standards/` 根不得重建。剩余 `docs/plan/` 与 `docs/task/`
路径只是归档容器：其每个 tracked 路径都必须含 `archive` 组件。新的维护工作
必须进入内容 owner 的 `standards/`、`reference/`、`work/active/`、
`work/issues/` 或 `reviews/` 表面。

### 生命周期状态

| Lifecycle | 含义 | 允许用途 |
| --- | --- | --- |
| `draft` | 范围或内容尚未验收。 | 仅用于讨论和审阅；不是实现权威。 |
| `maintained` | 当前有效并由 owner 有意维护。 | 声明范围的默认当前入口。 |
| `accepted` | 有界结果或审阅决定已通过 gate。 | 稳定证据或收口记录；新增范围需要新 task 或 plan。 |
| `superseded` | 已由明确命名的当前文档替代。 | 物理归档前的过渡历史。 |
| `archived` | 历史材料，默认不再是当前权威。 | 只用于 provenance 和路线历史。 |

目录存在不等于生命周期声明。局部 README 必须指出当前入口，每一份 superseded
文档必须指明替代者。

## 必需元数据

新文档和被实质重写的维护文档必须在标题和语言块后放置以下内容：

```text
Document kind: `<kind>`
Lifecycle: `<lifecycle>`
Canonical: `<仓库相对路径或 self>`
Owner: `<组件、领域或治理表面>`
Last verified: `<YYYY-MM-DD>` 或 `not established`
```

额外要求：

- `not established` 只允许用于事实基线未重新核验的迁移旧材料或 draft work；
  必须附带醒目的 content status，而且在 owner 给出带日期的核验边界前，不得提升为
  `accepted`、`reference` 或 `standard`；

- `plan` 与 `task`：范围、非目标、验收证据和残余；
- `reference`：实现来源和核验边界；
- `howto`：前置条件、平台假设、命令和预期结果；
- `review`：被审版本、审阅独立性、发现和结论；
- `evidence`：claim 边界、manifest、provenance 和保留理由；
- `generated`：生成命令、tracked 输入和禁止手改标记；
- `config-index`：canonical config/scenario 路径和生命周期类别。

旧文档不需要一次性进行全仓元数据重写。旧文档被提升、移动或实质修改时，必须在
同一变更中完成合规迁移。

## 最低内容契约

只有元数据并不足以构成合规文档。每种维护表面必须显式包含下列信息；标题名称
可以调整，但不能省略，也不能用指向无关流水账的链接替代。

| 表面 | 必需内容 |
| --- | --- |
| Owner README | owner 负责什么、不负责什么、当前权威入口、临时旧路由、维护触发条件。 |
| Standard | 规范范围、术语定义、强制与禁止行为、合规证据、变更流程。 |
| Plan 或 `work/issues` 页面 | 目标、证据基线、范围与非目标、拟议决策或顺序、验收证据、残余或下次评审触发条件。 |
| Task 或 `work/active` 页面 | 已授权结果、当前状态、负责表面、验证命令/证据、阻塞项、关闭条件。 |
| Reference | 实现/配置事实源、最后核验边界、当前支持行为、已知限制、更新触发条件。 |
| How-to | 预期结果、前置条件、准确步骤、可观察成功结果、适用时的回滚或恢复路径。 |
| Review | 被审 revision/日期、检查证据、发现与严重度、结论或决策状态、权威边界、后续 owner。 |

[文档编写实例](../structure_examples.zh.md)展示合规形状，
但不会建立第二套规范权威。

## README 边界

维护中的 README 是索引，不是只增不减的项目流水账。它只应包含：

1. 当前目的和生命周期；
2. 当前权威入口；
3. 当前状态和已接受能力边界；
4. 开放残余或明确 held 的工作；
5. 指向 review、evidence 和 archive 索引的链接。

已完成工作包的叙述应进入局部 `archive/README.md` 或有界验收记录。新建或实质
重写的维护 README 应不超过 200 行；超过 300 行时必须提供 `Size exception`，
说明拆分索引为何会造成实际损害。

不要在根 README、`docs/README`、领域 README 和任务包中重复复制同一状态叙述。
最窄的维护 owner 保存细节，上级索引只提供单行路由和成熟度边界。

把任务材料提升或抽取到 standards 时，不得扩大任务范围、验收状态、时间表或
authority。具体任务状态仍由当前任务 owner 的维护文档所有。

## 命名与位置

- 稳定维护文档使用不带日期的 `lower_snake_case.md`。
- 带日期快照使用 `<topic>_<YYYYMMDD>.md`。
- Review 使用 `<scope>_review_<YYYYMMDD>.md`，除非稳定局部 README 拥有该系列。
- Evidence 包使用 `evidence/<topic>_<YYYYMMDD>/`，包含 `README.md` 和
  `manifest.json`。
- `README.md` 只用于目录导航。
- 新归档目录统一使用小写 `archive/`。
- 禁止新增 `Archive/`、`archive/archive/` 或重复生命周期目录。既有遗留路径只在
  经过独立审阅且链接安全的迭代中迁移。

## 双语规则

英文 `.md` 为 canonical，中文 `.zh.md` 为 companion。详细翻译流程仍由
[双语文档政策](bilingual_documentation_policy.zh.md)规定。

以下表面必须有中文 companion：

- 根与主要目录导航 README；
- standards 和 governance 权威；
- 稳定 plan 权威；
- 维护中的 reference 和操作 how-to；
- 被提升为当前入口的 task/domain README。

高频变化的带日期 task、review、evidence 说明和 generated 输出可以只保留英文，
除非局部 README 将其提升到严格双语面。强制配对必须在同一迭代更新。配对发生
分歧时仍以英文为 canonical，但在中文 companion 对齐前不得声明双语收口。

登记哈希只能刷新本轮审阅范围内已经完成对齐的文档对。全量重写登记表本身不能
证明无关的历史分歧已经得到审阅。当前登记表以 `docs/` 为根；在仓库根 README
文档对被纳入机器可读登记前，对它的修改必须直接进行双语审阅。

## 链接规则

- 仓库内 tracked 目标使用相对 Markdown 链接。
- 目标为文档目录时，明确链接到 `README.md`。
- 禁止发布盘符路径或 `/home/...` 等工作站路径。
- 维护文档不得把 ignored、私有或不存在的文件伪装成 tracked artifact 链接。
- 若 artifact 有意保存在外部或已不再保留，应使用代码格式路径并说明 retention
  边界，而不是创建失效 Markdown 链接。
- 英文页默认链接英文 canonical；中文入口在 companion 存在时应链接中文页。
- 维护入口中的失效链接会阻断发布。archive 中的链接缺陷通常为 warning，除非它
  遮蔽当前替代入口或 evidence manifest。

## Evidence 规则

只有在 evidence 支撑明确 claim、验收 gate、可复现边界或权利/provenance 义务时
才保留。Evidence 包必须包含：

- 简短 README，说明支撑的 claim 和明确非 claim；
- 机器可读 manifest；
- 创建日期和 producer；
- 可行时记录输入身份与哈希；
- 可行时记录输出身份与哈希；
- 保留理由和许可/权利边界；
- 消费该证据的 task、review 或 standard。

Evidence 在验收后不可变。修正时创建新包，并把旧包标为 superseded 或 archived。
不得仅因证据陈旧而删除；当小型 manifest 和精选输出足以证明同一有界 claim 时，
也不得继续保留整个实验目录。

## Generated 文档规则

Generated 文档必须以可见说明开头：

```text
Generated by: <仓库相对工具和命令>
Inputs: <tracked 路径或 manifest>
Do not edit manually.
```

Generated 输出必须能在干净工作区重建。无法重建但因 claim 需要保留的结果，应归为
evidence。Generated 摘要可以帮助导航，但不能替代维护 README、standard、review
结论或验收决定。

## 配置规则

Canonical 配置 payload 不进入 `docs/`：

- scenario 保持在 `scenarios/`；
- 训练和 runtime 配置保持在 `examples/config/` 或对应维护配置表面；
- frozen 与 archived 输入由配置系统保留其声明的生命周期。

如果机器可读的文档维护注册表只由文档工具消费，它可以与所属 owner 的 reference
材料放在一起；这种文件属于治理索引，不是 runtime 配置 payload。

文档可以提供 `config-index`，链接这些文件并说明用途、生命周期、兼容边界和验证
命令。禁止把完整 JSON payload 粘贴进 Markdown，也不得在 review 或 task 包中维护
第二份可编辑配置副本。

## Review 与 Archive 生命周期

Review 必须标识它检查的准确 revision 或 diff，在该迭代中与实现作者保持独立，并按
行为风险而非文风偏好分类问题。行动项被转移或关闭后，review 变为 `accepted` 或
`archived`，不得继续表现为 active 实现队列。

文档只有满足以下条件才能进入 `archive/`：

1. 已存在维护中的替代文档或父 README；
2. 维护者仍需要的当前事实已提升到替代文档；
3. 维护入口链接已更新；
4. provenance 和 evidence 消费者已核查；
5. archive 索引记录了理由和日期。

Archived 文件除链接修复、许可/权利修正或显式 erratum 外不可变。不得向 archived
任务包追加新工作。

## 执行与迁移

每个文档迭代至少运行：

```bash
git diff --check
python tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
```

维护中的链接/文档 gate 建立后还必须运行该 gate。迁移采用渐进顺序：先建立合规
入口和替代者，再修复链接，最后移动或删除冗余材料。大规模路径迁移、archive
折叠、evidence 删除或双语重写必须分别进入独立审阅迭代。

全仓精简顺序仍记录在迁移期遗留的
仓库精简与整合路线图 (`git show 3dc34673:docs/plan/archive/repository_consolidation_completed_20260729/README.zh.md`)。

## 相关文档

- [Agent 文档权威索引](../../automation/rules/document_authority_map.zh.md)
- [双语文档政策](bilingual_documentation_policy.zh.md)
- [标准维护政策](standards_maintenance_policy.zh.md)
- [子项目创建标准](../../automation/rules/subproject_creation_standard.zh.md)
- 仓库精简与整合路线图 (`git show 3dc34673:docs/plan/archive/repository_consolidation_completed_20260729/README.zh.md`)
