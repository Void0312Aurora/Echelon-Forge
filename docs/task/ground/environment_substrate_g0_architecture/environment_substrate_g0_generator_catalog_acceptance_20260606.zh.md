# Environment Substrate G0-K Generator Catalog 验收

状态：`2026-06-06` 已接受 G0-K generator/catalog contract 子阶段。本验收只覆盖
Python 侧 deterministic request、tile、seed、catalog admission 与 in-memory
generated manifest fixture 行为。

## 已接受范围

已接受：

- `EnvironmentGeneratorRequest`、`EnvironmentGeneratorEvidenceRef` 与
  `EnvironmentTileScheme` request/tile contract data；
- deterministic seed material 所需的 canonical environment metadata
  serialization；
- 按 request metadata、stage、tile、catalog 与 local key 作用域派生 deterministic
  seed；
- 覆盖 terrain 与 non-terrain environment branches 的 default environment
  catalog descriptors；
- fail-closed catalog descriptor 与 catalog admission validation；
- deterministic in-memory generated `EnvironmentManifest` fixture output；
- `tests/scenario/test_environment_substrate_contracts.py` 下的 focused
  tests；
- 已返回 G0-K-A/B/C worker packets 的文档集成。

未接受：

- scenario compiler/runtime projection integration；
- checked-in generated scenario/environment data artifacts；
- C++ terrain 或 environment runtime ownership；
- road graph、movement-cost grid、passability mask、LOS index、cover index 或
  tactical-area graph 等 derived products；
- movement、passability、route following、LOS、cover、fires、damage、combat、
  weather simulation、hydrodynamics、hydrology effects 或 dynamic environment
  mutation。

## 证据矩阵

| Requirement | Evidence | Result |
| --- | --- | --- |
| G0-K-A/B/C worker packets 已集成。 | [cluster plan](environment_substrate_g0_generator_catalog_cluster_20260605.zh.md) | pass |
| Request、tile、seed 与 provenance contract 可验证并 fail closed。 | [generator.py](../../../../python/scenario/environment_substrate/generator.py)、generator/catalog tests | pass |
| Catalog descriptors 是 recipes，不是 feature-label schema roots。 | [catalog.py](../../../../python/scenario/environment_substrate/catalog.py)、generator/catalog tests | pass |
| Catalog admission 拒绝 unknown refs、branch mismatch、missing components 与 unsupported roots。 | [catalog.py](../../../../python/scenario/environment_substrate/catalog.py)、generator/catalog tests | pass |
| Generated fixture deterministic 且只存在于内存。 | [test_environment_substrate_contracts.py](../../../../tests/scenario/test_environment_substrate_contracts.py) | pass |
| G0-J static manifest regressions 仍通过。 | manifest/projection tests | pass |
| 未释放 runtime behavior。 | G0-K scope 与 residual boundary | pass |

## 验证

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py
# 22 passed
```

## 验收决定

作为 G0-K generator/catalog contract 接受。已接受实现只新增
`python/scenario/environment_substrate/` 下的 shared Python contract surfaces 与
`tests/scenario/` 下的 focused tests。它可以作为后续 G0-L projection preflight 的证据底座，
但自身不投影到 runtime setup 或 scenario compiler outputs。

## 残余边界

- G0-K 历史 residual 中的 G0-L 已由 accepted G0-L projection setup plus compiler
  data ingestion 取代；runtime setup application 继续 held。
- G0-K 历史 residual 中的 G0-M 已由 accepted metadata-only derived products
  取代；runtime consumers 继续 held。
- Ground route movement 仍走单独 G6-D3/G6-F release path。
- movement、LOS、cover、fires、damage、combat、weather simulation、
  hydrodynamics、hydrology effects 与 dynamic environment mutation 对所有 domain
  都继续 held。
