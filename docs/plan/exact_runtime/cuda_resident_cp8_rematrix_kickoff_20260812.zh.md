# CP-8 优化后矩阵重测——启动冻结草案

语言版本：
- 英文正本：[cuda_resident_cp8_rematrix_kickoff_20260812.md](cuda_resident_cp8_rematrix_kickoff_20260812.md)
- 中文伴随本：`cuda_resident_cp8_rematrix_kickoff_20260812.zh.md`

文档类型：`plan`
生命周期：`draft`
正本路径：`docs/plan/exact_runtime/cuda_resident_cp8_rematrix_kickoff_20260812.md`
责任方：`exact-runtime / CUDA 常驻后端晋升工作线`
最后核实：`2026-08-12`

- 所属程序：[CP 晋升程序](cuda_resident_promotion_program_20260808.zh.md)，
  迭代 CP-8
- 授权：仓库所有者于 2026-08-12 指示「启动 CP-8」。启动的含义是现在冻结
  范围并建好工具前置；它不改变程序顺序：测量本体仍按程序计划的要求，
  以 CP-5 与 CP-7 落地为门。

## CP-8 是什么

在优化后的构建上，以冻结的 CR2-6b campaign 设计重测生产矩阵
（worlds 1/4/16/64/256、双 lane、全模式），使优化后证据可与 CR2-6b
证据包直接对比。出口门禁按程序计划：优化后证据可与 CR2-6b 比较。

## 塑造本范围的两个已核实判断

1. **「顺序对调、两轮 campaign」对调的是 lane 顺序，且现有工具已支持。**
   冻结的 CR2-6b 清单设计是 `campaign_01_cpu_then_cuda` 之后
   `campaign_02_cuda_then_cpu`，`order_balanced: true`——两轮完整
   campaign，轮间对调双 lane 的执行顺序。本迭代筹备中曾有一个判断称
   矩阵探针「仅升序」的 `--worlds` 解析是 CP-8 阻塞，该判断有误并已
   撤回。探针改动不在范围内。
2. **真正的工具前置在证据链，且再次是计数器链的失败类别。** 矩阵证据
   校验器（`tools/diagnostics/cuda_resident_cr2_matrix_evidence.py` 配
   `cuda_resident_cr2_matrix_evidence_schema.py`）钉死了单一冻结世代：
   字面量 `evidence_date == "2026-08-04"`、单一 `MANIFEST_SCHEMA` /
   `EVIDENCE_SCHEMA` / `ITERATION` 身份、以及 CR2-6b 专属的建议/解读
   内容。今天的 CP-8 证据包会被我们自己的校验器拒收——与计数器链
   世代化之前 v3 计数器捕获的处境完全相同。

## 范围

1. **矩阵证据链世代化**（可在 CP-5 与 CP-7 落地前先建，镜像计数器链
   的模式）：
   - 冻结的 20260804 证据包在 v1 身份下继续逐字节通过校验；
   - v2 清单/证据世代注册一次（身份、自己的采集日期与源提交、相同的
     campaign 设计形态）；
   - 通读校验器后得到的完整钉定清单，v2 形态必须逐项重新拥有而非继承：
     字面量证据日期与 `CR2-6b` 迭代 id；`selection_policy` 按 CR2-6b 的
     建议**结果**校验（逐 world 路由规则烙在
     `selection_policy_contract()` 里）；`counter_status` 钉在 CR2-6b
     时代（`achieved_counter_gate_complete: False` 加当年的权限阻塞码，
     两者今天都已不成立）；`parity_confirmation` 钉定 12 字段的 v1
     切片；`cr2_6` 前缀的门禁键；
   - 实现时要记录的冻结决策：v2 保持跨 lane 对比形态（相同指标、逐
     world 数与模式），使两代证据包可并排阅读；把 CR2-6b 证据包作为
     哈希钉定的先前证据输入引用；去掉建议结果区块（路由权归 CP-7 的
     处置）；`counter_status` 反映采集时点的真实状态而非冻结的
     2026-08-04 时代；
   - 未知世代 fail closed。
2. **测量 runbook**（有门；所有前置齐备前不得执行）：
   - CP-5 融合、计数器链提交、CP-7 处置均已落地；采集时工作树干净
     （`source_worktree_clean_at_capture: true` 是清单的硬性要求，任何
     未提交内容都不允许存在）；
   - 机器安静：无构建、无编译器运行。2026-08-12 的污染事件（融合后
     campaign 与 ninja 扇出重叠，CPU lane 在 world 1 以上的数据不可用）
   是这条为硬性要求而非偏好的现成理由；
   - 双探针从落地 SHA 重新构建（`build-cuda` 与 `build-cpu`）；
   - campaign 1 先 CPU lane 后 CUDA lane；campaign 2 先 CUDA lane 后
     CPU lane；生产协议默认参数、完整 world 矩阵；
   - 清单带字节哈希、主机环境与诚实控制标志采集（保留 CR2-6b 设计的
     `background_load_uncontrolled` 一类诚实标志）；
   - 证据包构建后经世代化链校验，并登记进程序文档。
3. **对比目标：** CR2-6b 证据包，并显式注明 CR2-6b 测的是同一主机上的
   融合前二进制；程序约束中的单机边界继续成立。

## 非目标

- 不授予晋升、支持标志或调优权限；所有产物中四个授权标志保持 false。
- 不改探针 CLI 或 world 数顺序。
- 证据包端到端校验通过之前，不做任何性能主张。
- 评审方的污染复现重跑（`.memcheck/review_rerun/`）是诊断而非 CP-8
  证据：它跑在未提交的工作树上，天然不满足干净工作树要求。

## 顺序

1. 工具前置（范围第 1 项）作为下一个独立验证的变更实施；矩阵链不引用
   融合身份，可独立于 CP-5 提交。
2. 测量（范围第 2 项）在「全部落地前置 + 机器安静」首次同时成立的窗口
   执行。
3. CP-9 把通过校验的证据包与其余门禁证据一并消费。
