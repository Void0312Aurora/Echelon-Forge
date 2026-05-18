<!-- Machine-translated draft generated on 2026-05-18 from src/systems/physics/README.md. Review before treating this file as authoritative. -->

# `src/systems/physics` 边界

`systems/physics` 保存物理和飞行状态推进逻辑。

## 允许

- 空气动力学、控制、力、仪器、运动、蛙跳、地面接触等系统。
- 对 `components/physics` 和航空模型的逐帧更新。

## 禁止

- 定义物理组件。
- 任务/作业状态机。
- Python 绑定、外观模式或批处理运行时。

## 迁移备注

如果逻辑解释任务/命令并转换为物理动作，应谨慎划分：DTO 在 `components/command`/`components/tasking`，任务解释在 `core/mission`，物理执行在本目录。
