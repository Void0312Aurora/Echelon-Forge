# WP14-A Capability Bundle Contract

状态：`2026-05-21` planned / first-wave dispatch candidate。

语言版本：

- 英文主文：[wp14_capability_bundle_contract_cluster_20260521.md](wp14_capability_bundle_contract_cluster_20260521.md)
- 中文辅文：`wp14_capability_bundle_contract_cluster_20260521.zh.md`

输入：

- [WP14 capability composition](capability_composition_wp14_20260521.zh.md)
- [仿真系统架构设计](../../../plan/architecture/simulation_system_architecture_design.zh.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.zh.md)
- Current `src/runtime/contracts/*`
- Current `src/runtime/facade/runtime_facade_types.h`

## 1. 目的

`WP14-A` 创建后续 streams 共享的平台能力词汇。它必须把 `Capability`、
`CapabilityBundle` 与 resolved-plan evidence 定义为 platform setup concepts，而不是
backend/fidelity `RuntimeCapabilities`。

## 2. 范围

范围内：

- mobility、sensing、communication、launching、survivability、command 与 doctrine
  的 capability family vocabulary；
- typed bundle/template/request/evidence structs 或 schema；
- platform capabilities 与 backend runtime capabilities 的命名分离；
- 证明 required fields 与 family labels 的 architecture tests。

范围外：

- `WP14-B` 所属 content/factory lowering implementation；
- `WP14-C` 所属 kernel/world-batch bridge；
- public `spawn_platform` API promotion；
- backend/fidelity capability projection。

## 3. 候选实现缝

编辑前检查：

- `src/runtime/contracts/world_batch_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/contracts/backend_profile_contracts.h`
- `src/runtime/contracts/fidelity_profile_contracts.h`
- `tests/architecture/test_runtime_facade_layering.py`

首选方式：

- 新增 platform-focused contract header，而不是扩展 `RuntimeCapabilities`；
- 保持 capability family labels 稳定、可被字符串测试；
- 为 B/C 提供足够 evidence fields，用于说明 `type_name` 如何 resolve；
- focused tests 拒绝空 family/id/evidence fields。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Naming separation | Platform capability vocabulary 不复用 backend/fidelity capability projection fields。 |
| Required fields | Capability entries 携带 family、id、source/template、materialization target 与 evidence refs。 |
| Deterministic shape | Bundle ordering 与 resolved-plan evidence 足够稳定，可测试。 |
| Fail-closed validation | 缺少 family、id 或 evidence 时拒绝 contract fixture。 |

## 5. 验收测试

最低测试：

- architecture test 枚举 supported capability families；
- contract validation 拒绝缺失 family/id/source/evidence fields；
- 测试断言没有给 `RuntimeCapabilities` 添加 platform-family fields；
- bundle/resolved-plan fixture 具有 deterministic ordering 与 evidence refs。

建议命令：

```powershell
git diff --check
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp14_capability_bundle_contracts.py
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
```

## 6. 交接契约

返回：

- touched contract files；
- capability family vocabulary；
- validation helper names；
- added or updated tests；
- exact commands and outcomes；
- 给 `WP14-B`、`WP14-C` 或 `WP14-D` 的 blockers。
