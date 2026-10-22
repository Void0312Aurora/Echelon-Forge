# ADR：已解析实验输入锁与可比性

语言：
- 英文规范页：[resolved_experiment_input_lock_adr.md](resolved_experiment_input_lock_adr.md)
- 中文配套页：`resolved_experiment_input_lock_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/resolved_experiment_input_lock_adr.md`
Owner: `architecture/experiment-contracts`
Last verified: `2026-10-13`

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
| host mode 不同或缺失 | `incomparable` | dark/shadow 引用不证明生产执行路径 |
| 只引用锁文件，未观察到锁内语义的实际执行 | `incomparable` | 持久发布引用不等于完整实验执行 |

首个证明只证明静态 lock 构造，不证明运行重现性、native receipt 等价性或 host 持久发布。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

输入身份已深冻结，并与后续 native 证据分开；场景依赖复用 ScenarioCompiler，并在文件依赖时间戳之外校验已编译语义快照。已实现 topology 与声明 graph 身份分开。evidence join 会保留 host receipt identity、backend system-graph digest、native validator evidence digest 和 durable acknowledgement；native adapter 提供同一绑定时，冲突会 fail closed。新增的 file-bound helper 会先读取 host 发布的 canonical RunReceipt，拒绝非 canonical bytes 后再调用现有 validator，不会合成 receipt。可比性要求绑定的已校验 RunReceipt 和完整 outcome；合成 receipt 契约夹具仍保留；下面的 native receipt-reference 检查点只证明本地发布及重新读取，完整实验执行与生产 wiring 仍待验收。

native provenance source 新增可选的 `resolved_input_lock_path`，按 experiment owner
提供的 JSON 原始字节计算 digest，不重定义其 canonicalization，也不据此准入 scenario。
文件 ledger 在 admission、finalization 和 receipt 读取时验证可选锁 blob；缺失时拒绝
admission，运行中 source 变化时将宿主 receipt 标为 failed，后续 blob 丢失也会拒绝读取。

受限子进程复用 dark `RuntimeKernelCandidate`、native RunRecorder 和文件 ledger，引用
第一个 Air matrix 的编译输入锁，生成 native Aircraft、推进三步、关闭宿主，然后由只读
ledger owner 重新读取真实发布的 receipt。release/rollout 输入仍是资格夹具，不证明生产
信任或签名。此探针没有执行完整 Air 实验；明确
报告 `input_lock_semantics_executed=false`，因此比较会拒绝它。完整可比性还要求 owner
观察到语义执行为 true，且双方 `host_mode` 非空并一致；intentional input axes 不能越过
这些执行边界。

candidate 新增默认关闭的 topology 持久化选项：在关闭前调用现有 kernel owner，保存该次
运行的 realized CPU topology 原始 JSON，作为 run-retained 输出 artifact 由 receipt 引用。
它与不可变 composition seal 分开。ledger 重新读取时拒绝缺失或篡改的 topology bytes；
file-bound evidence join 在声明 topology artifact 时要求提供对应文件，核对 receipt 中的
digest、size、media、retention 及 native topology identity。这证明该单世界探针的同次
运行证据。完整 Air 执行准入、生产 wiring 和外部持久可用性仍待验收。

第一个 Air matrix smoke 要求 CUDA；Windows 开发环境仍为无 CUDA build，但维护中的
HEI checkout 有 RTX 3090 和声明配置所需的 PyTorch CUDA runtime。2026-10-22，HEI
通过现有 Python `WorldBatchVecEnv`/`RuntimeFacade` 路径，完整执行了注册的
`air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1` 512-step smoke 配置。这是实际
Air 训练执行证据，但该运行尚未在现有 native RunReceipt 边界绑定 resolved input-lock
digest，也尚未重新打开该训练运行的 durable RunReceipt。因此它只能证明执行链可运行，
不能满足 #239 可比性门槛。dark candidate 仍是独立的 receipt-reference 探针，不能替代
维护中的训练路径。

同一 HEI 环境也补充了 #239 要求的首轮 repeat/A-B 证据：使用 seed `239` 再次执行同一
注册配置并完成 512 steps；随后只替换 policy 为现有的
`SquashedMultiInputPolicy`，完成同样的 512-step 预算。两次运行都生成了正常训练
checkpoint 和 final model，但都没有在 native RunReceipt 上绑定，也没有重新打开 durable
receipt。因此它们证明了执行可重复性和可执行的 policy-only 对照面，仍不能证明可比性或
生产验收。

### 世界身份关联

世界数量相同不能证明 outcome 的 index 对应 receipt 中的世界。默认关闭的
`persist_world_scope_binding` 选项在关闭前读取实际 `RuntimeWorldRef`，沿用 native
candidate 向 RunRecorder 绑定身份的同一个 formatter，保存
`runtime-world-scope-binding` 输出 artifact。保留原有 boot、incarnation、world ID 和
world generation 含义，不用 composition instance ID 替代 receipt ID。启动前取消的
candidate 不声称存在已发布世界。

join 要求每个 expected outcome index 都有明确关联、世界身份唯一且与 receipt 一致，
并核对 host boot、incarnation 和 world epoch。关联缺失时，即使 receipt 与汇总 outcome
都为 completed，也保持 `unknown`。file-bound 关联声明还必须提供 receipt 所引用的
artifact bytes 及其匹配的 metadata。比较会重新检查保存的 scope 和逐世界完成覆盖；
不会按 receipt ID 排列顺序推导 index。已验证真实 native 单世界发布及新进程中的
blob 丢失/篡改；双世界映射测试仍是合成 owner 契约夹具。这不证明 batch 逐世界 commit、
生产信任或生产多世界准入。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。
