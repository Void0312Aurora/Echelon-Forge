# C2 指挥链与通信待解决问题分析

状态：`2026-05-17` 归档的待解决问题快照。

关联文档：

- [冻结分析基线](../../c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)
- [当前进展检查点](c2_command_chain_progress_checkpoint_20260517.zh.md)
- [海战推进检查点](../../naval/naval_progress_checkpoint_20260517.zh.md)

本文档定位：

- 用于把“还没解决的问题”从冻结分析稿中剥离出来，并与当前代码进度对齐。
- 只列当前仍影响下一轮实现决策的问题，不重复已经完成的收口项。

## 零、对当前文档口径的补充

当前更准确的阅读方式是：

1. 本文档列的是“还剩的收口点”，不是“当前系统完全没有的能力”。
2. `MissionCommand` 字段、profile、codec、runtime、world-batch roundtrip 已有一批显式测试锁定。
3. `RuntimeFacade` 主线也已进入 adapter 守门态，因此“raw runtime 散落直穿主链”不再是当前事实。

因此，如果只看旧冻结分析，会高估当前欠账；如果只看当前绿线，又会低估 compat/contract 收尾余量。

## 一、已经不再属于当前 blocker 的项

下列问题虽然在冻结分析里被提出，但当前已经有最小收口，不应继续当成“完全未动”的空白：

1. `PilotAction` 无条件覆盖 `MissionCommand`
   - 现状：已改为 deadband 接管，不再是无条件静默抢权。
2. 海军 `MissionCommand` 完全没有专属字段
   - 现状：已具备最小站位参考字段并完成 roundtrip。
3. `Ship` 仍以 `MovementCommand` 作为主 authority
   - 现状：已统一主写向 `MissionCommand`。
4. `ROE` 只有一个布尔位
   - 现状：已具备最小 `roe_state + authority holder` 和 runtime gate。
5. `DataLink` 单帧无限消息
   - 现状：已具备消息/报告双预算和 drop observability。
6. `MissionCommand` 队列被第二条提交静默覆盖
   - 现状：当前主线验证到的是 FIFO；之前失败主要来自测试误判。

这意味着下一轮不应再重复花时间证明这些点“是否真实存在”，而应转向“当前收口仍然差在哪里”。

## 二、当前仍待解决的问题

### 2.1 `CommandLink` 仍缺少真正的队列策略

当前状态：

1. `MissionCommand` 有最小 FIFO queue。
2. 但 `MovementCommand / ActionCommand` 仍是 refresh/覆盖式 pending 语义。
3. `CommandLink` 仍只有固定延迟 + 独立丢包，没有 priority、抖动、重传或确认。

为什么仍重要：

1. 当前 `CommandLink` 还不能表达“高优先级交战命令插队、低优先级阵位调整延后”。
2. 也不能表达“丢了之后重发”或“延迟分布有长尾”。
3. 这会限制后续更真实的 naval fire-control / tasking 实验。

建议下一步：

1. 先做最小 priority bucket 或 per-command-type queue policy，而不是直接做完整 ACK。
2. 再评估是否需要最小 jitter / retry。

### 2.2 `DataLink` 虽然已有预算，但仍不是网络模型

当前状态：

1. 已有 `report/message budget`。
2. 已有最小拥塞 drop 观测。
3. 仍然只是在单跳、同网、同阵营、LOS 条件下做近似广播。

为什么仍重要：

1. 还没有 relay，超视距协同仍无法表达。
2. 还没有 jamming / EMCON interaction。
3. 还没有任务下达类消息的 doctrine 或状态机。

建议下一步：

1. 先做压力补测和 budget scaling，确认 budget 行为在更多 fanout 下稳定。
2. 再选一条小线继续：
   - relay 近似
   - jamming loss 近似
   - tasking message priority

不建议同时开三条。

### 2.3 海军 tasking 仍然不是完整任务式指挥

当前状态：

1. 已有最小 naval station 字段。
2. 已有最小 station-hold / screen 行为闭环。
3. 但仍缺少真正的 task phase、威胁轴、巡逻区、编队职责转换。

为什么仍重要：

1. 这限制了 `MissionCommand` 继续向更真实 naval C2 推进。
2. 也限制了 `ROE / authority / fire-control` 与任务状态联动。

建议下一步：

1. 不要直接做完整 state machine。
2. 先挑一个最小可验收语义进入 `MissionCommand`：
   - threat axis
   - station sector
   - patrol area

### 2.4 `ROE / authority` 仍未进入完整任务与通信链

当前状态：

1. runtime weapon release 已能读最小 `roe_state`。
2. 但 authority transfer 仍未与通信、任务委派或消息确认链相连。
3. `DataLink` 也还没有正式的 `ENGAGE / ENGAGED / WILCO / UNABLE` 任务消息闭环。

为什么仍重要：

1. 没有 authority 流转，很多真实 C2 行为仍无法表达。
2. `ROE` 也还没有和更细的 IFF / track quality 联动。

建议下一步：

1. 先做一条最小消息闭环，例如：
   - `AssignTask -> REP_WILCO`
   - `ENGAGE authorization -> holder match`
2. 再决定是否推进 authority transfer。

### 2.5 `MissionCommand` 编解码冗余仍未收束

当前状态：

1. 一批 common / naval / ROE 字段已经补进了 codec / profile / runtime-state。
2. 但 C++ `MissionCommandCodec` 与 Python `build_kernel_mission_command()` 仍是双维护路径。

为什么仍重要：

1. 新字段越多，双路径漂移风险越高。
2. 这已经开始变成维护成本，而不是单点 bug。

建议下一步：

1. 不要立刻重写成一套全新 schema。
2. 先补一份字段对照表和 roundtrip contract，找出还没被测试钉住的字段。
3. 当前重点已从“naval 字段有没有 roundtrip”转向：
   - common / naval / air 字段矩阵是否一致
   - episode state / post-transition JSON 回填是否持续对齐

### 2.6 `RuntimeFacade / ScenarioLoader` compat 面仍未完全减载

当前状态：

1. `RuntimeFacade.runtime()` 已被文档和架构测试降级为 compatibility / diagnostics escape hatch。
2. Python 主线的 raw runtime/world 访问已收回显式 adapter。
3. 但 adapter 仍同时承担 facade 与 compat runtime 兜底，`ScenarioLoader` 侧也仍保留旧代理入口。

为什么仍重要：

1. compat 面如果继续扩张，会重新放大 `RuntimeFacade` 与 `ScenarioLoader` 的 owner/接口债务。
2. 这类问题虽然不一定立刻打红行为测试，但会持续稀释 `MissionCommand` 与 execution runtime 的收口边界。

建议下一步：

1. 继续把新增需求优先做成 facade-shaped adapter 方法，而不是回流 raw runtime 访问。
2. 继续减载 `ScenarioLoader` 的 compat facade，不要把新状态同步再塞回 `core.py`。
3. 保持 `tests/architecture/runtime_facade` 与 world-setup compat 测试为守门线。

### 2.7 文档口径仍需从“冻结分析”过渡到“当前现状”

当前状态：

1. 原分析文档仍然保存了 `2026-05-17` 冻结时点的判断。
2. 其中部分表述已经被当前实现推进部分改写。

为什么仍重要：

1. 如果后续读者只看冻结分析，会误以为这些点还完全没做。
2. 这会导致重复验证、错误排期或错误对外描述。

建议下一步：

1. 保留冻结分析不动。
2. 后续只在子项目目录里更新“当前进展 / 待解决问题”。

## 三、下一轮最值得推进的方向

按当前代码面和风险面排序，建议优先级如下：

1. `DataLink` 压力补测 / budget scaling
   - 理由：当前刚有 budget 与 counter，最适合先稳住。
2. `CommandLink` 最小 priority policy
   - 理由：能直接提升命令链真实性，但写集还算可控。
3. `MissionCommand` 最小 naval tasking 新语义
   - 理由：可以把 naval C2 从“最小站位”再往前推一步。
4. `ROE / authority` 最小消息闭环
   - 理由：能把任务、通信、武器链再接深一层。
5. `MissionCommand` codec/profile contract 对账
   - 理由：这是维护债，重要但不一定要先做。
6. `RuntimeFacade / ScenarioLoader` compat 减载收尾
   - 理由：这已经是当前 `C2/runtime` 方向的真实剩余量之一，不再只是结构旁支。

## 四、当前是否值得再分发 subagent

当前建议：

1. 主实现继续留在主线本地推进。
2. 当下一轮进入“边界验证、压力测试、文档对账”时，再把这些 sidecar 工作分给 subagent。

原因：

1. 当前 `DataLink / CommandLink / MissionCommand` 仍在同一组高重叠写集里。
2. 现在继续把实现分散出去，合并成本会高于收益。
3. 更适合分发的是：
   - 压力补测设计
   - roundtrip 字段对账
   - 文档口径复核
