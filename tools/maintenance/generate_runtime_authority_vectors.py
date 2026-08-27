"""Generate the P3-B cross-language authority vectors from their canonical owner."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from tools.maintenance.runtime_authority_contracts import (
  adapt_current_resolved_manifest,
  build_release_manifest_shell,
  build_rollout_decision_shell,
  build_state_checkpoint_shell,
  canonical_json_bytes,
  validate_authority_chain,
)
from tools.maintenance.runtime_artifact_ledger import ArtifactDescriptor, StoredArtifactInventory, inventory_payload


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "architecture" / "composition" / "fixtures"


def _read(name: str) -> dict[str, Any]:
  return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _vector(envelope: Mapping[str, Any]) -> dict[str, Any]:
  return {
    "vector_kind": "authority_envelope_v1",
    "canonicalization": envelope["canonicalization"],
    "domain": envelope["domain"],
    "media_type": envelope["media_type"],
    "canonical_payload_bytes": canonical_json_bytes(envelope["payload"]).decode("utf-8"),
    "payload_sha256": envelope["payload_sha256"],
    "envelope_json": canonical_json_bytes(envelope).decode("utf-8"),
  }


ROLLBACK_RELEASE_PACKAGE_BYTES = b"echelon-forge-generation-1-rollback-package-v1\n"
CANDIDATE_RELEASE_PACKAGE_BYTES = b"echelon-forge-generation-2-candidate-package-v1\n"


def build_inventory(
  plan: Mapping[str, Any],
  plan_generation_2: Mapping[str, Any],
  checkpoint: Mapping[str, Any],
) -> StoredArtifactInventory:
  artifacts: list[ArtifactDescriptor] = []
  for envelope, writer_generation, reader_min, reader_max, rollback_eligible in (
    (plan, 1, 1, 2, True),
    (plan_generation_2, 2, 2, 2, False),
  ):
    envelope_bytes = canonical_json_bytes(envelope)
    artifacts.append(ArtifactDescriptor(
      authority_kind="resolved_composition_plan",
      blob_sha256=hashlib.sha256(envelope_bytes).hexdigest(),
      media_type="application/vnd.echelon-forge.resolved-composition-plan-envelope.v1+json",
      size=len(envelope_bytes), writer_generation=writer_generation,
      reader_generation_min=reader_min, reader_generation_max=reader_max,
      state_schema_generation=1, truth_features=("native_step_authority",),
      topology="in-process", rollback_eligible=rollback_eligible,
    ))
  checkpoint_bytes = canonical_json_bytes(checkpoint)
  artifacts.append(ArtifactDescriptor(
    authority_kind="state_checkpoint",
    blob_sha256=hashlib.sha256(checkpoint_bytes).hexdigest(),
    media_type="application/vnd.echelon-forge.state-checkpoint-envelope.v1+json",
    size=len(checkpoint_bytes), writer_generation=1,
    reader_generation_min=1, reader_generation_max=2,
    state_schema_generation=1, truth_features=("native_step_authority",),
    topology="in-process", rollback_eligible=True,
  ))
  for package_bytes, writer_generation, reader_min, reader_max, rollback_eligible in (
    (ROLLBACK_RELEASE_PACKAGE_BYTES, 1, 1, 2, True),
    (CANDIDATE_RELEASE_PACKAGE_BYTES, 2, 2, 2, False),
  ):
    artifacts.append(ArtifactDescriptor(
      authority_kind="release_package",
      blob_sha256=hashlib.sha256(package_bytes).hexdigest(),
      media_type="application/vnd.echelon-forge.release-package.v1+octets",
      size=len(package_bytes), writer_generation=writer_generation,
      reader_generation_min=reader_min, reader_generation_max=reader_max,
      state_schema_generation=1, truth_features=(), topology="in-process",
      rollback_eligible=rollback_eligible,
    ))
  artifacts.sort(key=lambda item: (item.authority_kind, item.writer_generation, item.blob_sha256))
  return StoredArtifactInventory(
    release_id="release-2026-08-25",
    compatibility_generation=2,
    writer_generation=1,
    minimum_reader_generation=1,
    rollback_deadline="2026-09-01T00:00:00Z",
    last_reader_deadline="2026-10-01T00:00:00Z",
    irreversible_write_boundary="none",
    eligible_reader_ids=("reader-a", "reader-b"),
    artifacts=tuple(artifacts),
  )


def build_vectors() -> dict[str, dict[str, Any]]:
  resolved = _read("default_compatibility_manifest.resolved.json")
  request = _read("default_runtime_composition_request.v1.json")
  plan = adapt_current_resolved_manifest(
    resolved,
    source_request=request,
    source_requested_manifest=resolved["manifest"],
    plan_id="plan-1",
    reader_generation_max="2",
  )
  plan_generation_2 = adapt_current_resolved_manifest(
    resolved,
    source_request=request,
    source_requested_manifest=resolved["manifest"],
    plan_id="plan-2",
    writer_generation="2",
    reader_generation_min="2",
    reader_generation_max="2",
  )
  checkpoint = build_state_checkpoint_shell({
    "authority_kind": "state_checkpoint",
    "schema_version": "echelon_forge.state_checkpoint.v1",
    "contract_version": "echelon_forge.state_checkpoint_contract.v1",
    "writer_role": "runtime_host",
    "writer_generation": "1",
    "checkpoint_id": "checkpoint-1",
    "plan_sha256": plan["payload_sha256"],
    "release_id": "release-2026-08-25",
    "decision_id": "decision-1",
    "run_id": "run-1",
    "host_boot_id": "boot-1",
    "incarnation_epoch": "1",
    "transfer_fence_sequence": "7",
    "world_fragments": [{
      "world_id": "world-1",
      "episode_ids": ["episode-1"],
      "fragment_sequence": "0",
      "state_sha256": "d" * 64,
    }],
    "aggregate_state_sha256": "e" * 64,
    "state_schema_generation": "1",
    "target_reader_generation_min": "1",
    "target_reader_generation_max": "2",
  })
  inventory = build_inventory(plan, plan_generation_2, checkpoint)
  inventory_sha256 = hashlib.sha256(canonical_json_bytes(inventory_payload(inventory))).hexdigest()
  release = build_release_manifest_shell({
    "authority_kind": "release_manifest",
    "schema_version": "echelon_forge.release_manifest.v1",
    "contract_version": "echelon_forge.release_manifest_contract.v1",
    "writer_role": "release_artifact_pipeline",
    "release_id": "release-2026-08-25",
    "writer_generation": "1",
    "reader_generation_min": "1",
    "reader_generation_max": "2",
    "package_set": [{"name": "cmo", "sha256": hashlib.sha256(CANDIDATE_RELEASE_PACKAGE_BYTES).hexdigest()}],
    "supported_rows": ["windows-amd64-msvc"],
    "provenance_sha256": "b" * 64,
    "sbom_sha256": "c" * 64,
    "toolchain_identity": "msvc-v143",
    "source_revision": "82d5b6e893c442950e334eb3e9ec92f8174eeb35",
    "compatibility_generation": "2",
    "minimum_reader_generation": "1",
    "state_schema_generation": "1",
    "rollback_policy": "checkpoint-recovery",
    "stored_artifact_inventory_sha256": inventory_sha256,
    "rollback_deadline": "2026-09-01T00:00:00Z",
    "last_reader_deadline": "2026-10-01T00:00:00Z",
    "irreversible_write_boundary": "none",
  })
  rollout = build_rollout_decision_shell({
    "authority_kind": "rollout_decision",
    "schema_version": "echelon_forge.rollout_decision.v1",
    "contract_version": "echelon_forge.rollout_decision_contract.v1",
    "writer_role": "release_controller",
    "decision_id": "decision-1",
    "release_id": "release-2026-08-25",
    "manifest_sha256": release["payload_sha256"],
    "plan_sha256": plan["payload_sha256"],
    "plan_reader_generation_min": "1",
    "plan_reader_generation_max": "2",
    "predecessor_decision_id": "",
    "state": "prepared",
    "writer_generation": "1",
    "decision_sequence": "0",
    "cohort": "qualification",
    "rollback_deadline": "2026-09-01T00:00:00Z",
    "checkpoint_id": "",
    "irreversible_write_boundary": "none",
  })
  validate_authority_chain(plan, release, rollout, checkpoint)
  return {
    "authority_resolved_composition_plan.v1.json": _vector(plan),
    "authority_resolved_composition_plan.generation2.v1.json": _vector(plan_generation_2),
    "authority_cross_language_vector.v1.json": _vector(release),
    "authority_rollout_decision.v1.json": _vector(rollout),
    "authority_state_checkpoint.v1.json": _vector(checkpoint),
  }


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--write", action="store_true", help="rewrite checked-in vectors")
  args = parser.parse_args()
  stale: list[str] = []
  for name, vector in build_vectors().items():
    rendered = json.dumps(vector, indent=2, ensure_ascii=False) + "\n"
    path = FIXTURES / name
    if args.write:
      path.write_text(rendered, encoding="utf-8", newline="\n")
    elif not path.is_file() or path.read_text(encoding="utf-8") != rendered:
      stale.append(name)
  if stale:
    raise SystemExit(f"stale authority vectors: {', '.join(stale)}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
