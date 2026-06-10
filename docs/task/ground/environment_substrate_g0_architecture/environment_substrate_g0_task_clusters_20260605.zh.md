# Environment Substrate G0 任务簇

状态：`2026-06-05` 面向 [README.zh.md](README.zh.md) 的 accepted 有限 G0
architecture/design substage，branch-expansion diagnostics 已整合，并在
`2026-06-06` 更新到 complete G0 closure。G0 是整条 design-and-implementation
line；本文现在索引 architecture clusters 以及已接受 G0-J/K/L/M implementation
substages。

## 边界

本任务簇设计 environment-substrate architecture 和 accepted implementation map。
它现在记录已接受的 static manifests、deterministic generator/catalog contracts、
inert projection setup plus compiler data ingestion，以及 metadata-only derived
products。它不实现 runtime setup application、movement、LOS、cover、fires、damage
或 combat behavior。

支撑记录：

- Source inventory：
  [environment_substrate_g0_source_inventory_20260605.zh.md](environment_substrate_g0_source_inventory_20260605.zh.md)
- Architecture plan：
  [environment_substrate_g0_architecture_plan_20260605.zh.md](environment_substrate_g0_architecture_plan_20260605.zh.md)
- Terrain system architecture：
  [environment_substrate_g0_terrain_system_architecture_20260605.zh.md](environment_substrate_g0_terrain_system_architecture_20260605.zh.md)
- Subagent diagnostics：
  [environment_substrate_g0_subagent_dispatch_20260605.zh.md](environment_substrate_g0_subagent_dispatch_20260605.zh.md)

## 有限任务簇

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `G0-A Source Inventory` | main thread / diagnostics | n/a | 清点当前 C++ environment model、zone/world setup、scenario compiler/runtime setup 与 ground task boundaries。 | `environment_substrate_g0_source_inventory_20260605*.md` | 不写代码，不做 generator，不声明 runtime capability。 | 阅读被引用文件；task docs 的 `git diff --check`。 | Source inventory 记录现有机制和它不证明什么。 | 无依赖，可先于 architecture clusters。 | 1 | pass |
| `G0-B Ontology And Component Registry` | main thread | n/a | 定义 generic `EnvironmentObject`、branch registry、component registry、开放 layer-stack semantics、catalog boundary 与按 realism grade 的 capability requirements。 | `environment_substrate_g0_architecture_plan_20260605*.md`、README sync | 不把 road/forest/building/weather/wind/sea-state 写成 hardcoded schema roots。 | 对照 source inventory 和用户提出的 extensibility 要求做 architecture review。 | Components 与 branches 可扩展；feature labels 是由 components 组合的 catalog entries。 | 依赖 `G0-A`；与 `G0-C` 串行编辑同一计划。 | 1 | pass |
| `G0-C Manifest, Projection, Validators` | main thread | n/a | 定义 manifest shape、validator classes、到 `WorldZoneDefinition` 的 lossy projection boundary 与 derived-product placeholders。 | `environment_substrate_g0_architecture_plan_20260605*.md`、README sync | 不实现 manifest parser、projection code 或 derived product。 | projection 与 validator sections 对 unsupported features 明确 fail closed。 | Projection 明确是 lossy 且只服务 current-runtime compatibility；rich manifest 仍是后续 gates 的权威底座。 | 依赖 `G0-A`；与 `G0-B` 串行编辑同一计划。 | 1 | pass |
| `G0-E Terrain System Architecture` | main thread plus diagnostics workers | inherited parent / read-only diagnostics | 分析当前地形基础，并定义 shared、layered/tiled terrain-system architecture、generator boundaries、projection profiles 与 derived-product gates。 | `environment_substrate_g0_terrain_system_architecture_20260605*.md`、`environment_substrate_g0_subagent_dispatch_20260605*.md`、README/task-cluster sync | 不实现 terrain generator，不做 C++ domain runtime，不释放 movement/LOS/cover/fires/damage/combat，不接受 single-domain terrain ownership。 | C++ 与 Python diagnostics 返回 `pass`；本地 evidence 记录当前 setup limitations 和 held capabilities。 | Terrain system 将当前 C++/Python surfaces 保持为 compatibility/query consumers，并在其上定义 shared manifest-first structure。 | 依赖 `G0-A`；diagnostics 可并行，integration 串行。 | 1 | pass |
| `G0-F Non-Terrain Environment Branch Inventory` | read-only diagnostics worker | inherited parent / xhigh | 清点当前 C++ 与 Python setup surfaces 中已有 atmosphere/weather、wind、illumination/sun、maritime/ocean、hydrology 与 dynamic-environment 线索。 | none；仅 diagnostics packet | 不编辑文件，不新增 schema，不声明 runtime capability，不接受 terrain-only ownership。 | worker packet 引用 inspected files，并映射当前 surfaces 的 branch implications 与 gaps。 | 返回 packet 说明今天已有什么、哪些只是 compatibility setup、哪些必须继续 held。 | 可与 `G0-G`、`G0-H` 并行；依赖当前 branch-registry draft。 | 1 | pass |
| `G0-G Branch Ontology And Component Gap Review` | read-only diagnostics worker | inherited parent / xhigh | 审查 branch registry 与 component model 是否支持 cross-branch environment objects，并识别缺失的 branch/component/catalog rules。 | none；仅 diagnostics packet | 不编辑文件，不做 generator，不释放 branch-specific runtime behavior，不替代当前 docs authority。 | worker packet 审查 G0 architecture docs，并返回 branch/component gaps 与 rejected alternatives。 | 返回 packet 可整合进 architecture plan，且不把 G0-J 扩大到 static manifest/validators 之外。 | 可与 `G0-F`、`G0-H` 并行；依赖当前 branch-registry draft。 | 1 | pass |
| `G0-H Projection And Validator Gate Review` | read-only diagnostics worker | inherited parent / xhigh | 审查 branch-aware manifests 投影到当前 `WorldTerrainAssignment`、`WorldZoneDefinition`、wind、maritime 与 scenario setup fields 时如何 fail closed。 | none；仅 diagnostics packet | 不实现 projection code、parser 或 runtime branch behavior。 | worker packet 映射 accepted compatibility projections、rejected projections、validator classes 与 held gates。 | 返回 packet 定义 G0-J static contract work 所需的 validator/projection evidence requirements。 | 可与 `G0-F`、`G0-G` 并行；依赖当前 branch-registry draft。 | 1 | pass |
| `G0-D Implementation Package Map` | main thread | n/a | 命名当前与后续 G0 implementation files/tests，并同步 ground 父级文档。 | Ground 父 docs 加本 task package docs。 | 本子阶段不创建 generator code，不释放 runtime。 | 父级 README/progress/queue 指向本包；`git diff --check` clean。 | Ground README/progress/queue 已同步；route/terrain/LOS/fires 仍 held。 | 依赖 `G0-B`、`G0-C` 与 `G0-E`；收口串行。 | 1 | pass |
| `G0-I Branch Expansion Integration` | main thread integration | n/a | 在必要时把 `G0-F/G/H` 返回 diagnostics 整合进 source inventory、architecture plan、terrain-branch plan、task clusters 与父级文档。 | `docs/task/ground/environment_substrate_g0_architecture/*.md`、`docs/task/ground/README*.md`、`docs/task/ground/ground_current_progress_20260524*.md`、`docs/task/ground/ground_subagent_dispatch_queue_20260521*.md` | 本子阶段不实现 generator，不释放 runtime。 | 本地 review worker packets，并对 touched docs 跑 `git diff --check`。 | branch expansion evidence 已整合或显式拒绝，且 held capabilities 保持。 | 等 `G0-F/G/H` 返回后串行。 | 1 | pass |
| `G0-L-F Scenario Compiler Ingestion` | main thread implementation | n/a | 将 accepted projection setup payloads 接入 scenario compiler data ingestion。 | `python/scenario/environment_substrate/scenario_ingestion.py`、`python/scenario/compiler/service.py`、package exports、focused tests、G0 package docs | 不做 runtime setup application、不编辑 C++、不新增 generated scenario artifacts、不释放 movement/LOS/cover/fires/damage/combat。 | focused ingestion pytest 与 G0 closure suite。 | strict ingestion accepted 且 fail-closed；runtime setup 仍 held。 | 依赖 accepted G0-L-E。 | 1 | accepted |
| `G0-M Metadata Derived Products` | main thread implementation | n/a | 实现第一批 metadata-only derived-product indexes。 | `python/scenario/environment_substrate/derived_products.py`、package exports、focused tests、G0 package docs | 不做 road graph、movement-cost grid、passability mask、runtime LOS/cover product、tactical-area runtime graph 或 runtime consumers。 | focused derived-product pytest 与 G0 closure suite。 | metadata/index products accepted 且不声明 runtime capability。 | 依赖 accepted G0-L boundary。 | 1 | accepted |

## 派发规则

- 不编辑已归档 G0-G6 ground evidence packages。
- G0 不创建 terrain generator code。
- G0 不把 `WorldZoneDefinition` 扩成 canonical terrain schema。
- 不添加声明 movement、LOS、cover、fires、damage 或 combat 的 scenario 文件。
- `WorldZoneDefinition` 只作为 compatibility projection，不作为完整 environment schema。
- terrain 只是第一条被细化的 branch，不是整个 environment substrate；
  atmosphere/weather、wind、illumination、maritime/ocean、hydrology 与 dynamic
  environment branches 必须保留为同一 root 下的 merge targets。
- 每个 worker packet 必须精确映射到一个 assigned `G0-F`、`G0-G` 或 `G0-H`
  diagnostics cluster。
- diagnostics workers 只读，不得创建新的会话线程、编辑文件、stage changes 或 commit。
- 后续 G0 implementation write-scope 必须保持有限、已命名、且受 release gate 约束。

## Worker Packet 要求

任何 delegated diagnostics packet 必须返回：

- files inspected；
- existing mechanism summary；
- proposed architecture decision；
- rejected alternatives；
- acceptance or blocker status；
- explicit held capability claims。

## 验证计划

G0 验证是 documentation 与 architecture validation：

```bash
git diff --check -- docs/task/ground/environment_substrate_g0_architecture docs/task/ground/README.md docs/task/ground/README.zh.md docs/task/ground/ground_current_progress_20260524.md docs/task/ground/ground_current_progress_20260524.zh.md docs/task/ground/ground_subagent_dispatch_queue_20260521.md docs/task/ground/ground_subagent_dispatch_queue_20260521.zh.md
```

Focused code tests 由 G0-J、G0-K、G0-L 与 G0-M 这类 implementation substage 单独
要求；architecture-only diagnostics 与实现测试分开记录。

G0 closure validation：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

## 验收标准

G0 只有在以下条件成立时才接受：

- source inventory 与 architecture proposal 已存在；
- branch registry 与 component registry 足够通用且可扩展；
- validators、projection 与 derived-product boundaries 已命名；
- terrain-system architecture 将 shared layered/tiled manifest data 与当前
  compatibility projection/query consumers 分离；
- atmosphere/weather、wind、illumination、maritime/ocean、hydrology 与 dynamic
  environment branches 被表达为同一 environment manifest root 下的 merge targets；
- terrain ownership 不归 ground 独占；air、naval、ground 和未来 domains 都可迁移到
  同一 substrate；
- G0-J/G0-K/G0-L/G0-M implementation scope 有限且可测试；
- movement、LOS、cover、fires、damage、combat 与完整 ground runtime claims 全部继续 held。

## Residual Map

- G0-J static manifest contract 已接受：
  [environment_substrate_g0_static_manifest_contract_20260605.zh.md](environment_substrate_g0_static_manifest_contract_20260605.zh.md)。
  其范围只有 static data structures、registries、validators、deterministic fixture
  与 fail-closed projection contract tests。
- G0-K generator/catalog contract 已接受：
  [environment_substrate_g0_generator_catalog_20260605.zh.md](environment_substrate_g0_generator_catalog_20260605.zh.md)。
  其范围只有 Python request/tile/catalog contracts、deterministic seed
  derivation、catalog admission 与 in-memory fixture generation。
- G0-L projection setup payload contract 已接受：
  [environment_substrate_g0_projection_setup_acceptance_20260606.zh.md](environment_substrate_g0_projection_setup_acceptance_20260606.zh.md)。
  其范围只有 already validated `world_zone_definition` projections 的 Python inert
  payload/evidence conversion。
- G0-L-F scenario compiler ingestion 已接受：
  [environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md](environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md)。
  其范围只有 strict data ingestion into merged scenario zones；runtime setup
  application 仍 held。
- G0-M metadata-only derived products 已接受：
  [environment_substrate_g0_derived_products_acceptance_20260606.zh.md](environment_substrate_g0_derived_products_acceptance_20260606.zh.md)。
  其范围只有 `surface_zone_index` 与 `occlusion_candidate_index` contract products。
- G0 已由
  [environment_substrate_g0_closure_acceptance_20260606.zh.md](environment_substrate_g0_closure_acceptance_20260606.zh.md)
  闭合。Runtime setup application、runtime consumers、weather simulation、
  hydrodynamics、hydrology effects、dynamic environment mutation、movement、LOS、
  cover、fires、damage 与 combat 仍在后续 gates 之后。
