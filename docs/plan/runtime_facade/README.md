# `runtime_facade/`

本目录存放 runtime facade 主线的契约、执行记录与后续清理计划。

推荐阅读顺序：

1. [runtime_facade_contract_plan.zh.md](runtime_facade_contract_plan.zh.md)
2. [runtime_facade_task_bootstrap_plan.zh.md](runtime_facade_task_bootstrap_plan.zh.md)
3. [runtime_facade_layering_cleanup_freeze.zh.md](runtime_facade_layering_cleanup_freeze.zh.md)

使用规则：

- 契约文档定义边界，但不是自动生效的执行冻结单。
- `task_bootstrap` 现为第一批 `WP1-WP6` 执行记录。
- 后续实现若继续沿 runtime facade 主线推进，应以新的冻结任务单收口范围。
