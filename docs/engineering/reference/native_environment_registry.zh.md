# 原生进程环境变量登记

语言：[英文规范页](native_environment_registry.md)；本页为中文配套。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/reference/native_environment_registry.md`
Owner: `engineering`，以及物理／控制模型负责人
Last verified: `2026-10-08`

## 内置物理配置契约

内置运行时声明 `builtin.default_physics.v1`，使用下表的固定默认值。
`SimulationKernel` 在组合接纳和执行之前拒绝这七个旧环境变量；facade 创建同一
kernel，执行相同检查。变量只要存在就报错，包括空值、非法文本和恰好等于默认值
的文本；调用方应删除变量。修改物理设置需要有明确负责人和版本的模型配置，
此次没有新增另一套环境变量配置解析机制。

| 拒绝的旧变量 | 固定值 | 负责人／原范围策略 |
| --- | --- | --- |
| `CMO_ROT_MAX_RATE_CROSS_RAD_S` | 50 rad/s | 旋转积分；原下限 1 |
| `CMO_ROT_MAX_TORQUE_NM` | 5,000,000 N m | 旋转积分；原下限 10,000 |
| `CMO_ROT_MAX_ANG_ACCEL_RAD_S2` | 10,000 rad/s² | 旋转积分；原下限 10 |
| `CMO_ROT_MAX_RATE_RAD_S` | 6 rad/s | 旋转积分；原下限 0.1 |
| `CMO_ROT_SINGULARITY_MIN_PITCH_DEG` | 85 度，经余弦得到保护阈值 | 旋转积分；原范围 70–89.9 |
| `CMO_ROT_PITCH_LIMIT_DEG` | 89 度 | 旋转积分；原范围 70–89.9 |
| `CMO_FBW_PROTECTION_MODE` | strict | 默认 Air 控制模型；原 strict／relaxed／off 别名 |

实现仍由 `rotational_system.h` 和 `default_control_model.cpp` 负责，默认数值和
strict 控制分支保持一致。它们不再首次调用时读取并缓存环境。构造之后修改变量
不会改变已有世界的动力学或 reset 设置；此时创建另一个世界会被拒绝。
此次没有新增组件。

## 身份、回放与迁移

默认组合身份只接纳上述固定值。存在覆盖变量时，启动会在产生运行证据或轨迹
之前失败。已有 executable graph hash 仍表示组合贡献身份，不是数值轨迹摘要。
旧的覆盖变量实验需要原构建和外部设置，仅凭旧种子和摘要不能证明回放可复现，
也不能静默迁移到固定默认配置。

修复前的两个独立进程使用种子 17、初始俯仰 88 度的通用 Aircraft、无风以及
一次 1/60 秒步进，默认输出俯仰 87.63375811076725 度，设置
`CMO_ROT_PITCH_LIMIT_DEG=70` 后输出 70.0 度。两者的 graph hash 均为
`6c35e313f5a67ce7d6e76824a2652fc90319b0d8788723cb90ff5270297e3399`。
新测试 `test_fixed_physics_environment.py` 覆盖独立进程拒绝、默认配置的回放、
reset、多世界和构造后的环境变化。

## 登记范围

`src` 中的进程环境读取点包含这七项真值设置，以及原生测试中的
`EF_P7_PARITY_REPORT`；后者只选择报告输出路径，保留为诊断设置。
`CMO_BUILD_DIR`、`CMO_SIM_LOG_LEVEL` 等 Python 构建／日志设置沿用现有负责人。
本登记不宣称覆盖第三方库或外部启动器自行解释的环境变量。
