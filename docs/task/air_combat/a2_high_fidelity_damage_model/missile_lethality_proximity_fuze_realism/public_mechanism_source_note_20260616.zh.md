# 公开资料机制说明

状态：`2026-06-16` PF-R1 pass / 非权威机制说明，用于
[README.zh.md](README.zh.md)。

英文辅文：[public_mechanism_source_note_20260616.md](public_mechanism_source_note_20260616.md)。

## 范围边界

本文只准入公开资料中的高层机制事实，用来塑造非权威近炸引信 surrogate。它不准入真实导弹阈值、
真实 target-detecting-device 逻辑、涉密 burst-control 逻辑、deterministic fuze authority、Pk
或具体弹种杀伤结论。

## 使用的公开来源

| 来源 | 准入的公开事实 | 拒绝的 authority claim |
| --- | --- | --- |
| [FAS Naval Weapons, Chapter 14 Fuzing](https://man.fas.org/dod-101/navy/docs/fun/part14.htm) | 引信系统区分保险/解保、目标探测或识别、战斗部起爆，有些还会决定起爆方向。近炸引信是 target-detecting device，可使用 range-gating、Doppler/range-rate 或其他 influence-sensing 方法。 | 不提供 AIM-120C 或 AIM-120C-class 实现、常数、隐藏电路或可靠性验证。 |
| [FAS Naval Weapons, Chapter 13 Warheads](https://man.fas.org/dod-101/navy/docs/fun/part13.htm) | 破片和爆风衰减不同；破片密度与距离和目标暴露面积有关；现代空中目标战斗部可能使用方向性或环形破片图样。 | 不授权真实飞机部件概率、真实战斗部图样或 stock lethality。 |
| [Smithsonian proximity fuze cutaway](https://www.si.edu/object/fuze-proximity-cutaway%3Anasm_A19940233000) | RF 近炸引信可以理解为发射/接收式目标探测装置，反射信号和交会几何重要。 | 不提供现代导弹引信参数真值。 |
| [JHU APL Talos continuous-rod paper](https://secwww.jhuapl.edu/techdigest/content/techdigest/pdf/V03-N02/03-02-Brown.pdf) | 连续杆应被建模成有方向的切割机制，而不是各向同性爆炸球。 | Talos 历史不能把常数或杀伤 authority 转移到当前 A2 导弹 surrogate。 |

## 准入的机制事实

1. 引信决策是独立链路，不是一个距离公式。可用 surrogate 至少应保留：保险/解保、目标探测、
   起爆信号决策、可选延迟和起爆交接。
2. 近炸引信不需要接触目标。关键事件不只是“最近点进入半径”，而是“目标回波进入可用的传感器/战斗部机会窗口”。
3. 对空导弹的优选起爆点通常不是 closest approach。它依赖相对运动、闭合速度、目标姿态、战斗部图样和目标脆弱区覆盖。
4. 距离和距离率重要。公开 surrogate 可以建模 range window、closing state 和依赖闭合速度的延迟，但不能声明真实引信常数。
5. 目标签名重要。Radar/RF、laser/optical 和 generic proximity 可以共享合同，但不应共享完全相同的 evidence 字段。
6. 战斗部机制重要。Blast-fragmentation 应关心破片密度、距离、入射和暴露面积；continuous rod 应关心相对导弹轴线的侧向切割带或环形扫掠。
7. 未起爆是一等结果。目标可以很近，但因为传感器、跟踪、burst window、可靠性或机制覆盖门失败而不产生载荷。

## 拒绝的声明

- 公开来源不准入真实 AIM-120C 引信阈值、延迟曲线、TDD 实现细节、战斗部图样、破片质量分布或目标 kill probability。
- 公开来源不支持 deterministic fuze authority。
- 公开来源不支持在没有实现和验证包的情况下修改默认 runtime 路径。
- 公开来源不支持用 reward shaping 替代引信真实性。

## 对本子项目的含义

后续 surrogate 应从单一最近距离触发 proxy 移到事件链：

```text
nearest approach observed
  -> fuze sensor opportunity
  -> target detection / terminal track
  -> trigger or no trigger
  -> detonation point / delay
  -> mechanism-specific coverage
  -> effects or no-load event
```

这仍是 research surrogate。它可以用于趋势和诊断，不是校准武器模型。
