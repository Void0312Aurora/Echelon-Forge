# ADR：已解析实验输入锁与可比性

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
