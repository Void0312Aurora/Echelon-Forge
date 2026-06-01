# 游戏前端集成

状态：探索性工作线；截至 `2026-05-30`，Arma 是当前保留在活跃
`game/` 工作区中的项目。

语言：

- 英文主文：`README.md`
- 中文辅文：[README.zh.md](README.zh.md)

## 目标

这条工作线用于探索：在保持 Echelon Forge 后端为权威仿真真值的前提下，
是否可以接入一个可玩的外部游戏前端。

初始目标不是“玩家手飞飞机”，而是：

- 由 Echelon 训练出的策略驾驶飞机；
- 飞行、任务、武器、毁伤等真值归 Echelon 后端；
- 外部游戏壳负责地形、资产、镜头、HUD、音频和沉浸感；
- 主仓库继续保持 simulation-first，而不是为了前端方便倒向 frontend-first。

## 本地工作区边界

活跃的 `game/` 树当前保留 Arma proxy integration workspace。它并非整体被
git 忽略；只有 runtime log、session cache、bridge build output 等生成残留
继续被忽略。

`2026-05-30`，本地混合的 Godot/WebSocket playable-shell 实验已从 `game/`
移除，并归档到本地-only ignored 路径
`archive/20260530_game_godot_local_archive/`，使被跟踪的 `game/` 树重新对齐到
当前活跃的 Arma 项目。

这条 workline 的可评审、可讨论文档仍放在 `docs/task/game/` 下；`game/`
内部文档用于当前被跟踪的 Arma workspace，而不是通用任务导航入口。

当前已经进入主线维护面的仓库侧配套物为：

- [arma_proxy_backend_stub.py](../../../tools/diagnostics/arma_proxy_backend_stub.py)
  - 面向第一版 DLL bridge 协议的最小 TCP stub，可用于真实后端适配器晋级前的
    bring-up。
- [arma_proxy_backend_echelon_env.py](../../../tools/diagnostics/arma_proxy_backend_echelon_env.py)
  - 基于 env 的 TCP 后端，在 Echelon Forge 内真实 step 权威飞行状态，只把
    Arma host frame 当作刚体世界锚点。

## 权威模型

本工作线的默认假设是：

- 后端权威留在 Echelon；
- 外部游戏中的实体只是代理体/表现壳；
- AI 行为来自仓库内训练好的策略，而不是外部游戏自带 AI；
- 任何具有语义意义的世界状态变化，都应由后端计算或准入，而不是由前端壳决定。

这比“单纯接一个可视化界面”更强。它意味着外部游戏中的飞行逻辑、
毁伤真值、任务真值、AI 真值等内容，可能都要被绕开、替换，或者降格为纯表现层。

## 第一版 MVP

第一阶段维护中的探索目标为：

- 仅单机；
- 仅一类已知飞机资产，初始为 F-16；
- 仅一张已知且具备机场的地图；
- 由后端 AI 驱动飞行；
- 外部游戏中的代理机体由后端状态同步；
- 先闭合空中热启动，再推进跑道起飞。

第一版 MVP 至少要证明：

- 训练出的 Echelon 策略可以驱动权威飞机状态；
- 外部前端可以把该状态稳定渲染为代理飞机；
- 本地集成循环能够承受有意义的仿真节奏；
- 不需要削弱主线仿真语义，才能迎合前端壳。

## 当前操作路径

对当前单机、单机体 MVP，较实际的操作流是：

- 在 HEI 的 `~/Workshop/CMO` 内运行权威推理后端；
- 加载训练得到的策略以及成对保存的 `train_config_backup.json` 与
  `scenario_backup.json`；
- 通过 SSH 将 HEI 的 `127.0.0.1:8765` 转发到本地工作站；
- 本地启动 Arma 并连接该转发端口，使前端继续只是表现壳，而真值仍留在 HEI。

这样可以把训练与推理放在更适合承载 runtime 的环境里，同时让本地工作站只负责
游戏客户端。

## 非目标

- 不把外部游戏壳当作真值来源。
- 不默认把本地专用资产或启动胶水合入 `main`。
- 不以多人、联网或分布式 authority 作为起点。
- 不为了前端方便而扭曲后端语义。
- 不因为前端地图里“已经有机场”，就假设跑道、滑跑、滑行、落地语义天然成立。

## 提升规则

默认规则为：

- 活跃 Arma proxy 项目保留在 `game/` 下；
- `game/` 内生成残留继续留在现有 ignored 路径中；
- 与当前 Arma 线无关的本地-only 前端实验，在开始模糊 workspace 边界时归档到
  `game/` 之外；
- 如果集成过程中暴露出真实的后端 / runtime / contract / 文档耦合，那么相关
  变更可以直接按主线正常提交，不必为了形式维持一个长期 side branch；
- 即便未来放弃该外部游戏实验，被提升进主线的后端改动也应保持独立价值。

专门的 game 分支是可选项，而不是硬要求。优先级应当是：
一方面把本地-only 前端脚手架隔离在维护面之外，另一方面允许真正跨层的仿真改动
正常落到主线，而不是被人为藏进长期实验分支里。
