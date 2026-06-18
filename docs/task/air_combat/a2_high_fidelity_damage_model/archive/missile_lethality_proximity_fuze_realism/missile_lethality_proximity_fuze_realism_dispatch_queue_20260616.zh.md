# A2 近炸引信真实性代理派发队列

状态：`2026-06-16` PF-R5 验证派发和 PF-R6 收口完成，用于
[README.zh.md](README.zh.md)。

英文辅文：
[missile_lethality_proximity_fuze_realism_dispatch_queue_20260616.md](missile_lethality_proximity_fuze_realism_dispatch_queue_20260616.md)。

## 队列

| Dispatch | Cluster | Owner | Goal | Write set | Validation | Closure |
| --- | --- | --- | --- | --- | --- | --- |
| `PF-R1` | `PF-P1` | main thread | 写公开资料机制说明，区分 admitted/rejected claims | `public_mechanism_source_note_20260616.md`；`public_mechanism_source_note_20260616.zh.md` | 来源准入检查，无参数 claim | pass as source-bound planning note |
| `PF-R2` | `PF-P2` | main thread | 写当前 runtime gap audit | `current_runtime_gap_audit_20260616.md`；`current_runtime_gap_audit_20260616.zh.md` | 只读 code/test scan，无 runtime diff | pass as gap table |
| `PF-R3` | `PF-P3` | main thread | 写 surrogate contract 和聚焦验证计划 | `proximity_fuze_surrogate_contract_20260616.md`；`proximity_fuze_surrogate_contract_20260616.zh.md` | contract inspection 和 link check | pass as implementation-ready plan |
| `PF-R4` | `PF-P4` | main thread | 实现已接受 surrogate | runtime contracts、damage system、Python bindings、diagnostics、focused tests | `ef_py` build；聚焦 runtime、diagnostics、training、binding tests | pass as focused implementation |
| `PF-R5` | `PF-P5` | main thread | 生成聚焦机制对照矩阵 | `validation/pf_r5_proximity_fuze_validation.py`；CSV/JSON/heatmap/summary | 矩阵制品和摘要 | pass_with_residuals |
| `PF-R6` | `PF-P6` | main thread | acceptance closeout | README/status/acceptance/父 A2 文档 | link check、`git diff --check`、验证摘要 | pass |

## 派发规则

- `PF-R1` 到 `PF-R3` 已完成。
- `PF-R4` 已在明确继续后完成为聚焦实现切片。
- `PF-R5` 已完成为聚焦 surrogate 验证切片；后续不能只凭本队列扩大范围。
- worker 必须报告是否触碰实现文件。`PF-R1` 到 `PF-R3` 的预期答案是 `no`。
- 任何意外 code diff 都停止队列并进入复核。

## Held 实现触发条件

`PF-R4` 是在以下条件满足后打开的：

- `PF-R1` 和 `PF-R2` pass；已于 `2026-06-16` 完成；
- `PF-R3` 命名精确字段、测试、写集和预期行为变化；已于 `2026-06-16` 完成；
- 用户明确授权继续进入实现。

`PF-R5` 只为验证 PF-R4 surrogate evidence 在触发半径、初始横向/高度偏置和机制族上的行为而打开。
它没有加入 reward 调参、Pk 声明或真实引信校准。`PF-R6` 记录收口边界，并保留 live-guidance 对称性残余。
