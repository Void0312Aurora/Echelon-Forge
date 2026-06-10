# `src/components/physics` 边界

`components/physics` 保存共享物理状态 component 与 readout helper，包括动力学状态、控制律参数、力、
仪表、性能数据和 propulsion readout。它不应继续吸收 command/tasking 概念，也不应继续拥有 air-specific tuning。

## 允许

- 姿态、速度、加速度、角速度、力和质量等物理状态。
- 控制律参数、性能 envelope、仪表状态。
- 与物理系统直接读写的 ECS component。
- 共享物理状态的 readout helper，例如 propulsion fuel-flow 与 engine-RPM projection。

## 禁止

- 新增 pilot action、mission command、task order、leader intent 或 pilot report 类型。
- system tick、积分器、控制律执行逻辑。
- mission transition、episode runtime 或 Python binding。

## 迁移备注

`action.h` 是历史聚合头文件，现已降级为 compatibility umbrella header。真实类型定义已迁移到：

- `components/command/`
- `components/tasking/`

Air flight-dynamics tuning 现在只属于 `components/domains/air/platform/flight_dynamics_tuning.h`。
新增物理 component 可以继续放在本目录；新增命令或任务语义不能继续放在本目录，
新增 air-specific tuning owner 应放入 `components/domains/air/platform`。
