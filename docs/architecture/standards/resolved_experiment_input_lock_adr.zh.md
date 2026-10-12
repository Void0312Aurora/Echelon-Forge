# ADR：已解析实验输入锁与可比性

语言：
- 英文规范页：[resolved_experiment_input_lock_adr.md](resolved_experiment_input_lock_adr.md)
- 中文配套页：`resolved_experiment_input_lock_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/resolved_experiment_input_lock_adr.md`
Owner: `architecture/experiment-contracts`
Last verified: `2026-10-11`

**状态：** 可选的静态/资格验证投影；native composition 与 RunReceipt authority 仍是权威。

新增可选的 `ResolvedExperiment` 投影，只引用而不重算或替代现有 native composition identity、
realized scheduler topology evidence、RunReceipt 和 ledger。区分 experiment intent、解析后的
输入闭包、native admitted composition、run receipt 和 comparison profile。输入锁记录 scenario/
content/platform/force/mechanism/policy 引用、版本、evaluation protocol 和生效 seed policy，
并标记 claimed/admitted/observed/referenced。

规范化 identity 使用逻辑 ID、版本、规范化 JSON 和依赖闭包；键顺序及 import 遍历不应改变语义。
资源缺失/过期、schema 不支持和 native identity 不匹配时禁止声称完全可比。失败或 state-unknown
批次必须与成功样本隔离；声明式 composition 不等同于 Flecs realized topology。首个证明采用
不运行的 Air experiment，保持现有 Experiment、report、matrix 和 RunReceipt 默认行为不变。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

输入身份已深冻结，并与后续 native 证据分开；场景依赖复用 ScenarioCompiler，并在文件依赖时间戳之外校验已编译语义快照。已实现 topology 与声明 graph 身份分开。可比性要求绑定的已校验 RunReceipt 和完整 outcome；目前 receipt 使用合成契约夹具，真实 host 发布和持久性仍待验收。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。
