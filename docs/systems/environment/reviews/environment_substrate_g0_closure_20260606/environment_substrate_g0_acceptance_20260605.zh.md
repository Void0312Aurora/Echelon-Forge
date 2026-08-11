# Environment Substrate G0 验收

状态：`2026-06-05` accepted shared environment substrate 的 G0 design-and-
implementation boundary，并在 `2026-06-06` 更新到 complete G0 closure。本验收现
覆盖 architecture/design records、G0-J static manifest contract implementation、
G0-K generator/catalog contracts、G0-L projection setup 加 strict scenario
compiler ingestion，以及 G0-M metadata-only derived products。不释放 runtime setup
application、movement、LOS、cover、fires、damage、combat、weather simulation、
hydrodynamics、hydrology effects 或 dynamic environment mutation。

## 已接受范围

G0 作为 component-based、branch-aware、shared environment substrate 的有限设计与
实现线被接受。已接受的根对象是 `EnvironmentManifest` / `EnvironmentObject`；
terrain 是第一条被细化的 branch，而 atmosphere/weather、wind、illumination、
maritime/ocean、hydrology 与 dynamic environment 继续作为同一 manifest root 下的
merge targets。已接受 implementation substage 包括 G0-J static manifests /
validators、G0-K generator/catalog contracts、G0-L projection setup and compiler
data ingestion，以及 G0-M metadata-only derived products。

## 标准复核

| 标准 | 证据 | 结果 |
| --- | --- | --- |
| component registry、layer semantics、branch registry、manifest shape、validators、projection plan 与 consumer gates 已命名。 | [architecture plan](environment_substrate_g0_architecture_plan_20260605.zh.md) | pass |
| 当前 `src` terrain/query primitives 被表述为 shared primitives，而不是完整 terrain runtime。 | [source inventory](environment_substrate_g0_source_inventory_20260605.zh.md) | pass |
| terrain plan 将 shared layered/tiled data 与 compatibility projection/query consumers 分离。 | [terrain system architecture](environment_substrate_g0_terrain_system_architecture_20260605.zh.md) | pass |
| 当前 Ground 所有者、环境边界和 closure 索引保持互链。 | [Ground 所有者](../../../../domains/ground/README.zh.md)、[环境所有者](../../../../systems/environment/README.zh.md)、[closure 索引](README.zh.md) | pass |
| branch-expansion diagnostics 已被整合或本地拒绝。 | [subagent dispatch](environment_substrate_g0_subagent_dispatch_20260605.zh.md)、[task clusters](environment_substrate_g0_task_clusters_20260605.zh.md) | pass |
| G0-J static manifest implementation 有限且已测试。 | [G0-J static contract](environment_substrate_g0_static_manifest_contract_20260605.zh.md)、[G0-J acceptance](environment_substrate_g0_static_manifest_contract_acceptance_20260605.zh.md) | pass |
| G0-K generator/catalog contract 有限且已测试。 | [G0-K record](environment_substrate_g0_generator_catalog_20260605.zh.md)、[G0-K acceptance](environment_substrate_g0_generator_catalog_acceptance_20260606.zh.md) | pass |
| G0-L projection setup 加 scenario compiler ingestion 有限且已测试。 | [G0-L setup acceptance](environment_substrate_g0_projection_setup_acceptance_20260606.zh.md)、[G0-L-F ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md) | pass |
| G0-M derived products 是 metadata-only 且已测试。 | [G0-M acceptance](environment_substrate_g0_derived_products_acceptance_20260606.zh.md) | pass |
| G0 closure 不再留下 internal held slice，同时保留 downstream held gates。 | [G0 closure acceptance](environment_substrate_g0_closure_acceptance_20260606.zh.md) | pass |
| 不声明或释放 runtime setup application、movement、LOS、cover、fires、damage 或 combat capability。 | README scope、task clusters residual map、source inventory held boundaries | pass |

## 验证

Documentation validation：

```bash
git diff --check -- docs/systems/environment/reviews/environment_substrate_g0_closure_20260606 docs/domains/ground/README.md docs/domains/ground/README.zh.md docs/systems/environment/README.md docs/systems/environment/README.zh.md docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.md docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.zh.md
```

G0-J static contract implementation 的代码验证：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py
# 10 passed
```

G0-K generator/catalog continuation 的代码验证：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py
# 22 passed
```

G0 closure 的代码验证：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

## 继续决策

G0 当前包含已接受的 G0-J static manifest contract lane、G0-K generator/catalog
contract lane、G0-L projection setup plus compiler ingestion lane，以及 G0-M
metadata-only derived-product lane。已接受写入范围仍是
`python/scenario/environment_substrate/` 下的 shared `environment_substrate`
infrastructure、`python/scenario/compiler/service.py` 中的 strict compiler
data-ingestion hook，以及 focused `tests/scenario/` contract tests。G0 已闭合；
未来 runtime work 必须开启单独 release package。

## 继续 Held 的边界

以下能力在本次验收后作为 downstream gates 继续 held，而不是未完成的 G0 工作：

- 超出已接受 G0-K in-memory fixture 的 runtime 或 scenario-producing terrain
  generator plugins 和大面积 generation；
- runtime setup application 与 metadata products 的 runtime consumers；
- movement、passability、route following、LOS、cover、fires、damage、combat 与
  observation/export；
- weather simulation、hydrodynamics、hydrology effects 与 dynamic environment
  mutation；
- 任何把 wind 或 maritime setup values 解释为 domain behavior release 的声明。
