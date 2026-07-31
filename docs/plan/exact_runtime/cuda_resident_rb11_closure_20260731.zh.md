# RB11 CUDA 驻留计划收口

语言版本：

- 英文规范版：[cuda_resident_rb11_closure_20260731.md](cuda_resident_rb11_closure_20260731.md)
- 中文伴随版：`cuda_resident_rb11_closure_20260731.zh.md`
- 机器可读记录：[cuda_resident_rb11_closure_20260731.json](cuda_resident_rb11_closure_20260731.json)

- Closure ID：`rb11.closed_without_promotion.cuda_resident.20260731`
- 日期：`2026-07-31`
- Branch：`codex/cuda-resident-backend`
- 收口前 HEAD：`e5ea624fc1688d6e9d8b00ae64670ddcc2e3bd02`
- Baseline/main HEAD：`395e02b7dfeaa87baedb2611ec503d14ab137ce3`

## 处置

分支内 CUDA 驻留计划**无晋级关闭**。已实现 backend 保持为 unmaintained
research candidate；RuntimeFacade 不选择它，maintained support projection 不
声明它，它也不替代维护中的 CPU backend。

RB11 不修改 runtime、CUDA kernel、support、ABI、manifest、fallback、tuning 或
语义，只记录并守卫 closure boundary。未来若要继续实现，必须建立新的显式计划；
本分支不会自行重新开放。

文档/测试写集只包含本机器记录与双语 closure pair、双语 program 终态状态、
exact-runtime 与 parent-plan 两组 README、迭代账本、新 closure guard，以及既有
RB10 continuation guard 的终态断言。

本轮新增的两条 `.gitattributes` 规则属于 closure 写集：它们把 RB10 decision
JSON 与本 closure JSON 标为 `-text`，避免另一次 checkout 的 `core.autocrlf`
改变 committed bytes，进而造成 hash 漂移。

## 仓库与发布快照

RB11 前，candidate branch 在 baseline 上有 11 个已复核 commit，与本地 `main`
的 merge-base 是 `395e02b7...`；本地 `main` 仍精确停在该 baseline，candidate 未
merge 进去。现有本地 remote-tracking ref 均不包含收口前 HEAD。该 remote 观察
明确只覆盖未 fetch 的本地 ref snapshot，不声称代表不可见的服务器状态。

branch 与独立 worktree 均保留。RB11 不删除、archive、merge 或 push 它们，从而
保留完整 RB0-RB11 证据，且不改变 maintained worktree 即可继续审阅。

## 收口提交前的 accepted chain

| 迭代 | Commit | 结果 |
| --- | --- | --- |
| RB0 | `e7f3b144` | 冻结计划 |
| RB1 | `91195ea8` | CPU backend seam |
| RB2 | `6df115c0` | admission/parity contract |
| RB3 | `6e1a3b67` | CUDA lifecycle shell |
| RB4 | `939f962a` | resident state barriers |
| RB5 | `f287a4f8` | Phase A controls |
| RB6 | `3e4f4f44` | Phase B dynamics |
| RB7 | `4fe0f15c` | Phase D projection/device view |
| RB8 | `1304d050` | replay/shadow harness |
| RB9 | `c2175790` | held performance evidence |
| RB10 | `e5ea624f` | hold decision |

机器记录用 `this_commit` 代表 RB11，因为 commit 不能嵌入自身 hash；最终身份以
branch history 为准。

## 保留与回滚边界

- maintained recovery 不需要 rollback：本计划从未推进本地 `main`，其仍在 baseline。
- candidate recovery 是保留的 branch、worktree 与已复核 commit chain；compact
  RB9 evidence 与 RB10 hold decision 均继续 tracked。
- 不执行破坏性 cleanup。未来删除 worktree/branch 前，需要用户明确授权并重新
  审计 worktree/ref。
- 若未来重新考虑，必须以新授权开始，并重新测完整 facade-equivalent window、
  learner consumption、必需 counters、parity release 与 small-batch policy；不得把
  world-4 provisional private threshold 沿用为 promotion authority。

## 收口时的 maintained boundary

- `compiled_experimental_backend=false`；
- `supports_resident_state=false`；
- `supports_device_observation_view=false`；
- CPU 继续是 maintained default；
- 不声称 public ABI promotion。

RB9 已对最后一轮 runtime 写集提供 accepted runtime validation。RB10-RB11 只涉及
文档与 architecture guard，因此 RB11 复用该已接受的 CPU/CUDA 证据，并新运行只读
closure、decision、performance、双语链接、Git boundary guard 与独立复核。
