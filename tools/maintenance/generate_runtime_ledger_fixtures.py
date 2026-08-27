"""Generate P3-C inventory, shadow, and kill-switch contract fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.maintenance.generate_runtime_authority_vectors import build_inventory, build_vectors
from tools.maintenance.runtime_artifact_ledger import (
  KILL_SWITCH_SCHEMA_VERSION,
  LEDGER_CONTRACT_VERSION,
  QualificationEvidence,
  inventory_payload,
  rollout_qualification_payload,
  shadow_receipt_payload,
)
from tools.maintenance.runtime_authority_contracts import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "architecture" / "composition" / "fixtures"


def build_fixtures() -> dict[str, dict[str, object]]:
  vectors = build_vectors()
  plan = json.loads(vectors["authority_resolved_composition_plan.v1.json"]["envelope_json"])
  plan_generation_2 = json.loads(vectors["authority_resolved_composition_plan.generation2.v1.json"]["envelope_json"])
  checkpoint = json.loads(vectors["authority_state_checkpoint.v1.json"]["envelope_json"])
  release = vectors["authority_cross_language_vector.v1.json"]
  release_envelope = json.loads(release["envelope_json"])
  rollout = vectors["authority_rollout_decision.v1.json"]
  inventory = inventory_payload(build_inventory(plan, plan_generation_2, checkpoint))
  inventory_sha256 = hashlib.sha256(canonical_json_bytes(inventory)).hexdigest()
  shadow = shadow_receipt_payload(
    receipt_id="shadow-1",
    plan_sha256=plan["payload_sha256"],
    release_manifest_sha256=release["payload_sha256"],
    rollout_decision_sha256=rollout["payload_sha256"],
    comparison_kind="cpu-exact-result",
    outcome="match",
    evidence_sha256="9" * 64,
  )
  kill_switch = {
    "schema_version": KILL_SWITCH_SCHEMA_VERSION,
    "contract_version": LEDGER_CONTRACT_VERSION,
    "release_id": inventory["release_id"],
    "admissions_open": False,
    "writer_advancement_frozen": True,
    "reasons": ["wrong_epoch_results"],
    "authoritative_runtime_mutation": False,
  }
  qualification = rollout_qualification_payload(
    json.loads(rollout["envelope_json"]),
    inventory_sha256=inventory_sha256,
    release_manifest_blob_sha256=hashlib.sha256(canonical_json_bytes(release_envelope)).hexdigest(),
    active_plan_blob_sha256=hashlib.sha256(canonical_json_bytes(plan)).hexdigest(),
    evidence=QualificationEvidence(),
    admissions_open=True,
    writer_advancement_frozen=False,
  )
  return {
    "stored_artifact_inventory.v1.json": inventory,
    "shadow_comparison_receipt.v1.json": shadow,
    "kill_switch_record.v1.json": kill_switch,
    "rollout_qualification_record.v1.json": qualification,
  }


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--write", action="store_true")
  args = parser.parse_args()
  stale: list[str] = []
  for name, fixture in build_fixtures().items():
    rendered = json.dumps(fixture, indent=2, ensure_ascii=False) + "\n"
    path = FIXTURES / name
    if args.write:
      path.write_text(rendered, encoding="utf-8", newline="\n")
    elif not path.is_file() or path.read_text(encoding="utf-8") != rendered:
      stale.append(name)
  if stale:
    raise SystemExit(f"stale ledger fixtures: {', '.join(stale)}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
