# F-16C Block 50 目标几何/组件/材料候选 Source Ledger

状态：`candidate source ledger / non-authoritative`  
日期：`2026-05-28`  
目标 scope：`F-16C_Block50` target geometry、component layout、public material/armor gap inventory。  
禁止用途：不得作为 Pk、deterministic fuze、effect scale、component failure probability、真实装甲/材料厚度或校准脆弱性 authority。

## 判读枚举

| 字段 | 值 |
|---|---|
| source tier | `Tier A / 官方-标准`、`Tier B / 公开工程材料`、`Tier C / sanity check`、`rejected` |
| 证据角色 | `target_geometry`、`component_layout`、`mass_fuel_engine_quantity`、`material_gap`、`sanity_check`、`reject_record` |
| scope 匹配 | `full-ish`、`partial`、`generic-F-16`、`out-of-scope` |
| ingest 状态 | `candidate`、`sanity-check-only`、`rejected`、`pending-review` |
| authority 状态 | 当前全部为 `non-authoritative` |

## 来源台账

| `source_id` | tier / 类别 | `source_ref` | 发布方 / 持有人 | 可公开性 / 权利 | 证据角色 | scope 匹配 | 可采纳结论 | 交叉验证状态 | 不确定性 / residual | ingest / authority |
|---|---|---|---|---|---|---|---|---|---|---|
| `F16-TG-SRC-001` | Tier A / 官方 fact sheet | [USAF F-16 Fighting Falcon fact sheet](https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/) | U.S. Air Force | 美国政府公开网页；网页可链接引用，正文不做大段复制。 | `target_geometry`, `mass_fuel_engine_quantity` | `generic-F-16` | 可记录 F-16 外形尺寸、空重/最大重量、通用动力/发动机族量级和平台任务描述。 | 与 Shaw F-16C、NAVAIR Viper、仓库 airframe 字段交叉后支持 `length ~= 15 m`、`span ~= 10 m`、`height ~= 5 m`、空重约 `8.5 t` 量级。 | 通用 F-16 页面，不是 Block 50 专属；不提供内部组件位置、材料、装甲或油箱分隔。 | `candidate / non-authoritative` |
| `F16-TG-SRC-002` | Tier A / 官方基地 fact sheet | [Shaw AFB F-16C Fighting Falcon fact sheet](https://www.shaw.af.mil/About-Us/Fact-Sheets/Display/Article/663884/f-16c-fighting-falcon/) | U.S. Air Force / Shaw AFB | 美国政府公开网页；可链接引用。 | `target_geometry`, `mass_fuel_engine_quantity`, `component_layout` | `partial` for F-16C Block 50/52 | 可记录 Shaw F-16C 使用 Block 50/52 口径、F110/F100 发动机族、AN/APG-68(V)5 级 radar 公开关系、尺寸/重量量级。 | 与 USAF 通用 fact sheet、GE F110 data sheet、GD radome 资料交叉；可支持 Block 50 engine/radar family candidate。 | 基地 fact sheet 是公开简介，不是工程图；Block 50 与 Block 52 合并描述；radar version 与仓库 `AN/APG-68(V)9` 不完全一致。 | `candidate / non-authoritative` |
| `F16-TG-SRC-003` | Tier A / 官方军种产品页 | [NAVAIR F-16 Fighting Falcon Viper product page](https://www.navair.navy.mil/product/F-16-Fighting-Falcon-Viper) | Naval Air Systems Command | 美国政府公开网页；可链接引用。 | `target_geometry`, `mass_fuel_engine_quantity`, `component_layout` | `generic-F-16/Viper` | 可作为 F-16/Viper 公开尺寸、重量和单发战斗机平台量级交叉。 | 与 USAF/Shaw fact sheet 交叉验证外形和重量量级。 | NAVAIR 使用 Viper/服务支持语境，不给 Block 50 内部布局；不支持组件尺寸。 | `candidate / non-authoritative` |
| `F16-TG-SRC-004` | Tier B / 厂商发动机公开资料 | [GE Aerospace F110 engine family data sheet](https://www.geaerospace.com/sites/default/files/GE-F110-turbofan-engine-family-datasheet.pdf) and [F110-GE-129 data sheet](https://www.geaerospace.com/sites/default/files/datasheet-F110-GE-129.pdf) | GE Aerospace | 厂商公开 PDF；版权归 GE，ledger 只记录引用和公开量级。 | `mass_fuel_engine_quantity`, `component_layout` | `partial` for Block 50 engine family | 可支持 Block 50 GE F110 系列单发、推力量级、发动机尺寸/质量公开量级，用于 aft engine region candidate。 | 与 Shaw Block 50/52 发动机字段和仓库 `F110-GE-129` 模块交叉。 | 厂商资料覆盖 engine family / engine model，不等同具体 F-16 安装边界；不提供 F-16 内部管线/附件位置。 | `candidate / non-authoritative` |
| `F16-TG-SRC-005` | Tier B / 厂商雷达罩工程资料 | [General Dynamics Mission Systems F-16 wideband radomes fact sheet](https://gdmissionsystems.com/-/media/general-dynamics/maritime-and-strategic-systems/images/airborne-systems/radomes/pdf/f16-wideband-military-radomes-fact-sheet.ashx) | General Dynamics Mission Systems | 厂商公开 fact sheet；版权归发布方，ledger 只记录引用。 | `component_layout` | `generic-F-16` | 可支持 F-16 机鼻 radome/radar aperture 作为 nose sensor candidate。 | 与 Shaw Block 50/52 radar fact sheet、公开外形照片/三视图 sanity check 交叉。 | radome 材料/性能公开资料不等于雷达天线尺寸、安装位置或脆弱性；不得推导材料厚度或装甲。 | `candidate / non-authoritative` |
| `F16-TG-SRC-006` | Tier B / 厂商平台资料 | [Lockheed Martin F-16 Fighting Falcon / F-16V public pages](https://www.lockheedmartin.com/en-us/products/f-16.html) | Lockheed Martin | 厂商公开网页；版权归发布方，ledger 只记录引用。 | `target_geometry`, `component_layout`, `sanity_check` | `generic-F-16/F-16V` | 可交叉验证 F-16 平台构型、升级语境、航电/雷达/数据链作为组件族存在性。 | 与 USAF/Shaw/NAVAIR 交叉，不单独作为尺寸权威。 | F-16V 不是 F-16C Block 50；营销资料不提供可审计内部几何。 | `sanity-check-only / non-authoritative` |
| `F16-TG-SRC-007` | Tier A / 政府审计公开报告 | [GAO F-16 sustainment / SLEP related public reports, e.g. GAO-13-51](https://www.gao.gov/products/gao-13-51) | U.S. Government Accountability Office | 美国政府公开报告；可链接引用。 | `material_gap`, `component_layout` | `generic-F-16 fleet` | 可支持 F-16 老化/结构寿命/SLEP 是公开关键议题，证明 wing/fuselage structural components 是应登记的结构候选。 | 与 USAF SLEP 新闻和公开机队寿命资料交叉。 | 不给 Block 50 梁位、材料厚度、损伤阈值或结构冗余图；只能作为 structural criticality rationale。 | `candidate / non-authoritative` |
| `F16-TG-SRC-008` | Tier A / 官方新闻公开资料 | [USAF F-16 service life extension program public news](https://www.af.mil/News/Article-Display/Article/1516090/f-16-service-life-extension-program-a-great-deal-for-dod-taxpayers/) and related USAF SLEP news | U.S. Air Force | 美国政府公开网页；可链接引用。 | `material_gap`, `component_layout` | `generic-F-16 fleet` | 可支持 F-16 结构寿命/寿命延长公开事实，作为 wing/fuselage structural candidate 的背景。 | 与 GAO sustainment 报告交叉。 | 新闻稿不是结构图；不支持 wing spar 精确位置或结构强度。 | `candidate / non-authoritative` |
| `F16-TG-SRC-009` | Tier C / 民间百科 | [Wikipedia F-16 Fighting Falcon page](https://en.wikipedia.org/wiki/General_Dynamics_F-16_Fighting_Falcon) | Wikimedia contributors | CC BY-SA；可公开但二手汇编。 | `sanity_check` | `generic-F-16` | 可 sanity-check 外形尺寸、通用构型和公开照片。 | 只与 USAF/Shaw/NAVAIR/厂商资料交叉使用。 | 二手资料，版本可变；不能作为 authority。 | `sanity-check-only / non-authoritative` |
| `F16-TG-SRC-010` | Tier C / 民间专题数据库 | [F-16.net aircraft database](https://www.f-16.net/) | F-16.net community / site owner | 民间站点；权利归站点/贡献者；只链接，不复制数据库内容。 | `sanity_check` | `variant-specific but unofficial` | 可辅助核对 Block 50/52 批次、公开航电/发动机说法。 | 必须由 USAF/Shaw/厂商资料验证后才可引用结论。 | 非官方；批次和技术细节可能混杂；不能单独使用。 | `sanity-check-only / non-authoritative` |
| `F16-TG-SRC-011` | Tier C / 公共三视图 | [Wikimedia Commons F-16 three-view line drawing](https://commons.wikimedia.org/wiki/File:General_Dynamics_F-16_Fighting_Falcon_3-view_line_drawing.svg) | Wikimedia Commons contributor(s) | 公开共享许可依文件页为准；需保留 attribution；本 ledger 只链接。 | `sanity_check`, `target_geometry` | `generic-F-16` | 可辅助检查 low-fidelity hitbox axes、nose/cockpit/wing/tail 可见布局。 | 与官方尺寸缩放后做视觉 sanity check。 | 不是工程图；不能推导内部组件位置、截面、装甲或材料。 | `sanity-check-only / non-authoritative` |
| `F16-TG-SRC-012` | internal scaffold / 仓库现有数据 | [examples/config/database/aircraft/units/f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json) | CMO workspace | 内部工程 scaffold；不是外部公开来源。 | `sanity_check`, `component_layout` | `F-16C_Block50 scaffold` | 当前仓库已含尺寸、燃油、F110 engine ref、APG-68 radar ref、代表性 hitboxes/components，可作为本轮差距审计对象。 | 外形尺寸和内油量与官方 fact sheet 量级一致；组件位置多为工程假设。 | 不能作为 public source authority；`armor`、`threshold_scale`、component offsets/sizes 大量缺外部依据。 | `sanity-check-only / non-authoritative` |

## 候选字段映射

| 建模字段 | 可用来源 | 当前可写入级别 | 备注 |
|---|---|---|---|
| `airframe.length_m` | `F16-TG-SRC-001/002/003` | `target_geometry candidate` | 三源一致时可作为外形盒长度锚点；仍需单位和 rounding 记录。 |
| `airframe.wingspan_m` | `F16-TG-SRC-001/002/003/012` | `target_geometry candidate` | 可用于主翼 box span；不能推断翼梁宽度。 |
| `airframe.height_m` | `F16-TG-SRC-001/002/003` | `target_geometry candidate` | 用于 bounding box；不能推断垂尾/起落架精确几何。 |
| `empty_mass_kg` | `F16-TG-SRC-001/002/003` | `mass candidate` | 支持量级；任务构型需另行建模。 |
| `max_fuel_kg` | `F16-TG-SRC-001/002/012` | `mass/fuel candidate` | 支持总内油量量级；油箱分隔仍是公开缺口。 |
| `engine_ref=F110-GE-129` | `F16-TG-SRC-002/004/012` | `component layout candidate` | 可支持 aft single-engine region；不支持内部附件/管路。 |
| `sensor_ref=AN/APG-68 family` | `F16-TG-SRC-002/005/012` | `component layout candidate` | Block 50/52 fact sheet 提到 APG-68(V)5；仓库用 APG-68(V)9 应保留版本 residual。 |
| `nose/radar hitbox` | `F16-TG-SRC-002/005/011` | `component layout candidate` | 鼻锥/雷达候选可保留；雷达天线尺寸未知。 |
| `cockpit hitbox` | `F16-TG-SRC-001/002/011` | `component layout candidate` | 粗位置可见；乘员脆弱性不可公开推导。 |
| `center fuselage fuel / avionics` | `F16-TG-SRC-001/002/012` | `weak component candidate` | 总燃油和航电存在性可支撑；具体舱位是 residual。 |
| `wing fuel / flight-control` | `F16-TG-SRC-001/002/007/008/011/012` | `weak component candidate` | 翼面/控制面可见，结构寿命公开；油箱和作动器位置缺乏官方工程图。 |
| `wing_spar_center` | `F16-TG-SRC-007/008/011/012` | `engineering placeholder only` | 可保留结构候选，不可声称真实梁位/材料。 |
| `armor_mm`, `threshold_scale`, `component_failure_probability` | none in accepted public set | `must remain synthetic / rejected as authority` | 本轮无公开可再分发的 Block 50 装甲、材料层、失效概率来源。 |

## 材料 / 装甲公开缺口

| 缺口 | 当前状态 | 处理 |
|---|---|---|
| 机体蒙皮/框梁材料分布 | 公开来源只能支持“存在结构寿命/SLEP问题”和通用航空材料背景，不能给 Block 50 分区材料图。 | `material_gap`，不得填成真实材料。 |
| 雷达罩材料/厚度 | GD radome fact sheet 可证明 radome 是公开工程对象，但不支持厚度/抗破片性能。 | `material_gap`，只能记录 nose radome candidate。 |
| 座舱透明件/装甲 | 本轮无可采纳公开来源。 | `gap`，不得建装甲权威。 |
| 油箱自封/防火/惰化细节 | 未登记稳定、逐篇审计过的公开报告；本轮不采为几何 authority。 | `gap`；后续若新增 NIST/NASA/FAA 报告，必须逐条登记 source_ref、rights 和 scope。 |
| 发动机/液压/航电抗毁性 | 无公开 Block 50 校准阈值。 | `gap`，保持 synthetic。 |
| 翼梁/主框/挂架强度 | SLEP/GAO 只能证明结构寿命重要。 | `gap`，不能推导毁伤阈值。 |

## 拒绝 / 排除记录

| `rejection_id` | 来源 | 排除原因 | 影响范围 | 备注 |
|---|---|---|---|---|
| `F16-TG-REJ-001` | 公开网络镜像的 F-16 flight manual、maintenance manual、TO/technical order、结构维修手册、IPB/零件目录 | rights/provenance 不明，可能受发行限制或出口管制；不允许复制或派生内部组件几何。 | 内部组件位置、油箱分隔、航电舱、液压/电气/飞控细节。 | 即使网页可访问，也不进入仓库数据。 |
| `F16-TG-REJ-002` | 未授权 CAD、付费模型、论坛附件、网盘 3D 模型 | 来源不稳定、许可不明、常含派生/不可再分发内容。 | 高精度外形和组件舱位。 | 只可在本地人工视觉 sanity check 后丢弃，不保存模型或派生坐标。 |
| `F16-TG-REJ-003` | DCS/游戏/仿真模组配置中的 F-16 damage boxes | 民间仿真数据，权利和真实性不满足 A2 evidence gate。 | hitbox/component vulnerability。 | 可作为“不要照抄”的对照，不作为 sanity check 之外的来源。 |
| `F16-TG-REJ-004` | 单一厂商营销值或无来源图表 | scope 和 provenance 不足，可能是宣传或配置特定。 | 性能、重量、传感器能力。 | 需至少 Tier A/B 交叉后才可记录为量级。 |
| `F16-TG-REJ-005` | 声称含 Block 50 装甲厚度、组件脆弱性、Pk/杀伤概率或试验破坏数据但无公开 provenance 的资料 | 高风险敏感/专有/不可再分发；不满足 schema source gate。 | vulnerability evidence、component fragility、kill authority。 | 不得摘录，不得转写成参数。 |
| `F16-TG-REJ-006` | 未完成逐篇审计的 NASA/NIST/FAA/学术 PDF 搜索结果集合 | 只有来源类别或搜索结果，不是稳定 report-level source_ref。 | fuel/fire/material/airframe research 背景。 | 后续可按单篇报告重新登记为 candidate 或 rejected。 |

## 验收检查

| 检查项 | 状态 | 备注 |
|---|---|---|
| `source_ref` 非空且稳定 | `partial-pass` | 候选来源均给出 URL；具体 PDF checksum 未在本轮归档。 |
| 发布方 / 持有人记录 | `pass` | 每条来源记录发布方。 |
| 可公开性 / 权利记录 | `partial-pass` | 政府公开/厂商公开/民间许可已分类；下载物仍需逐项保留许可快照。 |
| scope 匹配逐项记录 | `pass` | 标出 Block 50、generic F-16、F-16V、fleet-level 等残差。 |
| 交叉验证状态记录 | `pass` | 尺寸/重量/发动机/雷达均说明交叉来源。 |
| 不确定性 / residual 记录 | `pass` | 材料、装甲、内部组件和脆弱性缺口已列明。 |
| 民间来源不授权 | `pass` | Tier C 全部为 sanity-check-only。 |
| 受限/不可再分发来源拒绝 | `pass` | 拒绝表明确记录。 |
| 不把宣传值当权威 | `pass` | 厂商资料仅作 candidate/sanity check，需官方交叉。 |
