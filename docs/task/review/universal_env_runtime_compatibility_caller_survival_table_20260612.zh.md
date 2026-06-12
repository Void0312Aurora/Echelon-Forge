# UniversalEnv Raw Compatibility 调用点生存表

状态：`2026-06-12` 活跃治理切片。
范围：活跃 Python 路径中把 `runtime_compatibility_enabled` 设为布尔 `True` 的调用点，不包含 `tests/archive/` 与 `tools/archive/`。

## 1. 结论

本轮已经删除两类活跃 raw compatibility 入口，并把剩余调用点登记为可机器检查的生存表。原因是剩余调用点不是同一种债务：

- JSON `env_regression` / `scripted_bridge` contract runner 已从活跃面删除；对应 JSON 规范归档到 `tests/archive/contracts/`。
- runtime 回归测试里还有若干 raw-env 对照基线，删除前需要 world-batch 或 facade 等价断言。
- diagnostics 是人工/操作入口，应该随工具迁移处理；viz session 已切到 batch=1 的 maintained `WorldBatchVecEnv`，Arma raw env-backed backend 已归档。
- `_RuntimeFacadeAdapter` 内部 compatibility flag 测试已在本轮后续切片中删除；剩余 `tests/world_batch/test_world_batch_vec_env.py` opt-in 只是 direct `UniversalEnv` action-wrapper parity baseline。
- 三个调用点是 fail-closed rejection guard，不是 raw-env 生存入口。

机器可读清单位于：

- `tests/architecture/fixtures/universal_env_runtime_compatibility_callers_20260612.json`
- `tests/architecture/runtime_facade/test_universal_env_compatibility_caller_inventory.py`

AST 口径统计结果：11 个活跃文件，13 个布尔 opt-in 调用。

## 2. 分类表

| 分类 | 调用数 | 路径 | 当前处理 |
| --- | ---: | --- | --- |
| runtime regression | 2 | `tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py` | 保留到 weapon-release 与 red scripted opponent 有 maintained adapter 等价覆盖。 |
| runtime regression | 2 | `tests/runtime/air_combat/test_air_combat_1v1_fixture.py` | 保留到 fixture observation 与 scripted-opponent 检查迁到 world-batch/facade 路径。 |
| runtime regression | 1 | `tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py` | 保留到 mission-observation window age 可从 maintained observation packet 断言。 |
| runtime regression | 1 | `tests/runtime/air_combat/test_fire_action_release_gate.py` | 保留到 fire-mask/release gate 检查迁到 maintained runtime adapter。 |
| runtime regression | 1 | `tests/runtime/mission/test_mission_runtime.py` | 保留到 observation parity 不再依赖 legacy `UniversalEnv` baseline。 |
| runtime regression | 1 | `tests/runtime/naval/test_naval_station_policy_surface.py` | 保留到 naval station action/deadband 检查迁到 maintained runtime path。 |
| mixed world-batch regression | 1 | `tests/world_batch/test_world_batch_vec_env.py` | `MultiTimescaleActionWrapper` direct-env parity baseline 暂保留，等待 maintained 等价基线；内部 `_RuntimeFacadeAdapter` compatibility flag 测试已删除。 |
| manual diagnostics | 1 | `tools/diagnostics/air_combat_weapon_employment_process_probe.py` | 先作为 operator-facing diagnostics 保留，后续迁移或归档。 |
| negative guard | 1 | `tests/leader/_leader_env_runtime_controls_cases.py` | 保留；这是 legacy execution config fail-closed guard。 |
| negative guard | 1 | `tests/runtime/core/test_env_config.py` | 保留；这是 training config runtime compatibility opt-in rejection guard。 |
| negative guard | 1 | `tests/world_batch/test_single_world_batch_runtime.py` | 保留；这是 single-world runtime opt-in rejection guard。 |

## 3. 下一轮删减顺序

| 优先级 | 目标 | 预期动作 |
| --- | --- | --- |
| P0 | `_RuntimeFacadeAdapter` 内部 compatibility flag 测试 | 已完成：删除 adapter-level opt-in 参数、capability 字段和 4 个内部 flag opt-in 测试。 |
| P1 | JSON env/scripted bridge contract runner | 已完成：删除 `env_regression.py` / `scripted_bridge.py` 活跃 executor，归档对应 JSON specs，并移除 batch runner group。 |
| P2 | runtime regression raw-env 对照 | 按能力迁移到 world-batch/facade：air-combat release、C2 ROE observation、mission observation parity、naval station action deadband。 |
| P3 | diagnostics/viz manual 入口 | viz 已迁到 maintained `WorldBatchVecEnv`；Arma env-backed backend 已归档；剩余 diagnostics 后续决定迁移到 maintained runtime adapter，或明确归档为 manual probe。 |

## 4. 验收规则

后续任何新增 `runtime_compatibility_enabled=True` 布尔调用必须同步更新 fixture 并说明分类、迁移目标和下一步动作。新增未登记调用会被 architecture guard 拦截。

这张表不把 raw-env 调用视为已验收主线；它只说明当前哪些调用暂时生存、为什么生存、以及哪一类最先可以删除。
