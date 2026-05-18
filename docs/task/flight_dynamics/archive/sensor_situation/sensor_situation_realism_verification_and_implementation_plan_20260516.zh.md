# 传感器/态势感知真实化核实与实现方案

状态：`2026-05-16` 方向二执行稿。

关联输入：

- [传感器与态势感知现实性分析](sensor_situation_realism_analysis_20260516.zh.md)
- [DefaultSensorModel](../../../../src/models/systems/default_sensor_model.cpp)
- [SensorSystem](../../../../src/systems/systems/sensor_system.h)
- [TrackManagerSystem](../../../../src/systems/systems/track_manager_system.h)
- [DataLinkSystem](../../../../src/systems/systems/data_link_system.h)
- [EWSystem](../../../../src/systems/systems/ew_system.h)
- [DefaultEnvironmentModel](../../../../src/models/environment/default_environment_model.cpp)
- [Sensor 组件](../../../../src/components/systems/sensor.h)
- [TrackManagement 组件](../../../../src/components/systems/track_management.h)
- [DataLink 组件](../../../../src/components/systems/data_link.h)
- [Comm 组件](../../../../src/components/systems/comm.h)
- [UnitDefinition Loader](../../../../src/content/unit_definition_loader.cpp)

文档目的：

- 核实现有调研中哪些判断已被代码证实，哪些需要修正或补充。
- 给出贴合当前 ECS/组件结构的落地方案，不空谈“理想系统”。
- 搜集一批足够靠谱、可直接服务参数化和近似标定的数据源。
- 为后续代码改造和真实性测试提供顺序明确的入口。

---

## A. 核实结论

### A.1 总体判断

现有调研的大方向是**属实的**：当前系统更接近“RL 训练级传感器抽象”，而不是“火控级雷达/航迹/数据链仿真”。

但结合代码后，需要把结论分成三类：

1. **完全属实**
2. **基本属实，但表述需要更精确**
3. **需要补充的遗漏点**

### A.2 完全属实的结论

#### 1. 当前探测概率不是 SNR/Pd 模型

属实。

- [default_sensor_model.cpp:127](../../../../src/models/systems/default_sensor_model.cpp) 到 [default_sensor_model.cpp:212](../../../../src/models/systems/default_sensor_model.cpp) 的探测主链路仍然是：
  `FOV/距离门控 -> range_factor -> aspect_factor -> doppler_factor -> weather/sun factor -> detection_prob`
- `signal_strength` 在 [default_sensor_model.cpp:235](../../../../src/models/systems/default_sensor_model.cpp) 之后才计算，且只用于输出 `Detection.signal_strength`，不回馈探测成功率。

因此“无 SNR 门限、无 Pd(Pfa,SNR) 映射”这个判断准确。

#### 2. 无 M-of-N 检测确认

属实。

- [SensorSystem:47](../../../../src/systems/systems/sensor_system.h) 每次扫描直接生成 `fresh_contacts`
- [TrackManagerSystem:131](../../../../src/systems/systems/track_manager_system.h) 首次看到 contact 即建 track
- 没有 tentative/confirmed 状态，也没有 `m_hits / n_scans`

这会直接导致边缘探测条件下的“闪烁目标”被立即视为可用航迹。

#### 3. 航迹管理没有滤波器

属实。

- [track_manager_system.h:135](../../../../src/systems/systems/track_manager_system.h) 和 [track_manager_system.h:183](../../../../src/systems/systems/track_manager_system.h) 都是“直接覆盖最新测量值”
- [SystemTrack:24](../../../../src/components/systems/track_management.h) 虽然有 `vx/vy/vz`，但当前系统没有赋值路径

所以“无预测、无平滑、无速度估计、无不确定性”这个判断成立。

#### 4. 数据链共享的不是滤波航迹，而是 contact/真值坐标

属实，而且比原文描述更严重。

- [data_link_system.h:103](../../../../src/systems/systems/data_link_system.h) 直接把发送方 `ContactList` 融到接收方 `ContactList`
- [data_link_system.h:143](../../../../src/systems/systems/data_link_system.h) 同时又通过 `CommQueue` 发 `ReportContact`
- 发消息时使用的是目标实体真值坐标 [data_link_system.h:147](../../../../src/systems/systems/data_link_system.h)，不是发送方的测量值或滤波估计

所以当前不只是“共享原始接触”，而是**共享 contact 外加真值位置抄送**。

#### 5. IFF/分类是上帝视角

属实。

- [classify_track_from_alliance():13](../../../../src/systems/systems/track_manager_system.h) 直接读 `Alliance.side`
- 本地探测和数据链航迹都沿用这条路径 [track_manager_system.h:141](../../../../src/systems/systems/track_manager_system.h)、[track_manager_system.h:190](../../../../src/systems/systems/track_manager_system.h)

这不是“简化 IFF”，而是“绕过 IFF/识别问题”。

#### 6. 环境对传感器影响几乎未真正启用

属实。

- `check_line_of_sight()` 只检查端点是否埋地 [default_environment_model.cpp:147](../../../../src/models/environment/default_environment_model.cpp)
- `get_weather_attenuation()` 固定返回 `0.0` [default_environment_model.cpp:153](../../../../src/models/environment/default_environment_model.cpp)
- 太阳干扰只是视觉/IR 探测概率乘 `0.1` [default_sensor_model.cpp:106](../../../../src/models/systems/default_sensor_model.cpp)

因此天气、地形遮蔽、杂波、真实太阳背景目前都没有形成可用的物理限制。

### A.3 基本属实，但需要修正或补充的结论

#### 1. “无多传感器融合”需要修正为“框架允许多个来源，但没有真正融合”

原文说“无多传感器融合”，大方向没错，但要更精确：

- `TrackSource::Fused` 已存在于 [track_management.h:7](../../../../src/components/systems/track_management.h)
- 观测接口也已经把 `source` 和 `classification` 暴露到 agent observation [simulation_kernel_observation_api.cpp:214](../../../../src/core/engine/simulation_kernel_observation_api.cpp)

真正缺的是：

- 多源关联
- 加权更新
- 来源质量管理
- `Fused` 状态落地

因此应修正为：

> 当前系统具备“多来源字段与观测出口”，但尚未实现真正的 track-to-track fusion。

#### 2. “无无线电地平线”不准确，应改成“数据链地平线已做一阶近似，但传感器 LOS 没做”

- 数据链链路里已经有标准近似公式 `3.57 * (sqrt(h1) + sqrt(h2))` [data_link_system.h:91](../../../../src/systems/systems/data_link_system.h)
- 但传感器 LOS 仍只有端点落地判断 [default_environment_model.cpp:147](../../../../src/models/environment/default_environment_model.cpp)

因此更准确的说法是：

> 数据链通信范围已经用了 4/3 地球近似的无线电视距公式；真正缺的是传感器侧的地形/曲率遮蔽，以及非标准折射条件下的变化。

#### 3. “航迹 ID = entity_id”需要补充一个后果

原文判断属实，但还应该补一句：

- 当前很多上层逻辑已经依赖 `track.id == entity_id`
- 例如武器发射前提就是 `ContactList` 中是否存在目标 `target_id`

这意味着从 `entity_id` 退出来不能一步到位，必须采用：

- `track_id` 内部分配
- `entity_ref` 仅作为 debug / truth hook
- 上层接口逐步改读 `track_id + classification + quality`

否则会牵一发动全身。

#### 4. “干扰判定为二值”需要修正为“两段式：探测前 burn-through 二值裁掉，探测后无连续退化”

- 在 [default_sensor_model.cpp:252](../../../../src/models/systems/default_sensor_model.cpp) 以后，若目标带噪声压制干扰且距离大于烧穿距离，直接 `return`
- 这意味着不是“先降概率再遮蔽”，而是“探测前硬截断”

所以更准确的说法是：

> 当前噪声干扰是 pre-detection hard kill 型处理，而不是基于 J/S 或 S/J 的连续退化。

### A.4 需要补充的遗漏点

#### 1. 当前雷达默认 `range_power` 配置明显不合理

这是现有分析文档没点出来，但非常重要。

- `Sensor` 注释里写雷达应接近 `R^4` [sensor.h:19](../../../../src/components/systems/sensor.h)
- 但公开配置里不少雷达都写成了 `2.0`
  - [an_apg_68.json:1](../../../../examples/config/database/aircraft/modules/sensors/an_apg_68.json)
  - [irbis_e.json:1](../../../../examples/config/database/aircraft/modules/sensors/irbis_e.json)
  - [e3_sentry.json:1](../../../../examples/config/database/aircraft/units/e3_sentry.json)

这会系统性高估远距离雷达表现，即便暂时不引入 SNR，也需要尽快纠正。

#### 2. DataLink 配置目前没有真正使用数据库里的 `network_id`

- loader 读了 `has_data_link` 和 `data_link_network_id` [unit_definition_loader.cpp:250](../../../../src/content/unit_definition_loader.cpp)
- 但默认工厂里实际按阵营强制赋值 `Blue=1, Red=2` [default_unit_factory.h:475](../../../../src/models/core/default_unit_factory.h)

这意味着文档中“network_id = side”不只是近似，而是**硬编码覆盖**。

#### 3. ContactList 与 TrackDatabase 的职责已经开始重叠

当前代码里：

- `ContactList` 既承载局部探测，又被数据链直接写入
- `TrackDatabase` 再从 `ContactList + CommQueue` 生成观测航迹

这会导致“contact 是点迹还是共享航迹”的语义越来越混乱。后续真实化必须尽早把两者分层。

#### 4. 观测接口暂未输出航迹质量/确认状态

- 观测当前只输出 `range/azimuth/elevation/closing_speed/time_since_update/source/classification`
- 没有 `confidence`、`track_quality`、`tentative/confirmed`

即使后端实现了 M-of-N 和滤波，如果不把质量暴露给上层 agent，训练还是会把“低置信临时点迹”和“成熟航迹”一视同仁。

---

## B. 实现方案

目标不是一步做成完整火控系统，而是在当前结构上优先补上五个最值钱的环节：

1. `SNR/Pd` 近似
2. `M-of-N` 探测确认
3. 基本航迹滤波
4. 数据链从 contact 升级为 track
5. 简化 IFF/分类与基础环境影响

### B.1 设计原则

#### 1. 保留现有 ECS 主流程，不大改系统顺序

当前顺序：

`SensorSystem -> DataLinkFusionSystem -> TrackManagerSystem -> EWSystem`

建议仍沿用该顺序，但重定义每层职责：

- `SensorSystem`：只产出本地测量 contact，不负责“航迹级共享”
- `DataLinkSystem`：共享 track report，不再直接写接收方 `ContactList`
- `TrackManagerSystem`：唯一负责 tentative/confirmed track 生命周期、本地滤波、多源融合、分类状态

#### 2. 允许过渡期保留 `entity_id` 真值钩子，但从业务逻辑里降级

短期可保留：

- `Detection.target_id`
- `SystemTrack.entity_id`

但要明确：

- 只用于测试/调试/真值对照
- 不再作为唯一关联键

#### 3. 先做“近似真实”，再做“精细真实”

本轮优先：

- 单脉冲/单通道近似
- 常数误警率用固定 `Pfa`
- `alpha-beta` 先于 Kalman
- IFF 状态机先于完整 Mode 5
- 雨雾/地平线/太阳角度先于复杂杂波图

### B.2 数据结构改造建议

#### 1. 扩展 `Sensor`

文件：

- [sensor.h](../../../../src/components/systems/sensor.h)
- [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)

建议新增字段：

```cpp
double reference_snr_db;          // 在 reference_range_m、reference_rcs_m2 条件下的单次检测 SNR
double reference_range_m;         // 标定参考距离
double reference_rcs_m2;          // 标定参考 RCS
double pfa;                       // 虚警概率，默认 1e-6
int confirm_hits_m;               // M-of-N 的 M
int confirm_window_n;             // M-of-N 的 N
double revisit_merge_ttl_s;       // 未命中时的 tentative 保留
double velocity_noise_std;        // 闭合速度/径向速度测量噪声
double iff_interrogation_period_s;
bool supports_iff_interrogation;
```

说明：

- 这套字段能在不引入完整雷达方程参数的情况下，先把 `SNR -> Pd` 跑起来
- `reference_snr_db` 比直接塞 `Pt/G/B/F` 更适合当前数据库现状

#### 2. 扩展 `Detection`

文件：

- [sensor.h](../../../../src/components/systems/sensor.h)

建议新增：

```cpp
double snr_db;
double detection_prob_used;
double measurement_sigma_range_m;
double measurement_sigma_bearing_deg;
double measurement_sigma_elevation_deg;
int sensor_type;
bool local_sensor_hit;
bool iff_reply_present;
```

原因：

- 这些字段后续既可喂给 track filter，也可直接写 diagnostic/test log

#### 3. 扩展 `SystemTrack`

文件：

- [track_management.h](../../../../src/components/systems/track_management.h)

建议新增：

```cpp
enum class TrackStatus { Tentative = 0, Confirmed, Coasted, Dropped };
enum class IffState { None = 0, FriendlyReply, NoReply, Ambiguous };
enum class TrackIdentity { Unknown = 0, AssumedFriendly, Friendly, Suspect, Hostile, Neutral };

TrackStatus status;
IffState iff_state;
TrackIdentity identity;

double quality;                  // 0..1
double covariance_pos_m2;
double covariance_vel_m2ps2;
int hit_count_window;
int miss_count_window;
double last_local_update_time;
double last_datalink_update_time;
double last_iff_time;
uint32_t source_mask;            // radar / ir / datalink / rwr
```

短期不必上全矩阵协方差，先用标量位置/速度方差即可。

#### 4. 扩展 `CommPacket`，新增“航迹报告”负载

文件：

- [comm.h](../../../../src/components/systems/comm.h)
- [comm_message.h](../../../../src/components/command/common/comm_message.h)

建议增加：

```cpp
ReportTrack,
ReportTrackQuality,
ReportIFF
```

同时在 `CommPacket` 增加：

```cpp
uint64_t track_ref;
double vx;
double vy;
double vz;
double quality;
int classification_code;
int source_code;
```

这样可以在不推翻现有消息框架的前提下，把数据链从 `ReportContact` 升级为 `ReportTrack`。

### B.3 探测模型：SNR/Pd 近似

#### 1. 推荐的第一版近似

文件：

- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)

建议替换当前 `detection_prob` 生成逻辑：

1. 先算几何门控
   - 量程
   - FOV
   - LOS
2. 计算等效 `sigma_rcs`
   - 基于 `RCSProfile` 前/侧/后插值
3. 计算参考 SNR 缩放
   - 雷达：`snr_linear = snr_ref_linear * (sigma / sigma_ref) * (R_ref / R)^4 * env_factor * jam_factor * aspect_doppler_factor`
   - IR/Visual：先保留 `R^-2` 族，但也统一转成“等效 SNR”
4. 将 `snr_db` 映射到 `Pd`
   - 先用 Albersheim 近似或 logistic 拟合
5. 产出单次 `Detection`

#### 2. 推荐的工程近似公式

第一阶段不强求完整 Marcum-Q，可用：

```text
Pd = 1 / (1 + exp(-k * (snr_db - snr_50_db)))
```

其中：

- `snr_50_db` 由 `Pfa` 与积分脉冲数近似决定
- `k` 用于控制阈值陡峭度

对雷达更进一步一点，可做成：

```text
Pd = logistic(albersheim_margin_db)
albersheim_margin_db = snr_db - snr_required_db(pd_ref, pfa, n_pulses)
```

在当前项目里，这已经比 `1 - (R/Rmax)^n` 靠谱很多。

#### 3. RCS 方向图最小落地方案

文件：

- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- [ew.h](../../../../src/components/systems/ew.h)

建议：

- 用目标视线角在 `frontal/side/rear` 三点插值
- 先不做 Swerling I-IV 全家桶
- 但允许加一个 `rcs_fluctuation_std_db`

例如：

- 迎头附近取 `frontal_rcs`
- 90 度附近取 `side_rcs`
- 尾追附近取 `rear_rcs`
- 线性或余弦插值
- 每次扫描叠加一个小幅随机起伏，例如 `N(0, 2~4 dB)`

这样就能明显优于“始终 frontal_rcs”。

#### 4. 多普勒与 beam aspect 的第一版修正

当前 `0.1` 乘子太粗。建议改为：

- 对 radar 增加 `clutter_notch_speed_mps`
- 增加 `beam_aspect_penalty`
- 当 `|v_closing| < notch` 且目标在下视/低空背景中时，直接把 `snr_db` 减一个固定量，例如 `-12 dB`
- 当是纯空空、天空背景时，只减 `-4 ~ -6 dB`

这样先把“完全盲 / 部分退化 / 正常”分开。

### B.4 M-of-N 检测确认

#### 1. 建议放在 `TrackManagerSystem` 而不是 `SensorSystem`

原因：

- `SensorSystem` 更适合只做 measurement generation
- `TrackManagerSystem` 天然负责 contact -> track 生命周期

#### 2. 具体实现

文件：

- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)

建议引入两层对象：

- `MeasurementContact`：单次扫描点迹
- `SystemTrack`：跨扫描维持的航迹

当前不必新建组件名，也可以先在 `SystemTrack` 里加状态：

- 新建 contact 时先建 `Tentative`
- 若最近 `N` 次扫描中命中次数 `>= M`，升级为 `Confirmed`
- 连续未命中时进入 `Coasted`
- 超过 `coast_timeout_s` 删除

推荐默认值：

- 机载火控雷达：`2-of-3`
- 大型预警机 / 对海搜索：`2-of-2` 或 `3-of-4`
- IRST：`2-of-4`

#### 3. 兼容现有上层逻辑

短期建议：

- `ContactList` 仍可保留原样供兼容
- 但武器发射、共享态势、agent 可信航迹应只读 `Confirmed track`

也就是先把“战术可用”和“传感器看见过”分开。

### B.5 基本航迹滤波

#### 1. 第一阶段用 `alpha-beta` 即可

文件：

- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)

建议针对每条 `SystemTrack` 维护：

- `x/y/z`
- `vx/vy/vz`
- `covariance_pos_m2`
- `covariance_vel_m2ps2`

更新流程：

1. 预测
   - `x += vx * dt`
   - `y += vy * dt`
   - `z += vz * dt`
2. 用 measurement residual 更新
   - `x += alpha * rx`
   - `vx += beta/dt * rx`
   - 其余维度同理

推荐起始值：

- 高刷新机载雷达：`alpha=0.55~0.75`, `beta=0.05~0.18`
- 低刷新 AWACS：`alpha=0.35~0.55`, `beta=0.02~0.10`

#### 2. 数据链航迹与本地航迹的融合

若本地 track 已存在：

- 本地测量命中时，以本地为主更新
- 数据链消息只做辅助修正或更新 `source_mask`

若仅有数据链：

- 可直接建立 `Tentative` 或 `Confirmed remote track`
- 但质量和时效应低于本地火控轨

### B.6 数据链从 contact 到 track 的升级

#### 1. 不再直接写接收方 `ContactList`

这是最重要的结构改动之一。

当前 [data_link_system.h:103](../../../../src/systems/systems/data_link_system.h) 直接把 sender contact 塞进 receiver contact，会混淆“本地探测”和“共享航迹”。

建议改为：

- `DataLinkSystem` 只发 `ReportTrack`
- 接收方不再把它写入 `ContactList`
- `TrackManagerSystem` 从 `CommQueue` 吃 `ReportTrack`，生成 `TrackSource::DataLink` 航迹

#### 2. 报告内容

发的不是原始点迹，而是：

- `track_id` 或 `remote_track_ref`
- `x/y/z`
- `vx/vy/vz`
- `quality`
- `classification_code`
- `timestamp`
- `age`
- `source_code`

#### 3. 最小职责控制

本轮不做完整 Link 16 网络管理，但建议先加两件事：

- `report_min_quality`
- “同目标仅最高质量节点上报”

实现上可简单做成：

- sender 遍历自己 `TrackDatabase`
- 只上报 `Confirmed`
- 每个目标在本节点只发一条最高质量 track

### B.7 简化 IFF/分类

#### 1. 不追求完整 Mode 5，但要摆脱上帝视角直读

建议新增一个最小 IFF 状态机：

- 平台可选 `supports_iff_interrogation`
- 目标可选 `has_iff_transponder`
- 友方且答复正常时：`FriendlyReply`
- 无答复：`NoReply`
- 数据链声明友方但本地未答复：`AssumedFriendly`
- 行为/阵营规则判定敌对：`Suspect -> Hostile`

#### 2. 当前代码结构下的落点

建议新增：

- `src/components/systems/iff.h`
- `src/systems/systems/iff_system.h`

如果暂时不想加新 system，也可先在 [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h) 中完成：

- 本地雷达 hit 后，若 owner/target 都有 IFF 组件且在 interrogation 周期到达，则更新 `iff_state`
- `classification` 不再直接等于 `Alliance.side`

#### 3. 推荐的简化分类映射

- `Friendly`：收到可信 IFF reply
- `AssumedFriendly`：仅数据链友方声明或任务编组已知
- `Unknown`：无答复且无其他依据
- `Suspect`：无答复且行为/区域异常
- `Hostile`：明确敌方交战方、红方网络、武器发射、或规则强制判敌

短期为了兼容现有 `TrackClass`，可以先映射回：

- `Friendly`
- `Hostile`
- `Neutral`
- `Unknown`

同时把更细的 identity 存在新增字段里。

### B.8 基础环境影响

#### 1. 先做“可测且稳定”的 4 项

文件：

- [default_environment_model.cpp](../../../../src/models/environment/default_environment_model.cpp)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)

优先补：

1. `地形/曲率 LOS`
2. `天气衰减`
3. `太阳角/背景强退化`
4. `低空背景杂波惩罚`

#### 2. LOS 改造建议

`check_line_of_sight()` 从端点判断改成：

- 沿路径采样 `8~32` 个中间点
- 若任一点地形高于视线高度则遮蔽
- 可选加地球曲率下沉项

这已经足够支撑“山挡住了”与“掠海低空难看见”的一阶效果。

#### 3. 天气衰减建议

当前类里已有 `weather_zones_`，但未真正使用 [default_environment_model.cpp:70](../../../../src/models/environment/default_environment_model.cpp)。

建议：

- 先把 `WeatherZoneImpl` 接到 `get_weather_attenuation()`
- 对不同传感器返回不同 attenuation
  - Visual：雾/云重
  - IR：云/湿度/雨中等
  - Radar：雨衰、云雾较轻

第一阶段可用区间衰减：

- clear: `0 dB/km`
- light rain: `0.02~0.08 dB/km`
- moderate rain: `0.1~0.3 dB/km`
- heavy rain/X-band: `0.4 dB/km` 以上

最终由路径长度换成 `snr_db` 扣减，而不是直接乘概率。

#### 4. 太阳/背景建议

当前 `sun_factor = 0.1` 偏弱。

建议：

- Visual/IR 中，当目标与太阳夹角小于阈值时直接降低 `snr_db`
- 阈值可按传感器类型区分
  - Visual：`5~8 deg`
  - IR：`3~6 deg`

不是永远完全遮蔽，但应允许出现“几乎不可用”的窗口。

### B.9 测试建议

建议后续配套新增一组方向二真实性守门测试，至少包括：

#### 1. `test_sensor_pd_snr_monotonicity`

验证：

- 同一目标、同一环境下，距离增大时 `snr_db` 非增
- `Pd` 随 `snr_db` 单调
- 侧向低 RCS 低于迎头高 RCS

#### 2. `test_track_confirmation_m_of_n`

验证：

- 单次命中不立即变 confirmed
- `2-of-3` 后升级
- 连续 miss 后进入 coast / drop

#### 3. `test_alpha_beta_track_velocity_estimation`

验证：

- 目标匀速直线时，`vx/vy/vz` 收敛到真值附近
- 测量噪声存在时，track 位置抖动小于 raw contact

#### 4. `test_datalink_reports_tracks_not_contacts`

验证：

- 接收方无本地探测时，`ContactList` 为空但 `TrackDatabase` 有 `DataLink` 航迹
- 数据链轨不应伪装成本地雷达 hit

#### 5. `test_iff_reply_and_unknown_behavior`

验证：

- 有答复友方 -> Friendly
- 无答复 -> Unknown/AssumedFriendly
- 不再直接等于 `Alliance.side`

#### 6. `test_environment_weather_and_los_penalties`

验证：

- 雨区路径比晴空路径 `snr_db` 更低
- 山体遮挡路径无探测
- 低空 beam/notch 情况显著更难探测

---

## C. 数据源建议

原则：

- 官方/标准优先
- 公开工程资料和高质量民间数据库可作为近似标定
- 对具体机型参数宁可用“多源交叉后的合理区间”，不要引用单个夸张宣传值

### C.1 SNR / Pd / 检测门限

#### 一级推荐

- [MathWorks Radar Toolbox: Detection and Tracking Statistics](https://www.mathworks.com/help/radar/detection-and-tracking-statistics.html)
  用途：
  - Pd / Pfa / threshold / Albersheim / 检测统计的工程化入口
  - 适合把当前 `detection_prob` 改造成 `SNR -> Pd` 近似

- [MIT Lincoln Laboratory / Radar 系列公开课程资料](https://www.ll.mit.edu/)
  用途：
  - 雷达检测理论、CFAR、跟踪门限
  备注：
  - 具体文档分散，适合作为二级佐证

#### 可落地的默认工程值

- `Pfa = 1e-6` 可作为机载搜索雷达默认
- 单次扫描 `Pd50` 对应的门限 SNR 可先放在 `10~13 dB` 区间调参
- 脉冲积累或多次扫掠后可等效降低所需门限几 dB

这组值不是严格型号级，但对当前项目作为第一版真实性门槛是合理的。

### C.2 M-of-N 航迹确认与滤波

#### 一级推荐

- [MathWorks 多目标跟踪与 tracker 文档](https://www.mathworks.com/help/fusion/)
  用途：
  - confirmation / deletion threshold
  - alpha-beta / Kalman 的工程使用方式

#### 可直接采用的默认值

- 机载火控雷达：`2-of-3`
- 预警机 / 慢刷新远程监视：`3-of-4`
- coast time：`4~8 s`
- track delete：`8~15 s`

这些值属于行业常见工程近似，比当前“首次看到即确认、10 秒统一删轨”更真实。

### C.3 IFF / 分类

#### 一级推荐

- [NATO / NAPMO Mode 5 IFF 概览资料](https://www.napma.nato.int/)
  用途：
  - 理解 Mode 5 的“加密问答 + 时间同步 + 友方确认”本质

- [MITRE 相关 IFF / cooperative identification 公开材料](https://www.mitre.org/)
  用途：
  - 作为“为什么不能直接阵营读值”的工程解释

#### 当前项目推荐的简化参考

不必追 Mode 5 协议细节，先抽象为：

- 有无问答能力
- 问答周期
- 友方答复概率
- 干扰/失步下的漏答概率

起始参数可用：

- 友方正常答复率：`0.95~0.995`
- 干扰/时间失步答复率下降到：`0.6~0.9`
- 非友方/无应答机：`0`

### C.4 环境影响

#### 一级推荐

- [ITU-R P.838](https://www.itu.int/rec/R-REC-P.838)
  用途：
  - 雨衰特定衰减 `gamma_R = k R^alpha`
  - 可给 radar weather attenuation 一个标准来源

- [ITU-R P.840](https://www.itu.int/rec/R-REC-P.840)
  用途：
  - 云雾衰减
  - 适合 visual / IR / microwave 的路径损耗近似

- [FAA / NOAA / UCAR 关于 radar horizon 与 beam propagation 的公开资料](https://www.faa.gov/) 、[UCAR MetEd](https://www.meted.ucar.edu/)
  用途：
  - 支撑 `3.57 * (sqrt(h1)+sqrt(h2))` 这类标准近似
  - 支撑 4/3 地球半径近似的合理性

#### 可直接用于本项目的近似区间

- 机载/舰载 X 波段中雨衰：
  - 小雨：`0.02~0.08 dB/km`
  - 中雨：`0.1~0.3 dB/km`
  - 大雨：`0.4~1.0 dB/km`

- 云雾对 radar：
  - 通常弱于降雨，可先忽略或设成很小项

- 云雾对 IR / Visual：
  - 应显著强于 radar，可优先按路径比例降 `snr_db`

### C.5 机型/传感器参数来源

#### 一级推荐

- 公开厂商资料、军贸宣传册、国会/审计文件、百科式军工资料

#### 二级推荐

- [Cmano-DB](https://cmano-db.com/)
  用途：
  - 可作为非官方但相对成体系的参考数据库
  - 适合拿来给 APG-68、Irbis-E、AWACS 雷达、IRST 做初始量级校准

使用方式建议：

- 不直接抄单点值
- 至少与另一公开来源或常识区间交叉
- 用于决定“80 km 级 / 120 km 级 / 400 km 级”这种量级，而不是宣称绝对真值

#### 当前项目里最需要先校的项

- [an_apg_68.json](../../../../examples/config/database/aircraft/modules/sensors/an_apg_68.json)
- [irbis_e.json](../../../../examples/config/database/aircraft/modules/sensors/irbis_e.json)
- [e3_sentry.json](../../../../examples/config/database/aircraft/units/e3_sentry.json)

当前这些文件最优先要修的不是“绝对最大探测距离”，而是：

- 把 radar `range_power=2.0` 改掉
- 给 `type` 明确设为 `Radar`
- 加入参考 `reference_snr_db / reference_range_m / reference_rcs_m2`
- 补 `confirm_hits_m / confirm_window_n`

---

## D. 建议优先级

### D.1 P0：立刻处理，否则后续空战结论会持续失真

#### 1. 停止数据链直接写入接收方 `ContactList`

落点：

- [data_link_system.h](../../../../src/systems/systems/data_link_system.h)

原因：

- 当前把共享态势伪装成本地探测
- 会直接污染发射条件、战术图、agent 观测

#### 2. 引入 `Tentative/Confirmed` 航迹状态和 `2-of-3` 确认

落点：

- [track_management.h](../../../../src/components/systems/track_management.h)
- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)

原因：

- 这是从“点迹闪烁”到“可用战术态势”的最低门槛

#### 3. 将 radar 探测概率从经验乘子改为 `SNR -> Pd` 近似

落点：

- [sensor.h](../../../../src/components/systems/sensor.h)
- [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)

原因：

- 不解决这个，后面所有“距离、姿态、天气、干扰”的效应都只能是假相

#### 4. 修正数据库中的 radar `range_power`

落点：

- [examples/config/database/aircraft/modules/sensors/an_apg_68.json](../../../../examples/config/database/aircraft/modules/sensors/an_apg_68.json)
- [examples/config/database/aircraft/modules/sensors/irbis_e.json](../../../../examples/config/database/aircraft/modules/sensors/irbis_e.json)
- [examples/config/database/aircraft/units/e3_sentry.json](../../../../examples/config/database/aircraft/units/e3_sentry.json)

原因：

- 这是当前最明显的结构性参数错误之一

### D.2 P1：应紧接着做，能显著提升空战可信度

#### 1. 为 `SystemTrack` 增加 `alpha-beta` 位置/速度滤波

理由：

- 不做速度估计，中制导、拦截、态势判断都不可靠

#### 2. 引入简化 IFF / identity 状态

理由：

- 继续直接读 `Alliance.side` 会让蓝军误伤、无答复、共享识别这类问题永远缺席

#### 3. 接通环境衰减和 LOS 采样遮蔽

理由：

- 这是让“低空掠海/山谷遮蔽/坏天气”真正产生战术差异的最低成本入口

### D.3 P2：在 P0/P1 稳定后推进

#### 1. RCS 三向插值 + 小幅波动

#### 2. 数据链报告职责 / 上报质量门槛

#### 3. 简化 clutter / look-down 惩罚

#### 4. RWR 与雷达模式关系细化

### D.4 P3：暂缓，除非明确进入电子战/高保真识别阶段

#### 1. DRFM 欺骗干扰

#### 2. 微多普勒 / NCTR

#### 3. 完整 Kalman / JPDA / MHT

#### 4. 完整 Link 16 时隙与 J-series 消息仿真

---

## 结论

方向二当前最关键的现实化任务，不是“加更多传感器类型”，而是把现有链路中的五个伪真值点拆掉：

1. `detection_prob` 直接乘出来
2. 首次命中即确认
3. 航迹无滤波无速度
4. 数据链把共享态势伪装成本地探测
5. 分类直接读 `Alliance.side`

如果这五点不先处理，后面的空战训练即使能跑，也更可能是在适应当前抽象的漏洞，而不是在学习更接近真实的传感器与态势感知约束。

最推荐的推进顺序是：

1. `SNR/Pd + M-of-N + DataLink 不再写 ContactList`
2. `alpha-beta filter + track quality + confirmed-only tactical use`
3. `simplified IFF + environment penalties`
4. `RCS/interference/clutter` 进一步细化
