# 手册

面向开发者和用户的参考文档与操作指南，按类别组织。

## 目录

### 参考指南（"是什么"）

系统能力、代码结构、物理实现的当前状态说明。

| 文档 | 说明 |
|------|------|
| [引擎能力说明](reference/engine_capabilities.zh.md) | 当前引擎能做什么、关键局限、RL 接口 |
| [代码层地图](reference/src_layer_map.zh.md) | `src/` → `python/` → `gym_envs/` → `tests/` → `tools/` 的导航入口与推荐阅读顺序 |
| [物理引擎基础清单](reference/physics_engine_inventory.zh.md) | ECS 管线、运动积分、控制模型、环境模型、数据来源的代码入口 |

### 操作指南（"怎么做"）

| 文档 | 说明 |
|------|------|
| [远程可视化](howto/visualization_guide.zh.md) | SSH 端口转发 + Web 实时查看仿真 |

### 归档

已过时的历史设计笔记。

| 文档 | 说明 |
|------|------|
| [起飞到巡航混合模式](archive/takeoff_to_cruise_mixedmode_notes.zh.md) | 历史 P3 实验基线，引用 20260316 实验制品 |

着陆任务设计已迁至 [docs/task/flight_dynamics/landing_task_notes.zh.md](../task/flight_dynamics/landing_task_notes.zh.md)。

---

维护规则：参考指南应随代码变更同步更新。操作指南在工具链变化时更新。历史设计笔记在实现落地后移入 `archive/`。
