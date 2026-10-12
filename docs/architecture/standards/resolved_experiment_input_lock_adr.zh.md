# ADR：已解析实验输入锁与可比性

语言：
- 英文规范页：[resolved_experiment_input_lock_adr.md](resolved_experiment_input_lock_adr.md)
- 中文配套页：`resolved_experiment_input_lock_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/resolved_experiment_input_lock_adr.md`
Owner: `architecture/experiment-contracts`
Last verified: `2026-10-12`

**状态：** 可选的静态/资格验证投影；native composition 与 RunReceipt authority 仍是权威。

新增可选的 `ResolvedExperiment` 投影，只引用而不重算或替代现有 native composition identity、
realized scheduler topology evidence、RunReceipt 和 ledger。区分 experiment intent、解析后的
输入闭包、native admitted composition、run receipt 和 comparison profile。输入锁记录 scenario/
content/platform/force/mechanism/policy 引用、版本、evaluation protocol 和生效 seed policy，
并标记 claimed/admitted/observed/referenced。

生命周期分为两个证据时刻：运行前 input lock 冻结意图和依赖闭包，不能包含运行完成事实，
也不能创建 RunReceipt；运行后的 evidence join 只引用 owner 产生的 native admitted composition、
realized scheduler identity 和 RunReceipt/status。experiment 层不重算或替代这些 native hash。

规范化 identity 使用逻辑 ID、版本、规范化 JSON 和依赖闭包；键顺序及 import 遍历不应改变语义。
资源缺失/过期、schema 不支持和 native identity 不匹配时禁止声称完全可比。失败或 state-unknown
批次必须与成功样本隔离；声明式 composition 不等同于 Flecs realized topology。首个证明采用
不运行的 Air experiment，保持现有 Experiment、report、matrix 和 RunReceipt 默认行为不变。

可比性矩阵如下：

| 情形 | 结果 | 原因 |
| --- | --- | --- |
| resolved lock、native identity 和完整成功 receipt 都相同 | `comparable` | 所有影响真值的输入与实际执行证据一致 |
| comparison profile 明确允许的 policy-only 或 mechanism-only 变化，其他证据相同 | `conditionally comparable` | 变化轴已声明，必须单独分析 |
| 隐藏的 content、native manifest、executable graph 或 realized topology 不同 | `incomparable` | 未声明的真值变化破坏比较 |
| 生效 seed 集合不同 | 除非 profile 明确允许，否则 `incomparable` | seed identity 改变采样实验 |
| WorldBatch 部分失败、失败或 state-unknown | 与成功样本 `incomparable` | #251/#210 不证明同步成功 |

首个证明只证明静态 lock 构造，不证明运行重现性、native receipt 等价性或 host 持久发布。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

输入身份已深冻结，并与后续 native 证据分开；场景依赖复用 ScenarioCompiler，并在文件依赖时间戳之外校验已编译语义快照。已实现 topology 与声明 graph 身份分开。可比性要求绑定的已校验 RunReceipt 和完整 outcome；目前 receipt 使用合成契约夹具，真实 host 发布和持久性仍待验收。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。
