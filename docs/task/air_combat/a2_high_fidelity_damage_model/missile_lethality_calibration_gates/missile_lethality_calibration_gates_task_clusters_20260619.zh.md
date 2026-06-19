# MLF-10 校准门任务簇

状态：`2026-06-19` finite task-cluster plan for
[MLF-10 校准门](README.zh.md)。

## 边界决策

MLF-10 可以盘点和门控 calibration-like evidence。它不得在 gate contract 存在并通过前
直接调 runtime damage parameters、声明真实 Pk、接纳 deterministic fuze truth，或提升
stock weapon/target lethality。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF10-P0` | main thread | n/a | 创建 MLF-10 子项目面和父级 A2 live entry。 | MLF-10 docs、父级 A2 README 文件 | Runtime code、archive registry entry、calibration claim | Markdown link check 和 `git diff --check` | README/status/dispatch/task-cluster docs 存在，父级链接可解析 | first；serial | 1 | active |
| `MLF10-P1` | read-only diagnostics worker or main thread | n/a | 盘点已有 calibration-like values、source gates、residuals 和 MLF-9 reports。 | 仅 MLF-10 inventory/current-status docs | Code edits、parameter tuning、source ingestion | cited source inventory；无断链 | 每个 artifact 分类为 engineering proxy、retained、candidate、admitted、rejected 或 blocked | after P0；可 read-only | 2 | planned |
| `MLF10-P2` | main thread | high | 定义 calibration-admission contract 和 report schema。 | MLF-10 contract docs；可选 schema tests | Runtime physics edits、public data scraping | contract inspection；如加代码则跑 focused schema tests | Contract 命名 provenance、source rights、denominator、uncertainty、independence 和 authority flags | after P1；serial | 2 | planned |
| `MLF10-P3` | implementation worker | high | 对 retained evidence manifests 和 MLF-9 reports 实现确定性 admission-audit tooling。 | `tools/diagnostics/**` 或 `tools/maintenance/**`；聚焦 tests | 修改模型参数、接纳新来源 | `py_compile`；focused pytest；fixture pass/fail-closed cases | Tool 输出稳定 audit reports，默认 fail-closed | after P2 | 2 | planned |
| `MLF10-P4` | integration worker | medium | 将 audit reports 暴露为 retained diagnostics artifacts，且不泄露 runtime authority。 | MLF-10 docs；可选 probe/report integration paths | Reward authority、entity deletion、training success claim | focused report-shape tests；link check | Report 明确标注 authority 和 non-claims | after P3 | 2 | planned |
| `MLF10-P5` | main thread | medium | 执行聚焦验证并记录 residuals。 | MLF-10 validation/status docs；若失败揭示范围内问题可改 tests | unrelated broad cleanup | focused tests；`git diff --check`；Markdown link check | Validation 记录 accepted 和 held boundaries | after P4 | 1 + 1 repair | planned |
| `MLF10-P6` | main thread | n/a | 接受 gate infrastructure、hold calibration authority 或重划范围。 | MLF-10 acceptance/archive docs；父级索引更新 | 缺 admitted evidence 时关闭真实 Pk | docs/link inspection；accepted-vs-held review | 父级索引和 archive registry 与最终结论一致 | last；serial | 1 | planned |

## 派发规则

- 每个 packet 必须对应上面一个 cluster。
- 不创建新的会话线程。
- 不修改已归档 MLF-1 到 MLF-9 证据包；除非只是修断链。
- `MLF10-P2`、`MLF10-P5`、`MLF10-P6` 保持串行。
- 如果 packet 需要接入新 source，先停止并重划范围，再抓取或接纳。

## Worker Packet 要求

每个 worker packet 必须声明：

- exact cluster id；
- allowed write set；
- 要读取的 source artifacts；
- forbidden claims；
- validation command 或 inspection checklist；
- 如果证据仍 fail-closed，需要返回的 residuals。

## 验证计划

- 对 MLF-10 docs 和父级 A2 README 文件做 Markdown link check。
- 对 MLF-10 docs 和任何触及的 tooling/tests 执行 `git diff --check`。
- 如果添加 tooling：执行 `py_compile` 和 focused pytest fixtures，覆盖 admitted、
  retained-non-authoritative、rejected、blocked 和 fail-closed evidence。

## 验收标准

- MLF-10 可以分类已有 calibration-like evidence，而不改变 runtime behavior。
- 每个 admitted 或 candidate calibration statement 都携带 source、provenance、
  denominator、uncertainty 和 authority metadata。
- Real-world Pk、deterministic fuze、weapon-specific lethality、target-specific
  lethality、reward authority 和 entity deletion 继续拒绝，除非 explicit gate 放行。

## Residual Map

| Residual | Handling |
| --- | --- |
| `RES-013` Pk boundary | 独立 Pk evidence chain 出现前保持 blocked |
| `RES-014` deterministic fuze boundary | live fuze/target-signature/reliability evidence chain 出现前保持 blocked |
| Fail-closed TP-21/BEC-O selected outputs | replacement signoff packet 通过前保持 fail-closed |
| Current runtime proxy parameters | contract 接纳更窄 claim 前，按 engineering proxies 处理 |
| MLF-9 trend outputs | 默认作为 synthetic trend input，不是真实世界 calibration |
