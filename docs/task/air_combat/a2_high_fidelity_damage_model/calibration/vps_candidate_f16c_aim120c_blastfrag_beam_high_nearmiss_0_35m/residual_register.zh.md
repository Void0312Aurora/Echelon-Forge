# Residual Register

状态：非权威 candidate 残差登记表。所有初始条目默认 open；任何 open residual 都阻止本候选包被描述为已校准或 authoritative。本文档不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

候选 scope 固定为：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。

## 当前残差

| `residual_id` | 区域 | 残差描述 | 对 scope 的影响 | 阻塞的 authority | close 条件 | 状态 |
|---|---|---|---|---|---|---|
| `RES-001` | source provenance | package-level source ledger 与 artifact pin manifest 已成形，但 external artifact hash、rights 和 retention chain 仍未完全冻结 | 无法证明全部输入、benchmark 或 criteria 已达到 release-grade 可追溯 | 全部 | source ledger 完整并经审阅 | open |
| `RES-002` | surrogate identity | 候选 surrogate 的 model card 与 identity manifest 已成形，但 worktree 仍 dirty，retained validation artifact chain 未闭合 | 无法把当前 author snapshot 升级为 release-grade surrogate identity | 全部 | model card 补齐版本、manifest 和复现说明 | open |
| `RES-003` | target geometry | F-16C Block 50 组件几何、材料、遮挡和暴露面积来源未审计 | 可能把工程 hitbox 当成真实 vulnerability | effect scale / component probability | geometry 来源、假设和误差界限可追溯 | open |
| `RES-004` | warhead scope | AIM-120C-class blast-fragmentation 候选参数未与可公开、可审计来源绑定 | 可能过拟合或暗示未知具体弹药参数 | effect scale / mechanism load | warhead class 假设、范围和敏感性分析完成 | open |
| `RES-005` | fragment mechanism | 破片质量、速度、方向 pattern、areal density 和穿透模型未验证 | 破片载荷 row 门槛不可作为权威 | component probability | benchmark 覆盖 fragment-energy / areal-density residual | open |
| `RES-006` | blast mechanism | blast scaled distance、超压、冲量和结构耦合未验证 | 爆轰载荷 row 门槛不可作为权威 | effect scale / component probability | benchmark 覆盖 blast residual 与适用区间 | open |
| `RES-007` | near-miss bucket | `near_miss_0_35m` 的 anchor、boundary probes 与第一版三点结果表已存在，但 candidate toy probe 仍缺独立 review 与更强的 bucket sensitivity 审计 | 当前结果仍可能把有限 probe 点误当成整个桶 | 全部 | bucket 内多点覆盖和边界敏感性报告完成 | open |
| `RES-008` | beam/high closure | `beam` / `high` 的轴定义、anchor、out-of-scope rejection 与第一版 boundary result table 已存在，但 closure 轴当前仍主要是 scope label，且缺独立 review | scope 仍可能泄漏到其他 aspect/closure，或把 bookkeeping 当成物理敏感性 | 全部 | scope 轴定义和 out-of-scope 检查通过 | open |
| `RES-009` | component failure | 组件失效概率与机制载荷之间的映射未由独立 benchmark 验证 | synthetic probability 可能被误提升 | component probability | 概率 residual、校准曲线和 uncertainty 通过预设门槛 | open |
| `RES-010` | validation criteria | Stage B `effect_scale` 的 metrics / acceptance criteria 已冻结，且第一版 fixed-seed candidate benchmark snapshot 已生成，但独立 reviewer signoff、release-level result closeout 与 Stage C criteria extension 仍缺 | 仍不能判断完整 surrogate 是否通过独立验证，且不能据此放行 Stage C 或 stock authority | 全部 | pre-run criteria 冻结、独立 review record、benchmark result table 与适用 scope 的 residual closeout 完整 | open |
| `RES-011` | uncertainty | Stage B uncertainty gate 已冻结，且 fixed-seed candidate snapshot 已给出 seed-window CV 摘要，但 coverage 解释、result-level 审计和独立 review 仍缺 | 无法把当前波动范围叙述成已验证的不确定性边界 | effect scale / component probability | uncertainty coverage 指标通过预设门槛 | open |
| `RES-012` | independence | benchmark/input separation manifest、第一版 scope probe result table 与第一版 candidate benchmark snapshot 已落文，但独立 reviewer 审计与结果级 independence 证据仍缺 | 验证仍可能循环引用 | 全部 | benchmark/input 分离审计完成 | open |
| `RES-013` | Pk boundary | 本候选包未覆盖 kill-chain Pk 校准 | 任何 Pk 声称都越界 | Pk | 不在本包关闭；需独立 Pk 证据链 | open |
| `RES-014` | deterministic fuze boundary | 本候选包未覆盖 live fuze trigger、target signature、reliability 或 miss-distance/fuze 联合验证 | 不能替换 RNG hit gate | deterministic fuze | 不在本包关闭；需独立 fuze/kill-chain 证据链 | open |

## Closeout 规则

- 关闭 residual 必须引用 source ledger、model card 或 validation report 中的稳定 artifact，不接受口头结论。
- `RES-013` 和 `RES-014` 是本候选包的 scope boundary，不应在本目录内关闭为已授权；只能在独立证据链存在后标注为外部处理。
- 任何 residual 关闭后仍需检查是否引入新的 out-of-scope 声称。
- 在所有适用 residual 关闭前，`calibration_status` 必须保持 `unvalidated`，所有 authority 字段必须保持 `false`。
