# 面向 Agent 的子项目创建标准

语言：
- 英文规范页：[subproject_creation_standard.md](subproject_creation_standard.md)
- 中文配套页：`subproject_creation_standard.zh.md`

状态：`2026-06-01`，用于创建新任务子项目和子项目文档的维护规则。

范围：`docs/task/**` 下的新建或重新启用子项目，以及 Agent 用于规划、派发、
实现、验证和收口有边界工作切片的任务簇文档。

本标准抽取维护中任务切片的通用结构，但不把任何历史子项目提升为当前权威。
委派工作应使用
[Subagent 使用规范](../standards/subagent_usage_policy.zh.md)。

## 何时创建子项目

只有当工作需要可持久化的执行表面时，才创建子项目目录。若工作很小，应使用
单篇评估记录或既有 README 中的一节。

满足以下任一条件时，可以创建子项目：

- 工作跨多个文件、阶段或 owner；
- 实现必须拆成有限任务簇；
- 工作会改变领域成熟度、公开能力声明、runtime contract、场景、配置或测试；
- 工作需要显式当前状态、验收、残余或 archive 处理；
- 未来 Agent 必须能在不依赖聊天历史的情况下恢复工作。

不要仅为了重述现有计划、停放模糊想法，或绕开最近的维护 README 更新而创建
子项目。

## 位置与命名

使用以下位置模式：

```text
docs/task/<domain>/<subproject_slug>/
```

规则：

- `<domain>` 必须已经存在，或同步加入 `docs/task/README*`。
- `<subproject_slug>` 应短、小写、稳定。
- 当父领域已有阶段序列时，优先使用 `<phase>_<short_scope>` 或
  `<domain_phase>_<short_scope>` 这类前缀。
- 避免名称暗示比已证明范围更高的成熟度。若历史名称存在误导，继续扩展前先在
  本地加 warning banner。
- 新增顶层任务领域时，必须更新 `docs/task/README*` 和受影响的 standards 或
  manual 入口。

## 必需最小文件集

每个维护中的子项目必须包含：

```text
README.md
<subproject_slug>_task_clusters_<YYYYMMDD>.md
```

当切片长期运行或风险较高时，增加：

```text
<subproject_slug>_current_status_<YYYYMMDD>.md
<subproject_slug>_dispatch_queue_<YYYYMMDD>.md
<subproject_slug>_acceptance_<YYYYMMDD>.md
archive/README.md
```

维护中的公开入口或稳定治理/状态文档应配中文辅文。高频变更的实现切片可在
父 README 明确说明后只维护英文规范页。

## README 必需章节

`README.md` 是子项目当前导航和范围权威。除非有强本地理由，应按以下顺序包含：

1. 标题
2. `Status:` 行
3. `Language:` 块
4. `Inputs:` 或 `Related authority:` 链接
5. `Purpose`
6. `Current state`
7. `Scope`
8. `Phase plan`
9. `Task clusters`
10. `Outputs and evidence`
11. `Acceptance gate`
12. `Residuals and next steps`
13. `Archive`

最小 README 模板：

```md
# <Subproject Title>

Status: `<YYYY-MM-DD>` <proposed | planning | active | accepted | held | closed | archived> <short status>.

Language:

- English canonical: `README.md`
- Chinese companion: <link or "not required yet; high-churn task slice">

Inputs:

- <parent task README>
- <relevant standard>
- <relevant code/test/scenario entry>

## Purpose

<一到两段说明工作内容，以及为什么需要这个子项目。>

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| <area> | <accepted/active/held> | <code/test/doc link> | <what this does not prove> |

## Scope

In scope:

- <specific work item>

Out of scope:

- <explicit non-goal and forbidden capability claim>

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope and authority. | <input> | <gate> | <status> |
| `P1 Evidence` | Collect source/code/test facts. | <input> | <gate> | <status> |
| `P2 Implementation` | Implement the scoped behavior. | <input> | <gate> | <status> |
| `P3 Integration` | Wire maintained runtime/config/test surfaces. | <input> | <gate> | <status> |
| `P4 Validation` | Run acceptance and record residuals. | <input> | <gate> | <status> |
| `P5 Closure` | Sync docs/index/archive. | <input> | <gate> | <status> |

## Task Clusters

- Task cluster plan: `<subproject_slug>_task_clusters_<YYYYMMDD>.md`

## Outputs And Evidence

- <code/config/scenario/test/doc output>

## Acceptance Gate

This subproject can be marked accepted only when:

- <testable condition>
- <documentation condition>
- <forbidden overclaim remains refused>

## Residuals And Next Steps

- <held item>
- <next credible expansion>

## Archive

Superseded or historical records move to `archive/README.md` when the
subproject has a replacement current-status or closeout surface.
```

## 任务簇文档必需章节

任务簇文档是有限执行计划，用来防止子项目变成开放式追加 wave。

必需章节：

1. 标题
2. `Status:` 行
3. 父子项目链接
4. 边界或决策说明
5. 有限任务簇列表
6. 派发规则
7. worker packet 要求
8. 验证计划
9. 验收标准
10. 残余地图

必需任务簇表格列：

| 列 | 含义 |
| --- | --- |
| `Cluster` | 稳定任务簇 id，例如 `P1-A`、`D2-B` 或 `INT-C`。 |
| `Owner` | main thread、具名 worker、future worker、integration worker 或只读 diagnostics worker。 |
| `Capability tier / model ID / reasoning` | 记录能力档与可用 reasoning 控制；只有当前执行环境明确暴露精确 model ID 时才填写，否则使用 `n/a`。 |
| `Goal` | 一个有边界结果。 |
| `Write set` | 该任务簇可修改的精确文件或文件族。 |
| `Non-goals` | 明确排除项和禁止能力声明。 |
| `Validation` | 命令、链接检查、contract runner 或检查项。 |
| `Closure gate` | 改变任务簇状态的条件。 |
| `Dependency / parallel` | 依赖关系和是否可并行。 |
| `Round cap` | 重新划分范围前允许的最大实现/修复轮次。 |
| `Status` | `planned`、`active`、`pass`、`partial`、`blocked`、`failed`、`accepted` 或 `closed`。 |

最小任务簇模板：

```md
# <Subproject> Task Clusters

Status: `<YYYY-MM-DD>` finite task-cluster plan for `<Subproject README.md>`.

## Boundary Decision

<本子项目允许改什么，以及不能暗示什么。>

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<ID>` | <owner> | <tier / 当前明确可用的 model ID 或 n/a / reasoning> | <goal> | <files> | <excluded work> | <commands> | <gate> | <dependency/parallel rule> | <round cap> | <status> |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same normative table, scenario contract,
  public API, or status line concurrently.
- Keep acceptance/closure clusters serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a follow-up
  wave.
- 遵循 [Subagent 使用规范](../standards/subagent_usage_policy.zh.md)。

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

```bash
<repo-root command>
```

## Acceptance Criteria

- <condition>

## Residual Map

Immediate:

- <residual>

Follow-on:

- <next scoped package>

Deferred:

- <explicitly held surface>
```

## 当前状态文档

长期领域或多切片子项目应保留 current-status 文档。它不替代局部 README，而是记录
某日状态。

推荐文件名：

```text
<domain_or_subproject>_current_status_<YYYYMMDD>.md
```

必需内容：

- status 行和日期；
- 相比上一个 checkpoint 发生的变化；
- 成熟度矩阵：accepted、active、held、blocked、deferred；
- 指向代码、场景、配置、测试、保留制品或任务簇记录的 evidence 链接；
- residual register 或 residual map；
- 推荐的下一步行动顺序；
- 显式拒绝的过度声明。

## 验收与收口文档

当子项目改变能力状态、关闭高风险残余，或将某个场景/配置/测试提升为维护证据时，
应新增 acceptance 或 closeout 文档。

验收文档必须说明：

- 已接受范围；
- 验证命令和结果；
- evidence artifacts；
- 仍然开放的 residual；
- 仍然禁止的能力声明；
- 已同步的索引。

当当前 README、父 README、测试、reference artifacts 或 standards 链接仍指向过期
状态时，不得将子项目标为 `closed`。

## Archive 规则

只有在已有当前 README、current status 或 acceptance 表面告诉读者从哪里开始时，
才将被取代的本地记录移入 `archive/`。

Archive 规则：

- archive 文件超过一个时，保留 `archive/README.md`；
- 新 Agent 提示词不得默认把 archived records 当作权威；
- 不要因为历史证据过期就删除它；
- 如果 archived file 中有仍然相关的事实，应把该事实提升到当前 README 或 status
  文档，并把 archive 作为 provenance 引用。

## 状态词汇

统一使用以下状态词：

| Status | 含义 |
| --- | --- |
| `proposed` | 想法存在，但尚未接受为工作表面。 |
| `planning` | 正在限定范围；不应开始实现。 |
| `active` | 工作开放且当前有效。 |
| `pass` | 被分配的任务簇通过其范围内 gate。 |
| `partial` | 有证据，但 gate 尚未解锁。 |
| `blocked` | 具名 blocker 阻止诚实推进，除非重划范围或 owner 输入。 |
| `accepted` | 范围内验收 gate 通过；仍可有 residual。 |
| `held` | 显式推迟；本切片不应实现或声明。 |
| `closed` | 已验收，并完成 index/archive/doc 同步。 |
| `archived` | 历史记录；默认不是当前权威。 |

## 反模式

避免：

- 创建没有父 README 链接的子项目；
- 创建没有有限任务簇列表的 cluster plan；
- 省略 non-goals，随后过度声明成熟度；
- 不重划范围就反复追加“再修一轮”；
- 把 dispatch queue 当作实现证据；
- 把 scenario-only 资产标成 active training/runtime acceptance；
- 把 docs-only pass 标成 runtime pass；
- 让重要发现只留在聊天里；
- 让 retained 或 signoff artifact 代表更广项目成熟度。

## Agent 检查清单

创建或更新子项目前，Agent 必须确认：

- 父领域 README 存在，并会链接该子项目；
- 已链接相关 standards owner；
- README 包含 purpose、current state、scope、phase plan、task clusters、
  acceptance gate 和 residuals；
- 任务簇文档有有限任务簇和 round cap；
- 验证命令可从 repo root 运行，或明确标为 docs-only；
- 状态词有范围，不暗示更广成熟度；
- archive/current 边界明确；
- 本地 Markdown 链接检查通过。
