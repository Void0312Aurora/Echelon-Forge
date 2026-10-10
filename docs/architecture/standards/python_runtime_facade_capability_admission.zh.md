# Python RuntimeFacade 能力准入

`RuntimeFacadeAdapterCapabilities` 是维护中的 Python world-batch adapter 使用的唯一
能力快照。facade 对象发生替换时会重新计算快照，因此测试和 provider 替换仍然是显式
行为，也不会探测旧式 fallback。

## 能力分类

必需生产 ABI 包含维护中的窗口、观测请求/导出、TaskOrder、LeaderIntent、PilotReport、
发射、Mission、CommandLink 以及相应的批量读写 binding。缺少必需字段时会通过
`capabilities.missing_required` 暴露；需要该字段的操作会在 dispatch 前抛出
`RuntimeError`。

`get_unit_messages_batch` 是可选的通信查询族。缺少它时不会静默替代；请求该查询会
经过同一显式能力门并封闭失败。不会探测兼容写入器或 raw runtime fallback。

`RuntimeWindowEvidence` 的 `uses_compat_fallback` 字段在维护路径中继续保持稳定的
false 值。它属于证据 schema 数据，不会把缺少 binding 的情况转换成有效结果。

## TaskOrder 读取契约

`get_task_orders_maintained_batch` 必须有维护中的 binding。缺少方法时会返回说明缺少
能力的错误；方法存在但没有合同则返回合法空列表。调用方和证据消费者可以区分这两种
结果。
