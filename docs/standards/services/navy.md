# US Navy Profile

本文档定义项目在海战/海上行动建模时采用的 US Navy profile。

## 1. 官方现实基础

Navy 公开资料显示，海军战术组织比陆军更“任务编组化”，并且在战术控制上广泛采用
`Task Force` 与 `Composite Warfare Commander (CWC)` 体系。

当前公开官方依据：

- [U.S. 7th Fleet, CTF 71 establishment](https://www.c7f.navy.mil/Media/News/Display/Article/2641477/ctf-71-establishment-enhances-readiness-in-7th-fleet/)
- [TTGP Warfare Commanders Conference I](https://www.ttgp.navy.mil/OFRP-Syllabus/Warfare-Commanders-Conference-I/)
- [NAVIFOR, IW Has a Seat at the Table](https://www.navifor.usff.navy.mil/Press-Room/News-Stories/Article/2395110/iw-has-a-seat-at-the-table/)
- [COMPHIBRON 5 About](https://www.surfpac.navy.mil/Ships/Amphibious-Squadron-COMPHIBRON-5/About/)

从这些官方页面可以确认：

- `Task Force` 是实际任务组织单元
- sea combat / amphibious / information warfare 等能力会围绕 `CWC table`
  与 warfare commanders 组织
- `Officer in Tactical Command` 与 `Composite Warfare Commander` 在舰队/编队场景中是现实存在的角色

## 2. 建模结论

### 2.1 不应进入 tight-loop runtime 的层

- numbered fleet
- major theater maritime component

这些更适合作为：

- operation-level command nodes
- scenario tasking and force packaging nodes

### 2.2 更适合进入 tight-loop runtime 的层

海战 tight-loop runtime 更适合放在：

- `task group / task unit` 级 tactical grouping
- `warfare commander` 级角色协同
- `single ship / ship section`

说明：

- Navy profile 的关键不是“像空军一样分 element”，而是
  `task organization + warfare commander role`

## 3. 对项目通用模板的影响

如果项目后续扩海战，joint/core 层必须能表达：

- `task_group_id`
- `warfare_role_code`
- `supported/supporting relation`
- `officer_in_tactical_command`

而不能把核心协同对象预设成：

- `lead / wingman`

那只适合空战 sortie 级编组，不适合舰队/编队控制。
