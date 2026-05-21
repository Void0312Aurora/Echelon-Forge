# WP20 Public Capability-Platform Composition 验收审查

状态：`2026-05-21` accepted / implementation mergeable。

语言版本：

- 英文主文：[wp20_public_capability_platform_composition_acceptance_review_20260521.md](wp20_public_capability_platform_composition_acceptance_review_20260521.md)
- 中文辅文：`wp20_public_capability_platform_composition_acceptance_review_20260521.zh.md`

输入：

- [WP20 Public Capability-Platform Composition](../simulation_architecture/wp20_public_capability_platform_composition/public_capability_platform_composition_wp20_20260521.zh.md)
- [WP20-A Public Capability Fact Ledger](../simulation_architecture/wp20_public_capability_platform_composition/wp20_public_capability_fact_ledger_cluster_20260521.zh.md)
- [WP20-B Public Typed Platform Spawn Contract](../simulation_architecture/wp20_public_capability_platform_composition/wp20_public_typed_platform_spawn_contract_cluster_20260521.zh.md)
- [WP20-C Runtime Setup Consume Bridge](../simulation_architecture/wp20_public_capability_platform_composition/wp20_runtime_setup_consume_bridge_cluster_20260521.zh.md)
- [WP20-D Facade And Binding Public Surface](../simulation_architecture/wp20_public_capability_platform_composition/wp20_facade_binding_public_surface_cluster_20260521.zh.md)
- [WP20-E Compatibility And Schema Guard](../simulation_architecture/wp20_public_capability_platform_composition/wp20_compatibility_schema_guard_cluster_20260521.zh.md)
- [WP20-F Integration And Handoff](../simulation_architecture/wp20_public_capability_platform_composition/wp20_integration_handoff_cluster_20260521.zh.md)
- [WP20 dispatch queue](../simulation_architecture/wp20_public_capability_platform_composition/wp20_subagent_dispatch_queue_20260521.zh.md)

## 1. 结论

WP20 已作为一个有边界的 public capability-platform composition 增量验收。
它通过 validation-first admission/result evidence 公布 typed setup path，
保留 `spawn_unit(type_name)` 与 `WorldSpawnRequest.type_name`，保持
scenario-schema 稳定，并继续把 backend `RuntimeCapabilities` 与 platform
composition semantics 分离。

未发现阻塞性 findings。其余内容都是显式保留的 residuals，不是验收阻塞。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP20-A Public Capability Fact Ledger` | pass | fact ledger 冻结 capability contracts、typed setup DTO、internal resolved plans 与 public gaps 的 source/test inventory，并保持 WP20 seam 足够窄。 |
| `WP20-B Public Typed Platform Spawn Contract` | pass | public admission/result contract 与 focused architecture tests 定义 typed platform spawn request evidence，但不把 typed requests 变成强制路径。 |
| `WP20-C Runtime Setup Consume Bridge` | pass | runtime setup 通过 compatibility-preserving resolved-plan bridge 消费 validated typed requests，并返回稳定 result evidence。 |
| `WP20-D Facade And Binding Public Surface` | pass | facade 与 Python bindings 暴露 `TypedPlatformSpawnResult` 和 `BatchWorldSetupResult.typed_platform_spawn_results`，同时不改变 runtime materialization semantics。 |
| `WP20-E Compatibility And Schema Guard` | pass | architecture/schema/compatibility guards 保持 scenario schema、backend naming 与 type-name compatibility 稳定，并拒绝不受支持的 drift。 |
| `WP20-F Integration And Handoff` | pass | closure lane 集成 A-E evidence，记录 validation 与 residuals，同步 indexes，并且只在实现证据存在后准备验收。 |

## 3. 验证汇总

记录的 closure-pass validation：

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_wp14_boundary_guards.py tests/architecture/test_runtime_facade_layering.py tests/architecture/test_wp20_public_typed_platform_spawn_contract.py tests/architecture/test_wp20_runtime_setup_consume_bridge.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "typed_platform_setup or world_setup or capability or spawn"
cmake --build build-workshop --target ef_py -j2
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP20 --summary
```

观察结果：

- `git diff --check`：通过。
- Architecture batch：`34 passed in 3.05s`。
- Runtime binding DTO surface batch：`26 passed in 0.06s`。
- Runtime facade slice：`4 passed, 16 deselected in 0.27s`。
- `cmake --build build-workshop --target ef_py -j2`：通过，`ef_py` 已构建。
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP20 --summary`：
  通过，且 WP20 验收审查已记录、所需中文辅文已存在。

## 4. Residuals

WP20 有意保留这些 residuals：

- 没有引入 `spawn_platform`。
- 没有强制 scenario JSON、examples 或 Python callers 迁移。
- 任意 capability-bundle materialization 仍然在范围外。
- Backend `RuntimeCapabilities` 仍然与 platform composition semantics 分离。
- Type-name compatibility 继续维持。
- WP21 和 full counterfactual / experiment runtime 仍然是独立路线。

## 5. 下一路线

如果未来需要更广泛的 platform publicization，应从新的 evidence gate
重新起步，并保留 compatibility bridge，而不是重开 WP20。full
counterfactual / experiment runtime 继续路由到 WP21。
