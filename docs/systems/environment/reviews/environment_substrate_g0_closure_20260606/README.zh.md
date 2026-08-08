# Ground Environment Substrate G0 Architecture

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.md`
Owner: `systems/environment/reviews`
Last verified: `2026-08-08`
Review basis：`2026-06-06` G0 闭合证据；本页不是 active dispatch surface。

状态：保留的 closure review；`2026-06-06` accepted and closed shared component-based environment
substrate 的 G0 设计与实现线。已接受子阶段包括 G0 architecture/design records、
G0-J static manifest contract、G0-K generator/catalog contract、G0-L projection
setup payload 加 strict scenario compiler ingestion，以及 G0-M metadata-only
derived products。闭合后的 G0 仍不释放 runtime setup application、movement、LOS、
cover、fires、damage 或完整 terrain-runtime/domain behavior。

语言：

- 英文主文：[README.md](README.md)
- 中文配套：`README.zh.md`

输入：

- Ground 父入口：[../README.zh.md](../../../../task/ground/archive/owner_migration_20260808/README.zh.md)
- 已归档 Ground 进展快照：[ground_current_progress_20260524.zh.md](../../../../task/ground/archive/owner_migration_20260808/ground_current_progress_20260524.zh.md)
- 已接受 bootstrap 基线：
  [../archive/ground_domain_bootstrap_plan_20260521.zh.md](../../../../task/ground/archive/ground_domain_bootstrap_plan_20260521.zh.md)
- Runtime terrain/query primitives：
  [../../../../src/core/interfaces/environment_model.h](../../../../../src/core/interfaces/environment_model.h)、
  [../../../../src/models/environment/default_environment_model.cpp](../../../../../src/models/environment/default_environment_model.cpp)、
  [../../../../src/runtime/contracts/world_batch_contracts.h](../../../../../src/runtime/contracts/world_batch_contracts.h)
- Scenario compiler/generation surfaces：
  [../../../../python/scenario/compiler](../../../../../python/scenario/compiler)
- Source inventory：
  [environment_substrate_g0_source_inventory_20260605.zh.md](environment_substrate_g0_source_inventory_20260605.zh.md)
- Architecture implementation plan：
  [environment_substrate_g0_architecture_plan_20260605.zh.md](environment_substrate_g0_architecture_plan_20260605.zh.md)
- Terrain system architecture：
  [environment_substrate_g0_terrain_system_architecture_20260605.zh.md](environment_substrate_g0_terrain_system_architecture_20260605.zh.md)
- Subagent diagnostics dispatch：
  [environment_substrate_g0_subagent_dispatch_20260605.zh.md](environment_substrate_g0_subagent_dispatch_20260605.zh.md)
- Acceptance：
  [environment_substrate_g0_acceptance_20260605.zh.md](environment_substrate_g0_acceptance_20260605.zh.md)
- 已接受 G0-J static manifest contract：
  [environment_substrate_g0_static_manifest_contract_20260605.zh.md](environment_substrate_g0_static_manifest_contract_20260605.zh.md)
- 已接受 G0-K generator/catalog contract：
  [environment_substrate_g0_generator_catalog_20260605.zh.md](environment_substrate_g0_generator_catalog_20260605.zh.md)
- 已接受 G0-L projection setup payload：
  [environment_substrate_g0_projection_preflight_20260606.zh.md](environment_substrate_g0_projection_preflight_20260606.zh.md)
  与
  [environment_substrate_g0_projection_setup_acceptance_20260606.zh.md](environment_substrate_g0_projection_setup_acceptance_20260606.zh.md)
- 已接受 G0-L-F scenario compiler ingestion：
  [environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md](environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md)
- 已接受 G0-M metadata-only derived products：
  [environment_substrate_g0_derived_products_acceptance_20260606.zh.md](environment_substrate_g0_derived_products_acceptance_20260606.zh.md)
- G0 closure acceptance：
  [environment_substrate_g0_closure_acceptance_20260606.zh.md](environment_substrate_g0_closure_acceptance_20260606.zh.md)
- G0-Viz visualization follow-on：
  [environment_substrate_g0_viz_overlay_sync_acceptance_20260606.zh.md](environment_substrate_g0_viz_overlay_sync_acceptance_20260606.zh.md)

## 目的

本子项目从 ground planning lane 开启第一个 environment-substrate follow-on，但
environment substrate 本身是 shared infrastructure。ground 场景是当前最直接暴露
terrain、built environment、vegetation、infrastructure 与 tactical-area substrate
缺口的压力源；由此产生的架构必须可被 air、naval、ground 和未来 domains 共用，
而不是变成任一 domain 的私有 schema。

terrain 是第一条被细化的 branch，因为它是计划中的 land 场景最先缺失的 substrate。
但它不是整个 environment object。相同的 `EnvironmentManifest` 和
`EnvironmentObject` 边界还必须容纳 atmosphere、weather、wind、illumination/sun、
maritime/ocean state、hydrology，以及后续 dynamic environment branches。

G0 是这条 shared substrate 的设计与实现线。设计是 G0 的子阶段，不是整个 G0：
当前已接受的设计子阶段命名 owner map、component registry 形状、manifest/projection
边界、validator plan 和 accepted write-scope。G0-J 实现第一版 static contract，
G0-K 实现第一版 deterministic generator/catalog contract 与 in-memory fixture path，
G0-L 实现 already validated world-zone projection 的 inert projection setup payload
contract 加 strict compiler ingestion。G0-M 实现第一批 metadata-only derived-product
indexes。闭合后的 G0 实现刻意停在 runtime setup application、movement model、building
LOS 或 combat runtime 之前。

## 当前状态

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Ground bootstrap | accepted | [accepted baseline](../../../../task/ground/archive/ground_domain_bootstrap_plan_20260521.zh.md) | 不释放 terrain-aware runtime behavior。 |
| Native ground schema | accepted | current progress 中的 `Ground_Platoon_MVP`、`UnitType::Ground` evidence | 只关闭 identity；没有 movement 或 terrain behavior。 |
| 当前 C++ terrain model | available primitive | [source inventory](environment_substrate_g0_source_inventory_20260605.zh.md) | shared query/zone surface，不是 canonical terrain ownership。 |
| Scenario compiler/runtime setup | compiler data ingestion accepted；runtime setup held | [G0-L-F ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md)、[source inventory](environment_substrate_g0_source_inventory_20260605.zh.md) | Compiler 可将 inert payloads ingest 到 merged scenario zones；runtime setup application 不释放。 |
| Environment substrate architecture | accepted G0 plan | [architecture plan](environment_substrate_g0_architecture_plan_20260605.zh.md)、[acceptance](environment_substrate_g0_acceptance_20260605.zh.md) | shared environment plan；不释放 generator 或 runtime behavior。 |
| Terrain system architecture | accepted G0 design | [terrain system architecture](environment_substrate_g0_terrain_system_architecture_20260605.zh.md)、[diagnostics dispatch](environment_substrate_g0_subagent_dispatch_20260605.zh.md) | 定义 cross-domain layered/tiled terrain substrate 结构；不释放 terrain generator 或 domain runtime。 |
| G0-J static manifest contract | accepted implementation substage | [G0-J static contract](environment_substrate_g0_static_manifest_contract_20260605.zh.md) | static Python contract、validators、fixture 与 contract projection only；不做 runtime integration。 |
| G0-K generator/catalog contract | accepted implementation substage | [G0-K record](environment_substrate_g0_generator_catalog_20260605.zh.md)、[G0-K acceptance](environment_substrate_g0_generator_catalog_acceptance_20260606.zh.md) | Python request/tile/catalog contract 与 deterministic in-memory fixture only；不做 runtime integration。 |
| G0-L projection setup and compiler ingestion | accepted implementation substage | [G0-L preflight](environment_substrate_g0_projection_preflight_20260606.zh.md)、[G0-L setup acceptance](environment_substrate_g0_projection_setup_acceptance_20260606.zh.md)、[G0-L-F ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md) | Python inert setup payload 加 strict compiler data ingestion only；不做 runtime setup application。 |
| G0-M metadata-only derived products | accepted implementation substage | [G0-M acceptance](environment_substrate_g0_derived_products_acceptance_20260606.zh.md) | Contract/index products only；不释放 movement、LOS、cover 或 runtime consumers。 |
| G0-Viz tactical map overlay sync | accepted visualization follow-on | [G0-Viz acceptance](environment_substrate_g0_viz_overlay_sync_acceptance_20260606.zh.md) | 只把已接受 G0 data 画到 tactical map；不释放 runtime setup application、movement、LOS、cover 或 terrain behavior。 |
| Ground route/terrain/LOS/fires | held | ground progress 与 dispatch queue | 必须等单独 release gate。 |

## 范围

范围内：

- 将 terrain system 定义为 shared environment infrastructure，使其能服务 air、
  naval、ground 和未来 domains。
- 定义 environment-substrate root，使 terrain 成为更大 environment object 中的一条
  branch，并能合并 atmosphere、weather、wind、illumination/sun、maritime/ocean
  与 hydrology branches。
- 定义 component-based `EnvironmentObject` manifest architecture，使 components
  与 catalogs 可扩展。
- 定义默认 layer-stack 语义，但不把 layer stack 关闭成固定集合。
- 定义 generator plugin 边界，以及 deterministic seed / provenance 规则。
- 定义 validators：object identity、geometry、references、component completeness、
  layer compatibility 与 projection safety。
- 定义 rich manifest 到当前 `terrain_type` 加 `WorldZoneDefinition` 兼容面的
  runtime projection。
- 定义并实现第一批 metadata-only derived-product contracts，同时将 road graph、
  movement-cost grid、passability mask、runtime LOS/occlusion、cover/concealment
  与 tactical-area graph 留在后续 gates。
- 定义 terrain-system architecture：layered terrain、tiling、catalogs、
  generator stages、projection profiles 与 derived-product gates。
- 产出并维护 G0 子阶段的 accepted implementation package map。

范围外：

- 超出 G0-K deterministic in-memory fixture 的 runtime 或 scenario-producing
  terrain generator implementation。
- Runtime setup application，或 accepted metadata products 的 runtime consumers。
- 面向任何 domain 的新 C++ terrain runtime。
- route following、speed updates、passability behavior、stuck/off-route checks、
  LOS occlusion、cover、fires、damage、suppression 或 combat。
- 把 road、forest、village 或 building 硬编码为 core schema boundary。
- 替换当前 `WorldZoneDefinition` setup contracts。

## 架构方向

详细设计见
[environment_substrate_g0_architecture_plan_20260605.zh.md](environment_substrate_g0_architecture_plan_20260605.zh.md)。
简写形式是：

目标架构是：

```text
Scenario Intent
  -> Generator Plugins
  -> Component-Based Environment Manifest
  -> Validators
  -> Derived Products
  -> Runtime Projection
  -> Query / Simulation Consumers
```

核心对象形状保持通用：

```text
EnvironmentObject
  identity
  branch_membership[]
  geometry
  layer_membership
  components[]
  properties{}
  provenance
```

road、treeline、building、trench、minefield、flooded field、weather cell、
wind layer、sea-state area、village block 这类 feature label 是 catalog entry。
runtime 能力来自 mobility、occlusion、cover、material、structure、vegetation、
network、hydrology、atmospheric_profile、weather_effect、wind_field、illumination、
maritime_state、tactical semantic、hazard、damageable 等 components。

## 阶段计划

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `G0-A Architecture Implementation Plan` | 冻结 architecture、ownership、component registry、manifest/projection boundary 和 accepted implementation map。 | 已接受 ground bootstrap baseline 与当前 src terrain inventory。 | README、task clusters、source inventory、component registry proposal、manifest/projection/validator plan 与 acceptance gate 已同步。 | accepted |
| `G0-J Static Manifest Contract` | 实现 static manifests 的 schema/contract 与 validators。 | 已接受 G0 architecture/design substages。 | deterministic manifest fixture 与 validators 通过，且没有 runtime claims。 | accepted |
| `G0-K Generator Catalog Contract` | 实现 deterministic generator request/tile/catalog contracts。 | G0-J manifest contract accepted。 | generator 可生成带 catalog provenance 的 reproducible in-memory environment manifests。 | accepted |
| `G0-L Projection` | 将 manifest 子集投影到当前 scenario/world setup surfaces。 | G0-K generator output accepted。 | 已接受 inert setup payload/evidence conversion 与 strict scenario compiler data ingestion；runtime setup application 继续 held。 | accepted |
| `G0-M Derived Products` | 为后续 movement/LOS gates 引入第一批 derived products。 | 已接受 G0-L compiler ingestion boundary。 | metadata-only surface-zone 与 occlusion-candidate indexes 通过验证，且不越界声明 runtime behavior。 | accepted |

## 任务簇

- Task cluster plan：
  [environment_substrate_g0_task_clusters_20260605.zh.md](environment_substrate_g0_task_clusters_20260605.zh.md)

## 输出与证据

G0 应产出：

- [source inventory](environment_substrate_g0_source_inventory_20260605.zh.md)，清点
  existing C++ terrain/query 与 scenario compiler/runtime setup surfaces；
- [architecture implementation plan](environment_substrate_g0_architecture_plan_20260605.zh.md)，定义
  component registry、branch registry、catalog boundary、manifest、validators、
  projection 与 derived products；
- [terrain system architecture](environment_substrate_g0_terrain_system_architecture_20260605.zh.md)，定义
  layered/tiled terrain、generator boundaries、projection profiles 与
  derived-product gates；
- [subagent diagnostics dispatch](environment_substrate_g0_subagent_dispatch_20260605.zh.md)，记录
  只读 C++ 与 Python terrain-foundation analysis packets；
- [acceptance record](environment_substrate_g0_acceptance_20260605.zh.md)；
- [accepted G0-J static manifest contract](environment_substrate_g0_static_manifest_contract_20260605.zh.md)；
- [accepted G0-K generator/catalog contract](environment_substrate_g0_generator_catalog_20260605.zh.md)；
- [G0-K acceptance record](environment_substrate_g0_generator_catalog_acceptance_20260606.zh.md)；
- [accepted G0-L projection setup payload contract](environment_substrate_g0_projection_setup_acceptance_20260606.zh.md)；
- [G0-L projection preflight and task map](environment_substrate_g0_projection_preflight_20260606.zh.md)；
- [accepted G0-L-F scenario compiler ingestion](environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md)；
- [accepted G0-M metadata-only derived products](environment_substrate_g0_derived_products_acceptance_20260606.zh.md)；
- [G0 closure acceptance](environment_substrate_g0_closure_acceptance_20260606.zh.md)；
- G0-J implementation 的 accepted file/package write-scope；
- 保持 movement、LOS、cover、fires、damage 和 combat held 的 guardrails。

## 验收门

本子项目只有在以下条件成立时才能标记 accepted：

- G0 architecture plan 命名 component registry、environment branch registry、
  manifest shape、validator plan、projection plan 和 future consumer gates；
- 当前 `src` terrain/query primitives 被诚实表述为 shared primitives，而不是完整
  terrain runtime；
- terrain-system plan 将当前 C++/Python setup 保持为 compatibility projection/query
  surfaces，并在其上定义 layered、tiled、component-based terrain data；
- ground 父 README、progress tracker 与 dispatch queue 都指向本包作为 accepted
  environment-substrate G0 follow-on；
- G0-L-F strict compiler ingestion 与 G0-M metadata-only derived products 有 focused
  tests 和 acceptance records；
- touched docs 的 `git diff --check` clean；
- 不声明或释放 runtime setup application、movement、LOS、cover、fires、damage 或
  combat capability。

## 残余与下一步

- G0-J 已实现并接受的范围只有 static manifest contract、registries、validators、
  deterministic fixture 与 contract-level projection tests。
- G0-K 只接受 Python generator/catalog contract、deterministic
  request/tile/seed/provenance rules、catalog admission 与 in-memory generated
  manifest fixture。
- G0-L 已接受 Python projection setup payload contract，以及对 already validated
  `world_zone_definition` projection output 的 strict scenario compiler ingestion。
- G0-M 已接受 metadata-only `surface_zone_index` 与
  `occlusion_candidate_index` products。
- G0 closure acceptance 后不再留下 G0-internal held slice。Runtime setup
  application、runtime consumers、movement、LOS、cover、fires、damage 与 combat
  仍是 downstream release gates。
- Route movement 仍由单独的 G6-D3/G6-F-style release vote 管辖。
- implementation package 已命名为 shared `environment_substrate`；task record 仍由
  ground 索引为孵化需求来源。

## Archive

被取代的 G0 design records 只有在当前 README/status 或 acceptance surface 指向替代入口后，
才进入本子项目未来的 `archive/`。
