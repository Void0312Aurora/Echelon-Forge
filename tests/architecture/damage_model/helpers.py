from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tests.support.cli import run_maintenance_cli, run_maintenance_json_cli
from tests.support.manifests import (
  assert_authority_guards_false,
  assert_no_keys_anywhere,
  assert_retained_manifest_clean,
  walk_payload,
)


EXPECTED_BECO_SHA256 = (
  "82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc"
)
EXPECTED_TP20_SHA256 = (
  "293c5fd15a56b7ec4e6f4ad37d35f73a8e010083ce20baad56e39fb8423f165f"
)
EXPECTED_TP21_SHA256 = (
  "84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8"
)

HEX64 = re.compile(r"^[a-f0-9]{64}$")


def assert_hex64(value: str) -> None:
  assert HEX64.fullmatch(value)


def write_release_json(path: Path, payload: dict[str, Any]) -> Path:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  return path
