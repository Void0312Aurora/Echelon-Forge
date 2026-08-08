# Environment Substrate G0-L-F Scenario Ingestion Acceptance

状态：`2026-06-06` accepted G0-L-F scenario compiler ingestion for inert
projection setup payloads。本验收只关闭 compiler-ingestion slice；不应用 runtime
setup，也不释放 terrain behavior。

## 已接受范围

已接受：

- `python/scenario/environment_substrate/scenario_ingestion.py` 下的
  `ingest_projection_setup_payloads_into_scenario()`；
- `ScenarioCompiler` 在 scenario import/merge 之后、merged-shape validation 和
  runtime metadata compilation 之前执行 ingestion hook；
- 输入命名空间
  `environment.environment_substrate.projection_setup_payloads`；
- 将已经接受的 G0-L projection setup payload zones 转为 `environment.zones`；
- 从 scenario metadata namespace 移除已消费的 setup payloads；
- 在 `environment.environment_substrate.projection_ingestion_evidence` 下保留
  ingestion evidence；
- 对 contract mismatch、invalid surfaces、duplicate zone names、forbidden
  `world_index`、missing provenance、dropped rich attributes 与 held runtime
  claims fail closed；
- `tests/scenario/test_environment_projection_contracts.py` 下的 focused
  tests。

未接受：

- runtime setup application；
- C++ runtime edits、bindings、DTO changes 或 new world-query ownership；
- generated scenario artifacts；
- movement、passability、route following、LOS、cover、fires、damage、combat、
  weather simulation、hydrodynamics、hydrology effects 或 dynamic mutation。

## 证据矩阵

| Requirement | Evidence | Result |
| --- | --- | --- |
| Compiler ingestion 发生在 layout metadata 编译之前。 | `ScenarioCompiler._compile_from_data()` 与 ingestion test | pass |
| Payloads 严格校验，不落入 `SoftDirt` defaulting。 | scenario ingestion invalid-surface test 与 layout surface assertion | pass |
| Ingestion 是 data-only，不应用 runtime setup。 | ingestion evidence field `no_runtime_setup_application` | pass |
| 已消费 payloads 被移除，provenance evidence 保留。 | scenario ingestion test | pass |
| Runtime behavior 与 held capability claims 继续拒绝。 | rejection tests 与 G0 held-boundary docs | pass |

## 验证

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_projection_contracts.py
# 5 passed
```

已纳入 G0 closure suite：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

## 验收结论

作为最终 G0-L data-ingestion slice 接受。Compiler 现在可以把 already accepted
projection setup payload ingest 到 merged scenario data。Runtime setup application
gate 仍在 G0 closure 之外。
