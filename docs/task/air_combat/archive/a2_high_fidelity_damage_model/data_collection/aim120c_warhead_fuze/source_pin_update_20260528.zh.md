# AIM-120C-class Warhead / Fuze Source Pin Update

状态：`2026-05-28 / source pin update / non-authoritative`  
适用 ledger：[source_ledger.zh.md](source_ledger.zh.md)  
写入边界：本更新只补强公开来源固定、source role 和 authority gap；不创建 warhead/fuze runtime row。

## 准入边界复核

本目录继续遵守：

- [公开数据来源准入标准](../../../../../standards/foundation/public_data_source_admission.zh.md)
- [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)
- [fuze authority 放行证据清单](../../fuze_authority/fuze_release_evidence_checklist_20260528.zh.md)

没有使用 AIM-120 技术手册、训练材料、IETM、试验数据、论坛镜像、游戏数据库、未授权部件号表或疑似受限资料。公开军售公告中涉及 sensitivity 的内容只记录公开术语，不派生门限、算法、delay、可靠性或破片参数。

## 稳定来源固定补强

| ledger source_id | 固定后的 `source_ref` 口径 | 发布方 / 持有人 | 公开性 / 权利 | scope | cross-validation | residual |
|---|---|---|---|---|---|---|
| `AIM120-WF-001` | USAF `AIM-120 AMRAAM` fact sheet，官方 `af.mil` URL。 | U.S. Air Force | 官方公开网页；只链接与概述。 | AIM-120 family envelope and active-radar context。 | 与 `AIM120-WF-002/003/004` 对尺寸、全弹重量和制导描述互证。 | 不给 C 型战斗部质量、TDD 门限或破片参数。 |
| `AIM120-WF-002` | NAVAIR `AMRAAM` product page，官方 `navair.navy.mil` URL。 | Naval Air Systems Command | 官方公开网页；只链接与概述。 | AMRAAM family; includes public missile specs and warhead family label。 | 与 USAF/ACC/Navy fact sheets 互证 public envelope；与 `AIM120-WF-006` 互证 TDD 术语方向。 | 不提供 AIM-120C warhead internals、trigger radius、delay、reliability 或 fragment distribution。 |
| `AIM120-WF-003` | ACC AIM-120 fact sheet PDF，官方 `acc.af.mil` URL。 | Air Combat Command / U.S. Air Force | 官方公开 PDF；保留 URL 和题名。 | AIM-120 family public envelope and active-radar description。 | 与 USAF/NAVAIR/Navy pages 互证。 | 不含型号级战斗部/引信参数。 |
| `AIM120-WF-004` | U.S. Navy `AIM-120 AMRAAM` fact file，官方 `navy.mil` URL。 | U.S. Navy | 官方公开网页；只链接。 | AIM-120 family public role/spec context。 | 与 USAF/NAVAIR/ACC 互证公开规格和 active-radar 描述。 | 不给 C 型 TDD、safe-arm 或 lethality 参数。 |
| `AIM120-WF-005` | RTX/Raytheon AMRAAM product page。 | RTX / Raytheon | 厂商公开网页；版权保留，只作公开产品语境。 | AMRAAM family capability and program context。 | 与官方 fact sheets 交叉后仅作 sanity / variant context。 | 厂商宣传不授予 warhead mass、fuze threshold 或 lethality authority。 |
| `AIM120-WF-006` | Federal Register `76 FR 66048`, `FR Doc. 2011-27552`, DSCA Transmittal `11-38`; preferred stable PDF: `govinfo.gov/content/pkg/FR-2011-10-25/pdf/2011-27552.pdf`。 | U.S. Department of Defense / DSCA / Federal Register / govinfo | 公开 Federal Register notice；govinfo PDF 为稳定官方包引用。 | AIM-120C-7 public sensitivity notice terminology for TDD / target detection / burst-point context。 | 与 NAVAIR/USAF active-radar/proximity public descriptions and later public notice terminology 交叉。 | Notice 明确包含敏感/受控边界；只记录公开术语，不采纳 hardware/software/data details。 |
| `AIM120-WF-007` | National Museum of the U.S. Air Force `Hughes AIM-120 AMRAAM` exhibit page。 | National Museum of the U.S. Air Force | 官方博物馆公开网页；只链接。 | Early AIM-120/AIM-120A exhibit sanity for public HE warhead mass class and proximity wording。 | 与 official family specs 对全弹重量和 active-radar/proximity 语境交叉。 | AIM-120A 展品，不是 AIM-120C；40 lb class 只能作 early-series sanity。 |

## 通用物理方法来源 pin 状态

| ledger source_id | 当前 pin 状态 | 可支持 | 仍需补齐 |
|---|---|---|---|
| `PHYS-BF-001` | `pending-version-pin`，需固定 UFC 3-340-02 版本日期和 WBDG/official PDF entry。 | blast scaled-distance / overpressure / impulse method reference。 | 版本、章节、rights、benchmark linkage、surrogate validation manifest。 |
| `PHYS-BF-002` | `pending-version-pin`，需固定 DDESB TP-20 / BEC-O manual URL、版本和发布页。 | blast model implementation sanity / benchmark cross-check。 | PDF/version、tool assumptions、artifact refs、scope residual。 |
| `PHYS-BF-003` | `pending-section-pin`，需固定 UN SaferGuard IATG edition and section。 | public ammunition-management formula / safety-distance method reference。 | edition、section、rights、why applicable to surrogate method。 |
| `PHYS-BF-004/005` | `pending-acquisition`，只保留公开版本检索目标。 | protective-design / primary-fragment method candidate after acquisition。 | official public source_ref、distribution status、section and residual review。 |
| `PHYS-BF-006` | `bibliography-only` until DOI/book rights are pinned。 | Mott/Gurney/Kingery-Bulmash background bibliography。 | stable bibliographic refs, rights check, no copied tables, validation mapping。 |

这些 `PHYS-BF-*` 条目即使 pin 完成，也只支持 `method_reference` 或 `benchmark_design_reference`。它们不支持 AIM-120C 装药、壳体、预制破片、方向性、lethal radius 或 Pk。

## 字段级支持边界

| 字段 / 主题 | 当前最高支持级别 | 可用 source_id | 不能声明 |
|---|---|---|---|
| `warhead_model.public_platform_envelope` | `reference candidate` | `AIM120-WF-001/002/003/004` | AIM-120C 内部战斗部结构或装药。 |
| `warhead_model.weapon_family` | `family-level candidate` | `AIM120-WF-002`，其他 official pages 作 context。 | 破片数量、质量、速度、方向分布、lethal footprint。 |
| `warhead_model.public_mass_envelope` | `sanity only for early AIM-120` | `AIM120-WF-007` | AIM-120C specific warhead mass。 |
| `fuze_evidence.public_type` | `public terminology candidate` | `AIM120-WF-001/002/003/004/006/007` | trigger radius、SNR、TDD processing、safe-arm logic、delay、reliability。 |
| `validated_physics_surrogate.method_refs` | `pending method reference` | `PHYS-BF-001..006` after version/rights pin。 | 型号级 warhead/fuze truth 或 Pk。 |
| runtime fuze / warhead row | `unsupported` | none | deterministic fuze, effect scale, component failure probability, mission-kill probability。 |

## Authority gate 缺口

`warhead_model` 目前只支持 reference/sanity：

- 可记录 AMRAAM/AIM-120 family 尺寸、全弹重量和公开战斗部类别；
- 可记录 early AIM-120 展品的战斗部质量量级作为 sanity caveat；
- 可记录 TDD / target detection / burst-point 这类公开术语；
- 可记录 blast / fragmentation 通用方法候选。

仍缺真实 authority gate：

- 无 AIM-120C-class 公开、可再分发、scope 匹配的战斗部型号、装药、TNT 等效、壳体、破片、方向性或引信门限数据；
- 无 C-variant specific warhead/fuze public technical source；
- 无 external calibration dataset；
- 无 validated physics surrogate manifest、artifact checksum、scope-matched benchmark 和 residual closeout；
- 无 admitted fuze authority manifest 或 replay/admission result。

因此本目录不得被下游解释为 AIM-120C warhead/fuze runtime authority。
