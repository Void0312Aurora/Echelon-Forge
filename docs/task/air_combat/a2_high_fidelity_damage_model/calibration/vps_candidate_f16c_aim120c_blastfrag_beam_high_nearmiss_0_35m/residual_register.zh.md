# Residual Register

状态：非权威 candidate 残差登记表。所有初始条目默认 open；任何 open residual 都阻止本候选包被描述为已校准或 authoritative。本文档不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

候选 scope 固定为：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。

## 当前残差

| `residual_id` | 区域 | 残差描述 | 对 scope 的影响 | 阻塞的 authority | close 条件 | 状态 |
|---|---|---|---|---|---|---|
| `RES-001` | source provenance | source ledger 尚未填入稳定 `source_ref`、checksum、权利和保留位置 | 无法证明输入、benchmark 或 criteria 可追溯 | 全部 | source ledger 完整并经审阅 | open |
| `RES-002` | surrogate identity | 候选 surrogate 的 `model_ref`、代码版本、配置和运行 manifest 未定义 | 无法复现实验或验证结果 | 全部 | model card 补齐版本、manifest 和复现说明 | open |
| `RES-003` | target geometry | F-16C Block 50 组件几何、材料、遮挡和暴露面积来源未审计 | 可能把工程 hitbox 当成真实 vulnerability | effect scale / component probability | geometry 来源、假设和误差界限可追溯 | open |
| `RES-004` | warhead scope | AIM-120C-class blast-fragmentation 候选参数未与可公开、可审计来源绑定 | 可能过拟合或暗示未知具体弹药参数 | effect scale / mechanism load | warhead class 假设、范围和敏感性分析完成 | open |
| `RES-005` | fragment mechanism | 破片质量、速度、方向 pattern、areal density 和穿透模型未验证 | 破片载荷 row 门槛不可作为权威 | component probability | benchmark 覆盖 fragment-energy / areal-density residual | open |
| `RES-006` | blast mechanism | blast scaled distance、超压、冲量和结构耦合未验证 | 爆轰载荷 row 门槛不可作为权威 | effect scale / component probability | benchmark 覆盖 blast residual 与适用区间 | open |
| `RES-007` | near-miss bucket | `near_miss_0_35m` 桶的采样密度和边界行为未定义 | 单点近失可能被误当作整个桶 | 全部 | bucket 内多点覆盖和边界敏感性报告完成 | open |
| `RES-008` | beam/high closure | `beam` 与 `high` 的定义、速度范围和姿态扰动未固化 | scope 可能泄漏到其他 aspect/closure | 全部 | scope 轴定义和 out-of-scope 检查通过 | open |
| `RES-009` | component failure | 组件失效概率与机制载荷之间的映射未由独立 benchmark 验证 | synthetic probability 可能被误提升 | component probability | 概率 residual、校准曲线和 uncertainty 通过预设门槛 | open |
| `RES-010` | validation criteria | 验收指标和门槛仍是 `<待定义>` | 不能判断 surrogate 是否通过 | 全部 | criteria 在结果产生前冻结并记录来源 | open |
| `RES-011` | uncertainty | 随机性、模型误差和输入不确定性未量化 | 无法解释 residual 分布或置信区间 | effect scale / component probability | uncertainty coverage 指标通过预设门槛 | open |
| `RES-012` | independence | benchmark 是否独立于模型输入、调参和训练来源未证明 | 验证可能循环引用 | 全部 | benchmark/input 分离审计完成 | open |
| `RES-013` | Pk boundary | 本候选包未覆盖 kill-chain Pk 校准 | 任何 Pk 声称都越界 | Pk | 不在本包关闭；需独立 Pk 证据链 | open |
| `RES-014` | deterministic fuze boundary | 本候选包未覆盖 live fuze trigger、target signature、reliability 或 miss-distance/fuze 联合验证 | 不能替换 RNG hit gate | deterministic fuze | 不在本包关闭；需独立 fuze/kill-chain 证据链 | open |

## Closeout 规则

- 关闭 residual 必须引用 source ledger、model card 或 validation report 中的稳定 artifact，不接受口头结论。
- `RES-013` 和 `RES-014` 是本候选包的 scope boundary，不应在本目录内关闭为已授权；只能在独立证据链存在后标注为外部处理。
- 任何 residual 关闭后仍需检查是否引入新的 out-of-scope 声称。
- 在所有适用 residual 关闭前，`calibration_status` 必须保持 `unvalidated`，所有 authority 字段必须保持 `false`。
