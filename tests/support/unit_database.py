"""Test access to the maintained example unit database.

Tests must not hard-code hardpoint numbers or copy a hand-picked subset of
database files. Station layouts change when content is corrected, and a partial
copy drops the weapons a platform references, which the native spawn gate
rejects. Resolve stations by weapon name and patch a full temporary copy.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from python.content.unit_loadout import (
  DEFAULT_DATABASE_ROOT,
  find_unit_record,
  iter_unit_records,
  station_for,
  station_stores,
  stations_carrying,
)


__all__ = [
  "DEFAULT_DATABASE_ROOT",
  "patched_database",
  "station_for",
  "station_stores",
  "stations_carrying",
  "unit_record",
]


def unit_record(name: str, *, root: Path = DEFAULT_DATABASE_ROOT) -> dict[str, Any]:
  return find_unit_record(name, root=root)[1]


@contextmanager
def patched_database(
  patches: dict[str, Callable[[dict[str, Any]], None]],
  *,
  root: Path = DEFAULT_DATABASE_ROOT,
  prefix: str = "ef_unit_db_",
) -> Iterator[Path]:
  """Yield a full temporary copy of the database with named records patched.

  Each key is a unit `name`; its callable mutates that record in place. The
  rest of the database is copied unchanged, so every reference the patched
  records carry still resolves.
  """

  with tempfile.TemporaryDirectory(prefix=prefix) as tmpdir:
    copy_root = Path(tmpdir) / "database"
    shutil.copytree(root, copy_root)
    for name, mutate in patches.items():
      path, _ = find_unit_record(name, root=copy_root)
      payload = json.loads(path.read_text(encoding="utf-8"))
      record = next(record for record in iter_unit_records(payload) if record.get("name") == name)
      mutate(record)
      path.write_text(json.dumps(payload), encoding="utf-8")
    yield copy_root
