# 真实性与 Authority 边界规则

Language:
- English canonical: pending, Chinese companion first by request.
- Chinese companion: `realism_authority_boundary.zh.md`

状态：`2026-05-31`，从 A2 高真实度空战毁伤模型任务文档抽取的通用边界规则。

本文档把活跃任务文档中已经稳定下来的“真实性声明 / authority / 完成口径”抽取为 foundation 层通用规则。它不新增 runtime descriptor，不授予任何 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`，也不替代具体任务文档中的 scope、residual register、validation manifest 或验收记录。

来源文档：

- [梯度真实性原则](gradient_realism_principles.zh.md)
- [A2 高真实度空战毁伤模型](../../task/air_combat/a2_high_fidelity_damage_model/README.zh.md)
- [A2 Authority Promotion Backlog](../../task/air_combat/a2_high_fidelity_damage_model/authority_promotion_backlog.zh.md)
- [A2 历史 Authority 状态审计快照](../../task/air_combat/a2_high_fidelity_damage_model/archive/20260601_doc_governance/current_authority_status_and_minimal_closeout_20260530.zh.md)
- [A2 窄域 Authority 闭环任务定义](../../task/air_combat/a2_high_fidelity_damage_model/narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md)

## 1. 高真实度是方向，不是默认声明

任务标题、项目方向或 roadmap 中出现“高真实度”时，只表示该任务追求的真实性方向，不表示当前实现已经完成全高保真模型、可信 kill chain、校准 `Pk` 或确定性引信。

任何真实性声明都必须限定到当前已经实现、进入维护路径、能在 runtime contract 或可审计产物中观察，并由证据覆盖的最高层级。低层功能接通、测试 fixture 通过、候选包成形或 test-local authority exercise 成功，都不能自动升级为更高真实性声明。

## 2. 简化模型可以接受，但必须是可信简化

项目不要求默认实现研究级、工程级或全物理精确模型。对于 runtime、场景和 RL 任务，可接受的目标是在可实现、可维护、可验证的前提下构建尽可能真实的简化模型。

这里的简化必须相对工程级全细节模型而言，不能相对游戏式或玩具化抽象而言。一个可接受的简化模型至少要保留：

- 关键状态、动作和事件之间的因果结构；
- 更优 / 更差、更强 / 更弱、更近 / 更远等相对后果方向；
- 任务真正依赖的观测、约束、风险、损伤、失效或授权后果链；
- 与当前数据、测试证据和实现能力匹配的可验证边界。

因此，为了 RL 可训练性而把物理毁伤、传感器、武器、引信、authority 或任务后果退化为单一游戏式标量，不符合本规则。RL reward、terminal override、课程 shaping 或兼容 `health` 读数只能消费 runtime 事实，不能反向定义物理 authority。

## 3. 边界和完成口径以任务文档为准

具体任务的 scope、authority 字段、source kind、residual、验收门和非目标，必须以该任务当前维护中的 README、窄域任务定义、source admission 规则、validation manifest、residual register 和 closeout 文档为准。

标准文档只抽取通用边界，不把任务进展上卷为更高 authority。尤其要遵守以下拆分：

- runtime 主链进入维护路径，只说明实现和审计通路已经稳定，不说明 stock authority 已放开；
- candidate bundle、validation scaffold、schema fixture 和 test-local descriptor 只能说明候选包或通路可审计，不说明 stock 数据库默认授权；
- row-backed `effect_scale` 或 `component_failure_probability` 只能在对应 scope、descriptor、row 和 gate 都通过时逐字段放行，不能自动推出 `Pk`、确定性引信、全武器族、全目标或更高真实性梯度；
- 任务若明确 `pk_authority=false`、`deterministic_fuze_authority=false` 或 `deferred`，任何下层进展都不得绕过该边界。

## 4. Independent review / source authority 未完成前只能称 candidate

在独立 review、source authority、rights / provenance、artifact pin、validation result、metrics / acceptance criteria、uncertainty 和 residual closeout 尚未完成前，相关模型、数据、descriptor、row、benchmark 或 bundle 只能宣称为：

- `candidate`
- `non-authoritative`
- `test-local`
- `scaffold`
- `draft`
- `sanity-check`

它们可以用于方法设计、边界冻结、runtime 通路演练、合理性检查或评审准备，但不能被写成正式 runtime authority、校准 kill probability、确定性 fuze、stock 数据库默认授权或全域高真实度完成。

即使某个窄域已经具备 author-side snapshot、result pack、retained pack 或 review-readiness gate，只要独立评审和 release-grade authority 条件仍未关闭，声明仍必须停留在 candidate / non-authoritative 层。

## 5. 抽取整合不得新增任务承诺

把活跃任务口径提升到 standards 层时，只能做稳定边界的抽取、去重和归口，不得新增原任务文档没有承诺的能力、验收范围、放行时间表或 authority 结论。

文档作者应避免以下写法：

- 把“正在推进”“已有演练路径”“候选包成形”写成“已完成 authority”；
- 把某个窄域子轴的结果外推到其他 aspect、closure、miss-distance、target、weapon family 或 platform；
- 把公开资料、第三方资料、社区资料、游戏/民间参数或工程 scaffold 写成校准真值；
- 把 runtime 测试、数据形状测试或 smoke 成功写成真实性或 kill-chain 权威；
- 把下层字段 authority 上卷成场景级 `G6` / `G7` 或全域高真实度声明。

若标准文档与活跃任务文档在具体 scope 或完成状态上看起来不一致，应优先按活跃任务文档的当前 closeout / residual / validation 记录执行，并回到标准文档更新通用规则，而不是用标准文档扩大任务 authority。

