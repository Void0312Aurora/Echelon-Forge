# CUDA 常驻后端语义阶段迁移

语言版本：

- 英文主文：[cuda_resident_semantic_stage_migration_20260807.md](cuda_resident_semantic_stage_migration_20260807.md)
- 中文辅文：`cuda_resident_semantic_stage_migration_20260807.zh.md`

状态：迁移执行中，2026-08-07。

## 范围

CUDA 常驻运行时继续作为独立后端。本迁移只调整其私有执行图的命名；不会逐项替换 Flecs
类型、增加第二套公共 facade，也不会改变后端选择合同。

主要源码路径、kernel、状态字段、资源查询、诊断和维护中导航使用能力语义名称。历史 fixture
标识与已序列化 provenance 属于兼容数据，不做静默批量改写。

## 语义映射

| 语义主名称 | 兼容定义 | 能力 |
| --- | --- | --- |
| `control_preparation` | `Phase A` 表示旧控制预处理别名，`phase_a` 是其标识符形式 | 过滤并发布驾驶控制量 |
| `flight_dynamics` | `Phase B` 表示旧飞行动力学别名，`phase_b` 是其标识符形式 | 计算力、空气动力与状态积分 |
| `observation_projection` | `Phase D` 表示旧观测投影别名，`phase_d` 是其标识符形式 | 投影仪表、观测、奖励与 episode 状态 |

## 读写方清单

活跃写入方是 `src/runtime/facade/internal/cuda_resident/` 下的 CUDA world-store kernel
与快照投影；活跃读取方包括常驻后端、replay 投影、原生 CUDA 测试、架构合同测试和性能探针。

以下值可能已经存在于已保存 fixture 或证据中，因此继续作为兼容别名：

| 兼容值 | 语义替代项 |
| --- | --- |
| `cuda_resident.phase_a.direct_pilot.v1` | 控制预处理 fixture schema |
| `cuda_resident.phase_b.airframe_dynamics.v1` | 飞行动力学 fixture schema |
| `cuda_resident.phase_d.projection.v1` | 观测投影 fixture schema |
| `cuda_resident.rb5_phase_a` | 表示旧控制预处理后端身份 |
| `cuda_resident.rb6_phase_b` | 表示旧飞行动力学后端身份 |
| `cuda_resident.rb7_phase_d` | 表示旧观测投影后端身份 |
| `cuda_resident.rb6.explicit_device_reconstruction` | 表示固定翼快照 v2 provenance |
| `cuda_resident.rb7.explicit_phase_d_projection` | 表示固定翼快照 v3 provenance |
| `cuda_resident.rb7.explicit_d2d_ownership_copy` | 表示设备观测 view v1 provenance |

## 迁移与移除条件

本轮直接重命名私有实现符号和源码路径，因为仓库内全部读写方会同时更新；不增加旧名称的转发
API。

已序列化 fixture 与 provenance 值继续保持读写兼容。只有在具备带版本的新表示、读取方同时
接受新旧形式、写入方已在声明的支持窗口内持续输出语义形式，并且旧形式兼容测试可以退役后，
才允许删除旧值。在此之前，若修改暴露这些精确值的生产声明，必须添加
`internal-code: compatibility` 标记。

历史计划与测试文件名在定位旧证据确有需要时可以保留原标签；新的运行时接口和新测试必须使用
上述语义名称。

冻结的 kernel 资源证据合同及其捕获 JSON 保留原 kernel 标识与符号哈希。它们描述的是历史
二进制，不是改名后的当前源码。新的资源结论必须使用新 schema 版本并重新捕获；现有探针应在
旧 trace signature 上 fail closed，不能通过重贴标签伪造历史证据的连续性。

## 文件大小边界

本轮修改的每个实现模块都保持在 1000 个物理行以内。原 1399 行 parity-budget 合同现为
6 行兼容 include 面，其实现按责任拆为类型（221 行）、selected-slice 规则（572 行）、
profile-owned 记录（521 行）与注册表操作（115 行）。拆分同时把该合同最后一个面向运行时的
审阅批次代号改为 `selected resident-state slice` 语义说明。
