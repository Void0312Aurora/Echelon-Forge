# MLF-10 当前状态

状态：`2026-06-19` active P0 boundary surface。MLF-10 已作为 MLF-9 之后的
calibration-gate follow-on 打开，但目前没有任何 calibration authority 被验收。

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

- P0 不调 runtime 参数。
- 不声明当前工程代理值是真实 AIM-120C/F-16C/MQ-9 truth。
- 没有 source-rights 和 provenance review 前，不接纳 public-output data。
- 不回写已归档 MLF 包；除非只是修断链。

## 下一 Packet

执行 `MLF10-P1` inventory。第一个有用输出是一张表，把每个 calibration-like value 或
artifact 分类为：

- `engineering_proxy`
- `retained_non_authoritative`
- `calibration_candidate`
- `admitted`
- `rejected`
- `blocked`

在这张 inventory 写出来之前，不应启动代码实现。
