# 文档结构实例

语言：英文为规范页；[中文配套](structure_examples.md)。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/structure_examples.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-07`

这些实例定义可复用的文档形态，不为内容 owner 提供技术事实、验收或规范权威。
必须用已核验内容替换全部占位符；不适用的可选节可以删除，但不得为填满骨架而
虚构证据。

## Owner 目录形态

只有存在维护内容时才创建子目录：

```text
<owner>/
  README.md
  README.zh.md
  standards/                 # 由 owner 接受的规范规则
  reference/                 # 已核验的当前事实
  work/
    active/<work-package>/   # 已授权实现及验收状态
    issues/                  # 未接受的问题、路线图和提案
  reviews/                   # 有界判断与评审快照
```

嵌套 owner 使用同一形态。例如
`systems/physics/work/issues/physics_engine_roadmap.md` 是 physics system
拥有的 draft plan；其路径不会把路线图变成已授权任务。

## 1. Owner README

```markdown
# <Owner 名称>

语言：英文为规范页；[中文配套](README.zh.md)。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/<owner>/README.md`
Owner: `<owner>`
Last verified: `<YYYY-MM-DD>`

<用一段话定义该 owner 拥有什么，并明确排除什么。>

## 当前权威

- [<standard 或 reference>](<path>)：<权威边界>。

## 活跃工作

- [<工作包>](<path>)：<当前状态与验收边界>。

## 开放问题

- [<issue>](<path>)：<尚未授权或验收的原因>。
```

不得把已完成工作历史持续追加到 README；这里只保留当前路由和单行成熟度边界。

## 2. Standard

```markdown
# <主题>标准

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/<owner>/standards/<topic>.md`
Owner: `<owner>`
Last verified: `<YYYY-MM-DD>`

## 范围
<明确 producer、consumer 和排除表面。>

## 规范规则
- `<producer>` 必须 <义务>。
- `<consumer>` 不得 <禁止行为>。

## 核验
- `<测试或评审门禁>` 核验 <规则>。

## 例外与变更触发
<允许的例外、冲突解决方式和必须重新评审的事件。>
```

缺少规范规则和核验方式的建议、路线图或 example 集合仍是 plan 或 reference，
不是 standard。

## 3. Reference

```markdown
# <主题>参考

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/<owner>/reference/<topic>.md`
Owner: `<owner>`
Last verified: `<YYYY-MM-DD>`

## 核验边界
<已检查的 revision、代码/配置来源、平台和命令。>

## 当前状态
<只记录已核验事实。>

## 局限
<未知项、不支持场景和未核验事实。>

## 重新核验触发
<会使本页过期的变更。>
```

## 4. 活跃工作包

```markdown
# <工作包>

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/<owner>/work/active/<package>/README.md`
Owner: `<owner>`
Last verified: `<YYYY-MM-DD>`

## 目标
<一个有界结果。>

## 范围与非目标
<纳入和明确排除的工作。>

## 验收证据
- `<命令、测试或评审>`：`<要求结果>`。

## 当前状态
<Planned、active、mergeable、blocked 或带证据的 closed。>

## 残余
<未解决事项及其 owner。>
```

## 5. Issue 或路线图

```markdown
# <Issue 或路线图>

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/<owner>/work/issues/<topic>.md`
Owner: `<owner>`
Last verified: `not established`
Content status: 未核验 draft；提升前必须提供带日期的证据基线。

## 问题与证据
<已观察缺口和有界证据。>

## 候选方向
<候选方案；不得表述为已实现行为。>

## 提升门
<开始 active work 前所需的决策、证据和 owner 批准。>

## 非目标
<本 issue 未授权的相邻工作。>
```

第二阶段迁移的路线图使用该结构。`work/issues` 明确表示目录位置不会授权实现。

## 6. Review 快照

```markdown
# <范围>评审 — <YYYY-MM-DD>

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/<owner>/reviews/<scope>_review_<YYYYMMDD>.md`
Owner: `<owner>/reviews`
Last verified: `<YYYY-MM-DD>`
Review basis: `<revision 与日期>`

## 范围与独立性
<被审 revision、证据集、reviewer 角色和局限。>

## 发现
<由证据支撑的发现。>

## 结论
<在评审范围内 accepted、rejected、advisory 或 blocked。>

## 后续路由
<指向 owner 本地 issue 或 active work；review 本身不执行实现。>
```

带日期 review 始终是快照；移动到 owner 本地 `reviews/` 不会使其历史指标变成当前事实。
