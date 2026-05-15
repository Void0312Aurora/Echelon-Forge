# 双机 MVP 与验收标准 (Two-Ship MVP Scope and Acceptance Standard)

> ARCHIVED NOTE (2026-03-23): 该文档属于第一版 air-specific 双机标准草案，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)。

本文档定义双机阶段第一版实现必须覆盖的真实任务边界、训练边界与验收标准。

## 1. MVP 目标

双机阶段第一版不是“完整空战编队系统”，而是一个能够稳定执行 sortie 级协同任务的真实双机 `Element`。

必须覆盖的最小任务线程：

- `TASK_SCRAMBLE`
- `join-up`
- `TASK_CAP`
- `TASK_RTB`
- `TASK_RECOVER_LAND`

第一版不要求：

- 双边对抗
- 武器协同交战
- 四机 package
- 多 element 协同

## 2. 运行时对象边界

双机 MVP 只激活以下运行时对象：

- `C2 / GCI / AWACS`
- `Element Lead`
- `Wingman`
- `Execution Layer`

其中：

- `C2` 只下发 `element` 级任务
- `Lead` 负责 element 内的战术推进与协同模式
- `Wingman` 负责跟随、重组、支持与安全规避

## 3. 第一版必须支持的战术状态

双机 MVP 至少支持以下协同状态：

- `FORM_PREJOIN`
- `FORM_JOINING`
- `FORM_CRUISE`
- `FORM_CAP`
- `FORM_REJOIN`
- `FORM_RECOVER`
- `FORM_SPLIT_ABORT`

说明：

- 这些状态不是行政编制状态，而是 sortie 级战术协同状态。
- 其控制者应优先是 `Element Lead`，而不是 C2。

## 4. 第一版场景范围

### 4.1 初始条件

至少支持两类起始条件：

- 同场同向起飞
- 小范围偏置初始位形后集合

第一版不建议直接支持：

- 异场起飞
- 空中加油后编队
- 跨战区增援

### 4.2 CAP 几何

CAP 仍沿用现有 `TaskOrder` 口径：

- `anchor_x_m`
- `anchor_y_m`
- `station_type`
- `station_radius_m`
- `station_leg_length_m`
- `station_heading_deg`
- `target_altitude_m`
- `target_speed_mps`
- `on_station_time_s`

双机阶段新增的不是 CAP 本身语义，而是 “谁负责飞主任务、谁负责保持 slot 与支持”。

### 4.3 回收逻辑

第一版允许：

- route / RTB 阶段保持编队
- 进入 recover 时允许有条件松散队形
- landing final 阶段允许 wingman 解散 element 约束，转为独立回收

这更符合现实中 terminal 阶段的安全要求。

## 5. RL 训练边界

第一版训练必须遵守：

- 不同时从零训练 lead 与 wingman
- 不把 C2 纳入第一轮 RL
- 不把 wingman 设计成完整 sortie planner

推荐顺序：

1. 全脚本双机基线
2. `wingman-only RL`
3. `lead-only RL`
4. 交替冻结训练

## 6. 第一版验收标准

### 6.1 全脚本基线验收

必须通过：

- 两机正常起飞
- 加入编队成功
- CAP 阶段队形未丢失
- RTB 成功
- Recover 过程中未发生近失撞

### 6.2 Wingman-only 验收

必须通过：

- lead 脚本稳定时，wingman 能完成 join / rejoin
- CAP 阶段 slot 误差保持在约束范围内
- RTB / recover 时不出现持续失队

### 6.3 Lead-only 验收

必须通过：

- lead 不把 wingman 拉入危险闭合率
- lead 不在 recover 前过早触发解散或 landing
- 能在任务完成与编队完整性之间做出合理权衡

## 7. 第一版不允许的简化

以下做法不符合真实性，第一版明确禁止：

- 把 wingman 退化成纯瞬时位置偏移器
- 让 C2 每步直接写两架飞机的航向 / 高度 / 速度
- 把双机协同退化成两条互不关联的单机任务线程
- 在 landing final 仍强行要求编队紧密保持
