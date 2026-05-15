# 文档对齐映射

本文档用于明确“哪些文档是当前主依据、哪些文档是专用补充、哪些文档已经归档”。

## 1. 当前有效的主依据

### 1.1 Joint / Common Core

当前联合层主依据：

- [Joint 标准总览](./joint/README.md)
- [Joint 指挥关系与建模基线](./joint/command_and_modeling_baseline.md)

它们负责定义：

- 联合层 command relationship
- authority delegation
- task organization 的通用模板
- commander intent / order / report 的共通骨架

### 1.2 Service Profiles

当前军种 profile 主依据：

- [USAF Profile](./services/air_force.md)
- [US Army Profile](./services/army.md)
- [US Navy Profile](./services/navy.md)
- [US Marine Corps Profile](./services/marine_corps.md)

它们负责定义：

- 哪些层级适合进入 tight-loop runtime
- 哪些层级只应保留在 operation / scenario / campaign 层
- joint/common core 如何在各军种中具体落地

## 2. 当前仍有效但属于专用补充的文档

### 2.1 Air Platform/Task Specialization

以下文档仍有效，但不再作为全项目的共通标准：

- [Air 标准总览](./air/README.md)
- [obs.md](./air/obs.md)
- [act.md](./air/act.md)
- [aim.md](./air/aim.md)
- [rep.md](./air/rep.md)

它们只负责：

- air platform 的观测、动作、命令、报告语义

它们不负责：

- 定义 joint/common core
- 统一海战或陆战的指挥链

## 3. 已归档文档

以下文档仅保留作历史参考：

- `docs/standards/air/com/*.md`
- `docs/standards/air/com/two_ship/*.md`
- `docs/architecture/*.md`
- `docs/architecture/layers/*.md`

这些文档之所以归档，不是因为它们完全错误，而是因为它们建立在
“air-first 再尝试泛化”的路径上，已经不适合作为当前主基线。

## 4. 对项目代码的直接对齐含义

从文档标准出发，代码层后续应按以下方向对齐：

### 4.1 应尽量上提到 common core 的概念

- `command relationship`
- `authority scope`
- `task_family`
- `service_profile`
- `tactical_unit_type`
- `role_code`
- `coordination_mode`
- `recovery_site_id`

### 4.2 应尽量下沉到 air specialization 的概念

- `CAP`
- `runway`
- `approach_type`
- `wingman`
- `element`
- `flight`

说明：

- 上面的 air-specific 词汇在空战实现里仍然有用
- 但它们不应继续主导 core 层命名与通用模板

## 5. 推荐维护方式

后续新增文档时，先判断其层级：

1. 如果是跨军种共通关系，放 `joint/`
2. 如果是军种组织与控制方式，放 `services/`
3. 如果是平台或任务专用语义，放 `air/` 或未来的 `naval/`、`land/`
4. 如果是历史设计与已废弃路线，显式标 `ARCHIVED`
