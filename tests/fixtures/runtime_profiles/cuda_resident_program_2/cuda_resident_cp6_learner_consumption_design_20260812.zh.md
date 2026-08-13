# CP-6 Learner 等价设备消费——设计草案

语言版本：
- 英文正本：[cuda_resident_cp6_learner_consumption_design_20260812.md](cuda_resident_cp6_learner_consumption_design_20260812.md)
- 中文伴随本：`cuda_resident_cp6_learner_consumption_design_20260812.zh.md`

文档类型：`plan`
生命周期：`frozen——2026-08-12 冻结范围并落地`
正本路径：`docs/plan/exact_runtime/cuda_resident_cp6_learner_consumption_design_20260812.md`
责任方：`exact-runtime / CUDA 常驻后端晋升工作线`
最后核实：`2026-08-12`

- 所属程序：[CP 晋升程序](cuda_resident_promotion_program_20260808.zh.md)，
  迭代 CP-6，门禁 G-C
- 起草人：进行中 CP-5 融合变更的独立评审者
  （按程序协议，评审者未编辑任何实现文件）
- 权限边界：本草案只提出建议，不构成授权。CP-6 须待 CP-5 关闭后由程序
  所有者冻结本范围方可开工。

## 冻结记录（2026-08-12）

程序所有者于 2026-08-12 冻结本范围：交付物按草案原样，草案留白的空位
决定如下：

- 矩阵模式 id：`no_export_learner_consumer`，由
  `cuda_resident_learner_consumption_contract.h` 拥有。
- 归一化：逐字段仿射 `(value - offset) * scale`；十五组代表性常量入契约表，
  字段身份对投影契约的打包顺序做静态断言。
- 策略输入 feature 数：15（即打包观测布局；不做特征扩展）。
- smoke kernel 保留用于生命周期覆盖。

对草案字面的偏离及理由记录于程序计划文档的落地小节：learner 模式经显式
`--learner-consumer` 探针旗标交付，而非扩展冻结的 CR2-6a `kModes` 表
（矩阵证据校验器仍钉在单世代；扩展冻结范围属 CP-8 重跑矩阵车道）；冻结的
`*_device_consumer` 模式保留 smoke 消费者，使其数据行与 CR2-6b 及
CP-5/CP-7b 基线保持可比。门禁 G-C 以 learner 模式的实测数据行关闭。

## 为什么按远期视角来写这份设计

程序的终态——也是常驻后端值得晋升的根本理由——是一条观测不再经过 host
往返的 rollout 循环：learner（本仓库即 SB3 背后的 PyTorch 策略）就地消费
设备观测，CPU 不再充当拷贝中继。晋升程序自身交付不了这个集成，因为其约束
禁止在无兼容外壳时变更公共 ABI 与 Python 面。因此 CP-6 以在 CR2-3 lease 处
测量的 **learner 等价**消费者关闭 G-C，且下文每一个接口决策都以「让日后的
真实 learner 集成是增量式而非纠正式」为取舍标准。凡是对 CP-6 足够便宜、
但将来接 torch 时必须推倒重来的选项，本草案一律拒绝并写明理由。

## 「learner 等价」的范围界定（独立评审后的更正）

lease 暴露的是常驻后端的 **fixture** 观测契约：固定空域的十五个字段。生产
训练栈今天并不消费这个面——维护中的策略吃的是跨仪表/接触/告警/任务域的
字典观测，并带逐域预处理（`python/models/transformer.py`）。因此 CP-6 关闭
的是常驻后端真正拥有的面上的 G-C：一个读取 lease 张量每个元素、在设备上
执行代表性前处理工作的消费者，是**对常驻 fixture 契约而言**的 learner 等价
消费，门禁关闭记录必须明说这一点。让生产字典观测栈常驻设备是另一个更大的
面，记入残差；本迭代既不交付也不声称它。

## 已核实的现状事实（2026-08-12，CP-5 进行中的工作树）

若 CP-5 落地形态与受评审版本不同，须重新核实。

1. lease 载荷已经具备此 fixture 面上设备侧消费者所取输入的布局。
   `pack_device_observation_kernel`
   （`src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_observation.cu`）
   把仿真侧 field 主序 SoA 转置为 world 主序、C 连续的
   `[world_count, 15]` 缓冲，并把 `double` 窄化为有限值截断的 `float`。
   learner 适配器原本要做的布局与 dtype 工作在 pack 阶段已经完成。
2. `device_consumer::TensorDescriptor`
   （`src/runtime/contracts/cuda_resident_device_consumer_contract.h`）声明
   element 单位的 `shape`/`strides`/`dtype`。element 单位 stride 与未来的
   DLPack 导出一一对应；`__cuda_array_interface__` 只需机械乘以字节宽。
   descriptor 无需日后重设计。
3. 现有消费者是 smoke kernel：`device_observation_consumer_smoke_kernel`
   每 world 只读十五个值中的一个并复制 ids。它证明的是边界存在，不是消费
   发生。这正是 G-C 点名的残差：CR2-7 记录该门禁为 true 指的是**边界**，
   不是 learner 等价消费。
4. CR2-3 的测量路径规则持续生效且继续约束本迭代：消费路径增量 D2H 为零；
   诊断物化恰好两次 D2H 且在全部 sample timer 之外；lease 携带
   allocation/reset/window/source epoch；receipt 生命期长于 consumer。

## CP-6 范围

按程序协议：一次迭代，一个连贯 commit。

1. **Learner 等价消费 kernel。** 取代 smoke kernel 成为受测消费者（smoke
   kernel 可保留用于生命周期测试）。它必须：
   - 读取 lease 值张量的每一个元素，而非探测单个元素；
   - 施加钉定的逐字段观测归一化（对原始观测的一种代表性前推理变换；今天
     没有维护中的策略消费此面，所以主张的是「代表性」，不是与某个生产前向
     的等价）；
   - 写出常驻设备的策略输入缓冲，world 主序
     `[world_count, feature_count]` `float`，与 lease 载荷同一布局族；
   - 透传 ids，epoch 校验保持不变。
2. **归一化契约单一所有者。** 归一化常量放入新契约头（`constexpr`，C++
   契约为唯一所有者）。Python 或诊断侧如需使用，按 CP-4b 以来 kernel 目录
   的派生方式从契约解析，不得出现第二份硬编码副本。
3. **经现有矩阵通道测量。** CR2 矩阵会话新增 learner 等价消费者模式
   （mode id 在 CP-6 开工时冻结），测量方式与现有 `*_device_consumer`
   模式完全一致，使数据行可与 CR2-6b 及 CP-5 后的 campaign 对比。
4. **架构门禁**，尽可能免工具链：
   - 受测消费者读取完整张量（结构性钉定，使单元素 smoke 永远无法再满足
     G-C）；
   - 测量路径零隐藏 host 回读（把 CR2-3 规则对新 kernel 重新钉定）；
   - 策略输入布局/dtype 对契约钉定；
   - 归一化常量恰有一个所有者。
5. **CUDA-on 验证。** 消费 kernel 归一化数学的 CPU 参考 parity、
   lifecycle/replay 套件全绿、并按程序的逐迭代要求记录一次真实
   RTX 3090 运行。

## 面向未来的兼容性决策

| 决策 | CP-6 选择 | 为未来买到什么 |
| --- | --- | --- |
| 策略输入布局 | world 主序 `[world, feature]` `float`，C 连续 | 日后 DLPack/`__cuda_array_interface__` 导出零变换包装该缓冲；`torch.from_dlpack` 零拷贝得到该张量。 |
| stride 语义 | 沿用 element 单位的 `TensorDescriptor` | DLPack stride 即 element 单位；descriptor 无迁移。 |
| 同步 | 保持基于事件的排序：lease 钉定 `producer_stream = 0`（契约中的 `legacy_default_stream`），消费者用 `cudaStreamWaitEvent` 对 ready event 排序，绝不做设备级同步 | ready event 就是未来 torch 导出所等待的对象。legacy 默认流身份是当前钉定而非终态：导出设计必须显式决定流互操作的映射。 |
| 生命期/安全 | epoch 与共享所有权的 lease/receipt 语义不变 | 未来的 Python 句柄直接继承过期检测，无需另行发明。 |
| 暴露面 | 消费者保持私有 seam；不动 `RuntimeFacade` 与绑定 | 公开暴露是晋升范围的决策（CP-9 或之后），不是测量迭代的副作用。 |
| 归一化所有权 | 契约头，单一所有者 | torch 侧前处理将来读同一份常量；CPU/GPU/learner 三方永远不会静默漂移。 |

## 非目标

- 不做 learner update、不做训练循环集成：CR2-3 关闭记录的表述（「这不等于
  learner update 已实现」）继续成立；G-C 要求的是被测量的 learner 等价
  消费，不是训练。
- 不变更公共 ABI、Python 名称、CLI 标志或配置键。
- 不做超出矩阵数据行的性能主张，不授予晋升、支持标志或调优权限。四个
  授权标志全部保持 false。

## 前置条件与顺序

1. **CP-5 先关闭。** 截至本草案，融合 commit、变更后矩阵 campaign 与 v3
   静态重捕获正在本工作树进行。CP-6 从该落地状态起步。
2. **计数器链版本感知（属 CP-5/CP-8 车道，记录在此以免遗失）。** CP-5 独立
   评审发现 `tools/diagnostics/cuda_resident_cr2_counter_evidence.py` 仍钉在
   融合前世界：`PARENT_PROFILES` 只接受 v1/v2 profile id、
   `REQUIRED_LAUNCH_COUNT = 12`、Nsight Compute 调用硬编码
   `--launch-count=12`。v3 计数器捕获（7 次 launch、5 个 kernel）会被我们
   自己的采集器拒收——与 CP-4c 记录的是同一失败类别。服务于未来的修法是
   **派生而非再钉一版**：父 profile、launch 数与 kernel 身份经由既有的
   `kernel_catalog(version)` / `launch_sequence(version)` 访问器从契约取得。
   此后新世代不再于任何位置重钉 launch 数或命令预算；它仍需在 schema 模块
   注册一次身份、在 parser 注册一次测量单位映射。该项落地前不得申请提权
   采集会话。
3. CP-7（小批量处置）继续排在 CP-5 证据之后：launch 链缩减本身可能已改变
   world-1 的格局，「修复还是阈值路由」应先读融合后的矩阵数据再定。

## 本迭代必须产出的验收证据

- learner 等价消费者模式的矩阵 campaign JSON 数据行，可与 CR2-6b 及
  CP-5 后基线对比。
- 含归一化 CPU 参考 parity 的 C++ 消费者测试；在记录主机上 CUDA-on
  lifecycle/replay/full-window 套件全绿。
- 新架构门禁在 `ci_smoke_suite.json` 中转绿，外加常规
  `git diff --check` 与本文档对的双语审计。
- 程序文档中的迭代记录，含对本草案的任何偏离及理由。

## 有意留白的残差

- DLPack/`__cuda_array_interface__` 导出本体及任何 torch 侧消费者仍是
  晋升后工作；本草案只保证其路径畅通。
- 生产字典观测栈（仪表/接触/告警/任务域，带逐域预处理）没有设备常驻路径，
  也不在 CP-6 门禁关闭的覆盖范围内；为它建路是 fixture 面验证模式之后的
  独立程序范围。
- learner 等价消费者是否也应服务 leader/world-batch 协同通道，在空域线
  验证该模式之前不在范围内。
- 本草案在目录 README 阅读序中的注册推迟到 CP-6 冻结 commit 一并完成，
  以保证草案与进行中的 CP-5 会话零冲突。
