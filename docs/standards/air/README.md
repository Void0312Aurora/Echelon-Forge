# Air 平台专用标准总览

本目录定义项目在 air profile 下的**平台与任务专用标准**。

注意：

- 本目录不是 joint/common core
- 本目录也不是军种组织 profile 的主文档
- 本目录只负责 air platform 的观测、动作、命令和报告语义

当前应先阅读：

1. [标准化文档总览](../README.md)
2. [USAF Profile](../services/air_force.md)
3. [obs.md](obs.md)
4. [act.md](act.md)
5. [aim.md](aim.md)
6. [rep.md](rep.md)

## 1. 本目录的定位

本目录处理的是：

- aircraft/platform-level observation
- pilot action semantics
- air-specific mission / execution command semantics
- air-specific reporting semantics

它不处理：

- joint/common command relationship
- Army/Navy/Marine Corps 的战术组织结构
- 全项目统一的 common core 数据模型

## 2. 与旧 `air/com` 文档的关系

`docs/Archive/air_first_standards/com/*.md` 与 `docs/Archive/air_first_standards/com/two_ship/*.md` 当前均已归档，
原因是它们建立在旧的 air-first 标准化路线之上。

如果后续还需要空战协同或双机/四机专用标准，
应在新的 `joint/common core + USAF profile + air specialization`
框架下重写，而不是继续扩展旧目录。
