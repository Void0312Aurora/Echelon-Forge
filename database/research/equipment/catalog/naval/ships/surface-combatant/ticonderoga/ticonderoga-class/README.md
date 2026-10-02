# Ticonderoga-Class Guided-Missile Cruiser

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/naval/ships/surface-combatant/ticonderoga/ticonderoga-class/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-13`
Content status: extracted class-baseline simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-naval-ticonderoga` |
| Family / variant | Ticonderoga / Ticonderoga-class CG baseline |
| Configuration boundary | CG-47 through CG-73; dimensions and machinery are class-level. The first five ships used Mk 26 launchers; this leaf uses the representative 122-cell Mk 41 fit of CG-52 onward. Refits, deleted Harpoon launchers, and late SPY/CIWS upgrades are not collapsed into the baseline. |
| Role | Guided-missile cruiser; Aegis area air defense, strike, and anti-submarine warfare |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Hull dimensions | 173 m overall length x 16.8 m beam x approximately 9.5 m draft | `p5-us-naval-ticonderoga-factfile`; `p5-us-naval-ticonderoga-navaltechnology` | A/B | Overall dimensions; draft varies with stores and loading by roughly +/-0.5 m. |
| Displacement (standard proxy) | Approximately 8,100 long tons; bounded 7,900-8,300 LT | `p5-us-naval-ticonderoga-navaltechnology`; `p5-us-naval-ticonderoga-globalsecurity` | B/C | Navy fact files emphasize full load. This standard proxy is the light-ship/normal-load estimate used for simulation and must not be labelled full load. |
| Displacement (full load) | 9,600 LT for CG-47-CG-58; 9,800 LT for CG-59-CG-73 | `p5-us-naval-ticonderoga-factfile` | A | Class sub-block values; combat-system refits can add several hundred tons. |
| Propulsion / power | Four GE LM2500 gas turbines, COGAG, two shafts, 80,000 shp total | `p5-us-naval-ticonderoga-factfile`; `p5-us-naval-ticonderoga-navaltechnology` | A/B | Class machinery rating; delivered shaft power and plant condition are not modelled. |
| Maximum speed | 30+ knots | `p5-us-naval-ticonderoga-factfile` | A | Public Navy threshold, not a sustained sprint guarantee. |
| Range / endurance | Approximately 6,000 nmi at 20 knots; 30-45 days stores endurance | `p5-us-naval-ticonderoga-navaltechnology`; `p5-us-naval-ticonderoga-globalsecurity` | B/C | Range is a planning figure for normal fuel and load; endurance bound is a class-operational estimate. |
| Crew / aviation | 330-400 ship's company; two MH-60R/S-size helicopters in the hangar baseline | `p5-us-naval-ticonderoga-factfile`; `p5-us-naval-ticonderoga-navaltechnology` | A/B | Crew changed with automation and deployment; two-aircraft hangar is retained even when a detachment embarks fewer aircraft. |
| Sensors / combat system | Aegis Baseline combat system; four-face AN/SPY-1A/B phased-array radar; AN/SPS-49 air-search, AN/SPS-55 surface-search, AN/SPQ-9 gunfire, two AN/SPG-62 illuminators, AN/SQQ-89 ASW suite, AN/SLQ-32 EW | `p5-us-naval-ticonderoga-factfile`; `p5-us-naval-ticonderoga-globalsecurity` | A/C | Sensor names are class baseline. SPY-1B, Baseline 9, Cooperative Engagement Capability, and SEWIP upgrades are configuration branches. |
| Weapons / payload | 122 Mk 41 VLS cells (SM-2/SM-3/SM-6, ESSM quad-pack, Tomahawk mix); two Mk 45 127 mm guns; two Phalanx CIWS; two triple Mk 32 324 mm torpedo tubes; eight Harpoon launchers on representative early fit | `p5-us-naval-ticonderoga-factfile`; `p5-us-naval-ticonderoga-navaltechnology` | A/B | Cell count is fixed for CG-52 onward; missile mix and Harpoon retention vary by refit. |
| Protection / survivability | All-steel hull, watertight subdivision, NBC citadel, redundant fire-main and combat-system power, Kevlar/splinter protection around vital spaces | `p5-us-naval-ticonderoga-factfile`; `p5-us-naval-ticonderoga-globalsecurity` | A/C | No public armour schedule. Simulation bound for local splinter protection is 25-75 mm steel-equivalent; this is an explicit engineering estimate, not a published thickness. |

## Source References

- `p5-us-naval-ticonderoga-factfile`
- `p5-us-naval-ticonderoga-navaltechnology`
- `p5-us-naval-ticonderoga-globalsecurity`
