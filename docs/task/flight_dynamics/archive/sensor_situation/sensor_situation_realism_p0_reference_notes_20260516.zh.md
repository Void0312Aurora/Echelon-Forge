<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/sensor_situation/sensor_situation_realism_p0_reference_notes_20260516.md. Review before treating this file as authoritative. -->

# 传感器/态势真实化 P0 参考说明

状态：`2026-05-16` P0 参考摘记。

本文件只记录当前 P0 使用的公开方法血缘，不作为型号级真值数据库。

## 1. `SNR -> Pd`

- `公开来源支撑`：
  - Albersheim equation / radar detection literature
  - MathWorks Radar Toolbox 公开文档中的 detectability / probability of detection 说明
- `本仓库 P0 做法`：
  - 不直接实现 Marcum Q
  - 先算参考化 `snr_db`
  - 再用 logistic 曲线近似 `Pd(SNR, Pfa)`
- `性质`：
  - 属于 `工程近似`
  - 目标是恢复正确单调性和阈值感，不是复现严格探测统计

## 2. `M-of-N confirm`

- `公开来源支撑`：
  - 多目标跟踪与雷达 track initiation 的公开教材中常见 `2-of-3`、`3-of-4`
  - MathWorks 跟踪示例里也常见 tentative -> confirmed 的确认窗口语义
- `本仓库 P0 做法`：
  - fighter radar 默认建议 `2-of-3`
  - 只做单轨确认，不做复杂关联
- `性质`：
  - 属于 `公开工程实践`
  - 不是型号专属参数

## 3. `alpha-beta filter`

- `公开来源支撑`：
  - `alpha-beta` filter 是基础目标跟踪教材里的标准低阶滤波器
  - [kalmanfilter.net](https://kalmanfilter.net/alphabeta.html) 提供了通俗公开说明
- `本仓库 P0 做法`：
  - 只做笛卡尔位置/速度预测更新
  - 不输出完整协方差
- `性质`：
  - 属于 `标准公开算法`
  - 精度低于 Kalman，但足够作为 P0 骨架

## 4. `DataLink report`

- `公开来源支撑`：
  - Link 16 / tactical datalink 的公开材料普遍强调共享的是 track / surveillance report，而不是原始点迹
- `本仓库 P0 做法`：
  - 切断“共享 contact 后直接写接收方 ContactList”
  - 改为 `ReportTrack` 风格消息进入 `TrackManager`
- `性质`：
  - 属于 `架构语义修正`
  - 不是协议级高保真实现

## 5. `无线电视距公式`

- `公开来源支撑`：
  - 常见一阶近似：`3.57 * (sqrt(h1) + sqrt(h2))`
- `本仓库 P0 做法`：
  - 保留现有公式，只继续用于数据链物理约束
- `性质`：
  - 属于 `公开工程近似`
  - 不等于完整地形/折射/电磁传播建模
