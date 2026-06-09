# 域分离大拆分派发队列

状态：`2026-06-09`，面向 [域分离大拆分](README.zh.md) 的初始派发队列。

## 队列规则

- 不创建新的 Codex 会话或线程。
- 只有当 write set 隔离、且 worker packet 能映射到单一任务簇时，才允许本线程内 subagent 风格工作。
- public header、registration file 和 status document 优先串行集成。
- 本轮队列是有限队列；新增项必须更新任务簇表，而不是追加开放式 follow-up wave。

## Round 0：边界与清单

| Queue Item | Cluster | Owner | Write set | Dispatch condition | Required return |
| --- | --- | --- | --- | --- | --- |
| `Q0-A` | DS-P0-A | main thread | `docs/task/review/domain_separation_split/**`, `docs/task/review/README*` | Now | 子项目文件、父级索引链接、`git diff --check` 结果 |
| `Q0-B` | DS-P0-B | diagnostics worker | `*current_status*` only | After Q0-A | damage、weapon、systems、effects、sensor 的 include/type inventory |

## Round 1：Component Ownership

| Queue Item | Cluster | Owner | Write set | Dispatch condition | Required return |
| --- | --- | --- | --- | --- | --- |
| `Q1-A` | DS-C1-A | implementation worker | damage component headers and direct include users | Q0-B complete | 拆分结果、include migration、build/test evidence、residual wrapper list |
| `Q1-B` | DS-C1-B | implementation worker | weapon component headers and direct include users | Q0-B complete；避免与 Q1-A 文件重叠 | 拆分结果、include migration、build/test evidence、residual wrapper list |

## Round 2：System Ownership

| Queue Item | Cluster | Owner | Write set | Dispatch condition | Required return |
| --- | --- | --- | --- | --- | --- |
| `Q2-A` | DS-S1-A | implementation worker | combat damage systems and registration | Q1-A pass | common/air/naval/ground system split 与聚焦 runtime evidence |
| `Q2-B` | DS-S1-B | implementation worker | air systems/tuning wrappers and indexes | Q0-A complete | Air ownership candidate validation、wrapper policy、focused guards |
| `Q2-C` | DS-S1-C | implementation worker | naval logistics systems and registration | Q0-B complete；不与 Q2-A registration 重叠 | Naval logistics extraction 与 focused naval evidence |

## Round 3：Model Ownership

| Queue Item | Cluster | Owner | Write set | Dispatch condition | Required return |
| --- | --- | --- | --- | --- | --- |
| `Q3-A` | DS-M1-A | implementation worker | effects model routing and domain model files | Q1-A and Q2-A pass | Effects routing split、focused effects/damage tests |
| `Q3-B` | DS-M1-B | implementation worker | sensor model routing and naval sensor adapter files | Q0-B complete；避免与 Q3-A interface 重叠 | Sensor adapter split 与 naval sensor tests |

## Round 4：Guards And Closure

| Queue Item | Cluster | Owner | Write set | Dispatch condition | Required return |
| --- | --- | --- | --- | --- | --- |
| `Q4-A` | DS-T1-A | test/architecture worker | architecture/runtime guards | 相关 implementation surface 稳定 | Guard tests 与 failure targets |
| `Q4-B` | DS-D1-A | integration worker | docs/manual/source README and acceptance docs | implementation 与 guard evidence 存在 | Acceptance update、residual list、index sync |

## 必需 Worker Packet

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 派发记录

| Time | Queue Item | Cluster | Assignee | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `2026-06-09` | `Q0-A` | DS-P0-A | main thread | pass | 子项目文件和父级 review link 已创建；docs diff check 通过。 |
| `2026-06-09` | `Q0-B` | DS-P0-B | worker `Meitner` | pass | Inventory 已写入 current-status 文件；docs diff check 通过。 |
| `2026-06-09` | `Q1-A` | DS-C1-A | worker `Dirac` | pass | damage component split 已落地，采用 umbrella-header compatibility；combined `ef_py` build 与 diff checks 通过。 |
| `2026-06-09` | `Q1-B` | DS-C1-B | worker `Cicero` | pass | weapon component split 已落地，采用 umbrella-header compatibility；combined `ef_py` build 与 diff checks 通过。 |
| `2026-06-09` | `Q2-A` | DS-S1-A | worker `Popper` | pass | combat damage system split 已落地；combined `ef_py`、include search 与 diff checks 通过。 |
| `2026-06-09` | `Q2-B` | DS-S1-B | worker `Galileo` | pass | Air runtime ownership validation 已落地；旧 physics/tuning wrapper 保持 include-only。 |
