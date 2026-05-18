# 标准化文档总览

本目录用于定义项目后续采用的**标准化建模基线**。

语言迁移说明：

- 当前 `docs/standards/` 正在迁移到“英文 `.md` 为主、中文 `.zh.md` 为辅”的双语体系。
- 规则见 [bilingual_documentation_policy.md](bilingual_documentation_policy.md)。
- 在对应英文文档尚未补齐前，现有中文主文仍可作为过渡输入，但不应视为目标稳态。

从 `2026-03-23` 开始，标准化文档体系不再以“空战单域先行、再尝试泛化”为主线，
而改为：

1. `joint`：联合层共通模板
2. `services`：军种/域画像
3. `air/*`：平台或任务层的空战专用补充标准
4. `naval/*`：海战方向的早期占位与最小任务结构基线

这样做的原因很直接：

- 美军联合层有共通的指挥授权关系
- 但空军、陆军、海军、海军陆战队的战术组织与控制口径不同
- 因此真正可复用的不是“一条完全统一的指挥链”，而是
  `joint/common core + service profile + platform/task specialization`

## 1. 当前推荐阅读顺序

1. [联合标准总览](joint/README.md)
2. [联合指挥关系与建模基线](joint/command_and_modeling_baseline.md)
3. [军种标准总览](services/README.md)
4. [美国空军配置文件](services/air_force.md)
5. [美国陆军配置文件](services/army.md)
6. [美国海军配置文件](services/navy.md)
7. [美国海军陆战队配置文件](services/marine_corps.md)
8. [文档对齐映射](document_alignment_map.md)
9. [空中平台专用标准总览](air/README.md)
10. [海军标准占位](naval/README.md)

## 2. 与旧文档的关系

以下旧文档仍保留，但已按 `ARCHIVED` 口径处理：

- `docs/Archive/air_first_standards/com/*.md`
- `docs/Archive/air_first_standards/com/two_ship/*.md`
- `docs/Archive/architecture/*.md`
- `docs/Archive/architecture/layers/*.md`

这些文档仍可用于理解项目历史推演，但不再作为当前标准化建模的主依据。

## 3. 当前建模结论

本项目后续若以美军公开资料为现实基线，则应按下面三层建模：

- `联合/共通层`
  - 指挥关系
  - 授权范围
  - 任务编组
  - 指挥意图 / 命令 / 报告
- `军种画像层`
  - 美国空军
  - 美国陆军
  - 美国海军
  - 美国海军陆战队
- `平台/任务层`
  - 空中平台
  - 海上平台
  - 地面平台
  - 领域专用的回收 / 航线 / 传感器 / 武器语义

## 4. 调研基线

本轮重构只采用官方或官方托管公开资料，优先级如下：

- 参谋长联席会议
- 美国空军条令
- 美国陆军官方条令 / 条令相关官方页面
- 美国海军官方条令 / 舰队 / 训练页面
- 美国海军陆战队官方条令

当前使用的关键来源：

- [联合参谋部出版物](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C，联合报告结构](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)
- [AFDP 3-0.1，指挥与控制](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf)
- [陆军卓越指挥中心 (MCCoE)](https://usacac.army.mil/Organizations/Centers-of-Excellence-CoE/MCCoE)
- [陆军条令参考页面](https://www.ikn.army.mil/apps/IKNHostedWebsites/Home/LoadPublishedPage?PageUID=30c204aa-de54-471a-8252-2df7d9f5a5cc)
- [陆军部队结构参考](https://www.army.mil/core/support/best-practices/ap/ap_stylebook_quick_reference.html)
- [美国第七舰队，第71特遣部队 (CTF 71) 建立](https://www.c7f.navy.mil/Media/News/Display/Article/2641477/ctf-71-establishment-enhances-readiness-in-7th-fleet/)
- [TTGP 作战指挥官会议 I](https://www.ttgp.navy.mil/OFRP-Syllabus/Warfare-Commanders-Conference-I/)
- [NAVIFOR，信息战 (IW) 拥有席位](https://www.navifor.usff.navy.mil/Press-Room/News-Stories/Article/2395110/iw-has-a-seat-at-the-table/)
- [COMPHIBRON 5 简介](https://www.surfpac.navy.mil/Ships/Amphibious-Squadron-COMPHIBRON-5/About/)
- [MCDP 1-0 含第 1-3 章](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1323621/mcdp-1-0-w-ch-1-3/)

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
- `naval/*.md`：`Specialization (early-stage)`
- `docs/Archive/air_first_standards/com/*.md`、`docs/Archive/air_first_standards/com/two_ship/*.md`：`Archived`
- `docs/Archive/architecture/*.md`：`Archived`
