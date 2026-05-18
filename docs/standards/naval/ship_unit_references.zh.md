<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/naval/ship_unit_references.md. Review before treating this file as authoritative. -->

# 海军舰船单位参考

本记录记录了为最小海军屏卫场景选定的首批真实世界舰船单位。目的是保持单位数据可追溯到公开来源，并将测量/公开事实与运行时估算分开。

## 场景种子

第一个海军示例应为一艘单独护航舰保护后勤高价值单位：

- 护航/屏卫舰：阿利·伯克号（DDG-51），阿利·伯克级Flight I导弹驱逐舰。
- 被支援/高价值单位：刘易斯和克拉克号（T-AKE-1），刘易斯和克拉克级干货/弹药船。

这对直接映射到现有的海军任务骨架：

- DDG-51：`TASK_SCREEN`、`ScreenCommander`、`Screen`。
- T-AKE-1：`TASK_SUPPORT`、`LogisticsCoordinator`、`Support`。

## 公开来源基准

### DDG-51 Flight I / USS 阿利·伯克号

主要公开来源：

- 美国海军/SURFLANT USS 阿利·伯克号特性页面：https://www.surflant.usff.navy.mil/Organization/Operational-Forces/Destroyers/USS-Arleigh-Burke-DDG-51/About-Us/Characteristics/
- 美国海军/SURFLANT 驱逐舰舰级页面：https://www.surflant.usff.navy.mil/Organization/Operational-Forces/Destroyers/Destroyer-Ship-Class-DDG-Info-Page/

记录的公开值：

- 尺寸：153.8米 x 20.4米 x 9.3米，来自舰船专用页面。
- Flight I 满载排水量：8,230长吨，来自舰船级别页面。
- 速度：30+节，来自舰船专用页面；30节，来自舰船级别页面。
- 航程：20节时4,400海里。
- 船员：300+，来自舰船专用页面；303，来自舰船级别页面。
- 公开识别的系统包括：宙斯盾战斗系统、AN/SPY-1D雷达、AN/SPS-67(V)雷达、Mk 41垂直发射系统、5英寸/54倍径舰炮、鱼叉发射装置以及早期型号舰船的近防武器系统（CIWS）。

运行时转换在 `examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json` 中：

- 满载排水量：8,230长吨 -> 8,362,000千克（四舍五入）。
- 轻载排水量：6,711长吨 -> 6,819,000千克（四舍五入）。
- 长度：153.8米。
- 型宽：20.4米。
- 吃水：9.3米。
- 最大速度：30节 -> 15.43米/秒。
- 航程速度：20节 -> 10.29米/秒。

### T-AKE-1 / USNS 刘易斯和克拉克号

主要公开来源：

- 美国海军T-AKE概况文件：https://www.navy.mil/Resources/Fact-Files/Display-FactFiles/Article/2211797/dry-cargoammunition-ships-t-ake/
- 通用动力NASSCO T-AKE概况表（公吨排水量和14,000海里航程）：https://www.nassco.com/pdfs/T-AKE_FactSheet_Jan_2007.pdf

记录的公开值：

- 长度：689英尺。
- 型宽：106英尺。
- 吃水：30英尺。
- 排水量：来自海军概况文件为41,000吨；来自NASSCO概况表在标准吃水下为41,000公吨。
- 速度：20节。
- 航程：来自NASSCO概况表，在标准速度和吃水下为14,000海里。
- 列出的船员：来自海军概况文件为53名文职人员。

运行时转换在 `examples/config/database/ships/units/take1_usns_lewis_and_clark.json` 中：

- 满载排水量：41,000公吨 -> 41,000,000千克。
- 长度：689英尺 -> 210.0米。
- 型宽：106英尺 -> 32.31米。
- 吃水：30英尺 -> 9.14米。
- 最大速度：20节 -> 10.29米/秒。

## 建模边界

新的 `ShipPlatform` 字段是公开参数字段，而非便利占位符。它们代表排水量、尺寸、速度、航程和船员。

已知估算：

- `height_above_waterline_m` 是用于视距和未来雷达水平工作的运行时估算，因为公开的舰船特性页面列出的是吃水，而非精确的传感器/桅杆高度。
- 水面搜索雷达运行时范围目前由雷达地平线推理设定，而非保密的或未注明来源的最大雷达范围：
  - DDG-51水面搜索：3.57 * (sqrt(25米自身天线) + sqrt(5米目标)) = 25.8海里 = 46.3千米。
  - T-AKE导航/水面搜索：3.57 * (sqrt(15米自身天线) + sqrt(5米目标)) = 19.6海里 = 36.3千米。
- 舰船 `health` 按每公吨满载排水量一生命值（HP）缩放，直到存在海军伤害/杀伤校准。
- 战斗系统的武器库存仅记录在元数据中。当前运行时 `Ammo` 代表通用导弹数量，因此垂直发射系统单元、舰炮、近防武器系统和补给货物有意不被压缩成误导性的通用弹药。

## 首个场景建议

从一个不射击的屏卫保持/接触场景开始：

1. 生成 T-AKE-1，以稳定20节航向作为被支援单位。
2. 生成 DDG-51，在前方5-8海里或正横位置作为屏卫舰。
3. 添加一个未知水面接触点，位于高价值单位（HVU）地平线外但在DDG屏卫舰搜索画面内。
4. 对早期行为进行评分：维持屏卫几何、接触报告，以及高价值单位是否保持在接触点的最近接近阈值之外。

这使得首个海军场景保持真实：它从水面运动、地平线、任务分配和接触管理开始，而不是发明运行时尚未忠实建模的导弹/火炮交战。
