# Environment Substrate G0 Static Manifest Contract 验收

状态：`2026-06-05` accepted G0-J static manifest contract substage。本验收只覆盖
Python-side shared environment substrate contracts 与 focused tests。

## 已接受范围

已接受：

- shared package namespace `python/scenario/environment_substrate/`；
- default branch、component 与 layer registries；
- static `EnvironmentManifest` / `EnvironmentObject` data structures；
- deterministic static environment fixture；
- fail-closed manifest validation；
- contract-only `world_zone_definition` compatibility projection evidence；
- `tests/scenario/` 下的 focused tests。

未接受：

- generator plugins；
- scenario compiler/runtime projection integration；
- C++ terrain/environment runtime ownership；
- movement、passability、route following、LOS、cover、fires、damage、combat、
  weather simulation、hydrodynamics、hydrology effects 或 dynamic environment
  mutation。

## 证据矩阵

| 要求 | 证据 | 结果 |
| --- | --- | --- |
| Shared namespace，不是 ground-private package。 | [package](../../../../python/scenario/environment_substrate) | pass |
| default registry 包含 terrain 与 non-terrain environment branches。 | [components.py](../../../../python/scenario/environment_substrate/components.py)、manifest tests | pass |
| static manifest deterministic serialize。 | [test_environment_substrate_contracts.py](../../../../tests/scenario/test_environment_substrate_contracts.py) | pass |
| validators 拒绝 missing branch、missing component attributes、untyped behavior properties 与 held capability claims。 | [validation.py](../../../../python/scenario/environment_substrate/validation.py)、manifest tests | pass |
| projection 拒绝 unsupported rich features，而不是 silent default。 | [projection.py](../../../../python/scenario/environment_substrate/projection.py)、projection tests | pass |
| 不释放 runtime behavior。 | G0-J scope 与 task-cluster boundary | pass |

## 验证

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py
# 10 passed
```

## 验收决策

作为 G0-J static manifest contract 接受。后续 environment-substrate 子阶段应为
G0-K generator/catalog work，且必须先定义 deterministic generator requests、
tile/seed partitioning、catalog admission、fixture output 与 validation evidence，
不得声明 runtime release。

## 残余边界

G0-J 原本关于 G0-K 的 residual 已由已接受的
[G0-K generator/catalog contract](environment_substrate_g0_generator_catalog_20260605.zh.md)
取代。G0-J 原本关于 G0-L/G0-M 的 residual 已由 accepted G0-L projection setup plus
compiler data ingestion 与 accepted G0-M metadata-only derived products 取代。
Runtime setup application、runtime consumers、movement、LOS、cover、fires、damage、
combat、weather simulation、hydrodynamics、hydrology effects 和 dynamic environment
mutation 继续 held。
