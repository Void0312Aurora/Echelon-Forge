<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/exact_runtime/gpu_resident_state_implementation_plan.md. Review before treating this file as authoritative. -->

# GPU 设备常驻状态实施计划

## 目标

消除 write_back 瓶颈（当前占 79% 时间），通过保持状态在 GPU 上，仅同步训练需要的观测字段。

## 当前瓶颈分析

```
总时间 = GPU kernel (11.7%) + write_back (79.1%) + overhead (8.1%)
```

write_back 需要：
1. D2H 传输完整状态 (20+ 组件)
2. 应用每个组件到 Flecs ECS 世界
3. 每个 `entity.set<Component>()` 触发内部状态更新

## 实施方案

### Phase E1: 最小观测同步

**目标**: 仅同步训练需要的字段，而非完整状态

**需要的观测字段**:
- Transform (位置、姿态)
- Velocity (速度)
- InstrumentState (训练奖励需要)
- GroundState (终止条件需要)

**实现**:
1. 创建 `GpuResidentObservationSync` 结构
2. 实现 `sync_observations_only()` 方法
3. 仅同步上述字段到 CPU

**预期收益**: write_back 时间减少 60-70%

### Phase E2: 设备常驻步进循环

**目标**: 保持状态在 GPU 上，多步执行

**实现**:
1. 修改 `step_batch()` 支持设备常驻模式
2. 添加 `set_resident_mode(bool)` 方法
3. 在常驻模式下：
   - 初始上传状态到 GPU
   - 执行 N 步 GPU 步进
   - 仅最后同步观测字段

**预期收益**: 消除每步的 H2D/D2H 开销

### Phase E3: 训练循环集成

**目标**: 修改训练循环支持设备常驻

**实现**:
1. 添加 `WorldBatchVecEnv` 的 GPU 常驻模式
2. 修改观测提取路径
3. 修改奖励计算路径

## 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `src/gpu/gpu_resident_state.h` | 新增：设备常驻状态管理 |
| `src/gpu/gpu_resident_state.cu` | 新增：CUDA 实现 |
| `src/core/engine/world_batch_runtime.h` | 修改：添加常驻模式支持 |
| `src/core/engine/world_batch_runtime.cpp` | 修改：实现常驻步进 |
| `python/rl/world_batch_vec_env.py` | 修改：支持 GPU 常驻 |

## 风险

1. **语义对等**: 需要验证观测同步不影响训练结果
2. **内存占用**: GPU 常驻需要额外内存保持状态
3. **复杂度**: 增加代码路径复杂度

## 时间表

| 阶段 | 预计时间 |
|------|----------|
| E1: 最小观测同步 | 1 天 |
| E2: 设备常驻步进 | 1-2 天 |
| E3: 训练循环集成 | 1 天 |
| 测试验证 | 1 天 |
| **总计** | **4-5 天** |
