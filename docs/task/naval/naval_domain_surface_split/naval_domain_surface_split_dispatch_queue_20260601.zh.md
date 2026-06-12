# 海军领域执行面拆分分发队列

状态：`2026-06-12`，`P1-A/P1-B/P2-A/P3-A/P3-B/P4-A` 已验收；
`P2-B` 仍 ready，若触及 runtime contracts 必须串行；`P5-A` 在 command projection
解决或显式 held 前继续 held。

父项目：[海军领域执行面拆分](README.zh.md)

## Queue Rules

- 只分发
  [naval_domain_surface_split_task_clusters_20260601.zh.md](naval_domain_surface_split_task_clusters_20260601.zh.md)
  中列出的 cluster。
- 一个 packet 精确映射一个 cluster。
- 不要让实现 worker 与父 README、current status、acceptance doc 并发编辑。
- Runtime contract 编辑默认串行，除非 integration owner 确认符号和测试不重叠。
- Worker 输出必须分类剩余 air-first dependency。

## Ready Packets

| Packet | Cluster | Status | Write set | Validation |
| --- | --- | --- | --- | --- |
| `DS-P1-A-inventory` | `P1-A` | returned/pass, accepted from `Linnaeus` | status docs and optional diagnostics notes | read-only inventory 加 `git diff --check -- docs/task/naval` |
| `DS-P1-B-guards` | `P1-B` | returned/pass, accepted from `Locke` | training/eval guard tests | focused naval pytest |
| `DS-P2-A-action-transport` | `P2-A` | returned/pass, accepted from `Locke` | action/runtime contracts and adapters | 若触及则 C++/binding，加 world-batch naval tests |
| `DS-P2-B-command-projection` | `P2-B` | ready, choose serially | command contracts, naval profile, command-chain tests | command roundtrip and world-batch tests |
| `DS-P3-A-observation-packet` | `P3-A` | returned/pass, accepted from main thread | observation taxonomy/runtime/tests | mission observation and naval runtime tests |
| `DS-P3-B-config-alias` | `P3-B` | returned/pass, accepted from `Linnaeus` | env config, train CLI, docs/tests | env-config and bootstrap tests |
| `DS-P4-A-integration` | `P4-A` | returned/pass, accepted from main thread | active configs, eval, runtime naval tests | active entry, eval, scenario contract gates |
| `DS-P5-A-closeout` | `P5-A` | held until `P2-B` disposition | docs only | acceptance gate 加 `git diff --check` |

## Worker Packet Template

```md
status: pass | partial | blocked | failed
cluster:
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
air-first dependency classification:
```

## No-Dispatch Conditions

以下情况不要分发实现 worker：

- inventory 尚未识别 `PilotAction` 和 `MissionCommand` 依赖是 adapter、blocker 还是
  accepted shared infrastructure；
- worker 必须声明 N5/N6 成熟度才能关闭 packet；
- 测试需要在 cluster 写集之外大范围重写 air runtime。
