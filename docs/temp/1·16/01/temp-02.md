我看了你们现在仓库里的“最小可运行版本（MVP）”，整体方向是对的：**Flecs ECS + 固定步长仿真内核 + nanobind Python 绑定 + 最小状态观测**，已经把“训练友好内核”的骨架搭起来了。

下面是我按“能否支撑后续做对抗式训练/可扩展性/确定性”做的审查结论与修改建议。

---

## 当前版本已经做对的点

### 1) 固定步长内核打通了

`SimulationKernel::step()` 用 `ecs.progress(time_step)` 推进固定 dt ，而运动系统里读取 `it.delta_time()` 作为 dt 来更新位置 ——这意味着**只要 time_step 不变，你的动力学更新就是固定步长的**（训练必要条件之一）。

### 2) ECS 的最小组件/系统链路清晰

组件最小集合（Transform/Velocity/Alliance/KeyEntity）很干净 ，系统也只做一件事：UpdatePosition 。这非常适合先把训练闭环跑通，再逐步加复杂度。

### 3) Python 绑定具备“能训练”的雏形

你已经能在 Python 侧：

* `spawn_unit()` 生成实体并拿到 entity id 
* `get_unit_position()` 做最小观测（位置三元组）
  这是后续封装 PettingZoo Parallel 环境的关键起点。

---

## 需要尽快改的“硬问题”（否则后面会很痛）

### A) 命名/品牌不一致：仓库叫 Echelon-Forge，但工程叫 CMO

`CMakeLists.txt` 里 `project(CMO...)`，target 也叫 `cmo_core/cmo_py/cmo_app`  。
建议你尽快统一成：

* project: `EchelonForge`（或 `echelon_forge`）
* targets: `ef_core / ef_py / ef_app`（或 `echelon_forge_core`…）

这不是洁癖问题：后面加 CI、发布 wheel、写文档、写论文引用时，这种不一致会不断制造摩擦。

---

### B) Python 绑定里有一个“潜在复制 world”的细坑

`get_unit_position` 里写的是：

```cpp
auto world = self.get_world();
```


这里 `get_world()` 返回引用 ，但 `auto world` 可能导致**按值拷贝 wrapper**（flecs::world 通常是轻量句柄，但依赖实现细节）。建议显式写成：

```cpp
flecs::world& world = self.get_world();
```

这属于“现在不改，后面查 bug 很恶心”的类型。

---

### C) reset 的清理策略现在偏脆

目前 reset 只 `ecs.delete_with<Transform>()` 。
短期 OK，但你一旦加入：

* 没有 Transform 的“全局单例/管理实体”
* 或者某些实体组件变更导致不再含 Transform
  就会出现“残留实体污染下一局”的情况。

建议你明确一个规则：

* **训练 episode 的一切实体都带一个 EpisodeTag（或 SimEntityTag）组件**，reset 直接 `delete_with<Tag>()`，永不含糊。

---

### D) “确定性”目前只是“固定步长”，随机源还没锁死

你在 header 里明确写了“先用 mt19937 MVP，未来换 PCG/Xoshiro” ，reset 会 seed 。
这没错，但你要尽早定下“确定性合同”（否则并行/跨平台会翻车）：

最低限度建议：

* 所有随机都从 `SimulationKernel::rng` 派生（不要在系统里临时 new RNG）
* 系统执行顺序固定（先 movement，再 sensor，再 effects…）
* 回放校验：同 seed 同输入，每 tick 产出一个 state hash（后面做 CI regression 非常值钱）

---

## 设计层面的建议：你现在是“连续空间”，不用纠结网格 vs Unity

你当前 Transform 明确是 “Local ENU” 连续坐标 ，运动也是连续积分 。这很好：**先把训练接口与对抗闭环跑通，比早期就做网格/地理系统更重要**。

如果你们未来要做“夺控关键节点”的第一场战斗，我建议：

* 继续用连续空间（现在这套即可）
* 但把“可学习的动作”先抽象为：速度/航向/目标点/状态机切换（避免微操动作空间爆炸）
* 用事件驱动的 effects（命中/失效/占领）替代复杂弹道

---

## 我建议你下一步按优先级做 8 个小 PR

1. **Rename 全部 CMO → Echelon-Forge（项目名、target、Python module 名）** 
2. 给 episode 实体加 `SimTag`，reset 删除 `delete_with<SimTag>()`（替换当前 Transform 筛选） 
3. Python 绑定修正 `world` 引用写法 
4. 增加 `get_unit_velocity / get_unit_side / list_entities()`（训练需要批量观测，否则 Python 循环会慢）
5. 增加 `step(n)` 批量推进（减少 Python↔C++ 边界开销）
6. 增加“状态 hash + 回放 seed”的最小确定性测试（CI 可以跑）
7. README：构建命令、运行 `c++ app`、导入 Python module（现在 repo 里我没检索到 README）
8. 预留 Effects/Sensor/Comms 的系统注册框架（哪怕先空着），把系统 pipeline 固定下来

---

如果你把仓库链接（或你希望我重点看“目录结构 / CI / Python 包 / 训练 demo”哪一块）给我，我可以按“是否已经能封装成 PettingZoo Parallel 环境”这个标准，再做一次更贴近训练落地的审查清单。
