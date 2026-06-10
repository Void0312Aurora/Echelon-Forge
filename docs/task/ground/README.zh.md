# Ground

状态：active follow-on 入口；bootstrap 规划基线，以及 environment-substrate G0
设计/实现线已在 `2026-06-06` 接受并闭合至 G0-M；当前进展追踪更新于
`2026-06-06`。

语言：

- 英文主文：`README.md`
- 中文配套：[README.zh.md](README.zh.md)

本子项目是仓库当前早期 ground specialization bootstrap 的规划入口。它的目标是
在不新增垂直 runtime 路径的前提下，把地面域接入共享仿真生命周期。

## 当前状态

- 最新状态总结以
  [陆军 / 地面当前进展追踪](ground_current_progress_20260524.zh.md) 为准。
- 已接受 environment-substrate G0 design/implementation line：
  [environment_substrate_g0_architecture/README.zh.md](environment_substrate_g0_architecture/README.zh.md)。
  该包把 G0 定义为 shared environment-substrate 的设计与实现线。当前已接受子阶段包括
  architecture/design records、G0-J static manifest contract 与 G0-K
  generator/catalog contract、G0-L projection setup plus compiler-ingestion
  contract，以及 G0-M metadata-only derived products；不释放 runtime setup
  application、movement、LOS、cover、fires、damage 或 combat。
- 已接受 environment-substrate G0-J static manifest contract：
  [environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.zh.md)。
  该子阶段在 `python/scenario/environment_substrate/` 下新增 shared static manifest
  data structures、registries、validators、deterministic fixture 与 contract-level
  projection tests；不释放 generator 或 runtime behavior。
- 已接受 environment-substrate G0-K generator/catalog contract：
  [environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.zh.md)。
  该子阶段在 `python/scenario/environment_substrate/` 下新增 deterministic
  request/tile/seed/provenance rules、catalog descriptors/admission 与 in-memory
  generated manifest fixture；不释放 runtime projection 或 generated scenario
  artifacts。
- 已接受 environment-substrate G0-L projection setup payload contract：
  [environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.zh.md)。
  该子阶段新增 Python 侧 inert setup payload/evidence conversion，用于 already
  validated `world_zone_definition` projections。
- 已接受 environment-substrate G0-L-F scenario compiler ingestion：
  [environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md)。
  该子阶段在 layout metadata compilation 之前，将 accepted projection setup
  payloads ingest 到 merged `environment.zones`；不 apply runtime setup。
- 已接受 environment-substrate G0-M metadata-only derived products：
  [environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.zh.md)。
  该子阶段只新增 `surface_zone_index` 与 `occlusion_candidate_index` contract
  products；不释放 movement、LOS、cover、fires、damage、combat 或 runtime consumers。
- Environment-substrate G0 closure：
  [environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.zh.md)。
- 原始 bootstrap 计划已经满足其 planning-lane 成功标准，现作为 accepted
  archived baseline 保留，不再是 active dispatch surface。
- `services/army` 已经存在，并且是权威的军种画像边界文档。
- 当前任务树已经维护专门的 ground 执行特化规划线：G0-G4 tasking lifecycle
  证据与 G6-E native schema 证据已经接受；movement、sensing、terrain、fires、
  damage、combat 与完整 ground runtime 行为仍保持 held。
- G0 现已冻结 `ground` 作为维护中的特化名、`platoon` 作为第一批
  tight-loop 战术单元、`move / occupy / support` 作为第一任务族默认值。
- `army` 与 `land` 是可接受别名，并会规范化为 `ground`；导航通过
  `services/army` 加 `ground/`，而不是新的 `army` runtime stack。
- 当前工作线已拆成 G0-G6 阶段，便于 subagent 接收边界清楚、互不重叠的任务。
- G0 已由 main-thread G0-D 验收。
- G1 已验收一个窄范围 Python-profile-only 切片：`army`、`ground`、`land`
  与 `ServiceProfile.Army` 均规范化为 `ground`。该 G1 切片当时保留 C++ DTO
  壳、绑定、runtime 行为和场景加载器；后续 `2026-06-05` 基础设施更新只新增
  static G0/G1 owner-slice DTO 与绑定，不释放 runtime behavior。
- G2 已验收第一批 ground 内容/测试种子：`examples/config/database/ground/units/`
  下的非自动加载 `ground_platoon_starter.seed`，以及三个可运行的
  `tests/contracts/unit/ground/` common-core 合同。
- G3 已验收一个安全的 G4 候选：
  `tasking-only lifecycle proof through normalized ground TaskOrder ->
  LeaderIntent -> PilotReport status shell`。
- G4 已验收该有界切片，并封存为 tasking lifecycle baseline。
- G5 已接受 `scenarios/ground/` 下第一版规范 MVP 场景 shell；command delivery、
  observation/export、movement、sensing、terrain、fires 与 broad facade work
  仍保持 held。
- G6 开启第一批 realism-gradient MVP 场景。G6-A 记录梯度决策，G6-B
  新增两个 G1 compatibility-shell fixture：
  `ground_platoon_static_occupy_v1` 与
  `ground_platoon_support_relationship_v1`。
- G6-C 已接受 route-move boundary guardrails：未知显式 profile hint 现在会
  fail closed，当前 ground 场景必须保持 G0/G1，`G2` route movement 继续
  held，直到后续 movement-release vote 接受 native schema 支撑的 movement
  evidence 或等价 compatibility boundary。
- G6-D 开启 route-move release decision，并选择 schema-first 路径：第一版
  `G2` route-move 场景必须等待 native ground schema 证据和后续
  movement-release vote。当前 `Aircraft` compatibility shell 只保留给 G0/G1。
- G6-D1/D2 已以 `preflight-only` 返回：当时 native `Ground` unit
  type/schema blocker 仍处于打开状态。G6-E2/E3 后来只关闭 schema identity；
  movement evidence 仍需要单独 release vote。
- G6-E0 开启 native ground platform schema planning package。它定义
  loadable/spawnable native ground entity 的最小实现面和证据门槛，但不释放
  route movement 或 runtime movement behavior。
- G6-E1 source-inventory/design preflight 选择 `UnitType::Ground`、
  `type = "Ground"`、`Ground_Platoon_MVP`，以及现有 type-name/default factory
  materialization path，作为第一版 native schema implementation 路线。
- G6-E2/E3 已接受第一版 native ground platform schema：示例数据库现在能加载
  `Ground_Platoon_MVP`，Python 暴露 `ef_py.UnitType.Ground`，并且
  `spawn_unit(..., "Ground_Platoon_MVP", ...)` 能 materialize native ground
  entity，且可稳定检查 position、velocity、heading、instrument 与 health。
  这仅是 schema 证据；route movement、terrain、sensing、fires、damage 和
  combat 仍保持 held。
- 第一版 C++ ground static owner-slice 基础设施已经落到
  `src/components/domains/ground/tasking/` 与 `src/components/domains/ground/command/`。它通过现有
  compatibility shell、maintained batch contract、JSON round-trip 与 Python
  binding 暴露 G0/G1 static task/status metadata。它不释放 route movement、
  terrain、sensing、fires、damage 或 combat。
- ground profile 现在能从 ground task/status metadata 生成 G0/G1 static
  `MissionCommandGround` 字段。这是 static tasking 的 command-authoring
  独立，不是独立的 ground movement 或 combat runtime。

## 当前入口

- 当前进展追踪：
  [ground_current_progress_20260524.zh.md](ground_current_progress_20260524.zh.md)
- 已接受 environment-substrate G0 architecture package：
  [environment_substrate_g0_architecture/README.zh.md](environment_substrate_g0_architecture/README.zh.md)
- 已接受 environment-substrate G0-J static manifest contract：
  [environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.zh.md)
- 已接受 environment-substrate G0-K generator/catalog contract：
  [environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.zh.md)
- G0-K 验收：
  [environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_acceptance_20260606.zh.md)
- 已接受 environment-substrate G0-L projection setup payload contract：
  [environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.zh.md)
- 已接受 environment-substrate G0-L-F scenario compiler ingestion：
  [environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md)
- 已接受 environment-substrate G0-M metadata-only derived products：
  [environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.zh.md)
- Environment-substrate G0 closure：
  [environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.zh.md)
- Environment-substrate G0-L projection preflight and task map：
  [environment_substrate_g0_architecture/environment_substrate_g0_projection_preflight_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_projection_preflight_20260606.zh.md)
- Terrain system G0 architecture design：
  [environment_substrate_g0_architecture/environment_substrate_g0_terrain_system_architecture_20260605.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_terrain_system_architecture_20260605.zh.md)
- 已接受 bootstrap 基线：
  [archive/ground_domain_bootstrap_plan_20260521.zh.md](archive/ground_domain_bootstrap_plan_20260521.zh.md)
- Subagent 分发：
  [ground_subagent_dispatch_queue_20260521.md](ground_subagent_dispatch_queue_20260521.md)
- Review：
  [../review/ground_domain_bootstrap_plan_review_20260521.md](../review/ground_domain_bootstrap_plan_review_20260521.md)
- 架构基线：
  [../../plan/architecture/simulation_system_architecture_design.md](../../plan/architecture/simulation_system_architecture_design.md)
- 陆军画像：
  [../../standards/services/army.zh.md](../../standards/services/army.zh.md)
- Ground 标准总览：
  [../../standards/ground/README.zh.md](../../standards/ground/README.zh.md)
- Ground 最小任务结构：
  [../../standards/ground/minimal_task_structure.zh.md](../../standards/ground/minimal_task_structure.zh.md)
- `common / air / naval` 拆分（已归档）：
  [../archive/common_air_naval/README.zh.md](../archive/common_air_naval/README.zh.md)

## 已封存 / 归档子项目记录

以下子项目目录是已接受的证据记录，不再是 active dispatch surface。原路径现在只保留
轻量工作说明，完整 packet 位于 [archive/README.zh.md](archive/README.zh.md)。它们仍从
本索引链接，是因为当前 movement-release 规划仍消费这些 gate；新工作应新开
follow-on package，不要在这些已接受记录内继续追加实现任务。

- Ground bootstrap 计划：
  [archive/ground_domain_bootstrap_plan_20260521.zh.md](archive/ground_domain_bootstrap_plan_20260521.zh.md)
- G0 边界冻结：
  [archive/g0_boundary_freeze/README.zh.md](archive/g0_boundary_freeze/README.zh.md)
- G1 合同骨架：
  [archive/g1_contract_skeleton/README.zh.md](archive/g1_contract_skeleton/README.zh.md)
- G2 内容 / 测试种子：
  [archive/g2_content_test_seed/README.zh.md](archive/g2_content_test_seed/README.zh.md)
- G3 执行面设计：
  [archive/g3_execution_surface_design/README.zh.md](archive/g3_execution_surface_design/README.zh.md)
- G4 tasking runtime 切片：
  [archive/g4_runtime_slice/README.zh.md](archive/g4_runtime_slice/README.zh.md)
- G5 MVP 场景 shell：
  [archive/g5_mvp_scenario/README.zh.md](archive/g5_mvp_scenario/README.zh.md)
- G6 realism-gradient 静态 fixture：
  [archive/g6_realism_gradient_mvp_scenarios/README.zh.md](archive/g6_realism_gradient_mvp_scenarios/README.zh.md)
- G6-C route-move boundary guardrails：
  [archive/g6_route_move_boundary/README.zh.md](archive/g6_route_move_boundary/README.zh.md)
- G6-D route-move release decision：
  [archive/g6_route_move_release_decision/README.zh.md](archive/g6_route_move_release_decision/README.zh.md)
- G6-E native ground platform schema 证据：
  [archive/g6_native_ground_platform_schema/README.zh.md](archive/g6_native_ground_platform_schema/README.zh.md)
- Environment substrate G0 architecture：
  [environment_substrate_g0_architecture/README.zh.md](environment_substrate_g0_architecture/README.zh.md)
- Environment substrate G0-J static manifest contract：
  [environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.zh.md)
- Environment substrate G0-K generator/catalog contract：
  [environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.zh.md)
- Environment substrate G0-L projection setup payload contract：
  [environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.zh.md)
- Environment substrate G0-L-F scenario compiler ingestion：
  [environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md)
- Environment substrate G0-M metadata-only derived products：
  [environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.zh.md)
- Environment substrate G0 closure：
  [environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.zh.md](environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.zh.md)

## 已封存基线

G0-G4 现在作为 ground tasking 的 accepted baseline 封存：

- `ground` / `army` / `land` profile 识别与 starter common-core defaults
- 非 runtime ground content seed 与 focused ground unit contracts
- 已选定的 execution-surface 决策：tasking-only lifecycle proof
- 经由 normalized `TaskOrder -> LeaderIntent -> PilotReport` 的 maintained
  runtime bridge

## 当前继续推进重点

- 将已接受 G0-K 视为 Python request/tile/catalog contract 与 in-memory fixture
  baseline，供 projection work 使用
- 将已接受 G0-L 视为 payload/evidence conversion 加 strict scenario compiler data
  ingestion；runtime setup application 仍需要单独 release package
- 将已接受 G0-M 视为 metadata-only derived-product contracts；runtime consumers 与
  movement/LOS/cover behavior 仍需要单独 release package
- 将 terrain 保持为 shared environment root 中第一条被细化的 branch，并与
  atmosphere/weather、wind、illumination、maritime/ocean、hydrology 和 dynamic
  environment branches 并列
- 保持已接受 G0-J implementation 的 manifest-first 边界：当前 C++/Python terrain
  setup 仍是 compatibility/query surface，新增 Python package 是 shared
  `environment_substrate` contract namespace
- 维护 G0/G5 tasking smoke 与 G6 G1 static occupy/support fixtures，作为
  realism-gradient guardrails
- 在添加任何 movement 场景前，保持 G6-C/G6-D route-move guardrails 生效，但不重开这些已接受记录
- 将已接受的 G6-E2/E3 native schema 证据作为后续 route-move release vote 的输入
- G1 场景只验证 static occupy/support relationship 语义，不扩张为 ground
  combat/runtime 证明
- observation/export、movement、sensing、terrain、fires、effects、damage、
  combat 与 broad `MissionCommand` growth 继续 held；当前
  `MissionCommandGround` 路径只承载 static task metadata authoring
- 所有委派工作都通过 subagent queue 分发

已归档子项目的完整清单见 [归档注册表](archive_registry.zh.md)。
