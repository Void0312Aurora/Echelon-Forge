# Environment Substrate G0-L Projection Setup 验收

状态：`2026-06-06` 已接受 G0-L projection setup payload contract。本验收只覆盖
Python 侧将已经验证过的 `world_zone_definition` projection result 转换成带 evidence
的 inert setup payload。它不 apply runtime setup；scenario compiler ingestion 已由
G0-L-F continuation 单独接受。

## 已接受范围

已接受：

- read-only G0-L-A/B/C diagnostics packets 返回 `pass`；
- `python/scenario/environment_substrate/projection_setup.py` 下的
  `build_world_zone_projection_setup_payload()`；
- deterministic `EnvironmentProjectionSetupPayload` metadata；
- 为每个 projected zone 保留 source manifest/object/catalog/component/profile/provenance
  evidence；
- 当前 `WorldZoneDefinition` compatibility surface 的 strict surface-code admission；
- 对 unknown profiles、invalid surface codes、dropped rich attributes 与 held runtime
  claims fail closed；
- `tests/scenario/test_environment_substrate_projection_setup.py` 下的 focused tests。

未接受：

- runtime setup application；
- C++ runtime edits、bindings、DTO changes 或新的 world-query ownership；
- wind、maritime、hydrology、weather、illumination、dynamic environment、road、
  building、vegetation、LOS、cover 或 derived-product projection；
- movement、passability、route following、fires、damage、combat、weather
  simulation、hydrodynamics、hydrology effects 或 dynamic mutation。

## 证据矩阵

| Requirement | Evidence | Result |
| --- | --- | --- |
| G0-L-A/B/C preflight packets 返回 pass。 | [G0-L cluster](environment_substrate_g0_projection_preflight_cluster_20260606.zh.md) | pass |
| Payload builder 不 apply runtime setup。 | [projection_setup.py](../../../../python/scenario/environment_substrate/projection_setup.py) | pass |
| Payload 保留 projection evidence 与 source IDs。 | [projection setup tests](../../../../tests/scenario/test_environment_substrate_projection_setup.py) | pass |
| Surface mapping 严格，且不使用 implicit `SoftDirt` default。 | projection setup tests | pass |
| Dropped rich attributes 在本切片继续 reject。 | projection setup tests | pass |
| Held runtime claims 继续 reject。 | projection setup tests | pass |

## 验证

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_manifest.py tests/scenario/test_environment_substrate_projection.py tests/scenario/test_environment_substrate_generator_catalog.py tests/scenario/test_environment_substrate_projection_setup.py
# 27 passed
```

## 验收决定

作为第一版 G0-L implementation slice 接受：仅 projection setup payload contract。
下一条 G0-L continuation 已作为 strict scenario-compiler ingestion 单独接受，并命名了
有限 write set 与 focused tests。

## 残余边界

- projection payloads 的 scenario compiler ingestion 已在
  [G0-L-F ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md)
  中单独接受。
- runtime setup application 继续 held。
- G0-M metadata-only derived products 已单独接受。
- Ground route movement 仍由单独 G6-D3/G6-F release path 管辖。
- movement、LOS、cover、fires、damage、combat、weather simulation、
  hydrodynamics、hydrology effects 与 dynamic mutation 继续 held。
