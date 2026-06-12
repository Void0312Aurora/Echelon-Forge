# UniversalEnv Raw Compatibility 调用点生存表

状态：`2026-06-12` 活跃治理切片。
范围：活跃 Python 路径中把 `runtime_compatibility_enabled` 设为布尔 `True` 的调用点，不包含 `tests/archive/` 与 `tools/archive/`。

## 1. 结论

本轮已经删除两类活跃 raw compatibility 入口，并把剩余调用点登记为可机器检查的生存表。原因是剩余调用点不是同一种债务：

- JSON `env_regression` / `scripted_bridge` contract runner 已从活跃面删除；对应 JSON 规范归档到 `tests/archive/contracts/`。
- runtime 回归测试里还有若干 raw-env 对照基线，删除前需要 world-batch 或 facade 等价断言。
- diagnostics 是人工/操作入口，应该随工具迁移处理；viz session 已切到 batch=1 的 maintained `WorldBatchVecEnv`，Arma raw env-backed backend 已归档。
- `_RuntimeFacadeAdapter` 内部 compatibility flag 测试已在本轮后续切片中删除；剩余 `tests/world_batch/test_world_batch_vec_env.py` opt-in 只是 direct `UniversalEnv` action-wrapper parity baseline。
- fail-closed rejection guards 不再使用布尔 `runtime_compatibility_enabled=True` 形状登记；single-world maintained runtime 与 training env config 均不再暴露该参数。

机器可读清单位于：

- `tests/architecture/fixtures/universal_env_runtime_compatibility_callers_20260612.json`
- `tests/architecture/runtime_facade/test_universal_env_compatibility_caller_inventory.py`

AST 口径统计结果：7 个活跃文件，7 个布尔 opt-in 调用。

## 2. 分类表

| 分类 | 调用数 | 路径 | 当前处理 |
| --- | ---: | --- | --- |
| runtime regression | 1 | `tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py` | 保留到 weapon-release 有 maintained adapter 等价覆盖；red scripted opponent raw-env 对照已由 world-batch 覆盖取代。 |
| runtime regression | 1 | `tests/runtime/air_combat/test_air_combat_1v1_fixture.py` | 保留到 drone weapon-employment release smoke 迁到 world-batch/facade 路径；fixture observation raw-env 对照已由 world-batch reset shape 覆盖取代。 |
| runtime regression | 1 | `tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py` | 保留到 mission-observation window age 可从 maintained observation packet 断言。 |
| runtime regression | 1 | `tests/runtime/air_combat/test_fire_action_release_gate.py` | 保留到 fire-mask/release gate 检查迁到 maintained runtime adapter。 |
| runtime regression | 1 | `tests/runtime/mission/test_mission_runtime.py` | 保留到 observation parity 不再依赖 legacy `UniversalEnv` baseline。 |
| mixed world-batch regression | 1 | `tests/world_batch/test_world_batch_vec_env.py` | `MultiTimescaleActionWrapper` direct-env parity baseline 暂保留，等待 maintained 等价基线；内部 `_RuntimeFacadeAdapter` compatibility flag 测试已删除。 |
| manual diagnostics | 1 | `tools/diagnostics/air_combat_weapon_employment_process_probe.py` | 先作为 operator-facing diagnostics 保留，后续迁移或归档。 |

## 3. 下一轮删减顺序

| 优先级 | 目标 | 预期动作 |
| --- | --- | --- |
| P0 | `_RuntimeFacadeAdapter` 内部 compatibility flag 测试 | 已完成：删除 adapter-level opt-in 参数、capability 字段和 4 个内部 flag opt-in 测试。 |
| P1 | JSON env/scripted bridge contract runner | 已完成：删除 `env_regression.py` / `scripted_bridge.py` 活跃 executor，归档对应 JSON specs，并移除 batch runner group。 |
| P1.5 | maintained VecEnv public compatibility flag | 已完成：删除 `WorldBatchVecEnv` / `CooperativeWorldBatchVecEnv` 构造器死参数，并移除 single-world wrapper 的旧 opt-in rejection 用例。 |
| P2.1 | 有 maintained 等价覆盖的 raw-env regression | 已完成：删除 naval station raw action/deadband 对照、air-combat red scripted opponent raw 对照，以及 fixture reset raw observation 对照。 |
| P2.2 | training env config compatibility key | 已完成：`resolve_env_settings()` 不再返回 `runtime_compatibility_enabled`，旧字段一律 fail closed；leader/env-config guard 不再用布尔 `True` 形状登记。 |
| P2 | runtime regression raw-env 对照 | 按能力迁移到 world-batch/facade：air-combat release、C2 ROE observation、mission observation parity、action-wrapper parity。 |
| P3 | diagnostics/viz manual 入口 | viz 已迁到 maintained `WorldBatchVecEnv`；Arma env-backed backend 已归档；剩余 diagnostics 后续决定迁移到 maintained runtime adapter，或明确归档为 manual probe。 |

## 4. 验收规则

后续任何新增 `runtime_compatibility_enabled=True` 布尔调用必须同步更新 fixture 并说明分类、迁移目标和下一步动作。新增未登记调用会被 architecture guard 拦截。

这张表不把 raw-env 调用视为已验收主线；它只说明当前哪些调用暂时生存、为什么生存、以及哪一类最先可以删除。
