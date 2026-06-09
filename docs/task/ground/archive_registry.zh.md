# 陆军归档注册表

`docs/task/ground/archive/` 下已归档陆军子项目的注册索引。

## 已归档子项目

| 子项目 | 描述 |
|--------|------|
| `g0_boundary_freeze/` | G0 边界冻结。冻结 `ground` 为维护中特化名、`platoon` 为第一批战术单元、`move/occupy/support` 为第一任务族默认值。已 accepted。 |
| `g1_contract_skeleton/` | G1 合同骨架。窄 Python-profile-only 切片：`army`/`ground`/`land` 规范化为 `ground`。已 accepted；runtime behavior 保持 held。 |
| `g2_content_test_seed/` | G2 内容与测试种子。第一批 ground 内容种子与三个可运行 common-core 合同。已 accepted。 |
| `g3_execution_surface_design/` | G3 执行面设计。tasking-only lifecycle proof through normalized ground TaskOrder → LeaderIntent → PilotReport。已 accepted，封存为 baseline。 |
| `g4_runtime_slice/` | G4 Runtime 切片。G3 的有界切实验收。已封存为 tasking lifecycle baseline。 |
| `g5_mvp_scenario/` | G5 MVP 场景。第一版规范 MVP 场景 shell（`scenarios/ground/`）。command delivery/observation/export/movement/sensing/terrain/fires 仍 held。 |
| `g6_native_ground_platform_schema/` | G6-E Native Ground Platform Schema。`UnitType::Ground`、`Ground_Platoon_MVP` 的 loadable/spawnable schema 实现。已 accepted；movement/combat 仍 held。 |
| `g6_realism_gradient_mvp_scenarios/` | G6 Realism Gradient MVP 场景。第一批 realism-gradient 场景 batch，含 G6-A 梯度决策与 G6-B compatibility-shell fixtures。 |
| `g6_route_move_boundary/` | G6-C Route-Move Boundary。route-move boundary guardrails：未知 profile hint fail closed，G0/G1 场景 constrained。 |
| `g6_route_move_release_decision/` | G6-D Route-Move Release Decision。选择 schema-first 路径；G2 route-move 等待 native schema evidence + movement-release vote。 |

## 顶层归档文档

| 文件 | 描述 |
|------|------|
| `ground_domain_bootstrap_plan_20260521` | Ground 域引导计划 |
| `ground_domain_bootstrap_plan_acceptance_20260605` | 引导计划验收记录 |
