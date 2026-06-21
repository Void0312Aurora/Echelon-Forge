# 解耦阶段 facade 诊断切片

日期：`2026-06-21`

状态：本文记录的早期概念 facade 已被 runtime DTO-backed facade 取代。当前代码不再保留
load-row response 投影兜底；权威基线以
`kill_chain_runtime_facade_slice_20260621.zh.md` 和刷新后的 review packet 为准。

## 当前结论

`tools/diagnostics/kill_chain_decoupling_probe.py` 仍输出 `decoupled_facade`，但其来源已经是
runtime DTO：

- `approach_fact`：制导/接近事实。
- `fuze_decision`：引信/起爆事实。
- `warhead_load_field`：战斗部载荷和逐部件 load facts。
- `component_response`：逐部件 response rows。
- `consequence_projection`：平台后果投影。

旧的概念投影只作为历史背景，不再是运行路径。

## 当前基线

刷新后的 review packet 显示：

- `facade_status = runtime_dto_backed`
- `runtime_facade_case_count = 11`
- `component_response_row_count = 33`
- `rows_with_response_fields_on_load_row = 0`

## 边界

该 facade 用于工程诊断和单层校准准入。它不声明真实 Pk，不释放确定性引信权威，
也不直接改默认杀伤参数。
