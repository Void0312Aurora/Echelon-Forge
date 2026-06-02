# F-16C Material / Fuel / Fire / Systems Source Pin Update

状态：`2026-05-28 / source pin update / non-authoritative`  
适用 ledger：[source_ledger.zh.md](source_ledger.zh.md)  
写入边界：本更新只补强公开来源固定和 authority gap；不写运行时配置，不创建 descriptor row。

## 准入边界复核

本目录继续遵守：

- [公开数据来源准入标准](../../../../../standards/foundation/public_data_source_admission.zh.md)
- [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)

所有来源只支持方法、术语、后果分类、弱 scope anchor 或 sanity check。没有来源支持 F-16C Block 50 的真实材料厚度、油箱分隔、管线拓扑、火灾探测/灭火布局、组件失效概率或 Pk。

## 稳定来源固定补强

| ledger source_id | 固定后的 `source_ref` 口径 | 发布方 / 持有人 | 公开性 / 权利 | scope | cross-validation | residual |
|---|---|---|---|---|---|---|
| `F16-MFFS-SRC-003` | FAA `AC 25.981-1D`，`Fuel Tank Ignition Source Prevention Guidelines`，官方 FAA PDF URL。 | Federal Aviation Administration | FAA 官方公开 PDF；只引用题名、编号和方法范围。 | `civil-transport` fuel ignition-source method。 | 与 `F16-MFFS-SRC-004/005/006/007` 互证燃油箱点火/可燃性分析轴。 | Part 25 民机合规语境；不能给 F-16 点火概率或系统位置。 |
| `F16-MFFS-SRC-004` | FAA `AC 25.981-2A`，`Fuel Tank Flammability Reduction Means`，官方 FAA PDF URL。 | Federal Aviation Administration | 官方公开 PDF。 | `civil-transport` flammability reduction / inerting method。 | 与 FTFAM、TWA 800、AC 25.981-1D 互证。 | 不支持 F-16 是否装备或如何布置 FRM/惰化系统。 |
| `F16-MFFS-SRC-005` | FAA `AC 20-53B`，fuel vapor ignition by lightning protection，官方 FAA PDF URL。 | Federal Aviation Administration | 官方公开 PDF。 | `generic-aircraft` lightning / bonding / venting method。 | 与 AC 25.981 系列和 FAA handbook 互证点火源分类。 | 不给 F-16 雷击路径、电气 bonding 或油箱 routing。 |
| `F16-MFFS-SRC-006` | `DOT/FAA/TC-21/3`，FTFAM v11 manual，U.S. DOT ROSA P record。 | FAA William J. Hughes Technical Center / U.S. DOT | ROSA P 公开归档；保留报告编号和题录。 | `civil-transport` fuel tank flammability assessment method。 | 与 AC 25.981-2A 和 NTSB/FAA TWA 800资料互证。 | 方法模型不等于战斗机油箱爆炸概率。 |
| `F16-MFFS-SRC-007` | NTSB `AAR-00/03` 与 FAA lessons-learned TWA 800 页面。 | National Transportation Safety Board / FAA | 官方公开报告和网页；避免长文复制。 | `civil-transport` fuel-vapor ignition consequence case。 | 与 FAA AC/FTFAM 互证 fuel-air vapor ignition 与后果分类。 | Boeing 747 事故链；不能迁移为武器毁伤或 F-16 失效概率。 |
| `F16-MFFS-SRC-008` | `DOT/FAA/AR-00/12`，`Aircraft Materials Fire Test Handbook`，ROSA P / FAA Fire Safety entry。 | FAA William J. Hughes Technical Center | 官方公开报告入口；只引用测试类别。 | `generic-aircraft` materials fire-test methods。 | 与 FAA AC 25.869-1A、AMT handbooks、NIST FDS manuals 互证。 | 不给 F-16 材料清单、厚度或燃烧参数。 |
| `F16-MFFS-SRC-009/010/011` | FAA `AC 25.869-1A`、`AC 25.1309-1A`、`AC 25.795-7` 官方入口/PDF。 | Federal Aviation Administration | 官方公开 AC。 | `civil-transport` fire protection / system safety / survivability taxonomy。 | 互相交叉支持 system dependency、redundancy、flammable fluid 和 consequence 分类。 | 民机安全/安保口径；不能给 F-16 冗余距离、线束或作动器拓扑。 |
| `F16-MFFS-SRC-013/014/015` | NIST SP 984、SP 890 / NTIS record、NIST nacelle suppression publication pages。 | National Institute of Standards and Technology / NTIS | NIST/NTIS 公开题录或出版页；全文权利按入口核对。 | `generic-aircraft` engine nacelle / dry bay fire suppression studies。 | 与 FAA fire-protection AC、FDS manuals 互证 nacelle/dry-bay fire model axes。 | 试验舱/模拟舱不是 F-16/F110 安装；不能给探测器、瓶、喷嘴或灭火概率。 |
| `F16-MFFS-SRC-016` | NIST FDS and Smokeview manuals official page。 | National Institute of Standards and Technology | 官方公开模型文档。 | `generic-fire-model` fire/smoke/heat-transfer method. | 与 NIST nacelle/dry-bay studies 和 FAA material fire tests 互证 validation-manifest 要素。 | 通用 CFD 工具；缺 F-16 几何、材料、边界条件和 validation artifact。 |
| `F16-MFFS-SRC-017/018/019` | NASA NTRS records `20080034656`、`20120014568`、`20100002211`。 | NASA / NTRS | NTRS 公开记录；按记录 rights 引用。 | `civil-transport` damaged-aircraft consequence modeling。 | 三篇 NASA damaged-aircraft papers 互证控制面/机翼/尾翼损伤后果类目。 | Transport aircraft；不能给 F-16 控制律、结构阈值或武器效果。 |
| `F16-MFFS-SRC-020/021` | GAO `GAO-13-51` 与 USAF F-16 SLEP 新闻。 | GAO / U.S. Air Force | 官方公开报告/新闻。 | `generic-F-16` structural criticality background。 | 两者互证 F-16 C/D structural service-life work 是公开议题。 | 不提供材料、主梁、框位、强度、裂纹位置或毁伤阈值。 |
| `F16-MFFS-SRC-022/023/024` | FOI report page `FOI-R--2829--SE`；DOI `10.1016/j.cja.2013.02.010`；DOI `10.1016/j.aej.2022.07.040`。 | FOI / journal publishers | 公开题录或 open-access 入口；引用时核对许可。 | `generic-aircraft` survivability / vulnerability method. | 与 component-fragility ledgers 交叉支持 fault-tree、product-structure、fragment-impact method。 | 示例平台和概率不等于 F-16；不能抽取真实 fragility row。 |

## 字段级支持边界

| 字段 / 主题 | 当前最高支持级别 | 可用 source_id | 不能声明 |
|---|---|---|---|
| `fuel_fire_mechanism_axes` | `method_reference` | `F16-MFFS-SRC-003/004/005/006/007` | F-16 点火概率、油箱位置、爆炸阈值。 |
| `material_fire_test_axes` | `test_method_reference` | `F16-MFFS-SRC-008/012/016` | F-16 材料清单、厚度、燃烧参数。 |
| `engine_nacelle_fire_axis` | `generic method/reference` | `F16-MFFS-SRC-002/012/013/014/015/016` | F110/F-16 安装几何、灭火剂容量、传感器逻辑。 |
| `system_dependency_nodes` | `dependency taxonomy reference` | `F16-MFFS-SRC-009/010/011/012/022/023` | F-16 线束、液压、燃油、飞控拓扑或冗余距离。 |
| `damaged_aircraft_consequence` | `consequence modeling reference` | `F16-MFFS-SRC-007/017/018/019` | 空战命中到失效概率、控制律真值、战斗机气动退化量。 |
| `F16_structural_criticality_axis` | `weak F-16 reference` | `F16-MFFS-SRC-020/021/024` | 主梁位置、材料、强度、结构 kill threshold。 |
| component failure probability / Pk | `unsupported` | none | 真实概率、杀伤概率、runtime vulnerability row。 |

## Authority gate 缺口

`material_fuel_fire_dependency` 目前只支持 method/reference/sanity：

- FAA/NTSB 支持燃油点火、可燃性和后果分类；
- FAA/NIST 支持材料防火测试、火灾模拟和 nacelle/dry-bay 方法；
- NASA 支持损伤后飞行后果验证类目；
- GAO/USAF 支持 F-16 结构寿命是公开关注点；
- FOI/论文支持 component-to-system dependency 表达方法。

仍缺真实 authority gate：

- 无 F-16C Block 50 真实材料、油箱、管线、线束、防火/灭火拓扑；
- 无公开校准的 component fragility、fire growth、system cascade 或 mission-kill 数据；
- 无 external calibration dataset；
- 无 validated surrogate manifest、artifact checksum、scope-matched validation 和 residual closeout；
- 无逐字段授权可供 runtime 消费。

因此本目录只能作为后续方法设计和 residual register 输入，不得作为运行时材料/燃油/火灾 authority。
