# 可视化统一入口与会话化重构冻结计划

状态：`2026-05-16` 冻结设计版。

关联文件：

- [当前可视化主入口](../../../examples/viz/viz_runner.py)
- [当前 Web 服务骨架](../../../examples/viz/web_viz/server.py)
- [当前前端模板](../../../examples/viz/web_viz/templates/index.html)
- [现有旧式配置示例 departure](../../../examples/viz/configs/departure.json)
- [现有旧式配置示例 landing](../../../examples/viz/configs/landing.json)
- [当前海战最小场景](../../../scenarios/naval/ddg51_take1_screen_contact_report_v1.json)
- [海战现实性分层清单与下一步计划](../naval/naval_realism_layering_and_next_step_plan_20260516.zh.md)

文档定位：

- 本文档用于冻结一次围绕 `examples/viz` 的较大规模重构计划。
- 本轮目标不是继续在现有 `viz_runner.py` 上叠加临时按钮，而是将可视化改造成“常驻应用 + 可替换会话 + 配置分层”的结构。
- 本文档当前只冻结架构、边界、配置层与实施顺序，不授权在本轮文档中直接扩展新的海战语义或现实参数。

## 一、问题定义

当前可视化系统已经能承担较丰富的表现任务，尤其是海战场景下的：

1. 全屏战术二维视图；
2. 3D 场景与追踪视角；
3. 传感器圈、数据链、航迹等战术叠加；
4. 舰船与飞机模型加载；
5. 仿真状态的持续 Socket 推送。

但它的使用方式仍停留在“一次命令行对应一次仿真进程”的阶段。

这带来的直接问题是：

1. 更换场景、模型、速度策略、训练配置时，需要退出并重启整个进程；
2. 前端已经具备较强 UI 能力，但后端入口仍由命令行决定，导致交互中心不在应用内；
3. 模型映射、朝向修正、比例尺、水线偏移等视觉规则被硬编码在前端脚本中，后续舰种扩展会快速失控；
4. 旧的 `examples/viz/configs/*.json` 只覆盖很窄的启动信息，无法承担完整的可视化运行配置职责；
5. 可视化便利性配置、仿真真实性配置、训练控制器配置目前缺少清晰边界。

因此，本轮真正要解决的问题不是“再加一个启动脚本”，而是：

**把当前可视化系统从一次性 runner，演进为一个稳定的可视化应用。**

## 二、当前结构判断

根据 [viz_runner.py](../../../examples/viz/viz_runner.py) 与 [index.html](../../../examples/viz/web_viz/templates/index.html) 的现状，当前结构有以下特征。

### 2.1 当前前端已经接近应用壳

前端已具备：

1. 全屏战术视图与 3D 视图切换；
2. 单位列表、焦点单位、速度控制、暂停控制；
3. 模型加载、轨迹、战术叠加层绘制；
4. 面向海战的广域尺度显示能力。

这说明前端不是本轮的主要瓶颈，反而已经足以承接“统一入口后的 UI 壳”角色。

### 2.2 当前后端把多个职责绑死在一起

`viz_runner.py` 当前同时承担：

1. `argparse` 命令行解析；
2. 场景、训练配置、控制器加载；
3. env 初始化；
4. 仿真循环；
5. Socket 事件处理；
6. Flask 服务启动；
7. Web 页面渲染。

这意味着换一个场景，本质上就是重启整个应用。

### 2.3 当前配置层不足以支撑调试工作流

现有 `examples/viz/configs/departure.json` 与 `landing.json` 更像旧式 demo 配置：

1. 能指定 env module/class 与 model path；
2. 只能覆盖很少的 viz 设置；
3. 不支持资产映射、默认视图、叠加层、会话行为等更完整的可视化配置。

### 2.4 当前资产规则放错了层

当前前端中已经硬编码了：

1. 舰船平台识别；
2. 模型文件路径；
3. 朝向修正；
4. 缩放比例；
5. 水线偏移；
6. chase camera offset；
7. 某些“替代模型”的语义说明。

这类规则本质上属于“资产注册表”或“可视化 profile”，不应继续散落在前端逻辑中。

## 三、目标

本轮重构的目标是：

1. 建立统一且稳定的可视化启动入口；
2. 使 Web 服务能够常驻，不因切换场景而整体重启；
3. 将仿真会话从应用壳中解耦出来，支持应用内加载、重载、重置；
4. 建立独立的 `viz profile` 配置层；
5. 建立独立的资产注册表层，用于管理模型映射与修正参数；
6. 保持“场景真实性”与“可视化便利性”分层，避免混写。

## 四、非目标

本轮明确不做：

1. 不在本文档中推进新的海战战术语义；
2. 不在本文档中扩展武器、毁伤、沉没、电子战等真实性实现；
3. 不要求当前就实现完整的多会话并发；
4. 不要求当前就实现资源热更新或编辑器式场景编辑；
5. 不要求把前端完全重写成新的框架应用。

本轮允许：

1. 重构 `examples/viz` 的入口与运行时结构；
2. 新增 `viz app / viz session / viz profile / asset registry` 模块；
3. 逐步迁移当前前端中的资产规则；
4. 为后续海战与空战共用可视化壳建立稳定基础。

## 五、推荐架构

本轮建议收敛到三层主结构，加一层配置支撑。

### 5.1 常驻应用层 `viz_app`

职责：

1. 启动 Flask / SocketIO；
2. 提供统一 Web 入口；
3. 提供配置清单与会话控制接口；
4. 持有当前活动会话的引用。

它不直接承担：

1. `argparse` 风格的运行策略分发；
2. 某个具体场景的长期状态逻辑；
3. 平台资产识别与前端几何修正规则。

建议入口形态：

```text
examples/viz/run_viz.py
```

其职责是：

1. 启动常驻 viz app；
2. 打开统一浏览入口；
3. 由 UI 或 profile 触发后续会话加载。

### 5.2 仿真会话层 `viz_session`

职责：

1. 加载 scenario；
2. 加载 model 或 scripted controller；
3. 构建 env；
4. 管理 sim loop；
5. 生成 `map_setup / nav_setup / state_update`；
6. 支持 `start / pause / resume / reset / reload / stop`。

这一层是本轮最核心的拆分点。

它需要从当前 `viz_runner.py` 中剥离出的主要内容包括：

1. 训练配置加载；
2. env 初始化与模式判断；
3. 仿真步进循环；
4. mission / nav / tactical state 提取；
5. 终止后 reset 策略。

### 5.3 可视化配置层 `viz_profile`

`viz_profile` 负责描述：

1. 启动哪个 scenario；
2. 是否加载 model；
3. 是否使用 scripted controller；
4. 默认速度与默认视图模式；
5. 是否自动启动、是否暂停在 terminal；
6. 默认叠加层开关；
7. 资产映射方案；
8. 可选的焦点单位、默认 zoom 等 UI 偏好。

它不负责描述：

1. 舰艇真实排水量、航速、雷达等世界参数；
2. 训练本身的完整超参数；
3. 场景语义本体。

### 5.4 资产注册表层 `asset_registry`

该层负责将“平台语义”映射到“视觉模型与修正参数”。

推荐字段至少包括：

1. 匹配键：
   - `platform_type`
   - `name_patterns`
   - `service_profile`
   - `unit_type`
2. 资产字段：
   - `asset_path`
   - `label`
   - `substitute_for`
   - `realism_note`
3. 修正字段：
   - `scale`
   - `yaw_correction_deg`
   - `waterline_offset_m`
   - `chase_offset`
4. 可选控制：
   - `show_in_2d_as`
   - `show_sensor_ring`
   - `render_priority`

这一层的价值在于：

1. 让模型替代关系诚实可见；
2. 让舰种扩展不再依赖前端硬编码；
3. 使朝向修正与比例修正可配置化。

## 六、配置分层原则

本轮建议将可视化相关数据源明确拆成四层：

1. `scenario`
   - 世界、实体、任务、现实参数；
   - 是仿真真实性的来源。

2. `train_config`
   - 控制器训练与运行推断相关信息；
   - 是模型运行约束的来源。

3. `viz_profile`
   - 本次可视化如何启动、默认怎么看；
   - 是调试工作流的来源。

4. `asset_registry`
   - 平台如何映射到模型与视觉修正；
   - 是视觉表现的来源。

这里最重要的约束是：

**不要把真实性参数为了 UI 便利塞进 `viz_profile`，也不要把视觉替代规则写回 scenario。**

## 七、UI 设计建议

当前海战可视化已经明确以战术视图为主，因此新的统一入口 UI 不建议做成传统管理后台，而应保持“主画面就是战术图”的结构。

建议布局：

1. **全屏战术视图**
   - 作为默认主视图；
   - 打开应用后先看地图，而不是先看一个表单页。

2. **轻量启动/会话控制条**
   - 用于选择 profile、scenario、asset set；
   - 提供 `Start / Reload / Reset / Stop`；
   - 显示当前 session 状态。

3. **可折叠信息区**
   - 用于展示单位列表、焦点信息、模型替代说明、调试状态。

4. **3D 视图切换**
   - 保留为辅助视图；
   - 不能替代战术主视图。

## 八、后端接口建议

当前已有：

1. `start_sim`
2. `pause_sim`
3. `resume_sim`
4. `set_speed`

统一入口后建议补齐为两类接口。

### 8.1 清单类接口

1. `list_profiles`
2. `list_scenarios`
3. `list_asset_sets`
4. `get_session_status`

### 8.2 会话控制类接口

1. `load_profile`
2. `start_session`
3. `pause_session`
4. `resume_session`
5. `reset_session`
6. `reload_session`
7. `stop_session`

这样前端启动后可以先拿清单，再选择加载，而不是一进入页面就绑定某个启动时固定死的场景。

## 九、建议目录结构

建议在 `examples/viz` 下逐步演进到类似结构：

```text
examples/viz/
  run_viz.py
  app/
    server.py
    session_manager.py
    routes.py
    socket_handlers.py
  runtime/
    viz_session.py
    session_factory.py
    state_extractors.py
  profiles/
    naval_debug_minimal.json
    air_departure_debug.json
  assets/
    registry/
      naval_surface.json
      air_fixedwing.json
  web_viz/
    templates/
    static/
```

这里的重点不是目录名字必须完全一致，而是结构边界要清楚：

1. `app/` 管应用壳；
2. `runtime/` 管仿真会话；
3. `profiles/` 管 viz profile；
4. `assets/registry/` 管模型映射与修正；
5. `web_viz/` 仍然主要承载网页资源。

## 十、分阶段实施建议

本轮建议按以下顺序推进，避免边改边返工。

### WP-V1：抽取会话层

目标：

1. 从 `viz_runner.py` 中抽离 `VizSession`；
2. 让“仿真循环”不再直接依赖 `main()`；
3. 先做到应用内可创建、可销毁、可 reset。

冻结范围：

- [examples/viz/viz_runner.py](../../../examples/viz/viz_runner.py)
- 新增 `runtime/viz_session.py`

当前不做：

1. 不强求前端 UI 当场完成所有切换控件；
2. 不强求 asset registry 同步全部迁完。

### WP-V2：建立常驻应用入口

目标：

1. 增加统一入口 `run_viz.py`；
2. Web 服务常驻；
3. 页面首次打开时不强依赖某个 CLI 场景。

冻结范围：

- 新增 `app/` 层
- 调整启动逻辑

### WP-V3：引入 `viz_profile`

目标：

1. 为启动选择建立稳定配置；
2. 替代“每次手工敲一串命令”的工作流；
3. 支持海战与空战的不同默认视图与调试偏好。

冻结范围：

- 新增 `profiles/*.json`
- 增加 profile loader

当前进展（`2026-05-16` 已落地）：

1. 已新增首个 `viz_profile` loader：
   - [examples/viz/app/profile_loader.py](../../../examples/viz/app/profile_loader.py)
2. 已新增首批海战 profile：
   - [examples/viz/profiles/naval_ddg51_contact_report_debug.json](../../../examples/viz/profiles/naval_ddg51_contact_report_debug.json)
   - [examples/viz/profiles/naval_ddg51_closing_contact_debug.json](../../../examples/viz/profiles/naval_ddg51_closing_contact_debug.json)
3. 统一入口现已支持：
   - CLI 预加载 `--profile`
   - HTTP `GET /api/viz/profiles`
   - HTTP `POST /api/viz/load_profile`
   - Socket `viz_load_profile`
   - profile 会话下的 `RELOAD`
4. 前端轻量控制条已支持：
   - profile 下拉
   - `LOAD PROFILE`
   - 当前 session / scenario / profile 状态显示
   - profile 驱动的默认 UI 偏好：`presentation_mode` / `camera_mode` / `tactical_zoom`

本阶段仍明确未做：

1. 还未引入 `asset_registry`；
2. profile 目前不承载真实性世界参数；
3. profile 目前只覆盖启动会话与少量 UI 默认值，不覆盖完整叠加层开关或模型注册。

### WP-V4：引入 `asset_registry`

目标：

1. 把前端硬编码的模型映射和修正参数迁出；
2. 对临时替代模型给出诚实标注；
3. 为后续舰种扩展提供可维护路径。

冻结范围：

- `index.html` 中现有资产判定逻辑
- 新增资产注册表 JSON 或 Python loader

当前进展（`2026-05-16` 已落地第一版）：

1. 已新增首个资产注册表 loader：
   - [examples/viz/app/asset_registry.py](../../../examples/viz/app/asset_registry.py)
2. 已新增首个 registry 数据文件：
   - [examples/viz/assets/registry/default.json](../../../examples/viz/assets/registry/default.json)
3. 当前 registry 已覆盖：
   - `F-16` 基础可视化资产
   - `DDG-51` 驱逐舰资产与朝向/追踪修正
   - `T-AKE-1` 的临时 `USNS Patuxent` 替代资产与诚实标注
4. 统一入口当前会：
   - 默认加载 `default` registry
   - profile 可显式指定 `asset_registry`
   - 通过状态流向前端分发当前 registry
5. 前端当前已改为：
   - 用 registry 决定单位匹配、模型路径、yaw 修正、比例、水线偏移、chase offset
   - 在单位列表中显示替代模型说明，而不是把这层语义埋在注释里
   - 在战术图中按 registry 决定单位二维符号类型与传感器圈显示

本阶段仍明确未做：

1. 目前 registry 只覆盖已验证的最小海战/空战资产，不代表舰种库已经完整；
2. 目前还没有更细粒度的图层开关编辑器；
3. `show_in_2d_as` 目前只覆盖统一入口战术图，不代表所有未来视图都已接线。

### WP-V5：接入 UI 内部加载器

目标：

1. 在应用中选择 profile / scenario / asset set；
2. 支持 reload / reset / stop；
3. 保持战术图作为主工作界面。

冻结范围：

- [examples/viz/web_viz/templates/index.html](../../../examples/viz/web_viz/templates/index.html)
- 新的清单与会话控制事件

当前进展（`2026-05-16` 已落地）：

1. 统一入口当前已支持应用内选择并加载：
   - `profile`
   - `scenario`
   - `asset set`
2. 当前已接入的控制事件包括：
   - `viz_load_profile`
   - `viz_load_session`
   - `viz_load_asset_registry`
   - `viz_reload_session`
   - `viz_stop_session`
3. 当前已接入的清单接口包括：
   - `GET /api/viz/profiles`
   - `GET /api/viz/scenarios`
   - `GET /api/viz/asset_registries`
   - `GET /api/viz/assets`
4. 当前统一入口在 `STOP` 后会保留当前 profile / asset set 选择语义，便于重复调试，而不是强制清空整个工作上下文。
5. 当前已通过统一入口完整验证：
   - `UNLOADED -> LOAD PROFILE -> READY -> LOAD ASSET SET -> START -> RUNNING -> STOP -> UNLOADED`

本阶段收尾判断：

1. `WP-V4` 已完成第一版可用收口；
2. `WP-V5` 已完成第一版统一入口工作流收口；
3. 后续新增工作应默认进入“扩展 registry 内容”或“清理 runtime 退出路径噪音”这两条后续线，而不是回退到前端硬编码资产逻辑。

## 十一、现实性与工程边界

本轮有一个必须坚持的原则：

**可视化系统的重构，是为了更诚实、更高效地观察仿真，不是为了拿 UI 配置掩盖现实性缺口。**

因此：

1. `scenario` 仍然是现实参数的主来源；
2. 临时替代模型必须通过 `asset_registry` 显式标注；
3. 海战中的战术图叠加、雷达圈、共享链路等，应继续被理解为“观测表达层”，而不是自动等价于“更高保真世界建模”。

这条边界对后续海战推进尤其重要。

## 十二、当前冻结结论

本轮可视化系统的正确改造方向不是继续给 `viz_runner.py` 加开关，而是：

1. 把它拆成“常驻应用层 + 可替换会话层”；
2. 引入独立的 `viz_profile`；
3. 引入独立的 `asset_registry`；
4. 保持战术二维主视图作为海战调试的中心；
5. 把“重启整个进程才能切换场景”的工作流，替换为“应用内重载会话”的工作流。

在进入实现前，下一步应默认按 `WP-V1 -> WP-V2 -> WP-V3 -> WP-V4 -> WP-V5` 的顺序推进，而不是并行大改所有层。
