# Environment Substrate G0 Closure Acceptance

状态：`2026-06-06` accepted complete G0 closure for the shared environment
substrate design-and-implementation line。

## 闭合结论

G0 作为 shared environment-substrate contract baseline 闭合。已接受范围现在包括：

- G0-A branch-aware、component-based environment manifests 的
  architecture/design records；
- G0-J static manifest contract、default registries、validators、deterministic
  fixture 与 projection contract tests；
- G0-K generator/catalog request、tile、seed、provenance、catalog admission 与
  deterministic in-memory generated manifest fixture；
- G0-L projection setup payload，以及将 inert payloads 严格 ingest 到 merged
  `environment.zones` 的 scenario compiler ingestion；
- G0-M first metadata-only derived-product indexes。

此闭合不再留下 G0-internal held slice。剩余 held items 是 downstream release gates，
不是未完成的 G0 工作。

## 明确未释放边界

G0 仍不释放：

- runtime setup application；
- scenario-producing terrain generator plugins 或 checked-in generated terrain
  artifacts；
- road graph、movement-cost grid、passability mask、runtime LOS occlusion、
  cover/concealment runtime products、tactical-area runtime graph；
- route following、speed updates、terrain-aware movement、sensing、fires、
  damage、combat、suppression、reward/termination binding、observation/export；
- weather simulation、hydrodynamics、hydrology effects 或 dynamic environment
  mutation。

## 证据

| Slice | Evidence | Result |
| --- | --- | --- |
| Architecture/design | [architecture plan](environment_substrate_g0_architecture_plan_20260605.zh.md)、[terrain system architecture](environment_substrate_g0_terrain_system_architecture_20260605.zh.md) | accepted |
| G0-J static manifest | [static manifest acceptance](environment_substrate_g0_static_manifest_contract_acceptance_20260605.zh.md) | accepted |
| G0-K generator/catalog | [generator/catalog acceptance](environment_substrate_g0_generator_catalog_acceptance_20260606.zh.md) | accepted |
| G0-L setup payload | [projection setup acceptance](environment_substrate_g0_projection_setup_acceptance_20260606.zh.md) | accepted |
| G0-L-F scenario ingestion | [scenario ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md) | accepted |
| G0-M derived products | [derived products acceptance](environment_substrate_g0_derived_products_acceptance_20260606.zh.md) | accepted |

## 验证

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

闭合文档验证：

```bash
git diff --check -- docs/systems/environment/reviews/environment_substrate_g0_closure_20260606 docs/domains/ground/README.md docs/domains/ground/README.zh.md docs/systems/environment/README.md docs/systems/environment/README.zh.md docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.md docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.zh.md python/scenario/environment_substrate python/scenario/compiler tests/scenario
# clean
```

## 后续工作姿态

后续工作应开启单独 release package，而不是继续扩展 G0：

- runtime setup application；
- derived products 的 runtime consumers；
- route movement 与 terrain-aware movement gates；
- LOS/cover/fires/damage/combat gates；
- large-area environment generation 与 generated scenario artifacts。
