# 双机阶段标准总览 (Two-Ship Stage Standard)

> ARCHIVED NOTE (2026-03-23): 该目录属于第一版 air-specific 双机标准草案，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/Workshop/CMO/docs/standards/README.md) 及 `joint/service profile` 文档。

本目录定义项目从“单机 C2/长机/执行层”过渡到“双机协同”的标准化口径。

目标不是立刻实现完整空战编队体系，而是先把**双机战术单元**的职责边界、对象模型、训练范围和真实性约束固定下来，避免后续实现时把：

- 战术编组
- 行政编制
- 长机层决策
- 执行层操纵

混成同一层。

## 1. 本阶段的核心结论

### 1.1 运行时控制层级

双机阶段采用如下运行时控制链：

`C2 / GCI / AWACS -> Element Lead -> Wingman -> Execution Layer`

说明：
- `Element` 指一个双机战术单元。
- 第一阶段不引入四机 `Package Lead` 作为必需运行时对象。
- 第一阶段也不把“中队 / 大队 / 联队”作为每步参与控制的 agent。

### 1.2 真实性原则

必须明确区分：

- **战术编组**：双机、四机、任务包
- **行政编制**：中队、大队、旅/联队

本项目在双机阶段只把**战术编组**纳入实时控制。

原因：
- 现实中 sortie 级控制首先围绕双机/四机战术编组展开。
- 行政编制更适合出现在任务生成、资源调度、待战值班和增援逻辑里。
- 如果把“大队 / 中队”直接做成运行时 RL 控制层，会把行政结构错误地塞进 60Hz 决策闭环，真实性反而下降。

### 1.3 编组规模约定

本阶段约定：

- `2 机`：一个 `Element`
- `4 机`：下一阶段的一个 `Package`，由两个 `Element` 组成

因此：
- 双机阶段先只做 `Element`
- 四机阶段再引入 `Package`
- 行政上的“中队 / 大队”暂不做运行时控制对象

## 2. 推荐阅读顺序

1. [战术层级标准](/home/void0312/Workshop/CMO/docs/Archive/air_first_standards/com/two_ship/tactical_hierarchy_standard.md)
2. [数据模型增量](/home/void0312/Workshop/CMO/docs/Archive/air_first_standards/com/two_ship/data_model_delta.md)
3. [RL 范围与课程计划](/home/void0312/Workshop/CMO/docs/Archive/air_first_standards/com/two_ship/rl_scope_and_curriculum.md)
4. [双机 MVP 与验收标准](/home/void0312/Workshop/CMO/docs/Archive/air_first_standards/com/two_ship/mvp_scope_and_acceptance_standard.md)
5. [双机实现切分标准](/home/void0312/Workshop/CMO/docs/Archive/air_first_standards/com/two_ship/implementation_cut_standard.md)

## 3. 与现有标准的关系

本目录是下列标准的扩展，而不是替代：

- [Task Order & Leader Layer Standard](/home/void0312/Workshop/CMO/docs/Archive/air_first_standards/com/task_order_leader_standard.md)
- [CAP 任务与长机层落地计划](/home/void0312/Workshop/CMO/docs/Archive/air_first_standards/com/cap_task_bootstrap_plan.md)

现有单机标准继续成立，只是双机阶段需要把“单机 assignee”和“编组级 assignee”分开建模。

## 4. 本阶段不做什么

为保证真实性和工程收敛，本阶段明确不做：

- 不直接进入四机 RL 主线
- 不直接进入双边自博弈主线
- 不把 C2 训练成端到端控制器
- 不让 C2 直接逐步给每架飞机写 `heading / altitude / speed`
- 不把行政编制硬编码成运行时指挥树

## 5. 本阶段的正确落点

双机阶段的正确目标是：

- 建立一个真实的双机战术单元
- 明确 lead / wingman 的权责边界
- 让现有 `TaskOrder -> LeaderIntent -> MissionCommand` 链路能承载双机协同
- 为后续四机 package 和更高层 C2 奠定稳定接口
