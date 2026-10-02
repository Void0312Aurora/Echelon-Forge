# Patriot PAC-3 MSE

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/weapon/surface-to-air/patriot/pac-3-mse/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-weapon-patriotpac3` |
| Family / variant | Patriot / PAC-3 Missile Segment Enhancement (MSE) |
| Role | Ground-launched hit-to-kill interceptor for tactical ballistic missiles, cruise missiles and aircraft |
| Configuration boundary | U.S. Army PAC-3 MSE interceptor in Patriot/M903 canister; baseline PAC-3 CRI, PAC-2 GEM-T and future PAC-3 ACE are excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Mass | 312 kg all-up interceptor (bounded public estimates 312-321 kg) | `p5-us-weapon-patriotpac3-mda`; `p5-us-weapon-patriotpac3-lockheedmartin` | A/C | Canister and launcher excluded; exact production mass is controlled technical data |
| Dimensions | 5.2-5.3 m length; 255 mm forward body; 290-295 mm MSE motor diameter | `p5-us-weapon-patriotpac3-lockheedmartin` | C | Public diagrams disagree on whether the 11-inch motor diameter is reported; fin span is launcher-constrained and not established |
| Propulsion / motor | Dual-pulse solid rocket motor, larger 11-inch class MSE motor; attitude-control motors for terminal divert | `p5-us-weapon-patriotpac3-mda`; `p5-us-weapon-patriotpac3-lockheedmartin` | A/C | Pulse timing, propellant grain and thrust are not public |
| Guidance / seeker | Active Ka-band radar seeker with inertial midcourse, two-way RF data link, guidance processor and divert/attitude-control system | `p5-us-weapon-patriotpac3-mda`; `p5-us-weapon-patriotpac3-lockheedmartin` | A/C | Public material identifies seeker/data-link functions but not antenna pattern or ECCM settings |
| Range / flight envelope | 35 km against tactical ballistic targets and 50-70 km aerodynamic upper bound; intercept altitude 24-36 km; Mach 5.7-6.0 | `p5-us-weapon-patriotpac3-mda`; `p5-us-weapon-patriotpac3-lockheedmartin` | A/C | Exact defended footprint is threat- and radar-dependent; aerodynamic range values are specialist bounded estimates |
| Warhead | Hit-to-kill kinetic body plus aft lethality enhancer fragmentation charge; no conventional large blast warhead | `p5-us-weapon-patriotpac3-mda`; `p5-us-weapon-patriotpac3-lockheedmartin` | A/C | Lethality-enhancer mass and fragment pattern are not public; model direct kinetic intercept as primary effect |
| Fuze / trigger | Proximity/impact sensing for lethality enhancer, with terminal hit-to-kill contact event | `p5-us-weapon-patriotpac3-lockheedmartin` | C | Public sources do not name a fuze model; bounded trigger combines target-proximity cue and body-to-body impact |

## Source References

- `p5-us-weapon-patriotpac3-mda`: `raw/sources/missile_defense_agency/p5-us-weapon-patriotpac3-mda/manifest.md`
- `p5-us-weapon-patriotpac3-lockheedmartin`: `raw/sources/lockheed_martin/p5-us-weapon-patriotpac3-lockheedmartin/manifest.md`
