# 文档系统就绪度审查

状态：`2026-06-01` 基于实现对照的文档审查记录。

范围：顶层 README、`docs/`、`src/`、`python/`、`gym_envs/`、`tools/`、
`scripts/`、`examples/`、`scenarios/`、`tests/` 下维护中的 README 表面，
以及 reference-artifact 索引。历史 archive、临时笔记、A2 retained/signoff
脏产物不纳入本次“文档系统就绪”判断。

## 结论

文档系统已经显著接近当前实现，但还不能说完全就绪。

现在读者可以比较合理地把本项目理解为多域仿真与强化学习研究工程，而不是
只停留在空战的项目。维护中的入口已经开始区分成熟的 air/execution 路径、
cooperative/world-batch 集成、受限的 naval N4 tasking/contact evidence，
以及早期 ground tasking/schema bootstrap。

但它还不是可以对外称作完整产品手册的状态。若干历史目录仍保留旧机器翻译
标记、旧绝对路径和被取代的架构叙述。这些文件属于 archive/历史记录，但
current 与 archive 的边界必须继续显式，避免读者把旧记录当作当前事实。

## 已经与实现基本匹配的部分

| 区域 | 当前文档口径 | 实现支撑边界 |
| --- | --- | --- |
| 项目定位 | 多域仿真/RL 研究工程平台 | air/execution 是成熟 runtime baseline；naval 与 ground 按证据等级推进。 |
| C++ core | runtime/facade/ECS/component 层是真实维护表面 | `RuntimeFacade`、`WorldBatchRuntime`、`SimulationKernel`、component/tasking/command slice 存在，但各域成熟度不同。 |
| Python/RL | WorldBatch 与 cooperative 是维护中的训练方向 | 原始 `UniversalEnv` 仍偏 compatibility/debug/eval-adjacent，不能无条件写成现代主路径。 |
| Naval | N4 pre-fire tasking/contact/evidence 路径成立 | 平台组件、command/tasking DTO、token runtime、contact/report plumbing 和受限 engagement evidence hook 存在；不声明完整 naval combat outcome authority。 |
| Ground | 早期 tasking/schema/runtime bootstrap | `UnitType::Ground`、typed platform-schema evidence、tasking/profile fixture 和 aircraft/terrain contact primitive 存在；movement、sensing、terrain ownership、fires、damage 与 active RL 仍 held。 |
| Examples/scenarios/tests | active/frozen/diagnostic/archive 边界更清楚 | active config 和 runtime/test asset 是 evidence gate，本身不等于 learned-policy 或 full-domain acceptance。 |

## 剩余就绪缺口

| ID | 缺口 | 风险 | 建议 |
| --- | --- | --- | --- |
| DOC-READY-001 | Archive/temp 目录仍有旧绝对路径、机器翻译标记和被取代叙述。 | 搜索结果仍可能暴露旧 claim，除非读者清楚 archive 边界。 | 保持 archive warning 显眼；除非单独安排历史清理，不要把清理 archive 当成当前入口维护的阻塞项。 |
| DOC-READY-002 | `docs/task/naval/n5_rl_action_surface_split/` 目录名仍暗示 N5/active-RL 语义，但大量内容实际是 N4 pre-fire/training-entry repair。 | 读者可能高估 naval RL 和 weapon-outcome 成熟度。 | 单独迁移改名，或在该目录加更强 banner 解释目录名与实际语义不完全一致。 |
| DOC-READY-003 | 原始 `UniversalEnv`、eval helper、diagnostics 的 maintained/compatibility 分界仍需更硬。 | 文档后续可能再次把兼容路径说成主执行路径。 | 决定是迁移到 WorldBatch/facade，还是明确 quarantine 为 compatibility/debug。 |
| DOC-READY-004 | active cooperative/combined config 缺统一 scenario-path/manifest 配对规则。 | config 与 scenario 文档可能暗示比实现更强的 active acceptance。 | 升级文档前，先补 config/schema 测试或 manifest 规则。 |
| DOC-READY-005 | air-combat Stage 1-3 scenario 文件不等于 maintained active training/runtime evidence。 | scenario-only 资产可能被误读成 active runtime 支持。 | 增加 focused runtime smoke，或在索引中标为 planning/scenario-only。 |
| DOC-READY-006 | A2 retained/signoff 产物未在本轮审计。 | 本地脏 evidence packet 可能与维护文档状态用语冲突。 | 单独审计 A2/signoff；不要让该子树代表全项目成熟度。 |

## 文档操作规则

当前导航层以 root README、`docs/README*`、`docs/task/README*`、领域 README
和各目录本地 README 为准。`archive`、`Archive`、`temp`、retained artifact
和带日期的 cluster packet 都应视为支撑记录，除非当前 README 明确提升其权威性。

升级任何领域能力表述前，至少需要同时具备：

1. 维护中的实现 owner。
2. 维护中的 runtime/config/test 表面。
3. 文档明确证据等级，且不暗示更高能力。

## 校验注记

本轮就绪度收口应继续用以下方式复核：

- `git diff --check`
- 对 changed Markdown 做相对链接检查
- 对 changed current-entry Markdown 做陈旧表述扫描，排除 `archive`、`Archive`、
  `temp`、`retained_artifacts` 和明确的 A2/signoff 脏路径

当前结论：维护入口已经不再明显落后于实现，但它应被描述为“已做实现对齐且
保留已知残余”，而不是“完全完成”。
