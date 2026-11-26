from __future__ import annotations

import hashlib
from pathlib import Path

from tools.diagnostics import kill_chain_guidance_calibration_visualize as visualize
from tools.diagnostics import kill_chain_guidance_envelope_rebuild as envelope
from tools.diagnostics import kill_chain_guidance_exact_mechanism_ablation as exact_ablation
from tools.diagnostics import kill_chain_guidance_mechanism_ablation as mech_ablation
from tools.diagnostics import kill_chain_guidance_scalar_calibration as scalar
from tools.diagnostics.common import file_sha256, write_csv_rows


def test_file_sha256_matches_aliases_and_empty_file(tmp_path: Path) -> None:
  empty_file = tmp_path / "empty.bin"
  empty_file.write_bytes(b"")
  assert file_sha256(empty_file) == hashlib.sha256(b"").hexdigest()

  payload_file = tmp_path / "payload.bin"
  payload = b"echelon-forge-diagnostics-parity\n" * 64
  payload_file.write_bytes(payload)
  expected = hashlib.sha256(payload).hexdigest()

  assert file_sha256(payload_file) == expected
  assert envelope._sha256(payload_file) == expected
  assert scalar._sha256(payload_file) == expected
  assert visualize._sha256(payload_file) == expected


def test_write_csv_rows_preserves_caller_value_encoding_and_empty_rows(tmp_path: Path) -> None:
  empty_csv = tmp_path / "empty.csv"
  write_csv_rows(empty_csv, [], value_transform=lambda v: v)
  assert empty_csv.read_text(encoding="utf-8") == ""

  rows = [
    {"b": {"k": "α"}, "a": 1},
    {"a": 2, "c": [1, 2]},
  ]

  env_csv = tmp_path / "envelope.csv"
  envelope._write_csv(env_csv, rows)
  assert env_csv.read_text(encoding="utf-8") == (
    'a,b,c\n1,"{""k"": ""α""}",\n2,,"[1, 2]"\n'
  )

  scalar_csv = tmp_path / "scalar.csv"
  scalar._write_csv(scalar_csv, rows)
  assert scalar_csv.read_text(encoding="utf-8") == env_csv.read_text(encoding="utf-8")

  exact_csv = tmp_path / "exact.csv"
  exact_ablation._write_csv(exact_csv, rows)
  assert exact_csv.read_text(encoding="utf-8") == (
    'a,b,c\n1,"{""k"": ""\\u03b1""}",\n2,,"[1, 2]"\n'
  )

  mech_csv = tmp_path / "mech.csv"
  mech_ablation._write_csv(mech_csv, rows)
  assert mech_csv.read_text(encoding="utf-8") == exact_csv.read_text(encoding="utf-8")
