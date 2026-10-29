"""Read station loadouts from the authored unit database.

The native `UnitDefinitionLoader` owns how `default_loadout` is materialized.
This reader follows the same JSON shape (a station maps to one store name or an
ordered list of store names) so Python callers can name a weapon instead of a
hardpoint number. It does not validate admission; the native spawn gate does.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from python.runtime_bootstrap import resolve_repo_path


DEFAULT_DATABASE_ROOT = Path(resolve_repo_path("examples", "config", "database"))


def iter_unit_records(payload: Any) -> Iterator[dict[str, Any]]:
    """Yield unit records from a single object, a list, or a `{"units": [...]}` file."""

    if isinstance(payload, dict) and isinstance(payload.get("units"), list):
        payload = payload["units"]
    if isinstance(payload, list):
        for record in payload:
            if isinstance(record, dict):
                yield record
    elif isinstance(payload, dict):
        yield payload


def find_unit_record(name: str, *, root: str | Path = DEFAULT_DATABASE_ROOT) -> tuple[Path, dict[str, Any]]:
    """Return the file and record for the unique unit named `name` under `root`."""

    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(Path(root).rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        matches.extend((path, record) for record in iter_unit_records(payload) if record.get("name") == name)
    if len(matches) != 1:
        raise LookupError(f"expected exactly one unit record named {name!r} under {root}, found {len(matches)}")
    return matches[0]


def station_stores(platform: str, *, root: str | Path = DEFAULT_DATABASE_ROOT) -> dict[int, tuple[str, ...]]:
    """Map each loaded station of `platform` to its ordered store names."""

    loadout = find_unit_record(platform, root=root)[1].get("default_loadout") or {}
    stations = {
        int(key): tuple(stores) if isinstance(stores, list) else (str(stores),)
        for key, stores in loadout.items()
    }
    return dict(sorted(stations.items()))


def stations_carrying(platform: str, weapon: str, *, root: str | Path = DEFAULT_DATABASE_ROOT) -> tuple[int, ...]:
    """Return every station of `platform` whose stores include `weapon`, ascending."""

    return tuple(station for station, stores in station_stores(platform, root=root).items() if weapon in stores)


def station_for(platform: str, weapon: str, *, root: str | Path = DEFAULT_DATABASE_ROOT) -> int:
    """Return the lowest station of `platform` that carries `weapon`."""

    stations = stations_carrying(platform, weapon, root=root)
    if not stations:
        raise LookupError(f"{platform!r} default loadout carries no {weapon!r}")
    return stations[0]
