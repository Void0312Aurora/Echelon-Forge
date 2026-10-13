# ADR：策略观测与动作字段级接纳

语言：
- 英文规范页：[policy_observation_action_contract_adr.md](policy_observation_action_contract_adr.md)
- 中文配套页：`policy_observation_action_contract_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/policy_observation_action_contract_adr.md`
Owner: `architecture/agent-contracts`
Last verified: `2026-10-12`

**状态：** 待评审的资格验证设计；现有 `DecisionModel`、Gym space 和领域 packet owner 不变。

Policy 是一个一等生命周期契约：scripted、learned、human、规则、搜索和 composite 实现都可以
遵守同一契约。category 只是作者声明的可选发现元数据，不是 dispatch ABI 或权限。引入可选、
非权威的 policy compatibility descriptor，用于协商字段级 observation/action 契约，
并降低到现有 `ObservationViewSpec`、Agent/role 权限、命令端点和 owner 管理的生命周期接纳。
descriptor 不替换 `DecisionModel`，不把 `model_kind` 变成权限系统，也不把作者声明的 category
视为 authority。

Policy 与 Agent 分离：Policy 声明身份、端口和执行要求；Agent/role binding 授予 observation
可见性、authority 和 action 权限。自称 `human` 或 `commander` 的 category 不能改变仲裁权限。

字段声明稳定 ID/version、shape、dtype、单位、坐标系、时序、truth/belief 可见性、可选性和源
authority；动作还声明端点、边界、时序和所需权限。缺失字段、shape/unit/version 冲突、未授权
truth、未支持动作族和时序冲突必须在 policy binding 或 runtime side effect 前拒绝。每次决策还
必须通过现有 action endpoint 校验实际动作值、当前 mask/authorization、过期和时序；动作值只能
在 Policy 产生后校验，不能提前声称已验证。

未知 category 只保留为元数据，不授予能力；minor/optional projection 需显式默认策略并保持
tensor 顺序和 provenance。legacy `model_kind` 通过分阶段显式 bridge 迁移，确定性的 `policy_id`
选择和 category 匹配属于可选 descriptor；现有 registry kind 检查及 report 字段在单独迁移决策
前仍是权威。新增的 `PolicyRuntimeBinding` 包裹现有 `DecisionModel` 的 reset/decide/close
生命周期，保留 observation provenance，并在动作返回现有 runtime 前校验。owner 签发的
`PolicyCheckpoint` 元数据契约现在可以在 binding 前绑定 artifact digest 以及 policy、observation、
action 身份。新增的 checkpoint seam 会先校验不可变 artifact bytes，再交给 owner 提供的 loader；
framework 反序列化和模型构造仍由 owner 负责；`PolicyRuntimeBinding.from_checkpoint_artifact`
会在构造现有 binding 前完成这一步校验。维护中的 selected observation view 会先由其 owner
准入，identity/version 会进入现有 model context。binding 还可在通用 bounds/timing 校验后、
投影前调用 owner action-authorizer，由 owner 判断实时 mask、authority 和 expiry；通过后再交给
显式 owner projector。生产 native action endpoint 的实际 wiring 仍待验收。此层不会自动接纳 Python
或第三方代码；通过生产 owner 加载真实外部 checkpoint 仍待验收。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

试点复用 mission_obs_taxonomy 的 basic 任务字段和现有 Air action 维度、边界，校验来源、frame、时序、显式可选默认值、确定性选择及 legacy kind。binding 通过现有 `DecisionRuntimeAgent` 运行，模型仍拥有 reset/decide/close；维护中的 observation view 在 binding 前准入，owner authorizer 可在 projector 前拒绝实时 mask、authority 或 expiry 不满足的 action。checkpoint digest 校验及 owner-loader 协议 seam 已覆盖；生产外部 checkpoint 加载与 native action endpoint wiring 仍待验收。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。
