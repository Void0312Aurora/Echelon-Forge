# WP21 Subagent Dispatch Queue

状态：`2026-05-21` planned / ready for first-wave dispatch。

Language:

- English canonical:
  [wp21_subagent_dispatch_queue_20260521.md](wp21_subagent_dispatch_queue_20260521.md)
- Chinese companion: `wp21_subagent_dispatch_queue_20260521.zh.md`

输入：

- [WP21 main plan](full_counterfactual_experiment_runtime_wp21_20260521.zh.md)
- [Subagent 使用规范](../../../standards/governance/subagent_usage_policy.zh.md)

## Queue

| Stream | Dependency | Dispatch status | Write scope |
|--------|------------|-----------------|-------------|
| `WP21-A Fact Ledger And Residual Freeze` | none | ready | Docs only：source-backed fact ledger 与 final residual register。 |
| `WP21-B Snapshot Restore And Worldline Boundary` | A readiness | queued after A | Snapshot/restore DTO/runtime/facade tests；不做 experiment orchestration。 |
| `WP21-D Scenario Intervention Generation Runtime` | A readiness | queued after A | Python scenario/intervention generator、artifacts、non-mutation tests；不改 C++ rollout。 |
| `WP21-C Counterfactual Rollout And Causal Difference` | B | queued after B | Parent/branch execution 与 causal-difference runtime。 |
| `WP21-E Experiment Facade And Evidence Collection` | C and D | queued after C/D | Experiment facade/binding/evidence collection 与 ancestry tests。 |
| `WP21-F Final Cleanup And Acceptance Handoff` | A-E | serial closure | Integration、validation rollup、final residual closure、indexes、acceptance review。 |

## First-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP21-A` | `gpt-5.4-mini`, xhigh | 生成 source-backed fact ledger 与 residual register。除非 broken link 阻塞规划，只编辑 WP21-A docs。 |

## Second-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP21-B` | `gpt-5.4`, xhigh | 在 A 后实现 bounded snapshot/restore 与 worldline boundary。拥有 boundary 的 runtime/facade/binding tests；不实现 experiment orchestration。 |
| `WP21-D` | `gpt-5.4`, high | 在 A 后实现 deterministic scenario/intervention generation。拥有 Python/scenario tests 与 loader boundary guards；不编辑 C++ rollout。 |

## Third-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP21-C` | `gpt-5.4`, xhigh | 在 B 后实现 parent/branch rollout 与 causal-difference runtime。消费 B 的 boundary，并保持 scenario generation 不变。 |
| `WP21-E` | `gpt-5.4`, xhigh | 在 C/D 后实现 experiment facade/evidence collection。拥有 public surface、bindings、ancestry 与 non-truth-claim tests。 |

## Closure-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP21-F` | `gpt-5.4-mini`, xhigh | A-E 后串行 closure：validation rollup、residual closure、README/review sync、bilingual companions 与最终 acceptance review。 |

## Worker Return Packet

每个 worker 必须返回：

- status: `pass`、`blocked` 或 `preflight-only`；
- touched files；
- validation commands and outcomes；
- blockers and residuals；
- 给下一 stream 的 integration notes；
- closure impact；
- 确认没有 revert unrelated edits。

## Stop Rules

- 不晋级 exact GPU 或 resident-state support。
- 不把 experiment outputs 当作 truth/support claims。
- 不在 facade/request contracts 外修改 authoritative runtime state。
- 不强制 scenario schema migration。
- 遇到 blocker 时命名后停止，而不是重开早期已验收阶段。
