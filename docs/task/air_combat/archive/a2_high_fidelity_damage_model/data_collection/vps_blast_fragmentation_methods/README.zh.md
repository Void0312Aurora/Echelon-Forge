# VPS blast_fragmentation 公开方法来源收集

状态：`2026-05-28` 首个窄域 `validated_physics_surrogate` 候选包的数据/方法来源收集。本文档只记录公开 blast / fragmentation mechanism-load surrogate 的方法入口、可复现 benchmark 候选和准入边界；不创建 vulnerability evidence descriptor，不写 authoritative descriptor row，不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

上级准则：

- [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)
- [A2 数据候选到 Evidence Gate 映射](../gate_mapping_20260528.zh.md)
- [A2 validated_physics_surrogate 候选包总说明](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/README.zh.md)
- [公开机制模型方法收集](../mechanism_model_public_methods/README.zh.md)

候选 scope 固定为：`F-16C_Block50` x `AIM-120C-class/blast_fragmentation` x `beam` x `high` x `near_miss_0_35m`。本目录中的任何公开来源都只覆盖通用物理方法或工程 benchmark 形状，不覆盖 AIM-120C 真实战斗部、F-16C 真实组件失效概率、live fuze trigger 或 kill-chain Pk。

## 本包交付物

- [source_ledger.zh.md](source_ledger.zh.md)：公开 blast / fragmentation / penetration / spatial sampling 来源台账，逐条记录 source_ref、发布方、权利、Tier、scope、可采纳内容、交叉验证、不确定性和 admission/authority。
- [benchmark_candidate_matrix.zh.md](benchmark_candidate_matrix.zh.md)：首个窄域 VPS 的可复现 benchmark 候选组合，区分 `method_ref`、`benchmark_dataset`、`validation_criteria` 和 `reproducibility`。
- [validation_gap_update_20260528.zh.md](validation_gap_update_20260528.zh.md)：本轮 source pin 审计、BFM-BM-001..006 的 `benchmark_design_reference` 充分性判定，以及 artifact/hash/acceptance threshold 缺口。
- [source_pin_update_kingery_gurney_denix_20260528.zh.md](source_pin_update_kingery_gurney_denix_20260528.zh.md)：Kingery-Bulmash、Gurney、DDESB/DENIX TP-20/TP-21 的官方路径、访问状态、权利边界和 artifact/hash 状态核对。

## 收集结论

| 机制区域 | 可进入 VPS 的公开来源角色 | 当前推荐用途 | 不得声明 |
|---|---|---|---|
| Hopkinson-Cranz / Sachs scaled distance | UN IATG 01.80、UFC/WBDG、Kingery-Bulmash 报告引用链、公开爆炸工程教材 | `method_ref`、单位/适用域 `validation_criteria`、blast benchmark 轴 | 不能把 TNT 地面/自由场爆炸曲线直接当空空导弹近炸真值 |
| Kingery-Bulmash / UFC blast pressure impulse | UFC 3-340-02、UN IATG、Kingery-Bulmash ARBRL-TR-02555、DDESB/BEC-O 候选 | `method_ref`；后续可用公开工具/固定版本作 blast curve reproducibility check | 不能给 AIM-120C 装药、TNT 等效、引信触发半径或 Pk |
| Mott / Gurney fragmentation | Mott 1947 DOI、Gurney BRL-405、UN IATG、Cooper 等公开教材 | `method_ref`；生成非型号化 fragment mass/velocity proxy 和 sensitivity benchmark | 不能反推出具体 warhead 破片数、质量、初速、方向图 |
| Ballistic-limit / penetration | NASA-HDBK-8719.14、Recht-Ipson DOI、MIL-STD-662F ASSIST/QuickSearch 路线、DDESB TP-21；UFC 3-340-01 已因 WBDG 官方 FOUO/出口限制声明拒绝 | `method_ref`、`validation_criteria`；支持 `penetration_margin` 的公式形状、V50 thresholding 和域外拒绝指标 | 不能把航天 BLE、装甲 V50、debris 分析或 hardened-structure 公式直接转成飞机组件失效概率 |
| Fragment areal density / spatial sampling | IATG/GICHD/DDESB 候选、Mott/Gurney 组合、Marsaglia 均匀球面采样 | `reproducibility`、Monte Carlo sampling benchmark、areal-density convergence check | 不能把安全距离、球面稀释或 toy sampling 当作命中/杀伤概率校准 |

## 可进入 Evidence Gate 的方式

当前没有任何来源可直接作为 `a2.vulnerability_evidence.v1` 的 authoritative descriptor row。允许的最高用途是：

- `method_ref`：把公开公式族、适用域、单位和实现版本写入未来 surrogate model card。
- `benchmark_dataset`：只能是未来用公开方法和固定配置生成的 toy / unit benchmark，或经权利核验的公开工具输出；当前没有 scope 匹配的外部实测 dataset。
- `validation_criteria`：把单位一致性、适用域检查、单调性、采样收敛、版本锁定、scope leakage 和 residual closeout 写入验证报告。
- `reproducibility`：记录 source_ref、版本、sha256、代码 commit、容器、随机种子、采样策略和配置；来源存在本身不构成验证通过。

禁止用途：

- 不生成标为 calibrated 的 descriptor。
- 不把 effect-scale、component-failure probability、Pk 或 deterministic-fuze authority 置为授权。
- 不把公开 blast / fragment / penetration 公式直接写成 F-16C Block 50 组件概率 row。
- 不把 validation artifact 或 benchmark 计划单独当作 `validated_physics_surrogate` authority。

## 推荐首批 benchmark 组合

| 组合 | 来源角色 | 用途 | 当前状态 |
|---|---|---|---|
| `BFM-BM-001 blast_scaled_distance_curve_lock` | IATG + UFC + Kingery-Bulmash 引用链 | 固定 scaled-distance、pressure、impulse 的单位、版本和曲线形状检查 | `candidate / not_run` |
| `BFM-BM-002 mott_gurney_fragment_cloud_unit` | Mott + Gurney + IATG + Cooper | 非型号化破片质量/速度采样与能量分布 sanity benchmark | `candidate / not_run` |
| `BFM-BM-003 fragment_areal_density_spatial_sampling` | Mott/Gurney + Marsaglia + IATG/GICHD | 固定球面方向采样、面积通量、beam witness surface 收敛检查 | `candidate / not_run` |
| `BFM-BM-004 penetration_margin_ble_crosscheck` | NASA-HDBK-8719.14 + Recht-Ipson + MIL-STD-662F ASSIST/QuickSearch route + DDESB TP-21；UFC 3-340-01 rejected | 只验证 `penetration_margin` 的公式形状、单位和域外拒绝逻辑 | `candidate / not_run` |
| `BFM-BM-005 integrated_near_miss_mechanism_vector_toy` | 上述 method_ref 组合 + A2 scope gate | 输出非权威 mechanism-load vector，验证 source trace 和 scope leakage | `candidate / not_run` |

详见 [benchmark_candidate_matrix.zh.md](benchmark_candidate_matrix.zh.md)。这些组合目前只是候选计划，不是已执行 validation report。

## Residual

- 没有公开来源提供 AIM-120C-class 的真实 TNT 等效、壳体、预制破片、方向图、引信逻辑或可靠性。
- 没有公开来源提供 F-16C Block 50 的真实组件几何、材料、遮挡、冗余和组件失效概率。
- Kingery-Bulmash 原始报告仍未确认官方公开 artifact；Gurney 已识别 DTIC DOI/citation/PDF 候选路线但 artifact/hash 仍 pending；DDESB TP-20/BEC-O 与 TP-21 已识别 DENIX official-route candidates，但本轮本机网络未完成 artifact、rights、checksum、工具包版本和允许输出策略固定。详见 [Kingery/Gurney/DENIX source pin update](source_pin_update_kingery_gurney_denix_20260528.zh.md)。
- `near_miss_0_35m`、`beam`、`high` 的桶内采样密度和边界行为尚未定义。
- 任何 benchmark 结果都必须在结果生成前冻结 acceptance criteria，并与模型输入/调参来源分离。
- UFC 3-340-01 及任何第三方镜像因官方限制声明保持 rejected；不得用来补 penetration benchmark。
