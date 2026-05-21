# Ground

状态：已于 `2026-05-21` 建立活跃规划入口；G0、G1、G2 与 G3 均已由主线程验收。
G4 已释放为一个有边界的运行时切片。

语言：

- 英文主文：`README.md`
- 中文配套：[README.zh.md](README.zh.md)

本子项目是仓库“第三域”启动规划的入口，面向未来的 ground specialization。
它的目标是在不新增垂直 runtime 路径的前提下，把地面域接入共享仿真生命周期。

## 当前状态

- `services/army` 已经存在，并且是权威的军种画像边界文档。
- 当前任务树已经维护专门的 ground 执行特化规划线；runtime 执行仍保持延后。
- G0 现已冻结 `ground` 作为维护中的特化名、`platoon` 作为第一批
  tight-loop 战术单元、`move / occupy / support` 作为第一任务族默认值。
- `army` 与 `land` 是可接受别名，并会规范化为 `ground`；导航通过
  `services/army` 加 `ground/`，而不是新的 `army` runtime stack。
- 当前工作线已拆成 G0-G4 阶段，便于 subagent 接收边界清楚、互不重叠的任务。
- G0 已由 main-thread G0-D 验收。
- G1 已验收一个窄范围 Python-profile-only 切片：`army`、`ground`、`land`
  与 `ServiceProfile.Army` 均规范化为 `ground`；C++ DTO 壳、绑定、
  runtime 行为和场景加载器仍保持 held。
- G2 已验收第一批 ground 内容/测试种子：`examples/config/database/ground/units/`
  下的非自动加载 `ground_platoon_starter.seed`，以及三个可运行的
  `tests/contracts/unit/ground/` common-core 合同。
- G3 已验收一个安全的 G4 候选：
  `tasking-only lifecycle proof through normalized ground TaskOrder ->
  LeaderIntent -> PilotReport status shell`。
- G4 现在只为该有界切片释放；command delivery、observation/export、
  movement、sensing、terrain、fires 与 broad facade work 仍保持 held。

## 推荐阅读顺序

- 主计划：
  [ground_domain_bootstrap_plan_20260521.zh.md](ground_domain_bootstrap_plan_20260521.zh.md)
- Subagent 分发：
  [ground_subagent_dispatch_queue_20260521.md](ground_subagent_dispatch_queue_20260521.md)
- G0：
  [g0_boundary_freeze/README.md](g0_boundary_freeze/README.md)
- G1：
  [g1_contract_skeleton/README.md](g1_contract_skeleton/README.md)
- G2：
  [g2_content_test_seed/README.md](g2_content_test_seed/README.md)
- G3：
  [g3_execution_surface_design/README.md](g3_execution_surface_design/README.md)
- G4：
  [g4_runtime_slice/README.md](g4_runtime_slice/README.md)
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
- `common / air / naval` 拆分承接线：
  [../common_air_naval/README.zh.md](../common_air_naval/README.zh.md)

## 当前继续推进重点

- 仅按已验收的 tasking-only lifecycle-proof 切片推进 G4
- 在第一条 G4 切片验证完成前，继续保持 command delivery、observation/export、
  movement、sensing、terrain 与 fires 为 held
- 所有委派工作都通过 subagent queue 分发
