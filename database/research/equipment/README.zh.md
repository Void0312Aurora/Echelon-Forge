# 全球装备调研

Language:
- English canonical: [README.md](README.md)
- Chinese companion: `README.zh.md`

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/README.md`
Owner: `database/equipment-data`
Last verified: `not established`
Content status：第一轮调研。覆盖范围仍不完整；具体数量和子型号必须逐项回到来源核验。

## 目的

本调研建立全球现役装备数据收集的来源优先基线。中国、法国、俄罗斯、英国和美国是强制最低基线，不是研究范围上限。

第一轮覆盖五常主要平台，并建立继续扩展到其他国家和地区的目录层级。暂不追求一次穷尽全球所有子型号、弹药、传感器、电子战系统和支援车辆。

## 仿真参数收集规范

本节是仿真输入的调研与提取规范，不是最终 schema、运行时契约、校准数据集或运行时数据源。

- 必须落实到具体变型和配置；相关车辆应明确 FBH、DVH 或 DVHA1。家族值只能作为上下文。
- 库存数量、编制表、采购总量和现役数量是可选元数据，不是参数记录的验收门槛。
- 优先收集几何、配置相关的质量语义、动力、机动、乘员与载荷、武器、任务系统和公开防护信息。
- 保留来源对 `curb`、`gross`、`combat`、`operational`、`transport`、`GVW`、`GVWR` 的原始含义和单位，不得压成一个质量字段。
- 每个重要字段附 source ID、证据等级、配置上下文和不确定性说明。家族来源不能自动支撑所有叶子变型。
- `unknown` 或 `not established` 只能表示暂时缺口。叶子进入 `parameter_complete` 前，每个声明的目标字段都必须有带引用的数值或有界估算；不得无说明地把家族基线回填到更重、带附件或后续配置。
- 官方来源没有公布字段时，可使用可追溯的专业资料、博物馆/档案、专题社区或其他可靠二手来源。字段必须标明二手或估算属性，保留来源 URL、日期、配置口径和不确定性，不得把二手估算写成官方规格。
- 只保留 URL 和 manifest，不复制原文。叶子文档创建后可按既有定义标记 `cataloged`，但在记录 `parameter_complete` 并完成相关交叉核验前，不视为完整数据，也不得直接供运行时使用。

## 地理覆盖

- 强制基线：中国、法国、俄罗斯、英国、美国。
- 扩展区域：NATO 欧洲、非 NATO 欧洲、中东、南亚、东亚、东南亚、非洲、拉丁美洲和大洋洲。
- 其他国家通过 operator 文件和国家级索引扩展；规范装备记录不按国家复制。
- 区域只用于索引，不替代国家所有权。

## 证据规则

- `A`：第一方政府或官方军种出版物。对该来源自己声明的事实具有高可信度。
- `B`：政府评估、专业防务参考资料或同行评审分析。作为评估可信，不等于第一方库存事实。
- `C`：可追溯厂商、研究机构、可靠二手来源，或有明确页面、作者/维护者、日期和可复现数值的专业社区来源；在缺少 A/B 时使用，估算必须明确标注。
- `D`：无法核验。不得进入装备清单。
- 型号被提及不等于获得数量证据。一个条目可以“服役存在”为高置信度，而“当前数量”仍未确认。
- 外国政府评估必须标记为评估，不得当作中立库存事实。

## 记录粒度

- 系列和家族只能作为分组节点。F-15、Rafale、Su-35、Type 055、M1 等名称本身不是有效最终记录。
- 最终记录必须落实到具体型号、变型、批次、标准、使用方和有证据的服役状态。
- 参数必须归属于叶子记录，不能只挂在家族行上。
- 原始资料包按发布者和 source ID 保存在 [raw/sources/](raw/README.md)。
- 候选覆盖和处理状态集中记录在 [backlog/](backlog/README.md)。
- 更广泛的现役与冷战候选先记录在[覆盖计划](coverage/README.md)，再进入具体领域的 backlog。

## 覆盖矩阵

### 美国

| 领域 | 第一轮覆盖 | 证据 | 置信度 |
| --- | --- | --- | --- |
| 空战 | F-22A、F-35A/B/C、F-15 系列、F-16 系列、F/A-18E/F、EA-18G | USAF Fact Sheets、US Navy Fact Files | 型号存在 A；完整现役数量尚未归一 |
| 轰炸机 | B-1B、B-2A、B-52H | USAF/AFLCMC 公开资料 | 型号存在 A；B-21 是未来系统，不计现役 |
| 运输、加油、预警 | C-5M、C-17、C-130、KC-135、KC-46A、E-3 | USAF、AMC | 型号存在 A；换装状态需逐项核验 |
| 海军 | CVN、DDG-51、DDG-1000、SSN/SSBN、两栖舰、补给舰 | US Navy、MSC | 类别 A；逐级数量待补 |
| 地面 | M1、Bradley、Stryker、HIMARS、M109、Patriot、THAAD | 官方公开资料 | 类别 A；现役数量与批次待补 |
| 无人机 | MQ-9 系列、战术无人机 | USAF/USMC | 部分 A；整个无人机库存待补 |

### 英国

| 领域 | 第一轮覆盖 | 证据 | 置信度 |
| --- | --- | --- | --- |
| 海上 | 9 艘潜艇，其中 4 艘弹道导弹核潜艇、5 艘核攻击潜艇；皇家海军水面舰队 57 艘、RFA 13 艘 | UK MoD 2025 官方统计 | A |
| 地面 | 3,955 件战斗装备；其中 APC 997、防护机动车辆 1,903、AFV 1,055；火炮车辆 236、战斗工程装备 274 | UK MoD 2025 官方统计 | A |
| 空中 | 504 架固定翼、276 架旋翼机、180 套无人机系统 | UK MoD 2025 官方统计 | A |
| 已命名平台 | Typhoon 129、Chinook 50；Apache AH-64E 持续接装 | UK MoD 2025 官方统计 | A |
| 主要家族 | Queen Elizabeth 级航母、Type 45、Astute、F-35B、P-8A、A400M、C-17、Voyager、Wildcat、Merlin | UK MoD/公开项目资料 | A/B；逐级完整数量待补 |

### 法国

| 领域 | 第一轮覆盖 | 证据 | 置信度 |
| --- | --- | --- | --- |
| 海上 | 69 艘战斗与支援舰；4 艘 SSBN、4 艘 SSN、1 艘航母、3 艘两栖直升机母舰、15 艘一线驱逐舰、6 艘监视护卫舰、17 艘近海巡逻舰、8 艘扫雷舰 | Ministère des Armées | A（官方来源；完整表格提取待补） |
| 空中 | 184 架作战飞机：Rafale 112、Mirage 2000D 50、Mirage 2000-5F 22 | Ministère des Armées | A（官方来源；完整表格提取待补） |
| 运输/加油/预警 | C-130 家族、CN235、A400M、C-135/KC-135、A330 Phénix、E-3F | Ministère des Armées | A |
| 主要海军家族 | Charles de Gaulle 航母群、Triomphant、Suffren/Rubis、FREMM/Horizon 等 | 法国国防部公开资料 | A/B；来源的聚合口径不同 |
| 地面 | Leclerc、VBCI、Griffon、Jaguar、Caesar 及保障家族 | 国防部与项目资料 | B；统一数量表仍待补 |

### 中国

| 领域 | 第一轮覆盖 | 证据 | 置信度 |
| --- | --- | --- | --- |
| 空战 | J-20、J-16、J-10B/C、J-11 家族 | 中国国防部官方发布 | 服役存在 A；库存数量未公开 |
| 轰炸/预警/运输 | H-6K、KJ-500、Y-20、YY-20A | 中国国防部官方发布 | 服役存在 A |
| 航母 | Liaoning、Shandong、Fujian | 中国国防部官方发布 | A |
| 主要水面舰艇 | Type 055、Type 052D、Type 054A | 中国国防部官方发布 | A |
| 潜艇与支援舰 | Kilo、Type 039 家族、补给舰等 | US DoD 2025 China Military Power Report | B；属外国评估，数量必须加时间点 |
| 地面装备 | 主战坦克、火炮、防空与保障家族 | 尚未完成来源归一 | 待补 |

### 俄罗斯

| 领域 | 第一轮覆盖 | 证据 | 置信度 |
| --- | --- | --- | --- |
| 空战 | Su-30SM、Su-35S 为主力战斗机；Su-34 为主力轰炸机 | 俄罗斯国防部公开声明 | 角色宣称 A；不是完整库存 |
| 战略航空 | Tu-95MS、Tu-160M 家族 | 俄罗斯国防部和采购报道 | B；当前可用数量存在争议 |
| 海军 | Borei、Yasen、Project 22350/20380、Kilo/Improved Kilo | 俄罗斯国防部与 IISS Military Balance 2025 | B；A 级完整库存清单有限 |
| 战略/防空 | S-400 及相关防空家族 | 官方与专业来源 | B；构成待补 |
| 地面 | T-72B3、T-80BVM、T-90M、BMP-3、BTR-82A 等 | 俄罗斯国防部、IISS | B/C；战时损失和现役数量必须有明确日期 |

## 来源台账

| ID | 等级 | 来源 | 日期 | 用途 | 限制 |
| --- | --- | --- | --- | --- | --- |
| S1 | A | UK Ministry of Defence，[UK armed forces equipment and formations 2025](https://www.gov.uk/government/statistics/uk-armed-forces-equipment-and-formations-2025/uk-armed-forces-equipment-and-formations-2025) | 2025 | 英国总量和主要装备类别 | 统计截至 2025-04-01 |
| S2 | A | French Ministry of the Armed Forces，[Defence key figures 2025](https://www.defense.gouv.fr/sites/default/files/ministere-armees/Chiffres_Cle%CC%81s_2025_UK.pdf) | 2025 | 法国海军、空军、运输和加油数量 | 官方聚合来源；本轮使用官方 PDF 搜索结果片段，完整表格提取待补 |
| S3 | B | US Department of Defense，[Military and Security Developments Involving the PRC 2025](https://media.defense.gov/2025/Dec/23/2003849070/-1/-1/1/ANNUAL-REPORT-TO-CONGRESS-MILITARY-AND-SECURITY-DEVELOPMENTS-INVOLVING-THE-PEOPLES-REPUBLIC-OF-CHINA-2025.PDF) | 2025-12-23 | 中国潜艇、飞机与力量发展评估 | 外国政府评估 |
| S4 | B | IISS，[The Military Balance 2025](https://www.iiss.org/publications/the-military-balance/2025/the-military-balance-2025) | 2025-02 | 跨国装备基线与俄罗斯背景 | 专业评估，不是第一方 |
| S5 | A | US Air Force，[Aircraft Fact Sheets](https://www.af.mil/About-Us/Fact-Sheets/) | 访问于 2026-09-11 | 美国机型服役存在与说明 | 按机型页面，不是统一库存 |
| S6 | A | US Navy，[Fact Files](https://www.navy.mil/Resources/Fact-Files/) | 访问于 2026-09-11 | 美国舰级和说明 | 数量和状态随页面变化 |
| S7 | A | 中国国防部 J-20、J-10C、航母和 Type 055 发布 | 2022-2025 | 中国装备服役确认 | 不披露完整库存或数量 |
| S8 | A | Russian Ministry of Defence，[principal aircraft statement](https://eng.mil.ru/news/175302dd-98a6-4f5e-807d-f35ed935d174) | 访问于 2026-09-11 | Su-30SM、Su-35S、Su-34 的宣称角色 | 存在宣传与披露限制 |
| S9 | A | Russian Ministry of Defence，[Navy](https://eng.mil.ru/en/structure/forces/navy.htm) | 访问于 2026-09-11 | 俄罗斯海军结构和部分平台 | 无统一库存 |
| S10 | A | US Marine Corps，[2025 Aviation Plan](https://media.defense.gov/2025/Mar/12/2003665702/-1/-1/1/2025-MARINE-CORPS-AVIATION-PLAN.PDF) | 2025-01/03 | USMC 航空换装与库存背景 | 仅限 USMC |
| S11 | A | French Ministry of the Armed Forces，Rafale Marine 与航母页面 | 访问于 2026-09-11 | 法国舰载机与航母航空联队 | 平台页，不是库存总数 |

## 未闭合项

1. 俄罗斯和中国没有类似英国认证统计的完整现役库存公开口径。
2. 现役、储存、退役过程中的数量必须分别加时间戳。
3. 弹药、传感器、电子战、地面防空和支援车辆需要独立调研批次。
4. 美国需要按军种归一库存，不能长期依赖分散的 fact sheet。
5. 出口型、升级批次和原型/未服役系统不能混入同一计数规则。
6. 最终每个字段都应有自己的置信度和来源覆盖，而不只是行级置信度。

## 下一批调研

1. 将每个家族行替换为具体变型/批次叶子。
2. 美国：空军、海军、海军陆战队、陆军库存归一。
3. 英国：完整设备表提取和已命名平台映射。
4. 法国：完整 key-figures 提取，加主要陆军和海军项目。
5. 中国：区分官方确认的服役存在与外国评估数量。
6. 俄罗斯：区分平时库存宣称、战时损失、现代化计划与现役证据。
