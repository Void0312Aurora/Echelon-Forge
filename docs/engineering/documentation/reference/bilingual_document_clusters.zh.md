# 双语文档簇

语言版本：

- 英文主文：[bilingual_document_clusters.md](bilingual_document_clusters.md)
- 中文辅文：`bilingual_document_clusters.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/reference/bilingual_document_clusters.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-12`

状态：`2026-08-12`，双语同步机器可读注册表的参考说明。

本文档定义一个轻量的 cluster 记录，用于判断配对的 `name.md` / `name.zh.md`
是否仍然同步。

## 核验边界

- Canonical 注册表数据：
  [bilingual_document_clusters.json](bilingual_document_clusters.json)
- Producer 与 auditor：
  [tools/maintenance/translate_docs_batch.py](../../../../tools/maintenance/translate_docs_batch.py)
- 已核验范围：截至 `2026-08-12`，由共享文档范围规则选出的严格双语维护面。
- 注册表核验路径成员关系和相对基线的文件哈希；它不能证明两种语言在语义上等价。

归档规则：

- `docs/Archive/` 以及 `docs/**/archive/` 下的本地归档子树，默认不纳入维护中的双语簇审计。
- work 面（路径含 `work` 目录组件）属于 Tier B 英文单语面，不进入严格注册表
  范围，即使外层 owner 前缀（如 `docs/operations/`）本身属于严格面。
- `docs/plan/architecture/review/` 下的本地架构审查草稿，也默认不纳入维护中的双语簇审计。
- 归档镜像即使保留双语文件，也只用于追溯，不参与活跃漂移判定。
- 默认注册表范围是“严格维护的双语表面”，而不是整棵共享文档树；只有在明确要盘点更宽范围时，才应使用工具的 full-tree 覆盖。

## 簇记录内容

每个双语配对使用由英文 canonical 路径去掉 `.md` 后得到的 `pair_id` 跟踪。
canonical 路径稳定时，该标识符保持稳定；移动文档对会改变 `pair_id`，必须在同一
变更中删除旧记录并登记新记录。

每条记录存放：

- `pair_id`
- `english`
- `chinese`
- `source_of_truth`
- `last_verified`
- `english_hash`
- `chinese_hash`

当前同步状态由注册表基线与当前文件 hash 共同计算。

## 同步状态

- `synced`
- `needs-en-update`
- `needs-zh-update`
- `diverged`
- `missing-en`
- `missing-zh`

## 更新与重新核验触发条件

当一批翻译落地时，应同时刷新受影响的 pair 记录，让注册表基线跟着同步前进。

有界审阅应使用可重复的 `clusters --write --pair <pair_id>` 参数。未选择记录的
哈希和 `last_verified` 必须保持不变。全量重写通常只用于整个维护面的双语审阅。
canonical 路径或注册表路径迁移也可能需要通过全量重写删除失效标识符，但必须审计
结果 diff，确认无关文档对的记录没有漂移。

如果之后有人手工只改了一侧，审计命令就应该能立刻指出哪一侧已经落后。

## 限制与解释规则

- `audit` 的结果是“相对当前注册表基线”的判断，不是语义真相本身。
- 归档树默认不在判定面内；如果审计里出现 archive，通常意味着使用了显式包含覆盖，或者扫描规则还没刷新到最新口径。
- 如果有界文档整理后注册表基线已经过期，应先人工审阅变更文档对并只刷新这些
  记录，再判断报告出来的差异到底是真漂移，还是正常的后续维护。
- `needs-en-update` / `needs-zh-update` 通常意味着单侧维护滞后。
- `diverged` 表示两侧都相对记录基线发生了变化，应先结合最新意图人工确认，再把它定性为真实漂移。

## 工具

- [簇写入工具](../../../../tools/maintenance/translate_docs_batch.py)：`clusters`
- [注册表审计工具](../../../../tools/maintenance/translate_docs_batch.py)：`audit`
