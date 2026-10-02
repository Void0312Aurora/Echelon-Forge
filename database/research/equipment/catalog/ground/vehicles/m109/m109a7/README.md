# M109A7 Paladin

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/m109/m109a7/README.md`
Owner: `database/equipment-data`
Content status: current variant parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-m109a7` |
| Family / variant | M109 / M109A7 Paladin |
| Service state | Current US Army configuration; M109A2 and earlier are separate leaves |
| Role | Self-propelled 155 mm artillery system |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 9.7 m length × 3.9 m width × 3.3 m height | `p5-us-ground-m109a7-armytechnology` | C | Army Technology stowed/overall convention; gun elevation and fittings are not itemized |
| Mass semantics | 35,380 kg maximum gross weight; 40,590 kg public combat-weight estimate | `p5-us-ground-m109a7-armytechnology` / `p5-us-ground-m109a7-weaponspecs` | C | Gross and combat conventions are retained separately; not silently collapsed |
| Powerplant | 675 hp electronically controlled BFV-standard V903 diesel | `p5-us-ground-m109a7-armytechnology` | C | Trade-publication summary of the M109A7/PIM powerpack |
| Transmission | L3 HMPT-800 automatic | `p5-us-ground-m109a7-armytechnology` | C | Public technical summary; exact sub-block and control software are not itemized |
| Road speed / range | Up to 61 km/h; approximately 300 km cruising range | `p5-us-ground-m109a7-armytechnology` | C | Public nominal figures; terrain, payload and fuel effects are not modeled |
| Crew | 4 | `p5-us-ground-m109a7-peo` | A | Operational crew context; task allocation and resupply team excluded |
| Ammunition payload | 39 × 155 mm rounds | `p5-us-ground-m109a7-weaponspecs` | C | Public compilation; projectile/charge mix and ready/stowed split are not itemized |
| Main armament | 155 mm M284 cannon on M182A1 mount with automated loader | `p5-us-ground-m109a7-armytechnology` | C | Public technical summary; standard projectile range about 22 km and rocket-assisted about 30 km |
| Mission systems | Digital backbone, onboard fire-control/navigation computer, secure digital/voice fire missions, 70 kW power system | `p5-us-ground-m109a7-armytechnology` | C | Public trade summary; network performance and diagnostics coverage are not itemized |
| Public protection | Enhanced applique armour, AFES and gunner protection kit; crew remains under armour | `p5-us-ground-m109a7-armytechnology` | C | Qualitative public description; no armour thickness or calibrated protection value |

## Source References

- `p5-us-ground-m109a7-peo`
- `p5-us-ground-m109a7-baesystems`
- `p5-us-ground-m109a7-armytechnology`
- `p5-us-ground-m109a7-weaponspecs`
