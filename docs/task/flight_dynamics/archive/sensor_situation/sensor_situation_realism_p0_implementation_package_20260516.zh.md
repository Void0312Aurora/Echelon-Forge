# 传感器/态势真实化 P0 实施包

状态：`2026-05-16` 可开工冻结版。

关联文档：

- [传感器与态势感知现实性分析](sensor_situation_realism_analysis_20260516.zh.md)
- [传感器/态势感知真实化核实与实现方案](sensor_situation_realism_verification_and_implementation_plan_20260516.zh.md)
- [武器系统与制导回路真实化核实与落地方案](../weapon_guidance/weapon_guidance_realism_verification_and_plan_20260516.zh.md)

核心代码落点：

- [Sensor 组件](../../../../src/components/systems/sensor.h)
- [TrackManagement 组件](../../../../src/components/systems/track_management.h)
- [Comm 组件](../../../../src/components/systems/comm.h)
- [CommMsgType](../../../../src/components/command/common/comm_message.h)
- [UnitDefinition Loader](../../../../src/content/unit_definition_loader.cpp)
- [DefaultSensorModel](../../../../src/models/systems/default_sensor_model.cpp)
- [TrackManagerSystem](../../../../src/systems/systems/track_manager_system.h)
- [DataLinkSystem](../../../../src/systems/systems/data_link_system.h)

文档目的：

- 把方向二收敛成一个足够小、但能真正开工的 `P0` 工作包。
- 明确 `P0` 只做哪些事，不做哪些事。
- 冻结字段、文件、测试和外部数据落地口径，避免实现过程中再次发散。

---

## 一、P0 目标

P0 只解决四件事：

1. 把雷达探测从 `range_factor * detection_prob` 提升到 `SNR/Pd 近似`。
2. 给本地探测引入 `M-of-N` 确认，避免单次点迹直接变战术可用航迹。
3. 给 `TrackManager` 增加最小 `alpha-beta` 位置/速度滤波。
4. 让 `DataLink` 不再直接写接收方 `ContactList`，而是只上报航迹级信息。

P0 的交付目标不是“完整传感器仿真”，而是让以下表述首次成立：

- 本地 `ContactList` 表示单传感器测量接触，不再混入共享态势。
- `TrackDatabase` 才是跨扫描、可共享、可过滤、可确认的战术图。
- 远距离弱目标会先经历 `低 Pd -> tentative -> confirmed`，而不是“一次掷骰子成功就能开火”。
- 数据链共享的是 `track report`，不是“伪装成本地雷达命中的 copied contact”。

---

## 二、P0 非目标

本包明确不做以下内容：

1. 完整 Kalman、JPDA、MHT、多假设关联。
2. 完整 IFF/Mode 4/5、NCTR、行为识别。
3. DRFM 欺骗、角度欺骗、复杂 ECM/ESM 对抗。
4. 海杂波/地杂波/波导/非标准折射的高保真环境建模。
5. 多传感器真融合和 `TrackSource::Fused` 正式启用。
6. Python/RL 观测结构的大改版。
7. 机密级或型号级精确参数复刻。

这些内容要么属于 `P1/P2`，要么会显著扩大这轮改动面，不适合纳入当前开工包。

---

## 三、P0 成功口径

P0 完成后，至少应满足：

1. 雷达探测概率由 `snr_db -> pd` 决定，且对距离和 RCS 单调合理。
2. 单次探测不会立即生成 `confirmed` 航迹。
3. `TrackDatabase` 中的 `x/y/z/vx/vy/vz` 不再长期为“位置更新、速度全零”。
4. `DataLink` 共享后，接收方能得到 `TrackSource::DataLink` 的航迹，但本地 `ContactList` 不会凭空出现共享目标。
5. 现有 `mission_runtime` / `naval_screen` / `air_combat_1v1` 的相关测试要么继续通过，要么被明确、有限地更新到新语义。

---

## 四、需要新增/修改的具体文件

### 4.1 必改文件

#### 1. 组件与配置

- [src/components/systems/sensor.h](../../../../src/components/systems/sensor.h)
  - 增加 SNR/Pd 和 M-of-N 所需字段
  - 扩展 `Detection`

- [src/components/systems/track_management.h](../../../../src/components/systems/track_management.h)
  - 增加 `TrackStatus` 和最小滤波/质量字段

- [src/components/systems/comm.h](../../../../src/components/systems/comm.h)
  - 给 `CommPacket` 增加最小航迹报告字段

- [src/components/command/common/comm_message.h](../../../../src/components/command/common/comm_message.h)
  - 新增 `ReportTrack`

- [src/content/unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
  - 读取新增 `sensor` 字段

#### 2. 系统逻辑

- [src/models/systems/default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
  - 引入 `snr_db` 计算
  - 引入 `pd_from_snr()` 近似
  - 产出扩展后的 `Detection`

- [src/systems/systems/track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)
  - 实现 tentative/confirmed/coast 生命周期
  - 实现最小 `alpha-beta` 滤波
  - 实现 `ReportTrack` 接收逻辑

- [src/systems/systems/data_link_system.h](../../../../src/systems/systems/data_link_system.h)
  - 删除“直接写 receiver ContactList”的逻辑
  - 改为只发 `ReportTrack`

### 4.2 建议一并调整的文件

- [src/models/core/default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)
  - 暂不改行为，但要确认 `TrackDatabase` 初始化对新增字段安全

- [src/core/engine/simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)
  - P0 默认不改观测 schema
  - 仅在必要时补 `closing_speed` 或过滤未确认航迹

### 4.3 新增测试文件

- `tests/runtime/air_combat/test_sensor_track_runtime_contracts.py`

如需拆得更细，可分成：

- `tests/runtime/air_combat/test_sensor_pd_snr.py`
- `tests/runtime/air_combat/test_track_manager_p0.py`
- `tests/runtime/link/test_datalink_track_reporting.py`

但 P0 更推荐先收敛到一个测试文件，减少组织成本。

---

## 五、字段设计

P0 只加最少字段，优先不引入大而全结构。

### 5.1 `Sensor` 字段

文件：

- [sensor.h](../../../../src/components/systems/sensor.h)

建议新增：

```cpp
double reference_snr_db;      // 在 reference_range_m / reference_rcs_m2 下的参考单次检测 SNR
double reference_range_m;     // 标定参考距离
double reference_rcs_m2;      // 标定参考 RCS
double pfa;                   // 虚警概率，P0 默认 1e-6
int confirm_hits_m;           // M-of-N 的 M
int confirm_window_n;         // M-of-N 的 N
double velocity_noise_std;    // 径向速度测量噪声
double alpha_beta_alpha;      // 建议允许按传感器类别给出默认滤波参数
double alpha_beta_beta;
```

P0 不建议现在就加：

- `Pt/G/B/F`
- `n_pulses`
- `supports_iff_interrogation`
- 全套 environment/clutter 参数

这些会把这轮范围拉大。

### 5.2 `Detection` 字段

文件：

- [sensor.h](../../../../src/components/systems/sensor.h)

建议新增：

```cpp
double snr_db;
double detection_prob_used;
double measured_vr;
int sensor_type;
bool local_sensor_hit;
```

用途：

- `snr_db` 和 `detection_prob_used` 直接服务真实性测试与调试
- `measured_vr` 给 P0 的速度估计一个入口

### 5.3 `SystemTrack` 字段

文件：

- [track_management.h](../../../../src/components/systems/track_management.h)

建议新增：

```cpp
enum class TrackStatus {
    Tentative = 0,
    Confirmed,
    Coasted
};

TrackStatus status;
double quality;
int confirm_hit_count;
int confirm_miss_count;
double last_update_time;
double last_local_update_time;
double last_datalink_update_time;
double alpha_beta_alpha;
double alpha_beta_beta;
```

P0 不建议现在引入矩阵协方差；先用 `quality + time_since_update + status` 作为最小质量表示。

### 5.4 `CommMsgType` 与 `CommPacket`

文件：

- [comm_message.h](../../../../src/components/command/common/comm_message.h)
- [comm.h](../../../../src/components/systems/comm.h)

建议：

- 新增 `CommMsgType::ReportTrack`
- `CommPacket` 新增最小字段：

```cpp
uint64_t track_ref;
double velocity_x;
double velocity_y;
double velocity_z;
double quality;
int source_code;
```

P0 仍保留 `entity_ref`，便于真值对照与兼容现有逻辑，但要明确它只是过渡期调试钩子。

---

## 六、核心实现约束

### 6.1 `SNR/Pd` 近似约束

P0 推荐采用：

1. 先基于参考量得到 `snr_db`
2. 再用 logistic 或 Albersheim 风格近似映射到 `Pd`

建议函数形态：

```text
snr_linear = snr_ref_linear
           * (sigma / sigma_ref)
           * (range_ref / range)^4
           * env_factor
           * doppler_factor
           * jam_factor

pd = 1 / (1 + exp(-k * (snr_db - snr_50_db)))
```

P0 允许的工程简化：

- `sigma` 仍可先用 `frontal/side/rear` 三点插值
- `doppler_factor` 仍可保留经验退化，但作用到 `snr_db`
- `jam_factor` 仍可保留 burn-through 式门限，但输出到 SNR 链上

P0 不允许继续保留：

- `range_factor = 1 - (R/Rmax)^n` 作为主探测概率来源

### 6.2 `M-of-N` 确认约束

P0 只做单目标单航迹窗口确认，不做复杂关联。

推荐默认值：

- fighter radar：`2-of-3`
- awacs/long-range surveillance：`2-of-2` 或 `3-of-4`

最低语义要求：

- 首次 hit -> `Tentative`
- 在窗口内累计 hit 达阈值 -> `Confirmed`
- miss 时先 `Coasted`
- 超时删除

### 6.3 `alpha-beta` 滤波约束

P0 只做笛卡尔坐标最小滤波：

- 预测：`x += vx * dt`
- 更新：`x += alpha * residual`
- 速度：`vx += beta / dt * residual`

推荐默认参数区间：

- fighter radar：`alpha = 0.65`, `beta = 0.12`
- awacs：`alpha = 0.45`, `beta = 0.06`

P0 不做：

- IMM
- EKF/UKF
- covariance matrix 输出

### 6.4 `DataLink` 约束

P0 必须满足：

- `DataLinkSystem` 不再把 sender contact 直接写到 receiver `ContactList`
- 只发 `ReportTrack`
- 接收方 `TrackManager` 决定是否建立 `TrackSource::DataLink`

P0 过渡期允许：

- 发报文时仍使用 `entity_ref` 做目标对照
- 但不允许再生成“像本地点迹一样的 shared contact”

---

## 七、测试清单

### 7.1 新增测试

#### 1. `test_radar_pd_decreases_with_range_and_increases_with_rcs`

验证：

- 在同一参考配置下，距离增大 `snr_db` 和 `Pd` 不增
- 更大 RCS 的 `snr_db` 和 `Pd` 更高

#### 2. `test_single_hit_creates_tentative_not_confirmed_track`

验证：

- 首次探测只会创建 `Tentative`
- 不会立刻成为观测/战术可用 confirmed track

#### 3. `test_two_of_three_promotes_track_to_confirmed`

验证：

- `2-of-3` 命中窗口有效
- 命中序列具备确定性

#### 4. `test_alpha_beta_filter_estimates_velocity_for_constant_velocity_target`

验证：

- 匀速目标下 `vx/vy/vz` 逐步收敛
- 滤波轨迹抖动小于 raw measurement

#### 5. `test_datalink_shared_track_does_not_create_local_contact`

验证：

- 接收方无本地传感器命中时，`ContactList` 不包含共享目标
- 但 `TrackDatabase` 中存在 `TrackSource::DataLink`

#### 6. `test_datalink_report_track_reaches_hvu_picture`

用于替换当前 `ReportContact` 语义测试：

- 对应 [test_naval_screen_scenario.py](../../../../tests/runtime/naval/test_naval_screen_scenario.py)

### 7.2 需要更新的现有测试

以下测试在 P0 后大概率需要同步更新：

- [tests/runtime/naval/test_naval_screen_scenario.py](../../../../tests/runtime/naval/test_naval_screen_scenario.py)
  - 原因：当前断言仍显式依赖 `ReportContact`

- [tests/runtime/mission/test_mission_runtime.py](../../../../tests/runtime/mission/test_mission_runtime.py)
  - 原因：共享态势路径仍要存在，但“共享接触”与“本地接触”的语义要重新校准

- [tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py](../../../../tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py)
  - 原因：若发射前提改为 `confirmed track`，需要预留更多步数或更清晰的探测确认条件

P0 不建议大改这些测试的结构，只调整其语义和等待条件。

---

## 八、外部数据落地方式

P0 不要求这轮就把所有参考值写进数据库，但必须统一“怎么落地”。

### 8.1 数据源层级

按可信度从高到低：

1. `官方/标准`
   - MathWorks radar/tracking 文档
   - ITU-R P.838 / P.840
   - FAA / NOAA / UCAR 的 radar horizon / propagation 公共资料

2. `公开工程材料`
   - 厂商 brochure
   - 国会/审计公开文件
   - 学术课程公开课件

3. `非官方但成体系数据库`
   - [Cmano-DB](https://cmano-db.com/)

### 8.2 P0 推荐的参数落地方法

对每型雷达先只落三类参数：

1. `reference_range_m`
2. `reference_rcs_m2`
3. `reference_snr_db`

不直接在数据库里硬塞“理论最大探测距离”，而是用这三项反推 `snr_db`。

推荐做法：

- 若公开资料写“对 5m² 目标探测距离约 80km”
- 则把 `reference_range_m = 80000`
- `reference_rcs_m2 = 5`
- `reference_snr_db` 设为使该距离点接近所选 `Pd` 阈值的值

也就是说，P0 先把公开“探测距离”翻译成统一的参考点，而不是直接做魔法常数。

### 8.3 文档落点建议

P0 完成前，外部数据建议先记录在文档，不急着新建独立目录。

建议后续新增：

- `docs/standards/sensors/sensor_reference_notes_20260516.md`

记录格式建议：

- 传感器名称
- 来源链接
- 原文量级
- 使用到的折算值
- 采用原因
- 不确定性说明

P0 代码实现阶段则只把最终折算值写入 JSON / loader。

---

## 九、推荐实现顺序

P0 推荐拆成 `6` 个步骤，按顺序推进：

### Step 1. 冻结组件字段与加载路径

修改：

- `sensor.h`
- `track_management.h`
- `comm.h`
- `comm_message.h`
- `unit_definition_loader.cpp`

目标：

- 先把新增字段编译通过
- 不改运行时语义

完成判据：

- 全量编译通过
- 现有传感器测试不变

### Step 2. 在 `DefaultSensorModel` 引入 `snr_db` 与 `pd_from_snr()`

修改：

- `default_sensor_model.cpp`

目标：

- 保持现有扫描流程不变
- 仅替换“单次命中概率”的来源

完成判据：

- `Detection` 中能看到 `snr_db`
- 距离/RCS 单调性测试通过

### Step 3. 在 `TrackManagerSystem` 引入 `Tentative/Confirmed/Coasted`

修改：

- `track_manager_system.h`

目标：

- 先实现 M-of-N 生命周期
- 暂不接 alpha-beta

完成判据：

- `single hit != confirmed`
- `2-of-3 => confirmed`

### Step 4. 在 `TrackManagerSystem` 接入最小 `alpha-beta` 滤波

修改：

- `track_manager_system.h`

目标：

- 给 confirmed/tentative 轨都加位置/速度预测与更新

完成判据：

- 匀速目标能收敛出非零 `vx/vy/vz`

### Step 5. 把 `DataLinkSystem` 改成 `ReportTrack` only

修改：

- `data_link_system.h`
- `track_manager_system.h`

目标：

- 去掉 receiver `ContactList` 注入
- 仅保留航迹共享

完成判据：

- 接收方 `TrackSource::DataLink` 仍能出现
- 接收方 `ContactList` 不会因为共享而增长

### Step 6. 调整现有 runtime 测试并补 P0 守门测试

修改：

- 新增 `tests/runtime/air_combat/test_sensor_track_runtime_contracts.py`
- 更新 `test_naval_screen_scenario.py`
- 必要时更新 `test_mission_runtime.py` 和 `test_air_combat_1v1_fire_missile.py`

完成判据：

- 新增 P0 测试通过
- 受影响旧测试回到绿色

---

## 十、建议的最小开工策略

如果只允许先开一个很小的分支，建议按下面的“最小可提交单元”来切：

1. `fields-only`：
   - 只改组件字段和 loader
2. `sensor-pd`：
   - 只把 `DefaultSensorModel` 的 `Pd` 逻辑换成 `SNR/Pd`
3. `track-confirmation`：
   - 只上 `Tentative/Confirmed`
4. `track-filter`：
   - 只上 `alpha-beta`
5. `datalink-track-report`：
   - 只切掉 `ContactList` 注入

这样每个 PR 都有明确语义，也更容易定位回归。

---

## 十一、当前冻结结论

方向二的 `P0` 不应该继续讨论“要不要做更真实”，而应该直接进入下面这个很具体的包：

1. `Sensor`: 加参考 SNR / Pfa / M-of-N / alpha-beta 参数
2. `DefaultSensorModel`: 用 `SNR/Pd` 取代经验概率
3. `TrackManager`: 加 `Tentative/Confirmed/Coasted + alpha-beta`
4. `DataLink`: 改成 `ReportTrack`，不再写 `ContactList`
5. `Tests`: 新增 P0 守门测试，少量更新现有共享态势测试

只要这个包落地，当前传感器/态势感知系统就会从“训练级接触复制器”跨到“最小可用战术态势链”的层次，这也是继续往空战真实化推进前最值得先做的一步。
