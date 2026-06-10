# Environment Substrate G0-L Projection Preflight 任务簇

状态：`2026-06-06`，面向
[environment_substrate_g0_projection_preflight_20260606.zh.md](environment_substrate_g0_projection_preflight_20260606.zh.md)
的 accepted finite G0-L projection setup and compiler ingestion task-cluster
plan。

## 边界决策

G0-L 可以检查 projection integration paths、定义 gates，实现 Python-only inert
projection setup payload contract，并将 accepted payloads 接入 scenario compiler data
ingestion。它不得 apply world setup，不得编辑 C++ runtime，不得把 generated manifests
投进 checked-in scenarios，也不得声明 movement、LOS、cover、fires、damage、combat、
weather simulation、hydrodynamics、hydrology effects、dynamic mutation 或 runtime
derived-product consumers。

## 有限任务簇

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `G0-L-A Scenario Compiler Surface Preflight` | Huygens read-only diagnostics | inherited parent / xhigh | 检查 Python scenario compiler/setup surfaces，并识别 projected `world_zone_definition` payloads 是否有 maintained ingestion path。 | none；仅 diagnostics packet | 不编辑、不 apply runtime setup、不新增 scenario files。 | worker packet 引用 inspected Python files，并命名 accepted candidates 或 blockers。 | packet 返回 `pass`。 | 可与 G0-L-B/C 并行；依赖 accepted G0-K。 | 1 | pass |
| `G0-L-B Runtime Setup Surface Preflight` | Pascal read-only diagnostics | inherited parent / xhigh | 检查 C++ batch/world setup contracts 对 `WorldZoneDefinition` 的兼容性与 runtime side effects。 | none；仅 diagnostics packet | 不编辑 C++，不新增 runtime terrain behavior，不做 derived products。 | worker packet 引用 inspected C++ files，并命名 accepted candidates 或 blockers。 | packet 返回 `pass`。 | 可与 G0-L-A/C 并行；依赖 accepted G0-K。 | 1 | pass |
| `G0-L-C Test And Validator Gate Preflight` | Carson read-only diagnostics | inherited parent / xhigh | 定义 G0-L implementation 前所需 focused tests、reason codes 与 fail-closed gates。 | none；仅 diagnostics packet | 不实现，不接 projection integration。 | worker packet 命名 tests、assertions、rejection reason codes 与 held capability risks。 | packet 返回 `pass`。 | 可与 G0-L-A/B 并行；依赖 accepted G0-K。 | 1 | pass |
| `G0-L-D Integration Decision` | main thread integration | n/a | 整合 A/B/C packets，并决定是否能打开有限 G0-L implementation write set。 | G0 package docs 加 ground 父 README/progress/queue docs | 不做 runtime application；不声明 runtime。 | 本地 packet review 加 touched docs 的 `git diff --check`。 | 接受有限 Python-only projection setup payload write set；compiler ingestion 通过 G0-L-F 续接。 | G0-L-A/B/C 返回后串行。 | 1 | pass |
| `G0-L-E Projection Setup Payload Contract` | main thread implementation | n/a | 为已接受 `world_zone_definition` projections 实现 inert payload/evidence conversion。 | `python/scenario/environment_substrate/projection_setup.py`、package exports、focused tests | 不做 scenario compiler ingestion、不 apply runtime setup、不编辑 C++。 | focused pytest 覆盖 deterministic payload、evidence preservation、strict surface codes、dropped attributes 与 held claims。 | payload contract 只作为 Python setup evidence 接受。 | 依赖 G0-L-D。 | 1 | accepted |
| `G0-L-F Scenario Compiler Ingestion` | main-thread integration / implementation | n/a | 将 accepted projection setup payloads 接入 scenario compiler data ingestion。 | `python/scenario/environment_substrate/scenario_ingestion.py`、`python/scenario/environment_substrate/__init__.py`、`python/scenario/compiler/service.py`、`tests/scenario/test_environment_projection_contracts.py`、G0 package docs | 不做 runtime setup application、不编辑 C++、不新增 generated scenario artifacts、不释放 movement、LOS、cover、fires、damage、combat 或 runtime derived-product consumers。 | focused ingestion pytest 加 G0 closure suite。 | strict ingestion accepted、payloads fail closed、runtime setup remains held。 | 依赖 G0-L-E。 | 1 | accepted |

## Worker Packet 要求

每个 worker 必须返回：

```md
status: pass | partial | blocked | failed
touched files: none expected
files inspected:
commands/outcomes:
accepted projection candidates:
fail-closed blockers:
held capability risks:
integration notes:
```

G0-L-C 可以用 `required tests` 与 `fail-closed reason codes` 替代
`accepted projection candidates`。

## 验证计划

本 dispatch 的文档验证：

```bash
git diff --check -- docs/task/ground/environment_substrate_g0_architecture docs/task/ground/README.md docs/task/ground/README.zh.md docs/task/ground/ground_current_progress_20260524.md docs/task/ground/ground_current_progress_20260524.zh.md docs/task/ground/ground_subagent_dispatch_queue_20260521.md docs/task/ground/ground_subagent_dispatch_queue_20260521.zh.md
```

当前 G0-J/G0-K/G0-L/G0-M focused validation：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

## 验收标准

G0-L projection 接受至 scenario compiler ingestion，因为：

- 三个 read-only packets 均返回 `pass`；
- 命名有限 Python-only write set，且与 derived products 和 movement/LOS/combat runtime
  behavior 分离；
- accepted projection targets 限于 compatibility setup fields；
- compiler ingestion 是 strict data ingestion，runtime setup 继续 held；
- payload 与 ingestion contracts 的 focused tests 与 fail-closed reason codes 已实现。

## Residual Map

- Runtime setup application 继续 held。
- G0-M metadata-only derived products 已单独接受。
- Ground movement/LOS/cover/fires/damage/combat 继续受单独 release gates 约束。
