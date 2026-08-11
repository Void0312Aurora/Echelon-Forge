# 架构重构审计 — God File、遗留代码与结构不一致

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/architecture/reviews/architecture_refactoring_audit_20260522.md`
Owner: `architecture/reviews`
Last verified: `2026-05-22`

状态: `2026-05-22` | 范围: 364 文件 (197 .h + 49 .cpp + 118 .py) | `2026-06-09` 更新：架构测试已重组为 14 子目录

## 1. 执行摘要

31 条发现: 4 Critical, 13 High, 9 Medium, 5 Low。

**最严重问题:**
1. 三个 god file >1600 行，每个处理 5+ 职责域
2. `legacy_command.h` 仍被 11 个 C++ 系统作为主要命令面消费
3. `RuntimeFacade` 不是真正的 facade — `runtime()` 逃生口是默认访问路径
4. 平面聚合继承 — 每个实体携带所有域字段；`LeaderIntentCore` 逐字镜像 `MissionCommandCore`
5. ECS 排序是隐式的（注册顺序），不可机器检查

## 2. God File (Critical)

| ID | 文件 | 行数 | 问题 |
|----|------|------|------|
| F-001 | `counterfactual_replay_contracts.h` | 2342 | 6 域混合, 159 常量, 18 结构体, 40 内联验证 |
| F-002 | `runtime_facade.cpp` | 2809 | 7+ 职责域, 4 个分散的 `using namespace` 块 |
| F-003 | `runtime_window_coordinator.h` | 1646 | 纯头文件, 125+ 内联函数, 零 .cpp |
| F-004 | `default_unit_factory.h` | 1457 | 35 个 #include, 所有单位类型内联初始化 |
| F-005 | 7 个契约文件 >300 行 | — | 全部混合常量+类型+验证于一个头文件 |
| F-006 | Profile 文件结构重复 | 652/540/297 | 12 函数模板在三文件中完全相同 |
| F-007 | Adapter 三重复制 | 49/47/53 | 结构相同模板 |

## 3. 遗留代码

| ID | 严重级别 | 问题 |
|----|----------|------|
| L-001 | HIGH | `legacy_command.h` — 11 个 C++ 系统活跃消费 MovementCommand/ActionCommand |
| L-002 | HIGH | `RuntimeFacade.runtime()` 逃生口是默认批处理目标 |
| L-003 | HIGH | `loader.sim.*` 直接调用绕过 facade (leader_tasking.py 10+ 处) |
| L-004 | MEDIUM | `loader.mission_cmd` 普遍作为原始字典访问 (10+ 文件) |
| L-005 | MEDIUM | Legacy 运行时模式仍是一等公民; legacy 地形是硬编码默认值 |
| L-006 | LOW | 基准测试中的遗留重实现 |
| L-007 | LOW | 物理中的稳定性 hack |
| L-008 | MEDIUM | `leader_tasking.py:210` 硬编码 air profile |

## 4. 架构文档 vs 现实

| ID | 严重级别 | 问题 |
|----|----------|------|
| A-001 | HIGH | `spawn_unit(type_name)` 是唯一生成路径（架构法则 15 目标是能力组合） |
| A-002 | HIGH | ECS 排序是隐式注册顺序（代码承认设计异味） |
| A-003 | MEDIUM | 信息状态六层模型被绕过（已知过渡模式） |
| A-004 | MEDIUM | `common_core_profile.py` 包含空中特定逻辑和回退 |
| A-005 | LOW | 猴子补丁 `ef_py` 到 profile 模块 |
| A-006 | HIGH | 平面聚合 — 域泄漏（见 S-001） |

## 5. ECS/DTO 结构问题

| ID | 严重级别 | 问题 |
|----|----------|------|
| S-001 | HIGH | 平面多重继承 — 域泄漏；LeaderIntentCore 镜像 MissionCommandCore |
| S-002 | HIGH | 恢复/起飞字段在 3 个聚合中重复三次 |
| S-003 | MEDIUM | 海军域分解不一致 (7/3/2/2 字段) |
| S-004 | HIGH | WorldBatchRuntime — 36 方法, 7 职责域; 3 个空间查询 90% 相同 |
| S-005 | MEDIUM | SimulationKernel 向 Python 暴露 55+ 方法 |
| S-006 | LOW | PilotWeaponRelease 是唯一内联定义的系统 |

## 6. 跨切面反模式

**双重路径:** 命令(PilotAction/MovementCommand)、生成(Typed/Legacy)、运行时(compiled/legacy)、飞行塑形(compiled/legacy)、观测(ObservationPacket/get_agent_observation)、任务命令(RuntimeFacade/loader.sim.*)

**逃生口:** 四处暴露内部运行时对象直接给 Python

## 7. 推荐修复顺序

- **第 1 波 (仅文档):** 确认 A-001/A-003 为接受过渡状态; 记录 L-007 过期标准
- **第 2 波 (低风险):** L-008, S-006, A-005, F-007
- **第 3 波 (中等重构):** A-004, F-003, F-006, L-004, L-005
- **第 4 波 (重大重构):** F-001, F-002, F-004, F-005, S-004
- **第 5 波 (架构级):** S-001/S-002/A-006 (聚合替换), L-001 (双重命令路径), L-002/L-003 (关闭逃生口), A-002 (ECS 管道阶段), S-005 (限制内核绑定)
