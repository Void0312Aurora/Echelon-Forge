# 舰艇单位参考基准

Language:
- English canonical: `ship_unit_references.md`
- Chinese companion: [ship_unit_references.zh.md](ship_unit_references.zh.md)

状态：`2026-05-18`，naval specialization 的参考基准补充页。

本文档记录当前海军特化首批采用的、可由公开资料追溯的舰艇单位基准。

它不是条令文档，也不是定义海军任务语义的主文档。它的职责更窄：

- 为第一批海军标准化工作提供现实锚定的参考单位对
- 让舰艇公开参数可回溯到官方或制造商来源
- 明确区分公开事实、运行时估算与临时建模规则

语义所有权继续归属于：

- [美国海军画像](../services/navy.md)
- [Naval 标准](README.md)
- [海军最小任务结构](minimal_task_structure.md)

## 参考配对

当前维护中的首批海军参考配对是：

- 护航/屏卫单位：USS Arleigh Burke（`DDG-51`），Arleigh Burke 级 Flight I 导弹驱逐舰
- 被支援高价值单位：USNS Lewis and Clark（`T-AKE-1`），Lewis and Clark 级干货/弹药船

这对样例的价值在于：它能够较干净地映射到当前维护中的海军任务骨架，而不会超出 runtime 的现有能力边界：

- `DDG-51`：`TASK_SCREEN`、`ScreenCommander`、`Screen`
- `T-AKE-1`：`TASK_SUPPORT`、`LogisticsCoordinator`、`Support`

这页的意义并不在于“这两艘舰是唯一有效样例”，而在于它们构成了一组可追溯、可复用的首批参考基线。

## 公开来源基准

### DDG-51 Flight I / USS Arleigh Burke

主要公开来源：

- [USS Arleigh Burke characteristics page](https://www.surflant.usff.navy.mil/Organization/Operational-Forces/Destroyers/USS-Arleigh-Burke-DDG-51/About-Us/Characteristics/)
- [Destroyer ship-class page](https://www.surflant.usff.navy.mil/Organization/Operational-Forces/Destroyers/Destroyer-Ship-Class-DDG-Info-Page/)

记录的公开值：

- 尺寸：`153.8 m x 20.4 m x 9.3 m`
- Flight I 满载排水量：`8,230 long tons`
- 速度：舰艇页面写为 `30+ knots`，舰级页面写为 `30 knots`
- 航程：`4,400 nautical miles at 20 knots`
- 编制：舰艇页面写为 `300+`，舰级页面写为 `303`
- 公开列出的系统包括 Aegis Combat System、`AN/SPY-1D`、`AN/SPS-67(V)`、
  `Mk 41 VLS`、`5-inch/54 gun`、Harpoon launchers，以及早期舰型的 CIWS

运行时转换见
[examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json](../../../examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json)：

- 满载排水量：`8,230 long tons -> 8,362,000 kg`
- 轻载排水量：`6,711 long tons -> 6,819,000 kg`
- 长度：`153.8 m`
- 型宽：`20.4 m`
- 吃水：`9.3 m`
- 最大速度：`30 kt -> 15.43 m/s`
- 航程速度：`20 kt -> 10.29 m/s`

### T-AKE-1 / USNS Lewis and Clark

主要公开来源：

- [U.S. Navy T-AKE fact file](https://www.navy.mil/Resources/Fact-Files/Display-FactFiles/Article/2211797/dry-cargoammunition-ships-t-ake/)
- [General Dynamics NASSCO T-AKE fact sheet](https://www.nassco.com/pdfs/T-AKE_FactSheet_Jan_2007.pdf)

记录的公开值：

- 长度：`689 ft`
- 型宽：`106 ft`
- 吃水：`30 ft`
- 排水量：海军 fact file 写为 `41,000 tons`，NASSCO 页面写为设计吃水下
  `41,000 metric tons`
- 速度：`20 knots`
- 航程：NASSCO 页面写为设计速度与吃水下 `14,000 nautical miles`
- 编制：`53 civilian`

运行时转换见
[examples/config/database/ships/units/take1_usns_lewis_and_clark.json](../../../examples/config/database/ships/units/take1_usns_lewis_and_clark.json)：

- 满载排水量：`41,000 metric tons -> 41,000,000 kg`
- 长度：`689 ft -> 210.0 m`
- 型宽：`106 ft -> 32.31 m`
- 吃水：`30 ft -> 9.14 m`
- 最大速度：`20 kt -> 10.29 m/s`

## 建模边界

这两型舰艇记录下来的 `ShipPlatform` 数据应被视为公开参数基线，而不是方便占位值。

它们当前主要锚定：

- 排水量
- 几何尺寸
- 速度
- 航程
- 编制

下列部分仍属于显式的运行时估算或临时建模规则：

- `height_above_waterline_m` 仍是用于视距与未来雷达地平线计算的估算值，因为公开资料通常给出吃水，而不会给出精确传感器或桅杆高度
- 水面搜索雷达的运行时范围目前由雷达地平线推算约束，而不是来自任何宣称保密或无来源的最大雷达距离
- 舰船 `health` 当前按“每公吨满载排水量对应 1 HP”缩放，直到海军伤害与杀伤标定被标准化
- 战斗系统武器库存目前仍保留在 metadata 中，因为当前 runtime 的 `Ammo` 只是一种通用导弹数量载体

当前基于地平线的运行时示例：

- `DDG-51` 水面搜索：
  `3.57 * (sqrt(25 m owner antenna) + sqrt(5 m target)) = 25.8 nmi = 46.3 km`
- `T-AKE-1` 导航/水面搜索：
  `3.57 * (sqrt(15 m owner antenna) + sqrt(5 m target)) = 19.6 nmi = 36.3 km`

这些内容应被理解为维护中的建模假设，而不是条令主张。

## 参考用途

这组基线的首个预期用途，是一个低复杂度海军屏卫场景：

1. 一个被支援的后勤高价值单位
2. 一艘单独的护航或屏卫舰
3. 一个或多个水面接触目标
4. 基于屏卫几何、汇报与高价值单位保护情况进行评分

这里保留这段用途说明，只是为了说明为何优先选择这两型舰艇。真正的场景流程与评估设计，仍应继续放在 scenario/task 文档里，而不是迁入这页参考基准。

## 相关文档

- [Naval 标准](README.md)
- [海军最小任务结构](minimal_task_structure.md)
- [美国海军画像](../services/navy.md)
- [文档对齐映射](../overview/document_alignment_map.md)
