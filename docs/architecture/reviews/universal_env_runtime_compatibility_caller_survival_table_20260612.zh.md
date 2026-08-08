# UniversalEnv Raw Compatibility 调用点生存表

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/architecture/reviews/universal_env_runtime_compatibility_caller_survival_table_20260612.zh.md`
Owner: `architecture/reviews`
Last verified: `2026-06-12`

状态：`2026-06-12` 活跃治理切片。
范围：活跃 Python 路径中把 `runtime_compatibility_enabled` 设为布尔 `True` 的调用点，不包含 `tests/archive/` 与 `tools/archive/`。

## 1. 结论

本轮已经把活跃 Python 路径中的 raw `UniversalEnv` 构造和布尔 `runtime_compatibility_enabled=True` opt-in 清到 0。此前剩余调用点分别迁移到 maintained world-batch/facade 路径，或从 active tools 归档：

- JSON `env_regression` / `scripted_bridge` contract runner 已从活跃面删除；对应 JSON 规范归档到 `tests/archive/contracts/`。
- runtime 回归测试中的 C2 ROE mission observation、fire-action release gate、mission observation parity、action-wrapper baseline 均已迁到 maintained `WorldBatchVecEnv`/observation packet 断言。
- diagnostics 中的 air-combat weapon-employment process probe 已改为 batch=1 `WorldBatchVecEnv` adapter；viz session 已切到 batch=1 的 maintained `WorldBatchVecEnv`，Arma raw env-backed backend 已归档。
- `_RuntimeFacadeAdapter` 内部 compatibility flag 测试已删除；active world-batch 测试不再构造 direct `UniversalEnv` baseline。
- fail-closed rejection guards 不再使用布尔 `runtime_compatibility_enabled=True` 形状登记；single-world maintained runtime 与 training env config 均不再暴露该参数。

机器可读清单位于：

- `tests/architecture/fixtures/universal_env_runtime_compatibility_callers_20260612.json`
- `tests/architecture/runtime_facade/test_universal_env_compatibility_caller_inventory.py`

AST 口径统计结果：0 个活跃 direct `UniversalEnv(...)` 构造；0 个活跃布尔 `runtime_compatibility_enabled=True` opt-in 调用。

## 2. 分类表

| 分类 | 调用数 | 路径 | 当前处理 |
| --- | ---: | --- | --- |
| runtime regression | 0 | n/a | C2 ROE、fire gate、mission observation、action-wrapper baseline 均已迁到 maintained world-batch/observation packet。 |
| manual diagnostics | 0 | n/a | air-combat process probe 已迁到 batch=1 `WorldBatchVecEnv` adapter；raw benchmark family 已归档。 |

## 3. 下一轮删减顺序

| 优先级 | 目标 | 预期动作 |
| --- | --- | --- |
| P0 | `_RuntimeFacadeAdapter` 内部 compatibility flag 测试 | 已完成：删除 adapter-level opt-in 参数、capability 字段和 4 个内部 flag opt-in 测试。 |
| P1 | JSON env/scripted bridge contract runner | 已完成：删除 `env_regression.py` / `scripted_bridge.py` 活跃 executor，归档对应 JSON specs，并移除 batch runner group。 |
| P1.5 | maintained VecEnv public compatibility flag | 已完成：删除 `WorldBatchVecEnv` / `CooperativeWorldBatchVecEnv` 构造器死参数，并移除 single-world wrapper 的旧 opt-in rejection 用例。 |
| P2.1 | 有 maintained 等价覆盖的 raw-env regression | 已完成：删除 naval station raw action/deadband 对照、air-combat red scripted opponent raw 对照、fixture reset raw observation 对照，以及两个 air-combat weapon-release raw smoke。 |
| P2.2 | training env config compatibility key | 已完成：`resolve_env_settings()` 不再返回 `runtime_compatibility_enabled`，旧字段一律 fail closed；leader/env-config guard 不再用布尔 `True` 形状登记。 |
| P2 | runtime regression raw-env 对照 | 已完成：C2 ROE observation、fire-action release gate、mission observation parity、action-wrapper parity 均迁出 raw env。 |
| P3 | diagnostics/viz manual 入口 | 已完成：viz 和 air-combat process probe 迁到 maintained `WorldBatchVecEnv`；Arma env-backed backend、raw visual/coarse-route benchmark 已归档。 |

## 4. 验收规则

后续任何新增 `runtime_compatibility_enabled=True` 布尔调用都会被 architecture guard 拦截；正常路线不是登记新生存项，而是迁到 maintained runtime/facade 或归档。

这张表现在作为闭合门槛：active Python 路径不再允许 raw `UniversalEnv` 构造生存。
