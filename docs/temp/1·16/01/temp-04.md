我按你给的 commit `4830f83f78d6c94253b903351f79ffe0e0233a18` 做了代码审阅（重点看“能不能跑通训练闭环 + API一致性 + 后续扩展是否会反噬”）。结论是：**你们把“空战骨架（控制→制导→运动→近炸）”搭出来了**，但现在最大的风险不在“模型粗糙”，而在 **约定/接口不一致**——这会让 demo、gym 环境、可视化脚本彼此互相打架。

下面按优先级列问题与建议。

---

## P0 必改：构建/绑定命名不一致，导致 Python 侧直接跑不起来

### 1) Python 模块名仍然是 `cmo_py`

`python_module.cpp` 里仍是 `NB_MODULE(cmo_py, m)` ，但你们在 CMake 里已经把模块 target 改成 `ef_py`（commit diff 里 `nanobind_add_module(ef_py ...)`），examples 也改成 `import ef_py` 。

**结果：**构建出来的扩展名与导入名很可能不一致（导入 ef_py 找不到 / 或生成 cmo_py）。
**建议：**把 `NB_MODULE(cmo_py, m)` 改为 `NB_MODULE(ef_py, m)`，并确保 CMake target、模块名、examples 三者统一。

---

## P0 必改：接口不一致（C++ Kernel / Python binding / gym env）互相冲突

### 2) `set_command` 参数不匹配（env 用了 3 参数，但 C++ 只有 2）

C++ Kernel 的命令接口只有 `heading_deg + speed_mps`，没有高度：`set_unit_command(uint64_t, double, double)` ，MovementCommand 也只有这两个字段 。
但 `examples/gym_env/echelon_env.py` 调用 `self.kernel.set_command(... heading, speed, alt)` 。

**建议二选一：**

* **方案 A（最快）：**gym env 先删掉 altitude 动作与参数，保持 2D（heading/speed + fire）直到你们真的做 vertical 控制。
* **方案 B（更对齐你们愿景）：**扩展 `MovementCommand` 增加 `target_alt`（或 `target_climb_rate`），并在 `control_system` 里处理 Z（目前写着“Ignore Z for now (2D control)” ）。

### 3) gym env 的时间步假设与内核不一致

Kernel 默认 60Hz：`time_step = 1.0/60.0` 。
但 env 注释写 “1000 ticks = 100s at 10Hz” ，且 action integration（每步 heading += turn*5 度等）是写死的，不随 dt 缩放 。

**建议：**

* 要么把 kernel dt 设置成 0.1（10Hz），要么所有 action integration 都乘上 `dt / dt_ref`（例如 dt_ref=0.1），否则策略学到的“转弯能力”取决于 tick 频率。

---

## P1 很快会咬人的问题：坐标/航向定义混乱（导致行为和观测对不上）

### 4) MovementCommand 的航向约定与 `get_unit_heading` 返回不一致

MovementCommand 注释是 “0=North, Clockwise” 。
`control_system` 也确实把速度向量换算成导航航向：`current_heading_nav = 90 - deg(atan2(vy,vx))` 。
但 Python 绑定的 `get_unit_heading` 只是 `atan2(vy,vx)` 转角度并归一到 0..360，**这其实是“数学角”（0=East，逆时针）** 。

**结果：**你在 Python 里打印的 heading、可视化的 heading、以及 `set_command` 用的 heading **不是同一种角度系**。
**建议：**把 Python 的 `get_unit_heading` 改成和 `control_system` 同样的 NAV 角定义（0 北顺时针），避免后续调试地狱。

### 5) `normalize_angle` 把角度压到 [-180,180]，但 target_heading 可能是 [0,360)

`normalize_angle()` 返回 [-180,180] ，`control_system` 又对 `current_heading_nav` 做了 normalize_angle ；但 `set_unit_command` 并没规范化 target_heading（直接写入）。

**建议：**

* 内部统一：**所有 heading 存 [0,360)**，计算误差时再 wrap 到 [-180,180]。
* 或者反过来：内部统一 [-180,180]，Python 侧也统一。

---

## P1 设计问题：系统顺序与“谁写 Velocity”缺少明确合同

你现在有两个系统会写 `Velocity`：

* `KinematicControl` 写速度（用于飞机）
* `MissileGuidance` 写速度（用于导弹）

目前它们都挂在 `flecs::OnUpdate`，注册顺序在 kernel 里是 control → guidance → movement → damage 。

**风险：**

* Flecs 的系统调度在复杂化后（多文件、多 phase、多线程）你会很难仅靠“注册顺序”保证确定性与依赖关系。
* 后续你加传感器、交战、得分等系统时，顺序会更重要。

**建议：**现在就定义“系统 pipeline 合同”，比如：

* Phase1: Control（写平台 Velocity）
* Phase2: Guidance（写武器 Velocity）
* Phase3: Integrate（用 Velocity 更新 Transform）
* Phase4: Effects（近炸/伤害/删除）
  用 flecs phase / depends_on 显式固定下来，后面扩展会省很多时间。

---

## P1 模型层面“粗糙但更关键”的缺口：你们的 demo 已经在呼唤这些能力

### 6) 你们已经写了 perception_demo，但引擎里还没有 Sensor/Detections

`examples/perception_demo.py` 自己就指出 “spawn_unit 没加 Sensor component… we need get_detections” 。
目前仓库里也确实还看不到 `get_detections` 绑定或 Sensor 组件（至少在当前检索到的 C++/bindings 中不存在）。

**建议（最小可用版）：**

* 给单位加 `SensorModel{max_range, p_det, scan_period, noise}`
* 给单位加 `TrackList`（vector<Track>）
* 每 N tick 扫描一次：距离<max_range 时按概率生成/更新 track
  这样就能立刻把“空战”从追逐变成“搜索—接敌—丢失—再捕获”。

### 7) 伤害模型是 “destruct()”，但 gym env 想要 health

damage_system 现在是近炸距离触发后直接 `target_entity.destruct()` 。
但 gym env 里写了 `get_unit_health()` 并用它判断终止 。目前 Kernel/Binding 并没有这个函数（header 里也没有）。

**建议：**

* MVP 也建议加一个 `Health{cur,max}`，命中就扣到 0，再 destruct。这样训练信号更稳定，也方便做“受损但未击落”。

---

## P2 工程建议：reset 仍然脆（会污染 episode）

reset 仍是 `ecs.delete_with<Transform>()` 。你们现在有 Missile/MovementCommand 等组件，短期没事；但后面加 singleton、全局 entity、无 Transform 的逻辑实体时会残留。

**建议：**引入 `SimEntityTag`，spawn_unit/fire_missile 都打 tag，reset 用 `delete_with<SimEntityTag>()`。

---

## 一份“下一步最划算的修复清单”（按收益排序）

1. **统一模块名：NB_MODULE(ef_py)**，同时保证 CMake target 与 examples 一致  
2. **统一航向定义**：`get_unit_heading` 改成 0北顺时针；内部 heading 统一到同一范围  
3. **修正 gym env 与 kernel API**：先删 altitude 或把 MovementCommand 扩展支持高度  
4. **把 action integration 按 dt 缩放**（或改 dt=0.1），避免“tick 频率改变=物理改变”  
5. **定义系统 pipeline phase**，明确 Control/Gdn/Integrate/Effects 顺序 
6. 加 `Health`（替代纯 destruct），然后再做 Sensor/Track（你们 perception_demo 已经在等它了） 

---

如果你愿意，我可以基于你们现有代码风格（header-only systems + 极简 component struct），给一套**Sensor/Track + Health + BulkSnapshot** 的最小字段表和绑定接口（例如一次性 `get_all_units()` 返回 `UnitData`，你们已经有 `unit_data.h` 的雏形 ），这样你们的可视化与训练就不用在 Python 里逐个 entity 调 C++ 了。
