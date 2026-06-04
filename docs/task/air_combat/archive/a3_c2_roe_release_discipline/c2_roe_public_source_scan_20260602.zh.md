# C2/ROE 公开来源扫描 - 2026-06-02

状态：`2026-06-02` A3 planning source scan。本文只支持
[README.zh.md](README.zh.md) 中的术语、状态机和边界设计，不授予真实 ROE、
真实 BVR shot doctrine、Pk、武器物理或空防 C2 authority。

## 来源准入边界

- 只使用公开可引用来源：联合/军种公开条令、多军种公开 brevity、官方平台说明、
  政府公开事故报告或可靠二手事实入口。
- 公开资料只能支持术语、控制状态和谨慎建模边界；不能支持保密交战规则、真实武器
  employment timeline、真实齐射/再攻击规则或机型专用程序。
- 若公开资料只提供方向性概念，A3 应把它实现为简化训练合同，并在验收中记录
  `non-authoritative` 与 `simulation contract` 语义。

## 可写入项目文档的事实

| Source | Tier | Safe fact for A3 | Modeling implication | Non-claim |
| --- | --- | --- | --- | --- |
| [JP 3-01, Countering Air and Missile Threats](https://irp.fas.org/doddir/dod/jp3_01.pdf) | Tier A / official-standard public doctrine mirror | 公开联合条令把 WCS、commit authority 与 engagement authority 作为空防 C2/控制概念；commit 不应直接等同开火。 | A3 应分离 target assignment/commit 与 fire authorization。 | 不推导具体战斗机 BVR 发射间隔、齐射规则或平台程序。 |
| [ALSSA Multi-Service Brevity Codes 2025](https://www.alssa.mil/Portals/9/Documents/mttps/brevity_2025.pdf) | Tier A / official-standard | `WEAPONS FREE/TIGHT/HOLD`、`ENGAGE`、`HOLD FIRE`、`CEASE FIRE`、`CEASE ENGAGEMENT`、`ABORT`、`BOGEY/BANDIT/HOSTILE` 是可公开引用的 brevity/control 术语。 | A3 可把 WCS、engage order、cease/abort override 和 target identity 做成离散状态。 | brevity 不是完整 ROE；不能把简语表写成真实战术流程。 |
| [ATP 3-01.81 Counter-Unmanned Aircraft System Techniques](https://rdl.train.army.mil/catalog-ws/view/100.ATSC/B6A1625F-6975-4367-82C8-E67E901218C7-1753193840461/ATP3_01x81.pdf) | Tier A / official-standard | 公开陆军防空资料也使用 weapons free/tight/hold 这组 WCS 概念。 | WCS 作为跨场景通用控制约束是合理抽象。 | 该来源不是战斗机 BVR 训练手册，不能定义空战射击规则。 |
| [AFDP 3-0.1 Command and Control](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf) | Tier A / official-standard | 空军公开 C2 条令说明 CRC、AWACS、BCC 等节点可承担检测、识别、commit、engagement 或空域控制相关职能，具体委托取决于命令安排。 | A3 应把授权源保守抽象为 `engagement_authority_holder_id` / `grantor_id` 或 controller state；长机不是默认唯一授权源。 | 不推断现实每次交战都由 AWACS 或长机给出最终开火许可。 |
| [USAF E-3 Sentry AWACS fact sheet](https://www.af.mil/News/Article-Display/Article/104504/e-3-sentry-awacs/) | Tier A / official public fact sheet | AWACS 公开定位包括监视、C2BM、战场管理和引导/控制空中力量。 | S1 可把外部 C2/controller 抽象成 mission command 输入，而不是让单机策略承担全部授权判断。 | 平台简介不提供具体口令、timeline 或保密控制程序。 |
| [GAO OSI-98-4 Operation Provide Comfort Black Hawk fratricide report](https://www.gao.gov/products/osi-98-4) | Tier A / government report | 1994-04-14 Operation Provide Comfort 黑鹰误击案公开说明识别、C2 信息共享和 ROE/职责理解错误会导致严重 fratricide 风险。 | A3 可把识别、授权、hold/abort 和目标分配建成显式约束，以避免把“敌方接触”直接等同于“可开火”。 | 该事故不能反推普遍空战开火流程，也不应复刻具体战术细节。 |

## 术语到仿真状态的建议映射

| Concept | A3 field candidate | Suggested values | Training use |
| --- | --- | --- | --- |
| Weapons Control Status | `wcs_state` or `roe_state` extension | `hold`, `tight`, `free` | 决定默认可交战条件；`hold` 默认禁止，`tight` 需要 hostile，`free` 仍受 ROE 和友方约束。 |
| Target identity | `target_identity_state` | `unknown`, `bogey`, `bandit`, `hostile`, `friendly` | 避免把 bandit 自动解释为可开火；`hostile` 才可进入 tight 下的授权检查。 |
| Engagement order | `engage_order_state` | `none`, `commit`, `engage`, `hold_fire`, `cease_fire`, `cease_engagement`, `abort` | 分离目标分配、准备拦截、授权开火和覆盖停止命令。 |
| Fire authorization | `authorization_to_fire` | `false`, `true` | 作为发射合法性 gate 和 policy-visible 状态。 |
| Authority source | `engagement_authority_holder_id`, `engagement_authority_grantor_id` | entity ids or `0` fallback | 记录授权来源和本机是否持有开火权限。 |
| Shot policy | `shot_policy_state` | `single_shot_then_assess`, `salvo_authorized`, `reattack_authorized`, `weapons_hold` | 把第二发区分为过早违规、授权齐射或授权再攻击。 |
| Pending assessment | `pending_assessment` / `own_missile_in_flight` | `0/1`, count, timer | 单发后等待导弹效果、超时或显式 reattack 授权。 |

## 对 S1/M1 的直接结论

- 当前多发问题不是纯“弹药管理”问题。单目标单机情景中，剩余弹药的长期价值很难给出
  足够清晰的训练信号。
- 更自然的训练信号来自 C2/ROE：是否被授权开火、是否被授权齐射、是否必须等待评估、
  是否收到停火或 abort 命令。
- M1 的 temporal window 可以帮助策略记住近期发射与在飞导弹，但如果场景没有公开
  `shot_policy` 和 `pending_assessment`，策略并不知道第二发究竟是违规还是合理。
- 因此 A3 是 M1/M2 的前置解释层：先让 command state 可观测，再判断剩余多发是否
  需要 sequence-native policy。

## 不采纳为 A3 事实的内容

- 未公开、受限、泄露或来源不明的 ROE、战术手册、训练课件和平台程序。
- 论坛/游戏/民间数据库中的具体发射间隔、命中率、齐射规则或战术建议。
- 从事故或战例倒推出的通用 BVR 开火流程。
- 用 reward 标量反向定义真实 ROE 或真实武器 authority。
