# AIM-120C-class Warhead / Fuze Source Ledger

状态：`2026-05-28` 公开候选来源台账。所有条目默认 `authority_status=non-authoritative`。本台账不复制受限正文，不保存受限数据，不把民间数据库、论坛或仿真库单点值当权威。

## Ledger 字段

| 字段 | 说明 |
|---|---|
| `source_id` | 本台账稳定 id |
| `tier` | `Tier A / 官方-标准`、`Tier B / 公开工程材料`、`Tier C / sanity check`、`rejected` |
| `source_ref` | URL、DOI、报告号、标准号或可审计入口 |
| 发布方 / 持有人 | 公开发布或维护主体 |
| 可公开性 / 权利 | public、Distribution Statement A、网页公开、版权/转载限制或未知 |
| scope 匹配 | 与 `AIM-120C-class / blast_fragmentation / fuze / method` 的匹配范围 |
| 候选字段 | 可进入 `warhead_model`、`fuze_evidence`、`validated_physics_surrogate`、`sanity_check_only` 或 `rejected` 的字段 |
| 交叉验证状态 | 已交叉、待交叉、只能 sanity、拒绝 |
| 不确定性 / residual | 采纳后仍未关闭的问题 |

## 官方 / 公开工程候选来源

| `source_id` | `tier` | `source_ref` | 发布方 / 持有人 | 可公开性 / 权利 | scope 匹配 | 候选字段 | 交叉验证状态 | 不确定性 / residual |
|---|---|---|---|---|---|---|---|---|
| `AIM120-WF-001` | Tier B / 官方公开 fact sheet | `https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104576/aim-120-amraam/`；题名：`AIM-120 AMRAAM` | U.S. Air Force | 官方网页公开；网页版权/转载按发布方规则处理 | AIM-120 系列全弹尺寸/重量/用途；不提供 AIM-120C 型号级战斗部结构 | `warhead_model.public_platform_envelope`：length/diameter/weight 量级；`fuze_evidence.public_guidance_context=active_radar`；`sanity_check_only` for variant envelope | 与 `AIM120-WF-002`、`AIM120-WF-003` 交叉尺寸/重量和 active-radar 描述 | 未给 C 型战斗部质量、TDD 门限、破片参数；不能单独授权 warhead mass |
| `AIM120-WF-002` | Tier B / 官方公开 product page | `https://www.navair.navy.mil/product/AMRAAM`；题名：`AMRAAM` | Naval Air Systems Command | 官方网页公开；网页版权/转载按发布方规则处理 | AMRAAM 系列任务、active radar / all-weather / beyond-visual-range；公开规格含 length 12 ft、diameter 7 in、AIM-120A/B/C/C-4 348 lb、AIM-120C-5/6/7 356 lb、AIM-120D 358 lb、warhead blast fragmentation | `warhead_model.public_platform_envelope`；`warhead_model.weapon_family=blast_fragmentation`；`fuze_evidence.public_type_description=active_radar_proximity_public_description` | 与 USAF/ACC/Navy fact sheet、USAF museum 交叉基本性能和 active-radar proximity 公开描述 | 公开页仍不含 C 型战斗部内部数据；不能导出 trigger radius、delay、reliability、fragment distribution 或 warhead mass |
| `AIM120-WF-003` | Tier B / 官方公开 fact sheet PDF | `https://www.acc.af.mil/Portals/92/Docs/Fact%20Sheets%20-%202020%20Update/Facts%20Sheets%202022%20Final/AIM-120_final.pdf`；题名：`AIM-120 Advanced Medium-Range Air-to-Air Missile` | Air Combat Command / U.S. Air Force | 官方 PDF 公开；网页/PDF 版权按发布方规则处理 | AIM-120 系列尺寸/重量、active radar、fire-and-forget 类公开描述 | `warhead_model.public_platform_envelope`；`fuze_evidence.public_guidance_context=active_radar` | 与 USAF fact sheet、NAVAIR 页交叉 | 不包含 AIM-120C-class 真实引信触发门限或战斗部参数 |
| `AIM120-WF-004` | Tier B / 官方公开 Navy fact file | `https://www.navy.mil/Resources/Fact-Files/Display-FactFiles/Article/2168352/aim-120-amraam/`；题名：`AIM-120 AMRAAM` | U.S. Navy | 官方网页公开；网页版权/转载按发布方规则处理 | AMRAAM 系列公开尺寸/重量/用途和 active-radar 空空导弹描述 | `warhead_model.public_platform_envelope`；`fuze_evidence.public_guidance_context=active_radar` | 与 USAF/ACC/NAVAIR 交叉 | 不提供 C 型战斗部、TDD、safe-arm 或 lethality 参数 |
| `AIM120-WF-005` | Tier B / 公开工程/采购材料候选 | `https://www.rtx.com/raytheon/what-we-do/air/amraam-missile` 或 RTX/Raytheon AMRAAM product page | RTX / Raytheon | 厂商公开网页；版权保留，不能大段转载 | AMRAAM 系列能力、active-radar/fire-and-forget、variant program context；通常不含内部战斗部数据 | `fuze_evidence.public_guidance_context`、variant context sanity | 可与官方 fact sheets 交叉基本能力措辞 | 厂商宣传资料不授予型号级参数；不作为 warhead mass 或 trigger threshold authority |
| `AIM120-WF-006` | Tier B / 官方公开公告 | `https://www.federalregister.gov/documents/2011/10/25/2011-27552/36b1-arms-sales-notification`；`76 FR 66048`, `FR Doc. 2011-27552`, Transmittal No. `11-38` | U.S. Department of Defense / Defense Security Cooperation Agency / Federal Register | 公开 Federal Register notice；FederalRegister.gov 为信息性 XML，官方 PDF 链接到 govinfo.gov | AIM-120C-7 / SL-AMRAAM sensitivity notice；公开文本点名 target detection device、radar signal processing、target detection 和 warhead burst point determination | `fuze_evidence.public_subsystem_terms`：TDD / warhead burst-point terminology；`sanity_check_only` for C-7 guidance-section sensitivity | 与 Congress.gov / 后续 Federal Register AIM-120D/C-8 公告和 NAVAIR/ACC 交叉术语 | 公告同时说明硬件/软件/数据有 classified 范围；只记录公开术语，不采纳任何细节、门限、算法、delay 或可靠性 |
| `AIM120-WF-007` | Tier B / 官方博物馆公开 fact sheet | `https://www.nationalmuseum.af.mil/Visit/Museum-Exhibits/Fact-Sheets/Display/Article/196742/AFmuseum/hughes-aim-120-amraam/`；题名：`Hughes AIM-120 AMRAAM` | National Museum of the United States Air Force | 官方网页公开；网页版权/转载按发布方规则处理 | AIM-120A 展品 / 早期 AIM-120 系列；公开 340 lb 全弹和 40 lb high-explosive warhead 级别描述 | `warhead_model.public_mass_envelope=early_aim120_40_lb_class` sanity；`fuze_evidence.public_type_description=active_radar_proximity` | 与 USAF/NAVAIR 全弹重量和 active-radar/proximity-fuze 描述交叉；C 型战斗部质量仍未交叉 | 展品为 AIM-120A，不是 AIM-120C；40 lb 只能作为早期系列公开量级，不可外推为 C 型 calibrated mass |

## 通用 blast / fragmentation 方法候选

| `source_id` | `tier` | `source_ref` | 发布方 / 持有人 | 可公开性 / 权利 | scope 匹配 | 候选字段 | 交叉验证状态 | 不确定性 / residual |
|---|---|---|---|---|---|---|---|---|
| `PHYS-BF-001` | Tier A / 标准公开工程方法 | `UFC 3-340-02, Structures to Resist the Effects of Accidental Explosions`；WBDG / Whole Building Design Guide UFC entry | U.S. DoD Unified Facilities Criteria / WBDG | UFC 文档通常公开发布；需在采纳版本中记录 Distribution Statement 和版本日期 | 通用 accidental explosion blast 载荷、scaled distance、结构防护方法；不是空空导弹战斗部真值 | `validated_physics_surrogate.method_ref` for blast scaled-distance / overpressure / impulse proxy；`validation_criteria` candidate | 可与 DDESB BEC-O / CONWEP / UN IATG 方法交叉 | 需要 TNT equivalent、自由场/反射面、爆高和目标几何假设；不能给 AIM-120C 装药或 kill probability |
| `PHYS-BF-002` | Tier A / 官方公开工具文档 | `DDESB Technical Paper 20, DDESB Blast Effects Computer - Open (BEC-O) User's Manual and Documentation` | Department of Defense Explosives Safety Board | DDESB 公开技术论文入口；需记录具体 PDF URL、版本和权利 | 通用 blast effects computer / Kingery-Bulmash 类 blast 计算方法 | `validated_physics_surrogate.method_ref` for blast model implementation / benchmark cross-check | 与 UFC 3-340-02 / CONWEP 系方法交叉 | blast-only；不含 AIM-120C warhead-specific fragmentation 或 fuze truth |
| `PHYS-BF-003` | Tier A / 国际公开指南 | `https://unsaferguard.org/`；UN SaferGuard IATG，候选 `IATG 01.80 Formulae for ammunition management` 和相关 calculators | United Nations SaferGuard / IATG | UN SaferGuard 公开网页/指南；按 UN/IATG 版权条款处理 | 通用弹药管理公式、爆炸/破片量级和安全距离方法；非型号级 | `validated_physics_surrogate.method_ref` for Gurney / scaled-distance / safety-distance sanity when exact section is pinned | 与 UFC / DDESB /公开教材交叉 | 需固定具体 IATG 版本和章节；安全距离方法不等价杀伤模型 |
| `PHYS-BF-004` | Tier A / 官方公开防护设计方法候选 | `TM 5-855-1 / Fundamentals of Protective Design for Conventional Weapons` 或公开 CONWEP 参考入口；需固定公开版本 | U.S. Army / DoD legacy protective design references | 仅采纳公开发布且可再引用的版本；不得复制受限表格 | 通用 conventional weapons blast/fragment protective design | `validated_physics_surrogate.method_ref` for fragment/blast protective design formulas | `pending`：需固定公开版本和 rights | 防护设计不等价空空导弹杀伤；需要 validation manifest |
| `PHYS-BF-005` | Tier A / DDESB 破片方法候选 | `DDESB Technical Paper 15 / 16` 中公开 primary fragment / protective construction / fragment characteristics 方法；需固定具体公开 PDF | Department of Defense Explosives Safety Board | 仅采纳公开发布、可审计版本 | 通用 primary fragment characteristics、protective construction fragment handling | `validated_physics_surrogate.method_ref` for Mott/Gurney/primary-fragment mass or velocity candidates after acquisition | `pending`：需固定具体 TP 号、版本、section、rights | 不能补 AIM-120C 壳体、预制破片或方向性；方法必须和 benchmark 分离 |
| `PHYS-BF-006` | Tier A / 经典公开论文/教材候选 | Mott fragment distribution、Gurney velocity equations、Kingery-Bulmash blast relations 的公开论文/教材/DOI 条目 | 原作者 / 学术出版方 | 可能有版权；可引用 bibliographic metadata，不复制受限正文 | 通用 blast-fragmentation 机制公式 | `validated_physics_surrogate.method_ref` / bibliography | 与 UFC/DDESB/UN 方法交叉 | 原始论文版权和适用域需逐条审查；不能作为 AIM-120C 型号真值 |

## Sanity check only

| `source_id` | 来源类型 | `source_ref` | 发布方 / 持有人 | 可公开性 / 权利 | 可用字段 | 交叉验证状态 | 限制 |
|---|---|---|---|---|---|---|---|
| `SAN-AIM120-001` | 民间数据库 | `https://www.designation-systems.net/dusrm/m-120.html` | Designation-Systems.net | 民间公开网站；版权归站点所有 | variant history、公开尺寸/重量量级、部件号线索 | 只能与官方 fact sheet 做量级对照 | 不作为 warhead/fuze authority；部件号和质量需要官方/标准来源确认 |
| `SAN-AIM120-002` | 民间安全/武器资料库 | MissileThreat / CSIS AMRAAM page | CSIS Missile Defense Project | 公开网页；版权归发布方 | 系列概述、尺寸/重量/射程量级 | sanity only | 不是 warhead/fuze engineering source；不得导出 trigger or lethality |
| `SAN-AIM120-003` | 百科/汇编 | Wikipedia AIM-120 AMRAAM 及其引用链 | Wikipedia contributors / linked sources | CC BY-SA，但引用链质量不一 | 用于发现公开引用线索，不采纳单点值 | sanity only | 不把 wiki 表格值写为 candidate authority |
| `SAN-AIM120-004` | 仿真/游戏/民间数据库 | CMANO / Command DB、DCS、War Thunder、论坛表格、GitHub 游戏配置 | 各站点/项目 | 权利不一，常不可审计 | 仅用于发现明显量级异常 | sanity only | 单点 warhead mass、fuse radius、fragment count、damage、Pk 必须拒绝权威化 |
| `SAN-AIM120-005` | 官方公告线索但非 C 型直接证据 | Federal Register / Congress.gov 中 AIM-120D / AIM-120D-3 / AIM-120C-8 军售公告，例如 `public-inspection.federalregister.gov/2024-12392.pdf` | U.S. Department of Defense / Federal Register / Congress.gov | 公开公告；需逐条固定最终 Federal Register 或 Congress.gov URL | 可帮助确认 AMRAAM target-detection / warhead-detonation terminology，但常针对 D/D-3 而不是 C 型 | terminology sanity | 与 `AIM120-WF-006` 交叉 | 不把 D/D-3 TDD 描述外推成 C 型参数；不采纳 classified/sensitive 技术细节 |

## 拒绝 / 排除记录

| `rejection_id` | 来源 | 排除原因 | 影响范围 | 备注 |
|---|---|---|---|---|
| `REJ-AIM120-001` | 标注 FOUO/CUI/ITAR/EAR-restricted、classified、limited distribution、export-controlled 或不可再分发的 AIM-120 技术手册、训练材料、IETM、维修手册、试验报告 | 权利/敏感性不允许 | 全部字段 | 不读取、不摘录、不入库；只保留“拒绝类别” |
| `REJ-AIM120-002` | 论坛、截图、网盘、社媒转帖中的 WDU/FZU 部件号、战斗部质量、引信触发半径、破片数、破片速度、kill radius | provenance 缺失且高敏感/高误差风险 | `warhead_model`、`fuze_evidence`、runtime rows | 可作为搜寻公开来源的线索，但不能进入候选字段 |
| `REJ-AIM120-003` | CMANO / Command DB 或其他仿真库单点 `warhead`, `fuse radius`, `damage`, `DP`, `Pk` 值 | 民间数据库不能单独授权，且常是游戏/仿真抽象 | `warhead_model`、`fuze_evidence`、`component_failure_probability` | 只能 sanity check；不得复制为真实参数 |
| `REJ-AIM120-004` | 未固定 source_ref 的 “AIM-120C has X lb warhead / Y m lethal radius” 说法 | source_ref / 发布方 / 权利 / provenance 缺失 | warhead mass、lethal radius | 拒绝进入 ledger 候选表，只可记为 unresolved claim |
| `REJ-AIM120-005` | 任何能具体描述 AIM-120C TDD 信号处理、safe-arm 逻辑、真实触发门限、delay、可靠性、抗干扰细节的非公开资料 | 可能受限且超出公开建模边界 | deterministic fuze | 不用于 Phase 4 admission |

## 候选字段准入矩阵

| 字段 | 当前状态 | 允许来源 | 禁止来源 | 备注 |
|---|---|---|---|---|
| `warhead_model.weapon_family` | candidate | 官方/公开工程材料描述 `blast-fragmentation`、`high-explosive fragmentation`、`directed fragmentation` 等类别 | 民间 DB 单点值 | 可写 `blast_fragmentation`，保留 source_ref 和 uncertainty |
| `warhead_model.mass_kg` | deferred / sanity only | `AIM120-WF-007` 可支持早期 AIM-120 40 lb 级公开 sanity；后续若找到官方/标准公开 C 型战斗部质量，可进入 candidate | wiki/论坛/CMANO 单点质量 | 当前只能记录 `early_aim120_40_lb_class / aim120c_specific_unknown`，不得作为 calibrated C 型 mass |
| `warhead_model.lethal_radius_m` | rejected for authority | 公开标准方法可生成 surrogate footprint for validation experiments | CMANO/game fuse radius、论坛 kill radius | 不得写型号级 lethal radius |
| `fuze_evidence.public_type` | candidate | NAVAIR/USAF/ACC/Navy 公开 active radar / proximity / TDD 类描述 | 论坛和不可再分发手册 | 只能描述类别，不导出门限 |
| `fuze_evidence.trigger_radius_m` | deferred / rejected for authority | 未来只有完整 fuze authority manifest 可授权 | CMANO/game/论坛值 | 当前不得进入运行时 authority |
| `fuze_evidence.delay_s` | deferred / rejected for authority | 未来公开验证 surrogate 或外部校准数据 | 未公开手册/仿真库值 | 当前无候选 |
| `validated_physics_surrogate.method_refs` | candidate | UFC、DDESB、UN IATG、公开论文/教材 | 受限表格、不可再分发软件、游戏配置 | 方法不是型号级真值，必须有 validation manifest |
| `vulnerability_evidence.rows` | deferred | 未来公开校准数据或已验证 surrogate 输出 | 本台账所有 sanity-only 来源 | 本包不生成 rows，只收集来源 |

## 交叉验证摘要

| 主题 | 交叉验证状态 | 当前判断 |
|---|---|---|
| AIM-120 系列尺寸/全弹质量 | NAVAIR / USAF / ACC / Navy / USAF museum 公开资料可交叉；C/C-4 和 C-5/6/7 全弹重量以 NAVAIR 公开页为最直接官方记录 | 可作为 public envelope candidate |
| active radar / fire-and-forget | USAF / ACC / NAVAIR / RTX 可交叉 | 可作为 guidance / fuze context candidate，但不是 trigger model |
| blast-fragmentation family | NAVAIR 公开规格直接列 `Warhead: Blast fragmentation`，可与其他公开资料方向交叉；C 型具体 warhead 细节不足 | 可写 family-level candidate；mass/debris distribution deferred |
| 40 lb 级早期 AIM-120 战斗部质量 | `AIM120-WF-007` 官方博物馆页支持早期 AIM-120A 展品量级；C 型未交叉 | sanity only for AIM-120 series, C-specific mass deferred |
| TDD / proximity fuze 细节 | `AIM120-WF-006` 可提供 C-7 级公开术语；缺少可公开工程参数 | deterministic fuze 仍 deferred |
| blast scaled distance | UFC / DDESB / UN IATG /公开工程教材可交叉 | 可作为 surrogate method candidate |
| fragmentation Gurney/Mott | DDESB / UN IATG /公开论文可交叉，但需固定版本 | pending method candidate |

## 残余风险

| `residual_id` | 缺口 | 影响 | 当前处理 |
|---|---|---|---|
| `RES-AIM120-001` | AIM-120C-class 真实战斗部型号、装药、壳体、预制破片和方向性未知 | 不能校准 fragment energy / areal density / lethal footprint | 只记录 family-level `blast_fragmentation`；surrogate 必须显式 uncertainty |
| `RES-AIM120-002` | 公开资料不给 C 型 TDD / radar proximity 触发门限、delay、可靠性 | 不能放行 deterministic fuze | Phase 4 继续 deferred |
| `RES-AIM120-003` | blast 方法需要 TNT equivalent 和环境假设 | blast overpressure / impulse proxy 不可直接型号化 | 在 surrogate model card 中列参数假设和 residual |
| `RES-AIM120-004` | fragmentation 方法需要壳体/破片初始条件 | fragment energy / areal density proxy 只能做机制载荷候选 | 需要 validation benchmark，不得用二手质量补真值 |
| `RES-AIM120-005` | F-16C component fragility/Pk 数据未收集 | 不能生成 component failure probability authority | 交给 component_fragility_vulnerability 包 |

## 下一步

- 为 `AIM120-WF-006` 补官方 PDF checksum / govinfo.gov PDF URL；若引用其他军售公告，逐条新增 source_id，不复用泛化线索；
- 为 `PHYS-BF-001` 到 `PHYS-BF-006` 各自补版本号、PDF checksum、章节和 rights；
- 若要进入 `validated_physics_surrogate`，另建 surrogate model card、validation manifest、benchmark source ledger 和 residual register。
