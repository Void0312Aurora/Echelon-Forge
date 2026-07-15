# 杀伤链期望标准化

状态：`2026-07-06` accepted / retained expectation-standardization track +
post-P5 KCES harness diagnostics、component-response 量化、standards-layer v0
期望包络，以及基于既有匀速 before report 的只读 envelope audit。本子项目先定义
理想化杀伤链期望合同，再考虑 runtime 参数校准。它不声明真实 AIM-120C、F-16C、
确定性引信或 Pk 权威。

语言：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- 父级 A2 入口：[../README.zh.md](../README.zh.md)
- 既有杀伤链校准记录：
  [../kill_chain_guidance_lethality_calibration_20260621.zh.md](../kill_chain_guidance_lethality_calibration_20260621.zh.md)
- 既有机制解耦记录：
  [../kill_chain_mechanism_decoupling_analysis_20260621.zh.md](../kill_chain_mechanism_decoupling_analysis_20260621.zh.md)
- 校准 admission gate：
  [../kill_chain_calibration_admission_gate_20260621.zh.md](../kill_chain_calibration_admission_gate_20260621.zh.md)
- 梯度真实性原则：
  [../../../../standards/foundation/gradient_realism_principles.zh.md](../../../../standards/foundation/gradient_realism_principles.zh.md)
- 公开来源准入标准：
  [../../../../standards/foundation/public_data_source_admission.zh.md](../../../../standards/foundation/public_data_source_admission.zh.md)
- 标准维护政策：
  [../../../../standards/governance/standards_maintenance_policy.zh.md](../../../../standards/governance/standards_maintenance_policy.zh.md)
- 仓库 AIM-120C-like 代理描述：
  [../../../../../examples/config/database/weapons/air_to_air/aim_120c.json](../../../../../examples/config/database/weapons/air_to_air/aim_120c.json)
- 仓库 F-16C-like synthetic 目标描述：
  [../../../../../examples/config/database/aircraft/units/f16c_block50.json](../../../../../examples/config/database/aircraft/units/f16c_block50.json)

## 目的

本子项目为杀伤链校准建立上游期望标准。当前需要先回答的不是“哪个数字调大”，
而是项目应如何声明发射窗口、制导最近距、近炸触发、战斗部载荷场、部件响应和后果投影
各自的理想化期望。

第一参考对象是 AIM-120C-like 主动雷达、blast-fragmentation 工程代理对
fighter-size synthetic 目标。这个措辞是刻意的：它是仓库工程期望包线，不是真实
AIM-120C 性能声明。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 制导 / 杀伤症状诊断 | retained | 父级 A2 目录下既有 8 km / 30 deg 记录 | 描述当前行为，不是期望标准。 |
| 杀伤链阶段解耦 | retained / diagnostics implemented | 既有 facade、scalar ledger、named load factors 和 response-owner records | 支撑分阶段校准检查，但不决定理想结果。 |
| 校准准入 | engineering proxy guarded | P6 gate 允许单层 engineering-proxy planning | 不授予真实世界权威或跨层调参。 |
| 期望标准化 | accepted / retained with standards planning supplement | 本子项目、P1-P5 closeout、post-P5 KCES harness diagnostics 和 standards-layer expectation envelope | 文档和只读诊断；不改 runtime 参数，不授予 calibration authority，也不授予真实世界权威。 |

## 范围

纳入：

- 在参数校准前定义理想化阶段期望。
- 使用归一化 miss distance 和已声明半径，而不是未声明的固定米数结论。
- 拆开发射窗口、制导、引信、战斗部、部件响应和后果期望。
- 提供 AIM-120C-like 种子画像和通用空空模板。
- 所有结论限制在仓库 engineering-proxy authority 内。

不纳入：

- 不声明真实 AIM-120C 战斗部、引信、破片形态或 Pk 权威。
- 不声明真实 F-16C 易损性或部件失效权威。
- P0 docs 种子不做 runtime 调参、descriptor 编辑或测试修改。
- 不用当前 runtime 的强弱输出倒推期望标准。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 创建子项目并冻结权威措辞。 | 用户要求标准化子项目。 | README、任务簇、状态、队列、archive 入口和父级 A2 链接存在。 | pass |
| `P1 Expectation Contract` | 起草理想化阶段合同和 AIM-120C-like 种子画像。 | P0 边界成立。 | 合同声明阶段、归一化分区、profile 字段、禁止声明和 `R_effect_policy=independent_review_variable`。 | pass |
| `P2 Scenario Matrix` | 将合同转成距离 x 偏置角 heatmap 约束。 | P1 合同完成审阅。 | heatmap 拆分 nominal、marginal 和 outside-envelope cells，包含锚点网格、推荐主采样网格、机动 sparse grid、边界加密预算，并选择第一轮 `R_effect_variant` 评价集。 | pass |
| `P3 Metric Mapping` | 把定性分区映射到可测报告字段。 | P2 矩阵存在。 | 指标引用 stage report 字段、`R_effect_variant` 派生规则、heatmap report row schema 和 guard 字段，但不选择 runtime 参数值。 | pass |
| `P4 Calibration Harness Plan` | 把单层 calibration dry run 绑定到期望分区。 | P3 指标存在且 P6 guard 可用。 | 计划命名单层 before/after 检查、frozen-stage guard、artifact family、case-grid batch 和 worker pilot 策略。 | pass |
| `P5 Standard Promotion Decision` | 判断稳定内容是否提升进 `docs/standards`。 | P1-P4 已审阅。 | 原 task-local workstream 继续 retained；后续 v0 期望包络已注册为空中特化 planning supplement，不是 runtime contract。 | pass |

## 任务簇

- 任务簇计划：
  [kill_chain_expectation_standardization_task_clusters_20260621.zh.md](kill_chain_expectation_standardization_task_clusters_20260621.zh.md)
- 当前派发队列：
  [kill_chain_expectation_standardization_dispatch_queue_20260621.zh.md](kill_chain_expectation_standardization_dispatch_queue_20260621.zh.md)
- 当前状态：
  [kill_chain_expectation_standardization_current_status_20260621.zh.md](kill_chain_expectation_standardization_current_status_20260621.zh.md)

## 输出和证据

- 初始理想化期望合同：
  [kill_chain_idealized_expectation_contract_20260621.zh.md](kill_chain_idealized_expectation_contract_20260621.zh.md)
- 初始场景期望矩阵：
  [kill_chain_scenario_expectation_matrix_20260622.zh.md](kill_chain_scenario_expectation_matrix_20260622.zh.md)
- 指标映射和 heatmap report row schema：
  [kill_chain_metric_mapping_20260623.zh.md](kill_chain_metric_mapping_20260623.zh.md)
- 组件响应量化阈值附录：
  [kill_chain_component_response_quantization_20260705.zh.md](kill_chain_component_response_quantization_20260705.zh.md)
- 标准化期望包络：
  [空空杀伤链期望包络](../../../../standards/air/kill_chain_expectation_envelope.zh.md)
- 校准 harness 计划：
  [kill_chain_calibration_harness_plan_20260623.zh.md](kill_chain_calibration_harness_plan_20260623.zh.md)
- 标准提升决策：
  [kill_chain_standard_promotion_decision_20260623.zh.md](kill_chain_standard_promotion_decision_20260623.zh.md)
- Harness 初始实现：
  [kill_chain_harness_implementation_20260623.zh.md](kill_chain_harness_implementation_20260623.zh.md)
- 匀速 anchor before-report 可视化入口：
  [kces_anchor_cv_visualization_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_visualization_summary_20260623.md)
- 匀速 anchor first-review-stage 归因入口：
  [kces_anchor_cv_first_review_stage_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_summary_20260623.md)
- 匀速 anchor component-response 局部诊断入口：
  [kces_anchor_cv_response_diagnosis_summary_20260628.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_summary_20260628.md)
- 匀速 anchor 期望包络审计入口：
  [kces_anchor_cv_expectation_envelope_summary_20260706.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_summary_20260706.md)
- 修正机制连续包络重建：
  [第四阶段结论](../review_packets/kill_chain_guidance_envelope_rebuild_20260715/kill_chain_guidance_envelope_rebuild_20260715_conclusions.zh.md)
- 受约束制导标量校准：
  [第五阶段结论](../review_packets/kill_chain_guidance_scalar_calibration_20260715/kill_chain_guidance_scalar_calibration_20260715_conclusions.zh.md)
- P0-P5 本身只产出文档和合同语言。P5 后的 initial harness implementation 新增只读
  diagnostic wrapper、测试、heatmap 可视化、首阶段复核归因和 component-response
  report-level local diagnosis；后续 envelope audit 把 standards-layer v0 期望
  包络作为只读后处理器应用到既有 before report。before report 现在还保留逐部件
  `component_detail` load/response 配对，但该配对由共享
  `component_detail_projection.py` 从既有 runtime facade 只读投影而来，并由
  response diagnosis 消费；它刻意不改 runtime descriptor、默认参数、仿真行为或
  校准数据。

## 验收门

本子项目只有在以下条件满足后才能标记为 accepted：

- 理想化期望合同能区分发射窗口、制导、引信、战斗部、部件响应和后果期望。
- AIM-120C-like 种子画像声明每个使用到的代理假设。
- 合同能通过已声明半径判断 10 m 量级 miss 属于核心、有效、边缘还是包线外，
  而不是凭空断言。
- 后续校准能把每个期望映射到唯一杀伤链阶段，或显式标为跨阶段。
- P5 已记录标准提升决策：原 P1-P4 workstream 继续 retained；后续 v0 期望包络
  注册在 `docs/standards/air` 下作为 planning supplement，但不成为 runtime
  contract。
- 真实武器、真实目标、确定性引信和 Pk 权威仍保持拒绝，除非未来 admission gate
  显式授予。

## 残余和下一步

- `P1-A` 已按 pass 收口，`R_effect` 保持独立 review variable。
- `P2` 已按 pass 收口，约束距离 x 偏置角 heatmap：`4/6/8/10/12/16 km`
  和 `0/15/30/45/60/75/90 deg` 只是锚点网格；推荐 P3/P4 主采样使用
  `4..16 km` 每 `1 km`、`0..90 deg` 每 `5 deg` 的 signed bearing 网格，
  约 `572` cases / seed，并对 `N/M`、`M/O` 边界追加局部加密；
  并选择 `REV-RUNTIME-PROJECTION`、`REV-EQ-FUZE` 和 `REV-SMALLER-LOAD` 作为
  第一轮评价变体；`REV-DECLARED-EFFECT` 保持 held。
- `P3` 已按 pass 收口，把 heatmap cells、采样层级、`R_effect_variant` 和
  owner guard 映射到 stage-report / derived-report 字段；`REV-SMALLER-LOAD`
  仍要求 P4 显式声明 `declared_effect_radius_m`，没有默认米制值。
- `P4` 已按 pass 收口，把 P3 report row schema 写成 harness plan，包含
  `32` worker pilot batch、`48-64` worker 上调条件、P6 delta guard 和 frozen-stage
  规则；`guidance_approach` 在本 harness 中保持只读诊断层。
- `P5` 已按 pass 收口：原 P1-P4 workstream 继续 accepted / retained；后续 v0
  expectation envelope 已注册到 `docs/standards/air` 作为 planning supplement，
  仍不是 runtime contract，未来 runtime-contract promotion 仍需验收
  runtime/test/admission 证据。
- P5 后已启动 initial harness implementation：`tools/diagnostics/kill_chain_expectation_harness.py`
  可生成 `anchor-grid` case grid，并已生成完整匀速目标 `78` case before report；
  `tools/diagnostics/kill_chain_expectation_visualize.py` 已把该 before report 渲染为
  launch class、guidance status、`rho_fuze`、max failure probability 和 effect band
  五类 heatmap；`tools/diagnostics/kill_chain_expectation_stage_attribution.py`
  已把当前 `78` rows 分成 `19` 个 `no_review_pressure` cells、`25` 个
  `marginal_observation` cells 和 `34` 个
  `negative_control_satisfied` cells。runtime variant 现在读取发射时
  `missile_runtime_projection.resolved_projection_radius_m`：`15 m * 0.60 = 9 m`。
  因而 `4/6/8 km +/-30 deg` rows 属于 `outside_effect`，
  `tools/diagnostics/kill_chain_expectation_response_diagnosis.py` 选出的
  `component_response` candidates 为 `0`。before report 仍通过共享投影保留
  `a2.kill_chain_expectation_component_detail.v1`，但这些细节不再构成当前
  runtime-projection residual。
  `2026-07-05` 已新增 post-P5
  [组件响应量化阈值附录](kill_chain_component_response_quantization_20260705.zh.md)，
  用 `p_max`、`delta_abs` 和独立 `sampled_failure_observed` 标记定义
  `trace_response` 到 `severe_response` 的 task-local 诊断分区；该附录仍是
  docs-only 标准完善，不授予 runtime calibration authority。`2026-07-06`
  的 [标准化期望包络](../../../../standards/air/kill_chain_expectation_envelope.zh.md)
  把 P1/P2/P3/addendum 注册为空中特化 planning supplement，覆盖人为定义输入、派生报告字段、
  response floor/ceiling、分布容忍度、连续性规则、cell status 和 owner-stage
  归因。只读
  [期望包络审计](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_summary_20260706.md)
  已在修正审计优先级和发射窗口分类后把该包络应用到既有 `78` 个匀速 rows：
  `25` 个 cells 为 `boundary_observation`，`53` 个 cells 为 `satisfied`，已无
  nominal guidance residual。launch / guidance 与 marginal 分类现在先于无关的
  effect metadata 检查执行。这只是后处理结果，不是重跑仿真、参数修改或真实世界
  calibration verdict。`4/6 km +/-45 deg` 在 `4..8 km` 的 `15 m` 进入边界稳定落在
  `36..38 deg` 后从 `N` 修正为 `M`；维持旧分类需要约 `N=10..12` 或 `50 g`。
  `18` 个 runtime-projection `core/effective` rows 全部满足响应下限（`14` severe、
  `4` material），`10` 个 outside-effect trace rows 均无 sampled failure。
  随后的 `2026-07-15`
  [制导机制消融](../review_packets/kill_chain_guidance_mechanism_ablation_20260715/kill_chain_guidance_mechanism_ablation_conclusions_20260715.zh.md)
  在 `20` 个左右镜像匀速案例和 `10` 个机制变体上运行了 `200` 次确定性仿真。
  结果表明 lead 是主导必要机制，PN 同样必要，而 direct APN 对 `4/6/8 km x
  30/45 deg` 核心单元只改变 `0.01..1.53 m`。移除 track filter 虽改善 `45 deg`
  miss，却会错误地把 `16 km / 30 deg` O 类负控推进 `R_fuze`；近瞬时标量
  autopilot 也只提供次要改善。因此“无 nominal guidance residual”仍只是分类结果，
  不是机制闭合。后续
  [严格机制消融](../review_packets/kill_chain_guidance_exact_mechanism_ablation_20260715/kill_chain_guidance_exact_mechanism_ablation_conclusions_20260715.zh.md)
  已完成 `320` 次精确开关运行和向量闭合验收。世界系 LOS-history PN 把核心
  `45 deg` 改善约 `5.6..7.4 m`，但同时把 `16 km / 30 deg` 从 `17.010 m`
  推到 `12.030 m`；truth-CV 又揭示 track 速度链约贡献 `3.1..4.4 m` 核心残差。
  因此当前 `45 deg -> M` 只描述 legacy runtime，N/M/O 窗口还吸收了 PN frame、
  track 估计和 capture 窗口整形，下一步必须先修机制、再重标定窗口。
  完整 `93` anchor-grid 中的
  `15` 个 mild-maneuver cases、`572` recommended-main-grid、并行 worker 和机动目标
  runtime 支持仍未完成。
- 随后的五阶段制导机制工作已按顺序完成：世界系 LOS-history PN 和世界系 CV tracker
  均已接入生产可选路径；capture 结构消融选择 disabled；修正后的三种子连续网格运行
  `1443` 次主网格和 `630` 次边界加密，得到 `N/M/O=146/32/69`，镜像、seed、35g、
  单连通和无孔洞门全部通过。第五阶段又执行 `13695` 次 OFAT/holdout 运行，比较
  `nav_gain=3.5/3.75/4/4.25/4.5`；所有非基线候选均因无材料性净收益或轮廓位移
  超限被拒绝，最终保留 `N=4`。该标量选择已完成，但默认发布仍 held：world-CV
  tracker 的 acceleration 输出固定为零，当前证据没有覆盖机动目标/APN authority，
  因而未修改 AIM-120 JSON。
- P6 engineering-proxy guarded single-layer dry-run plans 已准入；匀速候选机制的
  包络/标量批量执行现已完成，但默认 runtime 重调、descriptor 修改、真实世界
  after report 和 authority promotion 仍保持 held。

## Archive

只有当本子项目已有 replacement current-status 或 closeout surface 后，历史记录才移动到
[archive/README.zh.md](archive/README.zh.md)。
