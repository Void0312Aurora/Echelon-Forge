# 双语文档簇

语言版本：

- 英文主文：[governance/bilingual_document_clusters.md](bilingual_document_clusters.md)
- 中文辅文：`bilingual_document_clusters.zh.md`

状态：`2026-05-18` 双语同步的机器可读注册表。

本文档定义一个轻量的 cluster 记录，用于判断配对的 `name.md` / `name.zh.md`
是否仍然同步。

归档规则：

- `docs/Archive/` 以及 `docs/**/archive/` 下的本地归档子树，默认不纳入维护中的双语簇审计。
- 归档镜像即使保留双语文件，也只用于追溯，不参与活跃漂移判定。

## 簇记录内容

每个双语配对使用稳定的 `pair_id` 跟踪，`pair_id` 由英文 canonical 路径去掉
`.md` 后得到。

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

## 更新规则

当一批翻译落地时，应同时刷新受影响的 pair 记录，让注册表基线跟着同步前进。

如果之后有人手工只改了一侧，审计命令就应该能立刻指出哪一侧已经落后。

## 解释规则

- `audit` 的结果是“相对当前注册表基线”的判断，不是语义真相本身。
- 归档树默认不在判定面内；如果审计里出现 archive，通常意味着使用了显式包含覆盖，或者扫描规则还没刷新到最新口径。
- 如果做过大批量文档改动，而注册表基线已经过期，应先重新运行
  `clusters --write`，再判断报告出来的差异到底是真漂移，还是正常的后续维护。
- `needs-en-update` / `needs-zh-update` 通常意味着单侧维护滞后。
- `diverged` 表示两侧都相对记录基线发生了变化，应先结合最新意图人工确认，再把它定性为真实漂移。

## 工具

- `tools/maintenance/translate_docs_batch.py clusters`
- `tools/maintenance/translate_docs_batch.py audit`
