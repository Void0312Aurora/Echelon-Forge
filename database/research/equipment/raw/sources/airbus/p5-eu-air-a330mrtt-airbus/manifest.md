# Airbus — A330 MRTT

Source ID: `p5-eu-air-a330mrtt-airbus`
Tier: `B`
Publisher: Airbus Defence and Space
Author / maintainer: Airbus, military aircraft product pages
Title: A330 MRTT — multi role tanker transport
URL: https://www.airbus.com/en/products-services/defence/military-aircraft/a330-mrtt
Domain: air
Equipment: A330 MRTT / Voyager
Configuration: The manufacturer page covers the A330 MRTT family, which includes the A330 MRTT+ based on the A330neo. The Royal Air Force Voyager is the A330 MRTT in British service, and the family-level figures here are recorded as family readings rather than as Voyager-specific ones.
Retrieval:
  attempted_at: 2026-09-17T17:40:02Z
  method: tavily_proxy
  status: success
  returned: the capability blocks: maximum fuel offload up to 70 tonnes (154,000 lb) during a one-hour loitering mission at 1,250 nautical miles (2,315 km) from take-off; payload up to 45 tonnes (99,000 lb) of which 37 tonnes (82,000 lb) of cargo; up to 300 passengers; range up to 8,700 nautical miles (16,000 km)
  did_not_return: a maximum fuel capacity figure; the plain-text search return also showed a fuel-capacity line of 111 tonnes, which the page fetch did not confirm
Estimation / uncertainty: Tier B manufacturer documentation, authoritative for the capability of its own product. It publishes offload and payload, which are mission quantities, not a tank capacity. The distinction matters: an offload figure and a capacity figure are not the same quantity and are not converted into each other here.
Retention: manifest and extracted parameter notes only
Rights status: not_recorded
Provenance status: manifest+retrieval+retention
Residual status: open

## Extracted parameter notes

Maximum fuel offload: up to 70 tonnes (154,000 lb) during a one-hour loitering mission over a distance of 1,250 nautical miles (2,315 km) from take-off.

Payload: up to 45 tonnes (99,000 lb), of which 37 tonnes (82,000 lb) of cargo. Transport capacity up to 300 passengers with airline comfort. Range up to 8,700 nautical miles (16,000 km).

## A capacity figure this package does not carry

The A330 MRTT maximum fuel capacity of 111 tonnes (245,000 lb) that appears in the type's literature was not confirmed by the page retrieval. It is recorded on `p5-uk-air-voyager-kc2-ukdf` as a community reading where it appears as 111,000 kg maximum fuel capability, and the search return of this manufacturer page showed the same number in a capability line that the fetched text did not reproduce.

This package therefore does not attribute the 111-tonne capacity to the manufacturer. The 70-tonne offload and the 111-tonne capacity are different quantities under different conditions, and neither is derived from the other.

## Relationship to the Voyager packages

This package supplies the family-level offload and payload envelope. `p5-uk-air-voyager-kc2-raf` supplies the Royal Air Force KC2 fit and its fuel and cabin arrangement, and `p5-uk-air-voyager-kc2-ukdf` supplies the 111,000 kg capability reading and the 65,000 kg offload at 1,000 nautical miles.
