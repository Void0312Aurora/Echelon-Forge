# F-16C Block 50 Target Geometry Source Pin Update

状态：`2026-05-28 / source pin update / non-authoritative`  
适用 ledger：[source_ledger.zh.md](source_ledger.zh.md)  
写入边界：本更新只补强来源固定、公开性、scope、交叉验证和 residual；不授予 runtime authority，不创建 descriptor row。

## 准入边界复核

本目录继续遵守：

- [公开数据来源准入标准](../../../../../standards/foundation/public_data_source_admission.zh.md)
- [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)

本轮没有采纳 F-16 technical order、flight manual、maintenance manual、IPB、parts catalog、论坛镜像、游戏数据库、未授权 CAD 或疑似受限资料。所有来源默认 `authority_status=non-authoritative`。

## 稳定来源固定补强

| ledger source_id | 固定后的 `source_ref` 口径 | 发布方 / 持有人 | 公开性 / 权利 | scope | cross-validation | residual |
|---|---|---|---|---|---|---|
| `F16-TG-SRC-001` | USAF `F-16 Fighting Falcon` fact sheet，官方 `af.mil` fact-sheet URL。 | U.S. Air Force | 官方公开网页；只链接与概述，不复制长正文。 | `generic-F-16` 外形、全机重量、任务描述。 | 与 `F16-TG-SRC-002/003` 对尺寸和重量量级互证。 | 非 Block 50 专属；无内部组件、材料、油箱或装甲数据。 |
| `F16-TG-SRC-002` | Shaw AFB `F-16C Fighting Falcon` fact sheet，官方 `shaw.af.mil` URL。 | U.S. Air Force / Shaw AFB | 官方公开网页；只链接与概述。 | `partial-F16C-Block50/52`，可作 Block 50/52 scope anchor。 | 与 USAF 通用页、NAVAIR Viper 页、GE F110 公开资料互证。 | Block 50/52 合并描述；不提供工程图、舱段或脆弱性。 |
| `F16-TG-SRC-003` | NAVAIR `F-16 Fighting Falcon Viper` product page，官方 `navair.navy.mil` URL。 | Naval Air Systems Command | 官方公开网页；只链接。 | `generic-F-16/Viper` 平台量级。 | 与 USAF/Shaw fact sheet 对长度、翼展、高度、重量量级互证。 | Navy support/product 语境，不是 Block 50 内部几何来源。 |
| `F16-TG-SRC-004` | GE Aerospace `F110 engine family` 与 `F110-GE-129` datasheet URL。 | GE Aerospace | 厂商公开 PDF；版权归发布方，ledger 只记录引用。 | F110 系列 / F110-GE-129 发动机族候选。 | 与 Shaw Block 50/52 发动机族描述和仓库现有 engine ref 互证。 | 只支持 aft single-engine region 量级；不支持安装边界、附件、管路或毁伤阈值。 |
| `F16-TG-SRC-005` | GD Mission Systems `F-16 wideband military radomes` fact sheet URL。 | General Dynamics Mission Systems | 厂商公开 PDF/fact sheet；版权归发布方。 | `generic-F-16` nose radome / sensor aperture reference。 | 与 Shaw radar family、公开外形和三视图 sanity 互证。 | 不支持 APG-68 天线尺寸、radome 厚度、材料性能或脆弱性。 |
| `F16-TG-SRC-007` | GAO product page `GAO-13-51`。 | U.S. Government Accountability Office | GAO 官方公开报告入口。 | `generic-F-16 fleet` 结构寿命 / SLEP 背景。 | 与 `F16-TG-SRC-008` USAF SLEP 新闻互证结构重要性。 | 审计报告不提供梁位、材料、裂纹位置、强度或杀伤阈值。 |
| `F16-TG-SRC-008` | USAF `F-16 Service Life Extension Program` public news URL。 | U.S. Air Force | 官方公开新闻网页。 | `generic-F-16 C/D fleet` 结构寿命背景。 | 与 GAO-13-51 互证 wing/fuselage/structure 是应保留节点。 | 新闻稿不能派生主梁、框位、装甲或结构 failure probability。 |
| `F16-TG-SRC-011` | Wikimedia Commons F-16 three-view file page。 | Wikimedia Commons contributor(s) | 公开共享许可依文件页；本目录只链接，不派生高精度坐标。 | `generic-F-16` visual sanity check。 | 仅在官方尺寸锚定后检查 nose/cockpit/wing/tail 相对顺序。 | 不是工程图；不能推导内部组件、截面、材料或装甲。 |

`F16-TG-SRC-006/009/010/012` 保持 `sanity-check-only` 或内部 scaffold 对照：可用于检索线索、明显外形量级和仓库差距审计，不能作为型号级来源。

## 字段级支持边界

| 字段 / 主题 | 当前最高支持级别 | 可用 source_id | 不能声明 |
|---|---|---|---|
| F-16 外形盒 `length/wingspan/height` | `target_geometry reference candidate` | `F16-TG-SRC-001/002/003`，`F16-TG-SRC-011` 只作 sanity。 | 高保真截面、遮挡、组件体积或真实 hitbox。 |
| 全机重量 / 总内油量量级 | `reference / sanity candidate` | `F16-TG-SRC-001/002/003/012` | 任务构型质量分配、油箱分隔或燃油中心位置。 |
| F110 aft engine region | `component_layout candidate` | `F16-TG-SRC-002/004` | F-16 安装边界、附件位置、油/液压管线或发动机易损性。 |
| nose radome / radar region | `component_layout candidate` | `F16-TG-SRC-002/005/011` | APG-68 精确版本、天线尺寸、radome 材料厚度或雷达脆弱性。 |
| cockpit / pilot station rough region | `visual/reference sanity` | `F16-TG-SRC-001/002/011` | 透明件材料、座舱装甲、飞行员伤害模型或防护阈值。 |
| wing / fuselage structural nodes | `weak structural reference candidate` | `F16-TG-SRC-007/008/011` | 主梁位置、框梁材料、裂纹容限、结构 kill threshold。 |
| `armor_mm`, `threshold_scale`, component failure probability | `unsupported` | none | 任何真实装甲、材料、阈值、概率或 Pk。 |

## Authority gate 缺口

`target_geometry` 目前只支持 method/reference/sanity：

- 可支持低精度外形盒和粗组件区命名；
- 可支持 “engine/radar/cockpit/wing/fuselage/tail 是合理候选区域”；
- 可支持仓库现有 scaffold 的公开差距审计。

仍缺真实 authority gate：

- 无 Block 50 公开工程几何模型或可再分发三维结构数据；
- 无内部组件边界、材料分区、油箱分隔、线束/管线拓扑；
- 无 row 级 geometry provenance、uncertainty model、validation artifact 或 checksum；
- 无逐字段 runtime 授权 manifest。

因此本目录不得被下游解释为 F-16C Block 50 runtime geometry authority。
