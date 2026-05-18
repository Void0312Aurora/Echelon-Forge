# Runtime 性能优化分层与升级规则

状态：`2026-05-18` 活跃规划冻结。  
范围：真实性/保真度冻结后的 runtime 性能后续线。

## 1. 为什么有这个子项目

当前决策是：

- 临时冻结真实性/保真度深化线；
- 不再把继续加深真实感当作默认下一步投入；
- 把主线转向 runtime 性能测量与优化。

要完成这个转向，第一步需要一套稳定规则：什么算实现优化，什么已经算算法优化，什么会进入近似或语义权衡。

这份文档就是这套规则。

## 2. 工作假设

1. 真实性处于维护模式，不处于扩展模式，除非修正正确性 bug 迫使我们回去。
2. 性能工作必须以 benchmark 为驱动，不能凭直觉推动优化分支。
3. 默认升级顺序是：

```text
Level 1: implementation optimization
  -> Level 2: equivalent algorithm optimization
  -> Level 3: approximate optimization
```

## 3. 分级定义

### 3.1 Level 1：实现优化

定义：

- 保持相同的模拟/任务语义。
- 保持相同的对外任务契约。
- 保持相同的逻辑计算链路。
- 只减少 import 顺序、Python 调度、分配、转换、重复同步、重复刷新、buffer churn 和不必要序列化带来的开销。

典型形式：

- 去掉热路径重复工作；
- 重用已经逻辑存在的 buffer 或 cache；
- 把多个精确 API 调用压成一个已有的精确批调用；
- 减少 Python `dict` / `list` / `numpy` 物化开销；
- 修正错误入口点 / import 行为，避免走慢路径或旧路径。

非目标：

- Level 1 不允许改变计算内容，只能改变执行效率。

### 3.2 Level 2：等价算法优化

定义：

- 保留任务契约和目标语义；
- 但调整计算组织方式或算法结构，以更高效地得到同样结果。

典型形式：

- 把逐实体评估换成精确批处理；
- 把旧路径切换到精确编译路径；
- 精确增量重算并显式定义失效规则；
- 改变数据结构或遍历策略，但保持输出等价。

必需证据：

- 前后 benchmark 对比；
- 受影响任务契约的回归检查；
- 明确说明语义目标仍保持等价。

### 3.3 Level 3：近似优化

定义：

- 允许受控语义漂移或保真度损失，以换取 runtime 提升。

典型形式：

- 降低更新频率；
- 减少观察宽度或精度；
- 近似视觉 / 航迹 / 传感器产物；
- 使用更低精度或更低分辨率、会改变可观测结果的产品。

必需证据：

- 明确批准近似可接受；
- 说明漂移预算或接受边界；
- benchmark + 行为质量对比。

## 4. 参数调优归属

参数调优本身不是独立优化层。

它属于哪一层，取决于 knob 改变了什么：

- `worker_threads`、精确 backend 选择或精确 batching 开关：
  通常是 Level 1 的支撑工作。
- 只会解锁已有等价编译路径的参数：
  通常是 Level 2 的支撑工作。
- 会降低保真度、频率或观察内容的参数：
  属于 Level 3。
- reward 权重、任务阈值或场景难度设置：
  通常不算 runtime 优化，除非明确是近似策略的一部分。

## 5. 升级规则

1. 先测量。
   每次讨论优化都应从 benchmark 家族、场景或 timing 字段开始，例如 `obs_build_ms`、`state_read_ms` 或 `behavior_update_ms`。
2. 先穷尽 Level 1。
   如果成本仍主要来自 Python assembly、重复刷新或冗余精确工作，就不要跳到近似方案。
3. 只有剩余瓶颈是结构性的，才升级到 Level 2。
   例如：精确逐槽逻辑在清理实现后仍然过贵。
4. 只有 Level 1 和 Level 2 都不够时，才考虑 Level 3。
5. 每个 Level 3 提案都必须明确说明哪些语义可能漂移。

## 6. 当前仓库映射

### 6.1 当前 Level 1 桶

- benchmark / 入口正确性；
- 热路径 Python 分配和打包清理；
- 重复视觉 / 观测刷新移除；
- 在现有 runtime 契约内做精确 batch API 使用清理；
- 热路径上的 `step_info` / info 物化纪律。

### 6.2 当前 Level 2 桶

- 精确批 step-evaluation 准备；
- 更广的编译观测 / reward 导出路径；
- 精确增量数据产品重算；
- state read / reward / info export 的更大结构化 batching。

### 6.3 当前 Level 3 桶

- 作为性能优先选择，降低 visual / track refresh 频率；
- 减少 contact 数量或 observation 宽度；
- 近似或抽样的 sensor / mission 产品；
- 会改变任务可见输出的低精度路径。

## 7. 当前默认顺序

仓库当前顺序是：

1. 保持 benchmark 和 runtime 入口正确；
2. 先做活跃 runtime 链路上的 Level 1 实现优化；
3. 再判断是否还需要精确算法重设计；
4. 最后才讨论近似。

本阶段 Level 1 的配套分析文档是：

- [performance_runtime_level1_implementation_analysis_20260518.zh.md](performance_runtime_level1_implementation_analysis_20260518.zh.md)
