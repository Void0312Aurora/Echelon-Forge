# F-16C Block 50 目标几何/组件/材料候选来源收集

状态：`data_collection / non-authoritative / public-source-only`  
日期：`2026-05-28`  
适用任务：A2 高保真空战杀伤模型数据收集子任务，目标平台 `F-16C_Block50`。

本文档只登记公开来源能支持的目标外形、组件布局和材料/装甲缺口。它不是 F-16C Block 50 vulnerability descriptor，不授予 Pk、deterministic fuze、effect-scale、component-failure probability 或具体杀伤阈值 authority。

## 仓库准入边界

本目录遵守上级 A2 数据准入规则：

- 官方/标准优先：USAF、NAVAIR、GAO/NASA/NIST 等公开政府来源优先。
- 公开工程材料可用：GE Aerospace、GD Mission Systems、Lockheed Martin 等厂商公开资料可用于公开量级和组件候选。
- 民间数据库只做 sanity check：Wikipedia / F-16.net / DCS / 3D 模型等不能单独进入 authority 链。
- 受限、机密、专有、不可再分发或来源不稳定内容不得摘录入库；只能记录拒绝原因。
- 单一宣传值不能作为权威，必须保留 scope、交叉验证和 residual。

## 本轮结论

### 可作为 `target_geometry` 候选

这些来源可支持低精度外形盒、机体系轴向切分和量级质量字段，但仍需在后续几何包中保守化：

| 候选项 | 可用结论 | 来源组合 | 不确定性 |
|---|---|---|---|
| 外形尺寸 | `length ~= 15.0 m`、`wingspan ~= 10.0 m`、`height ~= 5.0 m` 可作为公开尺寸锚点。 | USAF / Shaw fact sheets，NAVAIR Viper 页，民间三视图 sanity check。 | Block 50/52 与通用 F-16 页混用；不提供高保真截面/体积。 |
| 重量量级 | 空重约 `8.5 t`、最大起飞重量约 `19 t` 可作为 mass sanity range。 | USAF / Shaw fact sheets，仓库现有 `f16c_block50.json`。 | 任务构型、外挂、批次改装影响大；不能推导组件质量分布。 |
| 内油量量级 | 内油约 `3.1-3.2 t` 可作为总燃油量候选。 | USAF / Shaw fact sheet 与仓库现有 `max_fuel_kg=3175` 交叉。 | 公开来源通常不给各油箱位置/容量分配；不得凭单一值拆分油箱。 |
| 发动机量级 | Block 50 使用 GE F110 系列，单发、后机身/尾喷口区域可作为 layout 候选。 | Shaw fact sheet，GE F110 data sheet，NAVAIR Viper 页。 | 公开来源可支持发动机系列和推力量级，不支持内部安装边界、附件/管路细节。 |
| 雷达/鼻锥 | 机鼻火控雷达和 F-16 radome 前向布局可作为 nose radar candidate。 | Shaw fact sheet，GD Mission Systems F-16 radome fact sheet，公开照片/三视图 sanity check。 | APG-68 版本、天线尺寸和具体安装边界未公开到可建模精度。 |
| 座舱 | 单座座舱位于机鼻后/进气道上方区域，可作为 cockpit crew station candidate。 | USAF / Shaw 公开照片和 aircraft role description，三视图 sanity check。 | 不支持飞行员伤害阈值、透明件材料/厚度或装甲。 |
| 翼面/翼梁近似 | 中翼/主翼作为结构和燃油/飞控候选区域；可保留 `wing_spar` engineering placeholder。 | 外形尺寸、SLEP/结构寿命公开资料、三视图 sanity check。 | 没有公开主翼梁精确位置、截面、材料和冗余路径；只能保守称为结构候选。 |

### 可作为 `component layout candidate`

以下组件的“存在 + 粗位置”可进入候选 ledger，但不得升级为真实组件几何：

| 组件族 | 候选位置 | 公开依据 | 采纳级别 |
|---|---|---|---|
| `fire-control radar` | 机鼻 radome 内/后方。 | Block 50/52 radar 公开 fact sheet，F-16 radome 公开资料。 | candidate |
| `cockpit / pilot station` | 机鼻后段、进气道上方。 | 官方照片/平台说明，通用 F-16 外形。 | candidate |
| `engine core / nozzle` | 机身后段、尾喷口前后。 | 单发 F110/发动机公开资料、外形可见尾喷口。 | candidate |
| `fuselage fuel` | 机身中部可作保守 fuel volume placeholder。 | 内油总量公开，公开工程/火灾研究说明 fuel tank 安全议题；仓库当前 JSON 已有 center-fuselage fuel placeholder。 | weak candidate |
| `wing fuel` | 主翼内 fuel candidate。 | F-16 通用机翼/燃油公开量级与民间 sanity check。 | weak candidate |
| `flight-control actuators` | 尾部 rudder/elevator/leading-edge/aileron 附近的工程候选。 | 外部控制面可见，FBW 飞控公开事实。 | weak candidate |
| `wing spar / wing structure` | 主翼根部/中翼结构候选。 | SLEP/结构寿命公开资料说明结构寿命是关键，但不提供精确梁位。 | weak candidate |
| `avionics / mission computer / power bus / data link` | 前机身/中机身 avionics bay placeholder。 | Block 50 航电/雷达/数据链能力公开；具体位置缺公开工程依据。 | engineering placeholder only |

### 只能作为 sanity check

- 民间三视图、Wikipedia、F-16.net、DCS/游戏配置、可下载 3D 模型：只能核对尺寸量级、可见外形和明显组件朝向。
- 仓库现有 `examples/config/database/aircraft/units/f16c_block50.json`：只能作为当前 engineering scaffold 的对照，不是外部来源。
- 厂商宣传页的单个性能值：只能和官方/其他公开工程来源交叉后使用，不能单独作为权威。

### 应拒绝

- 未明确公开发布/再分发权利的飞行手册、维修手册、TO/技术令镜像、航电/武器接口手册、结构维修手册、IPB/零件目录。
- 来历不明的 CAD/3D 模型、付费模型、论坛附件或网盘资料。
- 声称含有装甲厚度、油箱精确分隔、航电舱尺寸、液压/燃油管线、飞控计算机位置、脆弱性/Pk 曲线、试验杀伤数据但没有公开 provenance 或可能受限的数据。
- 任何需要保密/出口管制/专有许可才能使用的材料数据和毁伤评估资料。

## 与当前仓库 F-16 scaffold 的差距

当前仓库已有 `F-16C_Block50` authored damage model，包含 nose radar/cockpit、fuselage fuel/avionics/engine、aft engine/flight-control、wing flight-control/fuel 和若干代表组件。按本轮来源审计：

- 外形尺寸和总燃油/发动机量级与公开来源大体一致，可保留为 engineering candidate。
- 组件列表的存在性多数可由公开事实支持，但许多具体 `offset` / `size` / `armor` / `threshold_scale` 缺少公开依据。
- `armor_mm`、材料分层、结构梁截面、油箱分隔、线缆/管路、液压/电源冗余、雷达天线尺寸、飞控计算机具体位置均为公开缺口。
- 不得把当前 scaffold 的组件 failure probability、机制阈值、装甲值或 vulnerability scale 宣称为校准数据。

## 后续建议

1. 以本目录 `source_ledger.zh.md` 中标为 `candidate` 的 Tier A/B 来源，建立一个低精度 `target_geometry_candidate` 说明文档。
2. 几何只先冻结外形盒和粗组件区：nose / cockpit / center fuselage / aft engine / wing / tail。
3. 所有 `armor`、材料、组件阈值、component-failure probability 保持 synthetic/engineering，等待单独公开材料与校准证据链。
4. 对任何民间 3D 模型或公开手册镜像，先做 rights/provenance 审计；默认拒绝进入仓库数据。

## 文件

- [source_ledger.zh.md](source_ledger.zh.md)：逐条候选来源、sanity check 和拒绝记录。
- [source_pin_update_20260528.zh.md](source_pin_update_20260528.zh.md)：本轮 source pin、字段级支持边界和 target geometry authority gap 更新。
