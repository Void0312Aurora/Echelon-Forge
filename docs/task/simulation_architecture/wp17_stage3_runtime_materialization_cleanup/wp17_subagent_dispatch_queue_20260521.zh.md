# WP17 Subagent Dispatch Queue

状态：`2026-05-21` implementation waves returned；selected-slice validation passed。

英文主文：[wp17_subagent_dispatch_queue_20260521.md](wp17_subagent_dispatch_queue_20260521.md)

使用此队列启动 subagents。主线程负责 integration 与 final acceptance。

Preflight recovery：

- [WP17 first-wave preflight recovery](wp17_preflight_recovery_20260521.zh.md)

## First Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP17-A` | explorer 或 lightweight worker | `gpt-5.4-mini`, xhigh | 校验 code-fact ledger 与 residual boundaries。 | Docs/fixtures only；不改 runtime code。 |
| `WP17-B` | worker | `gpt-5.4`, high | 规划并实现 facade-shaped batch/training read migration 与 compatibility guards。 | `python/rl/runtime/world_batch*`、selected `tests/world_batch`、selected architecture guards。 |
| `WP17-C` | worker | `gpt-5.4`, xhigh | preflight §8 multi-rate runnable example，并命名 scheduler seams/tests。 | Scheduler/window-loop files 与 focused cadence tests。 |
| `WP17-D` | worker | `gpt-5.4`, high | preflight fidelity request/provider runtime slice，并命名 binding/test surfaces。 | Runtime facade capability/provider files 与 fidelity tests。 |
| `WP17-E` | worker | `gpt-5.4`, high | preflight capability spawn promotion 与 compatibility risks。 | Default unit factory/setup/spawn tests。 |

## Historical First-Wave Return State

| Stream | Dispatch status | Preflight result | Planning consequence |
|--------|-----------------|------------------|----------------------|
| `WP17-A` | dispatched / returned | `pass` | WP17 主计划中的当前代码事实准确；旧 Stage 3 wording 不应驱动实现。 |
| `WP17-B` | dispatched / returned | `pass` | Maintained business code 已通过 adapter methods 路由；后续实现需迁移剩余 test reads 并收紧 compatibility guards。 |
| `WP17-C` | dispatched / returned | historical preflight gap | 当时 §8 multi-rate example 仍需要 selected-slice cadence planning、hold/expiry evidence 与 runtime window traces。 |
| `WP17-D` | dispatched / returned | historical preflight gap | 当时已有 contract-level fidelity admission，但缺少 facade-owned admission/provider-selection runtime behavior。 |
| `WP17-E` | dispatched / returned | historical preflight gap | 当时 capability contracts/bindings/factory internal resolution 已存在，但 spawn materialization 尚未消费 resolved plans。 |

## Implementation Return State

| Stream | Implementation status | Evidence |
|--------|-----------------------|----------|
| `WP17-B` | implemented / focused pass | Maintained adapter/env methods 暴露 facade-shaped execution-episode ready/state reads；architecture guards 将 direct `batch_runtime` reads 保持 compatibility-only。 |
| `WP17-C` | implemented / focused pass | Runtime window selected-slice cadence emits `cadence_config`、`cadence_trace`、hold/expiry evidence 与 `selected_slice_cadence_trace_runtime_window_wp17c` reason。 |
| `WP17-D` | implemented / focused pass | `RuntimeFacade::admit_fidelity_request()` admits reference CPU exact evaluation，并拒绝 resident/exact-GPU/shadow requests。 |
| `WP17-E` | implemented / focused pass | `DefaultUnitFactory::spawn()` 内部消费 resolved platform spawn plans，同时保留 `spawn_unit(type_name)` compatibility。 |
| `WP17-F` | narrowed selected-slice implemented / focused pass | `RuntimeFacade::run_counterfactual_branch()` 从 explicit setup 构建 parent/branch worlds，拒绝 raw mutation，并报告 selected-entity causal deltas。 |

## Held Wave

| Stream | Release condition |
|--------|-------------------|
| Broad counterfactual/worldline rollout | 只有在 arbitrary live-world clone、snapshot/restore support 与 experiment orchestration 另有 runtime evidence 后才释放。 |

## Required Worker Return Packet

```md
Stream:
Status: pass | fail | blocked
Touched files:
Commands run:
Evidence:
Residuals:
Integration notes:
Closure impact:
```
