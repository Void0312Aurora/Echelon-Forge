# 场景配置指南

Language:
- English canonical: `bridge/scenario_guide.md`
- Chinese companion: [scenario_guide.zh.md](scenario_guide.zh.md)

状态：`2026-05-18`，场景 JSON 到标准/运行时映射的权威桥接文档。

本文档描述的是当前仓库中的场景 JSON 实现接口，而不是 doctrine 本体。它的职责是说明：

- 现有 loader / compiler 能直接消费哪些字段
- 哪些字段仍处于实现阶段的桥接状态，还不是稳定的 common-core ontology
- 场景作者应如何把任务概念映射到当前 runtime，而不混淆 common core、service profile 和 specialization

建议与下列文档配合阅读：

- [标准化文档总览](../README.md)
- [文档对齐映射](../overview/document_alignment_map.md)
- [运行时工作流与合同基线](runtime_workflow_and_contract_baseline.md)

## 本文档负责什么

本文档回答三个问题：

1. 当前 loader/compiler 能直接消费哪些场景字段？
2. 哪些字段只是“当前实现还在用的 JSON seam”，而不是长期稳定的标准语义？
3. 场景编写时，如何区分上游 tasking intent 和下游 executable command？

它不负责定义：

- 联合层 command relationship
- 军种 doctrine
- 完整的 runtime DTO 合同

## 与当前 runtime 的关系

当前场景链路大致是：

`scenario JSON -> loader/compiler -> task + mission command 规范化 -> behavior/command-chain update -> runtime step inputs -> mission observation/reward/termination products`

仓库中的主要入口包括：

- [gym_envs/scenario_loader/loading.py](../../../gym_envs/scenario_loader/loading.py)
- [gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py)
- [gym_envs/scenario_loader/behavior_runtime/](../../../gym_envs/scenario_loader/behavior_runtime)
- [src/core/mission/runtime/](../../../src/core/mission/runtime)

因此，scenario JSON 是配置输入面，不是最终运行时合同本身。

## 与标准树的映射

在维护中的分层下：

- `joint/common core` 负责共享任务组织与 tasking vocabulary
- `services/*` 负责军种解释
- `air/` 与 `naval/` 负责执行级特化

当前 runtime 仍处于桥接阶段，所以一个场景文件中可能混合出现这几层对象。此时应遵循：

- 共享归属的概念尽量保持 generic
- 军种解释尽量回到对应 service profile
- air/naval 执行细节保留在各自 specialization 字段中

例如：

- `service_profile`、`task_family`、`tactical_unit_type` 属于 common/service 对齐字段
- `takeoff_procedure_code`、`runway_slot_code` 属于 air specialization 字段
- `task_group_id` 是共享挂点，但其海军语义由 Navy profile 解释

## 顶层结构

一个维护中的场景文件通常包含：

```json
{
  "scenario_name": "Example Scenario",
  "environment": { ... },
  "entities": [ ... ],
  "task_order": { ... },
  "mission_command": { ... },
  "objectives": [ ... ],
  "rewards": { ... },
  "meta": { ... }
}
```

并非所有场景今天都会用到所有段，但这已经是当前维护中的有效桥接形态。

## `environment`

`environment` 定义世界级运行时设置，例如：

- `time_step`
- `max_steps`
- `terrain_type`

这些字段属于引擎/runtime 配置，不属于 doctrine 或军种画像语义。

## `entities`

`entities` 定义场景中被实例化的参与方。

常见字段包括：

- `name`
- `type`
- `side`
- `pos`
- `vel`
- `heading`
- `is_agent`

这些字段定义的是世界状态和场景 roster 组成，它们本身不定义 command relationship、
authority 或 task organization。

若任务组织本身很重要，应优先通过 task/tasking metadata 与 roster/task-order bridge
来表达，而不是把组织关系编码进实体命名里。

## `task_order`

`task_order` 是场景侧的 mission tasking 对象。

它是当前最接近 common-core 一侧的命令工作流桥接对象，实践中可能承载：

- task family 或 tasking intent
- target altitude / speed / heading hint
- route 或 waypoint-oriented intent
- runtime bridge 需要的 role/slot metadata

`task_order` 应被理解为上游 tasking intent，而不是最终 executable command。

## `mission_command`

`mission_command` 是场景侧对 executable command state 的表示，在规范化后可直接被 runtime 消费。

当前维护中的常见字段包括：

- `command_code`
- `target_heading`
- `target_altitude`
- `target_speed`
- route/waypoint 信息
- air-specific 的 takeoff、runway、formation 字段
- 当前已支持的 naval station/reference 字段

它位于 scenario JSON 和 runtime command state 的桥接边界。其共享语义由
joint/common-core command baseline 约束，其服务/平台扩展则由 `air/` 或 `naval/` 约束。

## `objectives`

`objectives` 定义成功条件或 mission phase 完成条件。

当前维护中的常见形态包括：

- `conditional`
- `capture_zone`

其中的 property 名称可能引用 runtime 暴露的值，例如 altitude、speed、runway geometry、
localizer/glideslope error 等。

这些 property 名是当前 runtime-contract 输入项，不代表它们全部都是 common-core ontology。

## `rewards`

`rewards` 定义 shaping 与 penalty 配置。

例如：

- `survival`
- `crash_penalty`
- task-specific shaping config

reward config 属于 runtime workflow bridge，不应用来偷偷承载军种 doctrine 命名。

## `meta`

`meta` 用于承载 loader/compiler 可以消费、但不应被视为 executable command state
的场景级元数据。

适合放在 `meta` 里的内容包括：

- 注释性信息
- 实验旋钮
- 编译/运行时开关

而不应把这些信息强塞进 mission tasking 字段。

## 编写规则

编写或修改维护中的场景时：

1. 真正跨域的概念优先使用 common/service 术语。
2. 只把 air/naval execution semantics 放进各自特化字段。
3. 保持 `task_order` 与 `mission_command` 的意图分离。
4. 不要仅靠实体命名模式去编码 authority/organization。
5. 若需要新增语义，优先增加显式 metadata 字段，而不是重载无关 command 字段。

## 相关文档

- [运行时工作流与合同基线](runtime_workflow_and_contract_baseline.md)
- [联合指挥与建模基线](../joint/command_and_modeling_baseline.md)
- [联合命令链与汇报基线](../joint/command_link_and_reporting_baseline.md)
- [美国海军画像](../services/navy.md)
- [空中平台标准总览](../air/README.md)
- [海军标准总览](../naval/README.md)
