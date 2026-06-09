# WP17 First-Wave Preflight Recovery

状态：`2026-05-21` historical preflight record；后续 implementation waves 已将 B/C/D/E/F 转换为 selected-slice runtime evidence。

英文主文：[wp17_preflight_recovery_20260521.md](wp17_preflight_recovery_20260521.md)

输入：

- [WP17 主计划](stage3_runtime_materialization_cleanup_wp17_20260521.zh.md)
- [WP17 dispatch queue](wp17_subagent_dispatch_queue_20260521.zh.md)

## 1. 结论

WP17 task family 与首轮 task clusters 与当时的代码事实相符。首轮 subagents 已派发并回收。

preflight 时的重要区分是：

- `WP17-A` 与 `WP17-B` 在 preflight 后 implementation-ready；
- `WP17-C`、`WP17-D` 与 `WP17-E` 范围正确，但当时尚未由代码满足；
- `WP17-F` 当时需要等待来自 `WP17-C` 与 `WP17-D` 的前置证据。

2026-05-21 后续实现波次已经满足 B/C/D/E selected-slice gates，并释放了 narrowed F runtime slice。此文档保留原始 preflight verdict 作为历史上下文，而不是当前任务状态。

## 2. 回收结果

| Stream | 结果 | 含义 |
|--------|------|------|
| `WP17-A Fact Ledger And Boundary Freeze` | `pass` | WP17 主计划中的六项当前代码事实准确；`RuntimeFacade::capabilities()` 已非空，但仍是静态 metadata，而不是 provider negotiation。 |
| `WP17-B Facade Business Migration And Compatibility Cleanup` | `pass` | Maintained business code 已使用 adapter/facade-shaped paths；剩余 direct `vec_env.batch_runtime` ready/state reads 主要在 tests 中，需要迁移或 guard。 |
| `WP17-C Multi-Rate Runtime Example` | historical preflight gap | §8 10Hz/20Hz/60Hz 示例需要 selected-slice cadence DTOs/traces、runtime-window planning、`hold_last`、expiry evidence，以及不翻转 global `kWp10ClockDomainAdvisoryOnly` 的 helper。 |
| `WP17-D Fidelity Provider Runtime` | historical preflight gap | contract-level fidelity request/admission helpers 已存在，但 `RuntimeFacade` 仍需 facade-owned request/admission/provider-selection method。 |
| `WP17-E Capability Spawn Runtime Promotion` | historical preflight gap | `CapabilityBundle`、`ResolvedPlatformSpawnPlan`、bindings 与 internal factory resolution 已存在，但 `DefaultUnitFactory::spawn()` 仍需在 materialization 前消费 resolved plan。 |

## 3. 后续实现顺序

preflight 后建议顺序：

1. 先实现 `WP17-B`，因为它是最小业务 cleanup，并在更大 runtime streams 前收窄 compatibility-only `batch_runtime` use。
2. 在 B 后或写入范围保持 disjoint 时并行启动 `WP17-C` 与 `WP17-D`。
3. 独立启动 `WP17-E`，并确认 spawn evidence 的归属。
4. 等 C 的 deterministic cadence/barrier evidence 与 D 的 profile/provider scope 返回后再释放 `WP17-F`。

当前 follow-up：该释放条件已为 narrow explicit-setup selected-entity branch/compare API 满足。Broad counterfactual orchestration 仍不在范围内。

## 4. Preflight Guardrails

- 不通过全局翻转 `kWp10ClockDomainAdvisoryOnly` 来通过 WP17-C。
- 不把 module-level fidelity helper bindings 当作 facade-owned runtime admission。
- 在 additive boundary changes 之前，不引入 public `spawn_platform` 或将 `TypedPlatformSpawnRequest` 路由到 maintained mainline。
- 第一批 cleanup 不删除 `WorldBatchRuntime`、`RuntimeFacade.runtime()` 或 `batch_runtime`。
- 当 `snapshot_restore_supported` 仍 fail-closed 时，不声明 counterfactual restore 或 rollout。

## 5. Worker 已报告验证

已报告通过的检查包括：

```bash
python -m pytest -q tests/runtime/facade/test_runtime_facade.py tests/architecture/runtime_facade/test_layering.py tests/architecture/platform_spawn/test_boundary_guards.py tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py
python -m pytest -q tests/architecture/runtime_facade/test_layering.py
python -m pytest -q tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "compatibility_view or execution_episode_controller_mainline or shadow_compare"
python -m pytest -q tests/architecture/runtime_spine/test_clock_domain_enforcement.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "capabilities or fidelity"
python -m pytest -q tests/test_gpu_runtime_bindings.py -k "capabilities or fidelity"
```

一个已报告 blocker 属于环境而非语义问题：

```text
tests/architecture/test_wp14_*.py compile-style checks: missing spdlog/spdlog.h
from hard-coded build-local-win include paths in the current environment.
```
