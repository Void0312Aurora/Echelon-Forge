# 任务领域

语言：[英文规范页](README.md)；本页为中文配套。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/README.md`
Owner: `mission-domain documentation`
Last verified: `2026-08-08`

维护中的任务领域只有四个 owner：`air`、`naval`、`ground`、`joint`。
flight dynamics、sensor、weapons、learning 和 visualization 不是额外任务领域。
Joint common-core 与 service profiles，以及 Air、Ground、Naval 标准均已使用
owner-local 路由。

## 当前 Owner 路由

- Air：[owner 索引、标准与开放问题](air/README.zh.md)。
- Ground：[owner 索引与维护中标准](ground/README.zh.md)。
- Joint：[owner 索引与 common-core 标准](joint/README.zh.md)。
- Service profiles：[嵌套 owner 索引](joint/service_profiles/README.zh.md)。
- Naval：[owner 索引、标准与 reference](naval/README.zh.md)。

位于 `work/issues` 的条目只是候选项或未解决缺口，不代表已授权实施。Air backlog
中的跨 owner 条目应在其 system 或 learning owner 迁移时拆分。

每个 domain owner 的重复文档形态使用
[共享文档结构](../engineering/documentation/structure_examples.zh.md)。
