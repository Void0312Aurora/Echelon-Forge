# Source Ledger 模板

状态：非权威 candidate 模板。此台账只用于记录候选 `validated_physics_surrogate` 的来源、版本、保留位置和适用范围；它不是 descriptor，不是校准证据本身，不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

候选 scope 固定为：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。

## 填写原则

- 每条来源必须有稳定 `source_ref`、来源持有人或发布方、可审计定位方式和 provenance 摘要。
- 运行输出、临时数据集和实验目录可以被清理；保留时记录稳定入口、checksum、manifest、外部归档位置或生成配置，而不是把当前工作区路径当作长期事实。
- 受限、专有或不可再分发来源只记录引用和访问条件，不粘贴受限正文或数据。
- 来源必须标注与本候选 scope 的匹配程度。部分匹配不能被扩展解释为全 scope 权威。
- 任何来源在完成验证报告和 residual closeout 前都只能作为 candidate provenance。

## 来源台账

| `source_id` | 来源类别 | `source_ref` | 稳定定位 / checksum | 证据角色 | scope 匹配 | 可用性 / 权利 | ingest 状态 | authority 状态 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| `SRC-001` | `<报告/论文/数据集/求解批次/代码版本/假设>` | `<待填>` | `<URL/DOI/archive ref/sha256>` | `<geometry/warhead/material/component/benchmark/criteria>` | `<full/partial/out-of-scope>` | `<public/restricted/internal/unknown>` | `<pending/acquired/rejected/superseded>` | `non-authoritative` | `<待填>` |
| `SRC-002` | `<待填>` | `<待填>` | `<待填>` | `<待填>` | `<待填>` | `<待填>` | `<待填>` | `non-authoritative` | `<待填>` |

## 证据角色枚举

| 角色 | 说明 | 当前可授权 |
|---|---|---|
| `target_geometry` | F-16C Block 50 外形、组件位置、遮挡或暴露面积来源 | 否 |
| `warhead_model` | AIM-120C-class blast-fragmentation 候选参数或物理假设来源 | 否 |
| `mechanism_load` | 破片能量、破片面密度、穿透裕度、爆轰超压/冲量等载荷来源 | 否 |
| `component_fragility` | 组件失效阈值或条件失效概率来源 | 否 |
| `benchmark_dataset` | surrogate 对照的外部数据、试验数据或高保真求解批次 | 否 |
| `validation_criteria` | 验收指标、残差门限和覆盖要求来源 | 否 |
| `reproducibility` | 代码版本、配置、随机种子、容器或运行 manifest | 否 |

## 来源验收检查

| 检查项 | 状态 | 备注 |
|---|---|---|
| `source_ref` 非空且稳定 | `<open>` |  |
| provenance 能说明数据来源、处理链和保留边界 | `<open>` |  |
| 与候选 scope 的匹配轴逐项记录 | `<open>` |  |
| 权利和再分发限制明确 | `<open>` |  |
| benchmark 与 model-input 来源分离 | `<open>` |  |
| checksum / manifest / 版本号可复现 | `<open>` |  |
| 不把 validation_artifact_ref 单独当作授权依据 | `<open>` |  |

## 拒绝 / 排除记录

| `rejection_id` | 来源 | 排除原因 | 影响的 residual | 备注 |
|---|---|---|---|---|
| `REJ-001` | `<待填>` | `<out-of-scope/unstable/provenance-missing/license-blocked/quality-risk>` | `<RES-...>` | `<待填>` |
