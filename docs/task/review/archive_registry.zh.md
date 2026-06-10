# 审查归档注册表

`docs/task/review/archive/` 下已归档审查记录的注册索引。

## 归档类别

| 子目录 | 描述 |
|--------|------|
| `pre-wp/` | 前 WP 审查记录。项目早期尚未建立 WP 体系时的架构审查快照。 |
| `temp/` | 原始文档。作为审查输入的外部架构计划（temp-01、temp-02）原始文档。 |
| `wp-acceptance/` | WP 验收审查。WP0 至 WP24 及 TM01-TM06 的 canonical acceptance reviews。 |
| `wp-superseded/` | 被取代的波次/计划审查。已被后续 wave 或最终 acceptance 取代的中间审查记录。 |
| `engineering_governance_p1/` | 已闭合的 P1 治理修复切片。stale architecture guard repair、compiler shape validation、adapter capability probing convergence、diagnostics callback split。 |
| `domain_separation_split/` | 已验收的域 ownership 大拆分子项目。旧 domain-split 兼容入口已退役，Air / Naval / Ground owner header、system、model routing 与 architecture guard 已通过验收。 |

## 归档文档

| 文件 | 描述 |
|------|------|
| `domain_separation_audit_20260609` | 域分离现状审计。Air / Naval / Ground 在 components / systems / models 三层的域耦合热点分析。6 个热点全部闭合，`domains/` 结构已落地。 |
