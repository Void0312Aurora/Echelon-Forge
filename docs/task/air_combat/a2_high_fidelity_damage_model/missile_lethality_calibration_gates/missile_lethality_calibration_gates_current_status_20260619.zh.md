# MLF-10 当前状态

状态：`2026-06-19` P0-P6 complete。Gate infrastructure 已 accepted / retained；
没有任何 calibration authority 被验收。

## 决策

已有 A2/MLF 工作包含看起来像校准的工程代理值和 retained source-admission artifacts。
MLF-10 把这些当作 audit inputs，而不是当作已经释放的真实世界校准。

## 当前证据图

| Evidence | Current reading | MLF-10 handling |
| --- | --- | --- |
| MLF-6 近场结构阈值和累计翼损行为 | 有测试和 diagnostics 的 engineering proxy | 作为 model-calibration candidate input 盘点；gate 前不提升 |
| MLF-7 平台后果 | 来自 accepted breakup facts 的有边界后果投影 | 作为 chain outcome evidence 盘点；不释放 Pk 或具体目标真值 |
| MLF-8 lifecycle facts | diagnostics-only detached-part 和 terminal-wreck lifecycle evidence | 作为 terminal outcome labels 盘点；不释放 debris physics calibration |
| MLF-9 statistical trends | 基于显式 rows 的确定性 synthetic trend reports | 只能作为 candidate report input；real-world Pk 继续拒绝 |
| A2 residual register `RES-013/014` | Pk 和 deterministic-fuze 边界 deferred | 除非存在独立证据链，否则保持 blocker |
| A2 source-admission packets | mixed retained pass/fail-closed gates | 必须显式读取 gate state；fail-closed 保持 fail-closed |

## 当前边界

- 在 contract 接纳更窄 claim 前不调 runtime 参数。
- 不声明当前工程代理值是真实 AIM-120C/F-16C/MQ-9 truth。
- 没有 source-rights 和 provenance review 前，不接纳 public-output data。
- 不回写已归档 MLF 包；除非只是修断链。

## P1 结果

[类校准证据盘点](missile_lethality_calibration_gates_inventory_20260619.zh.md)
已完成当前证据族分类。当前没有任何 evidence 被 admitted。Stage B 已具备 contract-ready
candidate 形状；Stage C、TP-21、BEC-O、Pk 和 deterministic fuze 继续 blocked。

## P2 结果

[校准准入契约](missile_lethality_calibration_admission_contract_20260619.zh.md)
已定义 evidence manifest、evidence record、逐字段 authority decision 和 retained
report schemas。Pk、deterministic fuze、reward 和 entity deletion 在 v1 中固定 blocked。

## P3/P4 结果

Audit tool 和 focused tests 已实现。Retained repository manifest 产生 7 条 decision：
1 条 engineering proxy、1 条 retained non-authoritative report、4 条 blocked
candidate/evidence、1 条 rejected source category，以及 0 条 admitted。

## P5/P6 结果

聚焦验证以 `18 passed`、确定性 report regeneration、clean diff whitespace 和零缺失本地
Markdown 链接通过。Gate infrastructure 已 accepted / retained；calibration authority
继续 held。

## 重开条件

只有在出现新 evidence、replacement signoff packet 或明确 authority-promotion request
时才重开。
