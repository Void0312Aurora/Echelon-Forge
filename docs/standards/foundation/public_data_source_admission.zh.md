# 公开数据来源准入标准

Language:
- English canonical: [public_data_source_admission.md](public_data_source_admission.md)
- Chinese companion: `public_data_source_admission.zh.md`

状态：`2026-06-01`，公开来源准入、研究级候选数据和运行时权威门控的 foundation 层权威规则。

本文定义公开数据、论文、标准、报告、生成 benchmark 和 source ledger 如何进入项目。它适用于 air、naval、ground、joint command、sensor、weapon、damage model、visualization 和未来领域。

核心规则是：

> 来源可以先支持文档、方法设计、benchmark 或 residual 跟踪；只有通过明确的 scope、provenance、权利、验证和 residual closeout 门控后，才可能支持运行时 authority。
>
> 在许多高真实度仿真领域，官方或权威校准数据通常不可获得。第三方、社区或开源资料可以被采纳为候选来源，但必须显式标记来源层级、provenance、权利状态、合理性评估和 residual；引用时不得把它们冒充为官方或校准权威。

## 仓库许可边界

本仓库的项目代码和维护文档采用 Apache-2.0 许可。该项目级许可不授予第三方输入资料的权利。

公开论文、数据集、厂商材料、社区代码、可视化资产、保留 source payload
以及依赖这些输入生成的 artifact，仍必须记录其自身的来源、许可证、版权、出口、
再分发和署名状态。如果某个外部输入按照其自身条款不能被复制、再分发，或不能用于生成保留输出，
仓库级 Apache-2.0 许可不会修复这个缺口。

## 来源层级

| 层级 | 可接受来源 | 允许用途 | 限制 |
| --- | --- | --- | --- |
| `Tier A / official-standard` | 公开标准、官方公开文档、政府报告、公开教材、公开论文、公开验证方法 | 方法引用、validation criteria、可复现 benchmark 设计、公开政策或术语基线 | 仍需 scope 匹配、权利检查和可复现记录 |
| `Tier B / public-engineering` | 厂商公开资料、公开审计/国会文件、公开课程材料、可识别发布方的营销或产品 fact sheet、带可追溯作者/版本/许可的第三方工程资料 | 工程量级、平台/武器/传感器族候选、几何或组件布局候选、非权威参数候选 | 必须标注近似和第三方性质；不能单独作为型号级真值 |
| `Tier C / sanity-check` | 民间数据库、开源配置、可追溯社区数据集、论坛汇编、百科式二手资料 | 关键词发现、符号/单位 sanity check、粗量级交叉检查、候选假设生成 | 必须标注社区/二手来源和合理性评估；不能单独授予 calibrated authority |
| `rejected` | 受限、不可再分发、不稳定、缺 provenance、可疑、泄露、权利不清或 scope 不匹配来源 | 只记录拒绝原因 | 不能进入 descriptor row、生成 benchmark 或运行时数据 |

## Source Ledger 必填字段

每条 source ledger 记录必须包含：

- `source_id`；
- 来源层级和类别；
- 稳定 `source_ref`，例如 DOI、URL、报告编号、官方目录记录、归档引用、ISBN、代码 commit 或 benchmark manifest；
- 发布方、持有人或负责机构；
- 可公开性、许可证、版权、出口或再分发限制；
- provenance 摘要，说明数据或方法如何获得、处理、保留以及边界；
- scope 匹配，包括相关 target、platform、weapon family、aspect、closure、range、miss-distance、mechanism、sensor、component、terrain 或 command-role 轴；
- 交叉验证状态，尤其是是否有 Tier A/B 互证，或是否只能作为 Tier C sanity check；
- 合理性评估：数值范围、单位、内部一致性、与公开物理/工程常识和其他来源的冲突情况；
- ingest 状态：`pending`、`acquired`、`rejected` 或 `superseded`；
- authority 状态，默认为 `non-authoritative`；
- 采纳后仍未关闭的 residual。

若记录缺少稳定 `source_ref`、权利、scope、provenance 或 residual 状态，可以保留为搜索线索，但不得成为输入来源。

## Research / Candidate Profile 准入

研究级候选模型不等同于工业级或 release-grade authority。若任务明确声明当前目标为
`research`、`candidate`、`non-authoritative` 或 `authority_opt_in_only`，可以在不等待官方或工业级数据的情况下使用
`Tier B`、`Tier C`、社区资料、开源配置、多源派生估计或 hash-only restricted references，
但必须满足以下条件：

- 数据项必须写明 source tier、data class、scope、rights / redistribution note、
  uncertainty / confidence、cross-check notes 和 replacement rule；
- `Tier C`、社区和二手来源只能形成 sanity envelope、候选假设、参数区间或派生估计，
  不能单独成为 calibrated truth；
- 有版权或再分发限制的资料不得在仓库中复制长段正文、表格、图片或 raw selected values；
  可保留 locator、hash、短摘要、审阅记录和派生参数；
- research profile 的 residual 可以标为 `research_closed` 或 `research_out_of_scope`，
  但若 authority 证据仍缺，必须同时保留 `authority_blocked`、`authority_fail_closed`
  或 `authority_boundary_deferred` 语义；
- 任何 runtime descriptor、stock row 或 release-grade claim 仍必须通过任务专属
  authority gate。

换句话说，研究级高保真允许“先用可追溯、可替换的合理数据把模型跑通并审计起来”；
它不允许把这些数据写成官方、校准或工业级权威。

## Artifact 规则

生成数据、验证运行、模型输出和 benchmark 输出是 artifact，不自动成为来源。

一个 artifact 只有具备以下内容时才可被引用：

- 稳定 artifact 引用或保留位置；
- 生成脚本、配置和代码版本；
- 必要时的环境或容器说明；
- 随机种子策略；
- 指标定义；
- 保留输出的 checksum 或 hash；
- 所有输入的权利和再分发状态；
- 每个外部输入对应的 source ledger 引用；
- residual 和 out-of-scope 说明。

临时 workspace 路径、本地临时文件、未跟踪 notebook 和随手截图都不是长期 provenance。

## Authority Gate

任务专属 runtime authority gate 必须声明允许的 `source_kind` 和必填 manifest 字段。在该 gate 被定义并通过之前，所有已采纳来源都只是文档或 benchmark 候选。

当以下任一项缺失时，runtime authority gate 必须 fail closed：

- 当前 schema 版本；
- 非空 `source_ref`；
- 非空 provenance；
- 权利或再分发状态；
- 领域所需的 scope 轴；
- calibration 或 validation 状态；
- 若来源是 surrogate，则需要 validation artifact 引用；
- 若消费生成输出，则需要 artifact checksum 或复现 manifest；
- 若 row 可被消费，则需要 row 级 `row_id`、`source_ref` 和 provenance；
- 显式的逐 authority 授权。

任何 runtime authority 放行都必须由未编写候选内容的 reviewer 给出 accepted
verdict。作者侧 snapshot、result pack、自行验收和 review-readiness 标签都不能
替代该审阅；独立审阅与 source authority 均未闭合前，相关声明仍只能是
`candidate` 或 `non-authoritative`。

Authority 按字段逐项授予。能支持几何的来源，不自动支持脆弱性。能支持 benchmark 的来源，不自动支持 Pk。能支持方法的来源，不自动支持确定性触发行为。

## Source Kind 边界

任务 schema 可以定义自己的 `source_kind`，但标准拆分如下：

- `external_calibration_dataset`：公开或权利已清理的数据集，其 scope、uncertainty、provenance 和再分发条款足以通过领域 gate；
- `validated_physics_surrogate`：带完整 validation manifest、scope 匹配、版本化代码/配置、指标、验收准则、artifact 和 residual closeout 的模型或生成 benchmark 包；
- `method_reference`：只支持公式、术语或建模结构的来源；
- `validation_criteria_reference`：支持“应该检查什么”的来源，而不是已经检查通过的结果；
- `benchmark_design_reference`：支持可复现 benchmark 设计的来源，不授予运行时 authority；
- `sanity_check_only`：只用于单位、符号、量级、命名、候选假设或边界情况检查的来源；
- `rejected`：不得作为数据使用的来源。

只有领域 schema 可以决定哪些 source kind 能进入 runtime authority。文档不得暗示 allow-list 之外的来源种类具备 authority。

## 拒绝来源

除非任务负责人能明确证明公开权利、provenance、scope 和合理性，否则以下来源必须拒绝或保持 `sanity_check_only`：

- restricted、proprietary、leaked、FOUO、CUI、ITAR、EAR 或出口管制材料；
- 未授权手册、技术令、IPB/零件目录、维修手册、训练课件、承包商附件或网盘/论坛镜像；
- 无 provenance 的游戏/商业仿真/论坛参数、匿名数据库或社区平衡数据；
- 截图、社媒、无来源表格、单行 Pk 曲线、匿名命中率图或无归属参数表；
- 当官方发布方、DOI、NTRS、NTIS、标准目录或归档入口可用时的非官方镜像；
- 只公开名称但底层数据不公开的受控工具或数据库。

拒绝来源类别可以记录下来，防止后续误用。它们不得被复制、摘要成参数或用于调运行时行为。

可追溯第三方或社区来源不应因“非官方”被自动拒绝。它们可以作为 `Tier B` 或 `Tier C` 候选进入 source ledger，但引用时必须保留标签，例如 `third_party_candidate`、`community_sanity_check`、`open_source_config_candidate` 或 `non-authoritative_estimate`，并说明为什么该数据在当前 scope 下合理或不合理。

## 声明规则

文档、训练报告、任务计划和评估总结必须：

1. 区分来源收集、方法设计、benchmark 生成、validation、calibration 和 runtime authority。
2. 按仍未关闭的最弱 residual 声明最高结论。
3. 保持 synthetic fixture、engineering scaffold 和 schema 示例的非权威语义。
4. 避免把公开公式、示例或教材方法直接转成 calibrated runtime row。
5. 避免用 reward、score 或场景终局逻辑定义物理 authority。
6. 对第三方、社区或开源资料，必须在正文和表格中标注来源性质、合理性评估和不能支持的结论。

数据形状测试通过，只证明数据通路。benchmark 通过，只证明该 benchmark 声明的 scope。二者都不自动推出更高真实性或 authority。

## 任务文档规则

任务级数据收集目录应包含：

- README，说明 scope、状态、authority 边界和相关标准；
- source ledger；
- 可选 benchmark matrix、schema mapping、residual register 或 validation manifest 草案；
- 拒绝清单；
- gate mapping，说明每类来源能支持什么和不能支持什么。

当任务创建领域专属准入规则时，该规则应链接回本标准，然后只补充任务专属 schema 字段和 authority gate。

## 与梯度真实性的关系

本标准支撑 [梯度真实性原则](gradient_realism_principles.zh.md)。如果某场景或领域模型依赖数据或验证来声明真实性梯度，则相应来源准入和 authority gate 必须先通过。

例如，武器释放场景可以在功能上达到 `G5` 链路接通，但杀伤模型仍保持非权威。只有数据来源、验证和 authority gate 通过后，才可以声明校准毁伤或确定性引信真实性。
