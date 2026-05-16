# 标准化文档总览

本目录用于定义项目后续采用的**标准化建模基线**。

从 `2026-03-23` 开始，标准化文档体系不再以“空战单域先行、再尝试泛化”为主线，
而改为：

1. `joint`：联合层共通模板
2. `services`：军种/域 profile
3. `air/*`：平台或任务层的空战专用补充标准

这样做的原因很直接：

- 美军联合层有共通的指挥授权关系
- 但空军、陆军、海军、海军陆战队的战术组织与控制口径不同
- 因此真正可复用的不是“一条完全统一的指挥链”，而是
  `joint/common core + service profile + platform/task specialization`

## 1. 当前推荐阅读顺序

1. [Joint 标准总览](/home/void0312/Workshop/CMO/docs/standards/joint/README.md)
2. [Joint 指挥关系与建模基线](/home/void0312/Workshop/CMO/docs/standards/joint/command_and_modeling_baseline.md)
3. [Service 标准总览](/home/void0312/Workshop/CMO/docs/standards/services/README.md)
4. [USAF Profile](/home/void0312/Workshop/CMO/docs/standards/services/air_force.md)
5. [US Army Profile](/home/void0312/Workshop/CMO/docs/standards/services/army.md)
6. [US Navy Profile](/home/void0312/Workshop/CMO/docs/standards/services/navy.md)
7. [US Marine Corps Profile](/home/void0312/Workshop/CMO/docs/standards/services/marine_corps.md)
8. [文档对齐映射](/home/void0312/Workshop/CMO/docs/standards/document_alignment_map.md)
9. [Air 平台专用标准总览](/home/void0312/Workshop/CMO/docs/standards/air/README.md)

## 2. 与旧文档的关系

以下旧文档仍保留，但已按 `ARCHIVED` 口径处理：

- `docs/Archive/air_first_standards/com/*.md`
- `docs/Archive/air_first_standards/com/two_ship/*.md`
- `docs/Archive/architecture/*.md`
- `docs/Archive/architecture/layers/*.md`

这些文档仍可用于理解项目历史推演，但不再作为当前标准化建模的主依据。

## 3. 当前建模结论

本项目后续若以美军公开资料为现实基线，则应按下面三层建模：

- `Joint/Common Layer`
  - command relationship
  - authority scope
  - task organization
  - commander intent / order / report
- `Service Profile Layer`
  - USAF
  - Army
  - Navy
  - Marine Corps
- `Platform/Task Layer`
  - air vehicle
  - naval platform
  - land platform
  - domain-specific recovery / route / sensor / weapon semantics

## 4. 调研基线

本轮重构只采用官方或官方托管公开资料，优先级如下：

- Joint Chiefs of Staff
- USAF Doctrine
- US Army official doctrine / doctrine-related official pages
- US Navy official doctrine / fleet / training pages
- US Marine Corps official doctrine

当前使用的关键来源：

- [Joint Chiefs Service Publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C, Joint Reporting Structure](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)
- [AFDP 3-0.1, Command and Control](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf)
- [Army MCCoE](https://usacac.army.mil/Organizations/Centers-of-Excellence-CoE/MCCoE)
- [Army doctrinal references page](https://www.ikn.army.mil/apps/IKNHostedWebsites/Home/LoadPublishedPage?PageUID=30c204aa-de54-471a-8252-2df7d9f5a5cc)
- [Army force structure reference](https://www.army.mil/core/support/best-practices/ap/ap_stylebook_quick_reference.html)
- [U.S. 7th Fleet, CTF 71 establishment](https://www.c7f.navy.mil/Media/News/Display/Article/2641477/ctf-71-establishment-enhances-readiness-in-7th-fleet/)
- [TTGP Warfare Commanders Conference I](https://www.ttgp.navy.mil/OFRP-Syllabus/Warfare-Commanders-Conference-I/)
- [NAVIFOR, IW Has a Seat at the Table](https://www.navifor.usff.navy.mil/Press-Room/News-Stories/Article/2395110/iw-has-a-seat-at-the-table/)
- [COMPHIBRON 5 About](https://www.surfpac.navy.mil/Ships/Amphibious-Squadron-COMPHIBRON-5/About/)
- [MCDP 1-0 w/ CH 1-3](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1323621/mcdp-1-0-w-ch-1-3/)

## 5. 对齐原则

从本轮开始，标准文档按以下状态管理：

- `Authoritative`
  - 当前标准化建模的主依据
- `Specialization`
  - 某军种或某平台的专用补充标准
- `Archived`
  - 历史设计与旧路线，保留但不再作为主依据

当前状态划分：

- `joint/*.md`：`Authoritative`
- `services/*.md`：`Authoritative`
- `air/obs.md`、`air/act.md`、`air/aim.md`、`air/rep.md`：`Specialization`
- `docs/Archive/air_first_standards/com/*.md`、`docs/Archive/air_first_standards/com/two_ship/*.md`：`Archived`
- `docs/Archive/architecture/*.md`：`Archived`
