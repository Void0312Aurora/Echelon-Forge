# Environment Substrate G0-M Derived Products Acceptance

状态：`2026-06-06` accepted G0-M first derived-product contract slice for
metadata-only environment indexes。本验收不释放 movement、LOS、cover 或 runtime
consumers。

## 已接受范围

已接受：

- `python/scenario/environment_substrate/derived_products.py` 下的
  `EnvironmentDerivedProductRequest`、`EnvironmentDerivedProduct`、
  `EnvironmentDerivedProductBundle` 与 `EnvironmentDerivedProductResult`；
- 对 validated `EnvironmentManifest` inputs 的
  `build_environment_derived_products()`；
- `surface_zone_index`，从已接受的 `world_zone_definition` projection profile
  派生，并要求 strict no-dropped-attribute evidence；
- `occlusion_candidate_index`，对 `occlusion`、`structure` 与 `vegetation`
  components 建立 metadata-only candidate index；
- bundle metadata 显式设置 `no_runtime_consumer_release` 与
  `no_held_capability_release`；
- 对 unknown products、held product kinds、held capability claims、missing request
  IDs、missing product kinds，以及 surface-zone indexes 的 missing projection
  profile IDs fail closed；
- `tests/scenario/test_environment_substrate_contracts.py` 下的 focused
  tests。

未接受：

- road graph、movement-cost grid、passability mask、LOS occlusion index、
  cover/concealment index 或 tactical-area graph；
- accepted metadata products 的 runtime consumers；
- movement、passability、route following、LOS behavior、cover behavior、fires、
  damage、combat、weather simulation、hydrodynamics、hydrology effects 或 dynamic
  mutation。

## 证据矩阵

| Requirement | Evidence | Result |
| --- | --- | --- |
| Derived product requests deterministic 且 metadata-only。 | derived products deterministic bundle test | pass |
| Surface-zone index 复用 accepted projection evidence。 | `surface_zone_index` test | pass |
| Occlusion candidates 被索引，但不释放 LOS/cover。 | `occlusion_candidate_index` test 与 evidence flags | pass |
| Held product kinds 被拒绝。 | `passability_mask` rejection test | pass |
| Held capability claims 被拒绝。 | `line_of_sight` rejection test | pass |
| Surface-zone index 要求显式 projection profile。 | missing-profile rejection test | pass |

## 验证

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py
# 4 passed
```

已纳入 G0 closure suite：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

## 验收结论

作为 G0-M metadata/index contract closure 接受。这些 products 是 future gates 可在
单独 release vote 后消费的 contract artifacts；它们本身不启用 movement、LOS、cover、
fires、damage 或 combat behavior。
