# Schema 映射说明：组件失效 benchmark 方法来源

状态：`2026-05-28` non-authoritative mapping notes。本文档把 [source_ledger.zh.md](source_ledger.zh.md) 的公开来源映射到 `a2.vulnerability_evidence.v1` 的可用边界。它不是 descriptor，不创建 row，不授予任何 runtime authority。

## 总体判定

当前目录没有任何来源满足 runtime authoritative descriptor 的完整条件：

- 没有 `external_calibration_dataset`：未找到公开、可再分发、scope 匹配、row-level provenance/uncertainty 完整的 aircraft air-combat component fragility calibration data。
- 没有 `validated_physics_surrogate`：NASA/FOI/FAA/NAP/公开论文可帮助设计 surrogate 和 validation criteria，但本目录没有项目内模型版本、benchmark hash、误差指标、验收门槛和 `validation_manifest`。
- 所有来源默认只能作为 `method_reference`、`validation_criteria_reference`、`benchmark_design_reference` 或 `residual_register_reference`。

因此，任何后续 descriptor 若引用本目录来源，仍必须保持：

```yaml
calibration_status: unvalidated
effect_scale_authority: false
component_failure_probability_authority: false
pk_authority: false
deterministic_fuze_authority: false
```

## 来源到 schema 角色映射

| 来源族 | 支持的文档态角色 | 可影响的 schema / validation 设计 | 不能声明 |
|---|---|---|---|
| FOI component kill criteria | `method_reference`、`component kill criteria`、`residual_register_reference` | `component_name`、`component_system`、`component_redundancy_group_id`、failure-state taxonomy、fault-tree propagation tests | `component_failure_probability` calibration、Pk、真实目标组件阈值 |
| NAP / GAO / 10 U.S.C. § 4172 LFT&E | `validation_criteria_reference`、`residual_register_reference` | evidence gate 分层、full-up / subscale / model evidence 记录、acceptance criteria 文档结构 | 任何 weapon-target table、row-level probability、deterministic fuze |
| NASA-STD/HDBK-7009 | `benchmark_design_reference`、`validation_criteria_reference` | `validation_manifest` 应包含模型版本、benchmark ref、metric ref、acceptance criteria ref、uncertainty / credibility 记录 | 证明某个 surrogate 已经 validated；必须由项目内验证报告另行证明 |
| NASA damaged-aircraft studies | `benchmark_design_reference`、consequence validation | damage-state to aerodynamic / control consequence benchmark，误差、coverage、sensitivity 指标 | weapon effects、hit probability、component failure probability |
| FAA AC 25.1309 / AC 20-128A | `redundancy_dependency_validation`、`residual_register_reference` | system failure severity、redundancy isolation、critical-system separation、fragment path qualitative tests | combat probability classes、warhead fragment lethality、Pk |
| Open vulnerability / shotline papers | `method_reference`、`benchmark_design_reference` | hit-to-component exposure、shotline coverage、component overlap、dependency graph、representative target benchmark | 真实 F-16C Block 50 layout、现代 missile fragility rows |
| JASP public articles | `residual_register_reference`、workflow sanity | LFT&E workflow vocabulary、component/system checklist | COVART/FASTGEN/Endgame Manager 参数或 validation data |
| JMEM/JWS/J-ACE/AJEM/COVART/FASTGEN/SLATE/Endgame Manager | `rejected` 或 `sanity_check_only` | 无 runtime schema role | 任何 source_ref authority、calibrated row、数值派生 |

## 可支持的四类能力

### 1. Component kill criteria

可用来源：

- `CFBM-FOI-001`
- `CFBM-BALL-001`
- `CFBM-MILHDBK-001`，待官方版本固定
- `CFBM-PAPER-001`
- `CFBM-PAPER-002`
- `CFBM-PAPER-003`

允许形成的产物：

- 组件失效状态词表，例如 `no_effect`、`degraded`、`mission_kill_contributor`、`mobility_kill_contributor`、`catastrophic_dependency_loss` 等项目内非权威标签。
- fault-tree / dependency graph 测试问题：单组件失效、多组件冗余失效、串联系统失效、局部功能降级。
- row 元数据要求：每个候选 row 必须保留 component/system/redundancy group、source_ref、provenance、scope 和 residual。

禁止转换：

- 不把 FOI 文献综述、Ball 教材或论文示例中的任何概率、阈值或案例结果直接写成 `component_failure_probability`。
- 不把 generic aircraft / representative helicopter 结果外推到 `F-16C_Block50`。

### 2. Failure probability surrogate benchmark

可用来源：

- `CFBM-MSVV-001`
- `CFBM-MSVV-002`
- `CFBM-NASA-001`
- `CFBM-NASA-002`
- `CFBM-NASA-003`
- `CFBM-NASA-004`
- `CFBM-PAPER-004`

允许形成的产物：

- 非权威 benchmark spec：输入空间、公开参考、模型版本、随机种子、checksum、metric、acceptance criteria。
- 误差指标候选：classification confusion matrix、Brier score、calibration curve、coverage interval、rank correlation、sensitivity / Sobol-style contribution、damage-state consequence error。
- uncertainty 记录：材料/几何/velocity/impact angle/fragment field/solver bias/scope mismatch。

禁止转换：

- 不把 surrogate benchmark 的通过/失败结果直接声明为 `calibration_status=calibrated`。
- 不把 NASA transport / GTM damaged-aircraft consequence 结果转成 air-combat component hit probability。
- 不把 high-velocity fragment structure paper 的局部结构结果外推成 full-aircraft Pk。

### 3. Redundancy / dependency validation

可用来源：

- `CFBM-FOI-001`
- `CFBM-FAA-001`
- `CFBM-FAA-002`
- `CFBM-PAPER-001`
- `CFBM-PAPER-003`
- `CFBM-JASP-001`

允许形成的产物：

- dependency graph validation cases：串联依赖、并联冗余、隔离/分离、共因碎片路径、功能降级传播。
- residual checklist：是否缺少真实内部布局、是否缺少组件隔离距离、是否缺少 redundant routing、是否缺少 common-cause damage model。
- validation report sections：dependency assumptions、component grouping、failure propagation, uncertainty and sensitivity。

禁止转换：

- 不把 FAA civil severity probability classes 映射为 combat component failure probability。
- 不把 JASP public workflow 的组件清单转成具体平台结构或真实组件概率。

### 4. Residual register

可用来源：

- NAP、GAO、10 U.S.C. § 4172 LFT&E、JASP public articles
- FOI 公开文献综述中的 empirical-data scarcity 结论
- NASA/FAA scope 限制
- 公开论文的 representative / generic case 限制

建议 residual 字段：

| residual_id | 缺口 | 影响 |
|---|---|---|
| `RES-CFBM-001` | 真实 aircraft component fragility calibration data 缺失 | 不能创建 `external_calibration_dataset`。 |
| `RES-CFBM-002` | 现代空空 warhead fragment field / burst-point / fuze 数据缺失 | mechanism-load surrogate 只能非型号化。 |
| `RES-CFBM-003` | F-16C 内部组件布局、冗余、routing、critical-system separation 缺失 | dependency graph 只能 schematic / candidate。 |
| `RES-CFBM-004` | full-up realistic LFT&E 原始试验和 acceptance thresholds 缺失 | validation_criteria 只能定义门槛形状，不能证明通过。 |
| `RES-CFBM-005` | 公开论文多为 generic / representative targets | 不能外推到 A2 target-specific calibrated rows。 |
| `RES-CFBM-006` | NASA/FAA 多为 civil transport / rotor debris / model credibility scope | 只能验证后果链和方法，不验证 weapon-target lethality。 |

## Descriptor gate 影响

若后续某个 descriptor 声称使用本目录来源，gate 应按以下方式处理：

| descriptor `source_kind` | 是否可由本目录直接支持 | 需要追加的证据 |
|---|---|---|
| `external_calibration_dataset` | 否 | 公开可再分发 calibration dataset，含 target/weapon/aspect/closure/miss-distance、row-level uncertainty、provenance 和 rights。 |
| `validated_physics_surrogate` | 否 | 模型/代码版本、公开或可审计 benchmark、validation metrics、acceptance criteria、validation scope、artifact sha256。 |
| `engineering_surrogate` | 可作为文档态方法来源，但不能进 authority gate | 必须保持 `calibration_status=unvalidated` 和 authority=false。 |
| `schema_fixture` / `synthetic_placeholder` | 可引用本目录设计字段，但不能授权 | 只能用于测试字段形状。 |

## Row-level 注意事项

若未来从公开 benchmark 派生非权威 row，至少要保留：

- `row_id`
- `source_ref`
- `provenance`
- `weapon_family`
- `aspect_bucket`
- `closure_bucket`
- `miss_distance_bucket`
- `component_name`
- `component_system`
- `component_redundancy_group_id`
- mechanism-load gate，例如 `fragment_energy_j`、`fragment_areal_density_per_m2`、`penetration_margin`、`blast_scaled_distance_m_kg13` 或 `surface_incidence_cos`
- uncertainty / residual ref

即便这些字段齐全，也不能因为字段完整而获得 authority。authority 只能源自 schema gate + source gate + calibration gate + validation manifest gate 的共同通过。

## Rejected source handling

以下来源不得作为 `source_ref` 写入任何 calibrated row：

- JMEM / JWS / J-ACE / JAAM / AJEM；
- COVART / FASTGEN / SLATE / ACEL / Endgame Manager / BlueMax 内部数据；
- CMO/CMANO、DCS、War Thunder、游戏配置、论坛、民间武器 DB；
- FOUO / CUI / ITAR / EAR / leaked PDF / 未授权课件 / 承包商附件；
- 单次战损照片、新闻、社媒和无官方报告的 combat damage anecdotes。

若后续为了字段覆盖做 sanity check，必须在 ledger 中标为 `sanity_check_only` 或 `rejected`，并保持 `authority=none`。
