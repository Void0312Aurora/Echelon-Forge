# Deagel — J-15 carrier fighter specification

Source ID: `p5-cn-air-j15-deagel`
Tier: `C`
Publisher: Deagel.com
Author / maintainer: Deagel.com, defence equipment database
Title: J-15 combat aircraft specification entry
URL: https://www.deagel.com/Combat%20Aircraft/J-15/a002954
Accessed: 2026-09-18
Domain: air
Equipment: J-15
Configuration: Carrier-based fighter of the Su-27 family in Chinese service.
Estimation / uncertainty: Tier C equipment database. Deagel is a commercial defence reference database, not an official Chinese source. Its field definitions do not always distinguish crew from seat count on family-derived airframes, so its crew value is treated with caution below.
Retention: manifest and extracted parameter notes only

## Extracted parameter notes

Crew 2. External stations 12. Number of engines 2. Wing area 62.0 m². Height 5.9 m; length 21.9 m; wingspan 14.7 m. Main gun calibre 30 mm. Empty weight 17,700 kg. Maximum takeoff thrust 64,000 lb.

## A field that must not be read as crew size

This package records `Crew 2`. The baseline J-15 is a single-seat aircraft and the twin-seat derivative is the J-15S. A crew of 2 on this entry is therefore not consistent with the baseline airframe, and it is most likely the database inheriting a two-seat value from the Su-27UB-derived family rather than a statement about the J-15 itself.

The value is retained here because it is what the source says, and the leaf does not use it. Recording it prevents the same entry being re-discovered later and read at face value.

## Why this package exists

The empty weight 17,700 kg, the maximum takeoff weight 32,500 kg, the engine note covering Shenyang WS-10H and early Saturn AL-31F, and the 12-hardpoint count all originate here or in a compilation of the same kind. An earlier revision of the J-15 leaf attributed them to a second compilation without naming it, and cited the same source id as the primary article for every row. This package gives those claims a real origin so the leaf's citations match where the values came from.
