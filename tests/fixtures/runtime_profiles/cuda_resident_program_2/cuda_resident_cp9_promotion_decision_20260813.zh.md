# CP-9 晋升裁定：范围化晋升

语言版本：
- 英文正本：[cuda_resident_cp9_promotion_decision_20260813.md](cuda_resident_cp9_promotion_decision_20260813.md)
- 中文伴随本：`cuda_resident_cp9_promotion_decision_20260813.zh.md`
- 机器可读记录：[cuda_resident_cp9_promotion_decision_20260813.json](cuda_resident_cp9_promotion_decision_20260813.json)

文档类型：`decision`
生命周期：`frozen`
正本路径：`docs/plan/exact_runtime/cuda_resident_cp9_promotion_decision_20260813.md`
责任方：`exact-runtime / CUDA 常驻后端晋升工作线`
最后核实：`2026-08-13`

- 裁定 id：`cp9.scoped_promotion.cuda_resident.20260813`
- 所属程序：[CP 晋升程序](cuda_resident_promotion_program_20260808.zh.md)，迭代 CP-9
- 裁定人：仓库所有者，2026-08-13，在「无限定晋升」与「hold」之外选择范围化晋升
- 依据：六个冻结门禁全部在追踪工件上核验为 green，加一次独立评审
  （独立上下文、零实现编辑）：零阻塞发现，推荐 `scoped_promote`
- 基准 commit：`b01a068a`（CP-8 落地）

## 裁定结论

**CUDA 常驻后端晋升为可选择、显式 opt-in 的维护后端——仅限证据实际覆盖的
范围，一步不多。**

晋升的内容：

- **面**：仅常驻 fixture 合同——每个门禁实测过的固定空域十五字段观测面。
- **选择方式**：显式 opt-in，建议下限 4 worlds。CPU 参考在**所有** world
  数下保持维护默认；world 1-3 按冻结的 CP-7a 规则
  （`cp7.small_batch_selection_rule.v1`）路由 CPU 参考，CP-8 重测确认该规则
  无需修订。
- **正确性主张,维护级**：导出状态摘要跨 lane、跨 campaign 逐位一致,选定
  切片 parity 12/12 字段在包构建时现采通过。以冻结、哈希闭环的证据与架构
  门禁背书。
- **性能主张,仅实验级**：全部时序数据出自单机（RTX 3090、balanced 电源、
  后台不受控）。按程序约束,在所有者记录第二主机证据或显式单机接受之前,
  不得成为维护性能合同。今日两者均未记录。

**不**晋升的内容：生产字典观测栈（任何门禁都未测过）、learner 更新/训练
循环集成、任何维护性能合同、kernel/launch 调优权限、任何无兼容外壳的公共
ABI 变更。

## 现在改变什么,不改变什么

本裁定记录**不改变任何运行时行为**。门面标志
（`compiled_experimental_backend`、`supports_resident_state`、
`supports_device_observation_view`、`supports_exact_gpu_backend`）保持
false；冻结工件的授权标志不做追溯编辑——它们描述各自工件授权了什么,
保持 false。

本裁定**授权**后续实现范围：带兼容外壳的公开 opt-in 选择面、其自身的
架构门禁、以及晋升后 profile 的注册。在该范围落地并通过其门禁之前,
运行时行为与裁定前完全一致。

## 门禁应用

| 冻结门禁 | 应用的证据 | 裁定 |
| --- | --- | --- |
| G-A 经公共 SPI 的整窗推进 | CP-3 移除非 SPI 入口；CP-8 报告钉定 `cuda_resident.full_window_spi.v1` 与 SPI-only 操作序列 | green |
| G-B CPU/CUDA 调用面等价 | CP-8 两条 lane 的调用面、操作序列、生产协议、主 trace 签名 `4b03b578675065d4` 逐项一致 | green |
| G-C learner 等价消费已测量 | CP-6：全张量消费者 + 契约拥有的归一化 + CPU parity oracle,按生产协议测量；范围为 fixture 合同 | green |
| G-D 达成硬件计数器齐备 | CP-4：12/12 launch、5/5 计数族有真值（占用率 8.32-11.38%、local 流量为零）；按程序记录在提权下采集 | green |
| G-E 选定切片 parity 出隔离 | CP-8 包构建时现采 parity：pass,12/12 释出数值字段全 matched | green |
| G-F 小批量默认不回归 | CP-7a 冻结路由规则 + CP-8 测量：world 1 各指标均偏向 CPU,≥4 全部偏向常驻 lane | green |

## 独立评审记录

2026-08-13 在独立上下文执行,未编辑任何实现文件。核验内容：238 条架构
门禁通过（15 个失败均为已知 g++ 缺失环境类,无一属 cuda_resident 范围）；
三个 CUDA-on 套件实机通过（16/643、4/77、6/154）；CP-8 包 80 条 campaign
比率从原始报告精确复算吻合；40/40 warmed-p50 单元相对 CR2-6b 改善,区间
[-62.2%, -1.8%]；方向翻转恰好一个（(4, host_export_no_device) mixed →
cuda_resident）；四个授权标志在全部契约与工件中为 false；门面维护边界
完好,晋升未被事实性预实施。阻塞发现：无。推荐：`scoped_promote`。

## 记录在案的缺口（随附义务）

1. **G-D 工件缺提权记录字段。** 程序约束要求计数器工件记录提权；该事实
   记录于程序计划正文而非工件本身。下一次达成计数器采集（对 v4 父级）
   必须把提权字段写入工件。
2. **达成计数器先于 CP-5 融合。** v4 执行图无达成捕获；融合 kernel 的
   占用率数字是理论值。任何调优结论需先做 v4 提权采集——且本裁定本就
   不授予调优权限。
3. **无 world 2-3 测量。** 建议下限 4 是最小实测获胜值,不是实测交叉点。
4. **v4 同步活动行带宽 [5,8] 含折叠前值 8。** 精确钉定的 API 计数
   （5 launch、3 sync）才是能捕捉折叠回归的不变量。

## 无新显式授权则禁止

变更维护默认后端；维护级性能合同主张；生产字典观测栈主张；kernel/launch
调优；无兼容外壳的公共 ABI/Python/CLI/配置变更；注册表或驱动策略修改。

## 程序收官

至此 CP-0 至 CP-9 全部完成,CUDA 常驻后端晋升程序交付裁定。后续工作
（opt-in 暴露范围、v4 计数器采集、任何第二主机证据）仅在本记录授予的
权限或所有者显式追加的权限下进行。

## 修订（2026-08-13）：PR 评审发现已解决

远端独立评审 bot 对集成 PR 提出三项阻塞发现,均已在记录与代码树中解决,
无一以削弱门禁的方式处理:

1. **G-D 提权出处。** 强制约束（"计数器工件必须记录提权"）在冻结的
   v1/v2 捕获中仅由计划文档散文承载。冻结工件保持逐字节不变;所有者豁免
   已显式写入 `recorded_gaps`（依据:哈希钉定的未提权前置尝试以
   `ERR_NVGPUCTRPERM` 失败,本身即是"提权是使能条件"的证据）,且计数器
   校验器对任何冻结后世代（v3+）的 available 捕获,若工件内缺提权记录即
   关死。
2. **G-C 证据世代。** 四份 CP-6 campaign 报告带 v1 schema id 却追加了
   learner 模式,冻结的四模式校验器拒收且无任何清单钉定其哈希。追踪包
   `cuda_resident_cp6_learner_consumption_evidence_20260813.json` 现在声明
   该世代、哈希钉定全部四份报告,其校验器（learner 扩展自检,其余原样委托
   给未改动的 v1 校验器）端到端接受;本记录的证据索引把 G-C 绑定到该包。
   自此 learner 旗标探针运行自声明
   `cuda_resident.cp6.production_matrix_probe.v2`。
3. **CUDA CI flag 覆盖。** 编译通道声称覆盖两个设备面却只启用常驻 flag,
   `src/gpu` 辅助 `.cu` 源从未过 nvcc。通道现启用双 flag,并新增架构门禁
   把通道构建的每个面映射到其所需的 CMake flag。
