# Boeing — F-15EX Eagle II

Source ID: `p5-us-air-f15ex-boeing`
Tier: `B`
Publisher: The Boeing Company
Author / maintainer: Boeing Defense, Space and Security
Title: F-15EX — fighters and bombers product page
URL: https://www.boeing.com/defense/fighters-and-bombers/f-15ex-eagle
Domain: air
Equipment: F-15 / F-15EX
Configuration: The page is specific to the F-15EX and does not tabulate the F-15E, F-15C or the Advanced Eagle export marks.
Retrieval:
  attempted_at: 2026-09-17T15:47:11Z
  method: tavily_proxy
  status: success
  returned: specifications block, performance block, capability text, customers block
  did_not_return: engine designation, engine model, thrust, empty weight, crew, ejection seat, ammunition
Estimation / uncertainty: Tier B manufacturer documentation, authoritative for the limits of the aircraft it builds. It is a marketing product page rather than a flight manual or a type certificate.
Retention: manifest and extracted parameter notes only
Rights status: not_recorded
Provenance status: manifest+retrieval+retention
Residual status: open

## Extracted parameter notes

Specifications block: Width 42.8 feet (13 m); Length 63.8 feet (19.4 m); Height 18.5 feet (5.6 m); Maximum Takeoff Weight 81,000 pounds (36,741 kg). Performance block: Maximum Speed Mach 2.5; Ceiling 50,000 feet (15,240 m); Payload 29,500 pounds (13,381 kg); Service Life 20,000+ hours.

Capability text: payload capacity 29,500 pounds (13,300 kg); the aircraft can accommodate up to 12 AMRAAMs or an equivalent mix of large ordnance; digital fly-by-wire controls; all-glass cockpit; open mission systems architecture; hypersonic weapon carriage; advanced AESA radar and the EPAWSS electronic-warfare suite; two-seat configuration stated in the operational section.

## Negative finding: this page states no engine

The retrieval of 2026-09-17 searched and read the full page text. The page contains no engine designation, no engine model, no thrust figure, no empty weight, no crew count and no ejection seat. It names neither F110, nor F100, nor General Electric, nor Pratt.

An earlier revision of this manifest was used as the source for the F-15EX powerplant row on the leaf. That attribution was wrong. The powerplant and thrust rows now rest on `p5-us-air-f15ex-f16net`, which states the engine and both thrust figures explicitly, with `p5-us-air-f15ex-globalmilitary` as a second page naming the same engine model. The engine edge is no longer written against this package.

## A note on the two payload figures

The specifications block states 29,500 pounds (13,381 kg) and the capability paragraph states 29,500 pounds (13,300 kg) for the same quantity. The imperial value is identical on both and only the metric rounding differs. The leaf records the imperial value with both metric roundings rather than selecting one as the page's own conversion.

## Relationship to the other F-15EX packages

This package is the manufacturer source of record for the F-15EX dimensions, maximum takeoff weight, payload, speed, ceiling and service life. The Tier C pages held for this leaf agree with it on the 81,000 lb maximum takeoff weight and on the 19.4 m length.
