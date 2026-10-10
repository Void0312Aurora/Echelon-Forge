# ADR：策略观测与动作字段级接纳

**状态：** 待评审的资格验证设计；现有 `DecisionModel`、Gym space 和领域 packet owner 不变。

引入可选、非权威的 policy compatibility descriptor，用于协商字段级 observation/action 契约，
并降低到现有 `ObservationViewSpec`、Agent/role 权限、命令端点和 owner 管理的生命周期接纳。
descriptor 不替换 `DecisionModel`，不把 `model_kind` 变成权限系统，也不把作者声明的 category
视为 authority。

字段声明稳定 ID/version、shape、dtype、单位、坐标系、时序、truth/belief 可见性、可选性和源
authority；动作还声明端点、边界、时序和所需权限。缺失字段、shape/unit/version 冲突、未授权
truth、未支持动作族、越界和时序冲突必须在 policy binding 或 runtime side effect 前拒绝。

未知 category 只保留为元数据，不授予能力；minor/optional projection 需显式默认策略并保持
tensor 顺序和 provenance。资格证明应保留现有输出和默认 structural-only 行为。
