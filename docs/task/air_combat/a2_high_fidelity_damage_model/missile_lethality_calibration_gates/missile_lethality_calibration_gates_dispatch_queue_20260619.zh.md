# MLF-10 校准门派发队列

状态：`2026-06-19` initial queue for
[MLF-10 校准门](README.zh.md)。本次 opening slice 只有 `MLF10-P0` active。

## Active Queue

| Date | Packet | Cluster | Owner | Write set | Goal | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `2026-06-19` | `MLF10-Q0` | `MLF10-P0` | main thread | MLF-10 docs 和父级 A2 README 文件 | 创建子项目面和父级 live entry | active |

## Planned Queue

| Packet | Cluster | Owner | Trigger | Output |
| --- | --- | --- | --- | --- |
| `MLF10-Q1` | `MLF10-P1` | read-only diagnostics worker or main thread | Q0 link/diff check 通过后 | Calibration-like evidence inventory |
| `MLF10-Q2` | `MLF10-P2` | main thread | Q1 inventory 后 | Admission contract 和 report schema |
| `MLF10-Q3` | `MLF10-P3` | implementation worker | Q2 contract 后 | 确定性 audit tooling 和 focused tests |
| `MLF10-Q4` | `MLF10-P4` | integration worker | Q3 tooling 后 | Retained report integration |
| `MLF10-Q5` | `MLF10-P5` | main thread | Q4 report integration 后 | Focused validation 和 residual record |
| `MLF10-Q6` | `MLF10-P6` | main thread | Q5 validation 后 | Acceptance、hold 或 re-scope decision |

## Hold 条件

- 如果请求在 admission contract 存在前直接调参，停止。
- 如果 report 会在 admission 前暗示 real-world Pk、weapon-specific lethality、
  target-specific lethality 或 deterministic fuze truth，停止。
- 如果 source 需要接入但缺 source-rights 和 provenance review，停止。
- 如果实现必须重写已归档 MLF evidence，而不是消费 accepted outputs，停止。

## Q0 验证

- 对父级 A2 README 文件和 MLF-10 docs 做本地 Markdown 链接检查。
- `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model`。
