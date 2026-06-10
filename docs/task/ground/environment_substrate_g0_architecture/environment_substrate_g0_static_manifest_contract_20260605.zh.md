# Environment Substrate G0 Static Manifest Contract

状态：`2026-06-05` accepted shared environment substrate 的 G0-J static
manifest contract 与 validator implementation substage。这是 Environment
Substrate G0 的组成部分，不是独立 G1 phase，也不是 ground-owned runtime
infrastructure。

语言：

- 英文主文：
  [environment_substrate_g0_static_manifest_contract_20260605.md](environment_substrate_g0_static_manifest_contract_20260605.md)
- 中文配套：
  `environment_substrate_g0_static_manifest_contract_20260605.zh.md`

输入：

- G0 package README：[README.zh.md](README.zh.md)
- G0 验收：
  [environment_substrate_g0_acceptance_20260605.zh.md](environment_substrate_g0_acceptance_20260605.zh.md)
- Architecture plan：
  [environment_substrate_g0_architecture_plan_20260605.zh.md](environment_substrate_g0_architecture_plan_20260605.zh.md)

## 目的

`G0-J` 将已接受的 G0 设计变成最小可测试的 static contract。它新增一个 shared
Python package，用于 environment manifest 数据结构、默认 branch/component/layer
registries、fail-closed manifest validation、deterministic fixture，以及
contract-level compatibility projection。

本切片刻意停在 generator plugins、scenario compiler integration、C++ runtime
ownership、movement、LOS、cover、fires、damage、combat、weather simulation、
hydrodynamics、hydrology effects 与 dynamic environment mutation 之前。

## 当前状态

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| G0 architecture | accepted | [G0 acceptance](environment_substrate_g0_acceptance_20260605.zh.md) | 仅 architecture evidence。 |
| Static manifest schema | accepted | [manifest.py](../../../../python/scenario/environment_substrate/manifest.py) | 只做 static data structures。 |
| Registries | accepted | [components.py](../../../../python/scenario/environment_substrate/components.py) | default descriptors；无 runtime consumers。 |
| Validators | accepted | [validation.py](../../../../python/scenario/environment_substrate/validation.py) | 仅 fail-closed contract checks。 |
| Compatibility projection contract | accepted | [projection.py](../../../../python/scenario/environment_substrate/projection.py) | 输出 contract evidence；不 apply runtime setup。 |
| Generator/runtime/derived products | outside G0-J | G0 residuals、本文与后续 closure records | G0-K/G0-L/G0-M 已单独接受；runtime setup 与 consumers 继续 held。 |

## 范围

范围内：

- 新增 `python/scenario/environment_substrate/` 作为 shared package namespace。
- 定义 `EnvironmentManifest`、`EnvironmentObject`、branch membership、components、
  geometry、generation metadata 与 projection profiles。
- 定义 terrain、atmosphere/weather、wind、illumination、maritime/ocean、hydrology
  与 dynamic environment branches 的默认 registries。
- 验证 manifest structure、required component attributes、branch/layer/profile
  references、held capability claims 与 untyped behavior properties。
- 提供一个 deterministic static fixture。
- 提供 contract-only `world_zone_definition` projection，记录 evidence 并拒绝
  unsupported rich features。

范围外：

- Terrain generation 或 generator plugin implementation。
- Scenario compiler/runtime integration。
- C++ environment runtime ownership。
- movement、passability、route following、LOS、cover、fires、damage、combat、
  weather simulation、hydrodynamics、hydrology effects 或 mutable environment state。

## 阶段计划

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `G0-J-A Static Schema` | 新增 shared manifest/registry data structures。 | G0 architecture accepted。 | Static dataclasses 可导入并 deterministic serialize。 | accepted |
| `G0-J-B Validators` | 新增 fail-closed manifest validation。 | Static schema present。 | 缺 branch、缺 attribute、untyped behavior 与 held claims 均 reject。 | accepted |
| `G0-J-C Projection Contract` | 新增 contract-only compatibility projection。 | Validators present。 | Zone projection 输出 evidence，并拒绝 unsupported rich features。 | accepted |
| `G0-J-D Documentation Sync` | 记录 acceptance 与 residuals。 | Tests pass。 | 父级和包内 docs 在 G0-J closeout 时标记 G0-J accepted 与 G0-K held；当前 G0-K acceptance 已取代该 residual。 | accepted |

## 任务簇

- Task cluster plan：
  [environment_substrate_g0_static_manifest_contract_cluster_20260605.zh.md](environment_substrate_g0_static_manifest_contract_cluster_20260605.zh.md)
- Acceptance：
  [environment_substrate_g0_static_manifest_contract_acceptance_20260605.zh.md](environment_substrate_g0_static_manifest_contract_acceptance_20260605.zh.md)

## 输出与证据

- Shared package：
  [python/scenario/environment_substrate](../../../../python/scenario/environment_substrate)
- Focused tests：
  [test_environment_substrate_contracts.py](../../../../tests/scenario/test_environment_substrate_contracts.py)、
  [test_environment_projection_contracts.py](../../../../tests/scenario/test_environment_projection_contracts.py)
- 验证：
  `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py`
  返回 `10 passed`。

## 验收门

本 G0 子阶段已接受，因为：

- package namespace 是 shared，不属于某一 service/domain；
- branch registry 包含 terrain 加 atmosphere/weather、wind、illumination、
  maritime/ocean、hydrology 与 dynamic environment branches；
- validators 对 missing registries、missing required component attributes、
  untyped behavior properties、held capability claims 与 unsupported projection
  targets fail closed；
- projection tests 证明 unsupported rich features 不会默默落入当前 loose setup defaults；
- 不释放 runtime behavior。

## 残余与下一步

- G0-J 原本 held 的 `G0-K` generator/catalog work 已由已接受的
  [G0-K generator/catalog contract](environment_substrate_g0_generator_catalog_20260605.zh.md)
  取代；该范围只覆盖 request contracts、deterministic tiling、catalogs、seed evidence
  与 in-memory fixture generation。
- G0-J 原本 held 的 G0-L projection integration 已由 accepted G0-L projection setup
  plus compiler data ingestion 取代；runtime setup application 继续 held。
- G0-J 原本 held 的 G0-M derived products 已由 accepted metadata-only
  `surface_zone_index` 与 `occlusion_candidate_index` products 取代。Runtime
  consumers 与 road graph、movement-cost grid、passability mask、runtime LOS/cover、
  weather attenuation field、maritime state field 等更丰富 products 继续 held。
- Ground route movement 仍由单独 G6-D3/G6-F-style release vote 管辖。

## Archive

本文是当前 accepted G0 evidence record。被取代的记录只有在 maintained replacement
README/status 或 acceptance surface 指向它们后，才移动到本地 `archive/`。
