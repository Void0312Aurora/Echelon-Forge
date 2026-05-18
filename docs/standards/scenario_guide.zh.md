<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/scenario_guide.md. Review before treating this file as authoritative. -->

# 场景配置指南

> 标准对齐说明（2026-03-23）：本文档描述的是“当前仓库 JSON 场景实现口径”，
> 不是新的联合层/军种 profile 标准本体。当前标准化建模主依据请先看
> [docs/standards/README.md](README.md)。

本项目采用 JSON 驱动的通用训练底座。所有的训练任务、环境设置和奖励机制均在 `.json` 文件中定义，无需修改 Python 代码。

## 文件结构概览

一个完整的场景文件包含以下四个主要部分：

```json
{
  "scenario_name": "示例场景",
  "environment": { ... },
  "entities": [ ... ],
  "objectives": [ ... ],
  "rewards": { ... }
}
```

## 与新标准体系的关系

在新的 `joint/common core + service profile + platform/task specialization`
体系下，本指南的定位是：

- 解释当前代码如何写场景 JSON
- 说明现有 loader / compiler 能直接消费哪些字段

它不直接定义：

- 联合层 command relationship
- 军种组织 profile
- 平台无关的 common core 数据模型

如果后续按新标准继续推进，场景层最终应显式承载：

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `task organization metadata`

但这些字段目前还不是现有 JSON 运行时的强制字段。

---

## 1. Environment（环境设置）

定义仿真环境的基础参数。

- `time_step` (float)：仿真步长（秒）。通常为 0.05 或 0.01。
- `max_steps` (int)：最大仿真步数，超过此步数将触发截断（Truncated）。
- `terrain_type` (string)：地形类型（目前支持 "flat"）。

**示例：**
```json
"environment": {
    "time_step": 0.05,
    "max_steps": 2000,
    "terrain_type": "flat"
}
```

---

## 2. Entities（实体列表）

定义场景中所有的参与方（飞机、地面目标、导弹等）。

- `name` (string)：实体的唯一标识名。
- `type` (string)：实体类型，必须与数据库匹配（如 "Aircraft", "Facility", "Missile"）。
- `side` (string)：阵营 ("Blue", "Red", "Neutral")。
- `pos` (list[float])：初始位置 [x, y, z]（米）。
- `vel` (list[float])：初始速度 [vx, vy, vz]（米/秒）。
- `heading` (float)：初始航向（度）。
- `is_agent` (bool)：**关键字段**。设为 `true` 的实体将由 RL 算法控制。目前仅支持一个 Agent。

**示例：**
```json
"entities": [
    {
        "name": "Blue_F16",
        "type": "Aircraft",
        "side": "Blue",
        "pos": [0.0, 0.0, 500.0],
        "vel": [200.0, 0.0, 0.0],
        "heading": 0.0,
        "is_agent": true
    },
    {
        "name": "Target_Bunker",
        "type": "Facility",
        "side": "Red",
        "pos": [5000.0, 5000.0, 0.0],
        "vel": [0.0, 0.0, 0.0],
        "heading": 0.0
    }
]
```

---

## 3. Objectives（任务目标）

定义任务成功的评判标准。支持多种目标类型。

### 类型 A：条件判别 (Conditional)
用于定义状态类任务（如起飞、巡航、保持速度）。

- `type`：固定为 `"conditional"`。
- `reward`：达成目标后的一次性奖励。
- `conditions`：条件列表，所有条件同时满足才算成功。
    - `property`：属性名。当前飞行任务常用项包括
      `"altitude"`, `"altitude_agl"`, `"speed"`, `"gear"`, `"heading"`,
      `"heading_error_deg"`, `"ground_track_error_deg"`, `"runway_cross_abs_m"`,
      `"on_runway_geom"`, `"on_runway"`, `"on_ground"`,
      `"sink_rate_abs_mps"`, `"vertical_speed_abs_mps"`,
      `"ils_localizer_abs"`, `"ils_glideslope_abs"`, `"dme_m"`。
    - `op`：比较符 (">=", ">", "<=", "<", "==")。
    - `value`：目标值。

**示例：起飞任务（高度 > 300 且 速度 > 150）**
```json
{
    "type": "conditional",
    "conditions": [
        {"property": "altitude", "op": ">=", "value": 300.0},
        {"property": "speed",    "op": ">=", "value": 150.0}
    ],
    "reward": 2000.0
}
```

### 类型 B：区域占领/打击 (Capture Zone)
用于定义位置类任务（如到达指定空域、打击目标）。

- `type`：固定为 `"capture_zone"`。
- `target`：目标实体的 `name`。
- `radius`：判定半径（米）。
- `duration`：需要在该区域停留的时间（秒）。
- `reward`：成功奖励。

**示例：接近目标 2km 范围内并保持 10秒**
```json
{
    "type": "capture_zone",
    "target": "Target_Bunker",
    "radius": 2000.0,
    "duration": 10.0,
    "reward": 1000.0
}
```

---

## 4. Rewards（奖励配置）

定义训练过程中的稠密奖励（Shaping Reward）和惩罚。

- `survival` (float)：每存活一步的奖励（鼓励生存）。
- `crash_penalty` (float)：坠毁或死亡时的惩罚（通常为负大数）。
- `distance_to_target` (object)：距离引导奖励配置。
    - `weight`：距离的权重系数（通常为负数，表示距离越近奖励越大/惩罚越小）。

**示例：**
```json
"rewards": {
    "survival": 0.01,
    "crash_penalty": -1000.0,
    "distance_to_target": {
        "weight": -0.001
    }
}
```
