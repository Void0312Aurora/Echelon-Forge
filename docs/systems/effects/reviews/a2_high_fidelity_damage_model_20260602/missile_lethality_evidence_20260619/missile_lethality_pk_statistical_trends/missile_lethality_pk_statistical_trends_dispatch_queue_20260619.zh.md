# MLF-9 Pk / 统计趋势派发队列

状态：`2026-06-19` queue closed，对应 accepted / archived 的
[MLF-9 Pk / 统计趋势](README.zh.md) 切片。`MLF9-Q0` 到 `MLF9-Q6` 均已完成。

## 队列

| Item | Cluster | Owner | Write set | Timing | Required return |
| --- | --- | --- | --- | --- | --- |
| `MLF9-Q0` | `MLF9-P0` | main thread | MLF-9 docs 和父级 A2 README 文件 | Now | 子项目存在，父级链接存在，docs diff check 结果 |
| `MLF9-Q1` | `MLF9-P1` | main thread or read-only diagnostics worker | 仅 MLF-9 inventory/status docs | After Q0 | accepted upstream fields、missing joins、safe implementation write sets |
| `MLF9-Q2` | `MLF9-P2` | main thread | MLF-9 contract docs，可选 schema tests | After Q1 | 包含 row shape、denominator、buckets、uncertainty、non-claims 的 metric contract |
| `MLF9-Q3` | `MLF9-P3` | implementation worker | diagnostics/replay tooling 和聚焦测试 | After Q2 | deterministic fixture reports 和 focused validation |
| `MLF9-Q4` | `MLF9-P4` | integration worker | report artifacts、probe/docs integration | After Q3 | report exposure 且无 reward/training/calibration leakage |
| `MLF9-Q5` | `MLF9-P5` | main thread | validation/status docs；必要时 scoped tests | After Q4 | focused 和 smoke validation outcomes |
| `MLF9-Q6` | `MLF9-P6` | main thread | MLF-9 closeout docs 和父级索引 | After Q5 | accepted/held decision、residual map、archive/index sync |

## 当前 Packet

当前 accepted simulation-trend/report 切片没有剩余 active packet。证据包已移动到父级
A2 本地 archive，旧 active 路径是兼容指针。

预期验证：

```bash
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602
PYTHONPATH=build-workshop:. pytest -q tests/tools/test_mlf9_statistical_trends.py
PYTHONPATH=build-workshop:. pytest -q \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py::DiagnosticsProcessProbeSnapshotTests::test_run_probe_payload_and_chain_csv_include_lethality_chain_rows
```

## Hold 条件

- 如果现有上游行无法定义诚实分母，停止。
- 如果实现必须修改已归档 MLF evidence，而不是消费 accepted outputs，停止。
- 如果用户要求的输出会在 MLF-10 之前暗示现实 Pk 或具体弹种校准，停止。

## 已完成 Packet

| Date | Item | Status | Evidence |
| --- | --- | --- | --- |
| `2026-06-19` | `MLF9-Q0` | pass | 子项目文档和父级 A2 链接已创建；`git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602` 通过；对 12 个文件的本地 Markdown 链接检查未发现缺失链接。 |
| `2026-06-19` | `MLF9-Q1` | pass | Inventory 命名 accepted MLF-5..8 inputs、diagnostics row gaps、safe write sets，以及 held calibration/debris/reward surfaces。 |
| `2026-06-19` | `MLF9-Q2` | initial pass | Metric contract 定义 row source、denominators、outcome buckets、grouping fields 和 uncertainty labels；diagnostics row surface 现在暴露 `structural_breakup`；聚焦验证 `47 passed`。 |
| `2026-06-19` | `MLF9-Q3` | initial pass | `tools/diagnostics/mlf9_statistical_trends.py` 将显式 row fixtures 摘要为有边界 trend payload；`tests/tools/test_mlf9_statistical_trends.py` 报告 `2 passed`。 |
| `2026-06-19` | `MLF9-Q4` | initial pass | Process probe 嵌入 `mlf9_statistical_trends`，并可写出 `--mlf9_report_json_out`；focused integration validation 报告 `3 passed`。 |
| `2026-06-19` | `MLF9-Q5` | pass | Focused validation 报告 `53 passed`、`git diff --check` clean，以及 30 个 docs 本地 Markdown 链接 0 缺失。 |
| `2026-06-19` | `MLF9-Q6` | pass | Acceptance record 将有边界 simulation-trend/report 切片标记为 accepted / archived；real-world Pk 和 calibration 继续 held；旧 active 路径是兼容指针。 |
