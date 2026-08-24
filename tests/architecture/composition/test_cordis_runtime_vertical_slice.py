from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from jsonschema import Draft202012Validator
import pytest

from tools.maintenance import runtime_composition_projection_contract as request_contract
from tools.maintenance import simulation_composition_contract as composition_contract


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE = REPO_ROOT / "packages/cordis-runtime"
FIXTURES = REPO_ROOT / "tests/architecture/composition/fixtures"
NATIVE_CONFORMANCE = REPO_ROOT / "src/tests/test_cordis_runtime_conformance.cpp"
PACKAGE_DESCRIPTOR = PACKAGE / "packages/default-compatibility.package.json"
DEFAULT_OVERLAY = PACKAGE / "overlays/default-compatibility.default.v1.json"
PACKAGE_CONTRACTS = PACKAGE / "contracts"


def _native_conformance_binary() -> Path | None:
  configured = os.environ.get("CMO_BUILD_DIR")
  candidates = tuple(
    ([Path(configured) / "ef_cordis_runtime_conformance_test.exe"] if configured else [])
    + [
    REPO_ROOT / "build-cordis-simulation-composition/ef_cordis_runtime_conformance_test.exe",
    REPO_ROOT.parent.parent
    / "build-cordis-simulation-composition/ef_cordis_runtime_conformance_test.exe",
    REPO_ROOT / "build-workshop/ef_cordis_runtime_conformance_test",
    REPO_ROOT.parent.parent / "build-workshop/ef_cordis_runtime_conformance_test",
    ]
  )
  return next((candidate for candidate in candidates if candidate.is_file()), None)


def test_cordis_package_declares_the_p2c1_and_p6a_boundaries() -> None:
  package = json.loads((PACKAGE / "package.json").read_text(encoding="utf-8"))
  assert package["dependencies"]["cordis"] == "4.0.0-rc.8"
  assert package["scripts"]["produce"] == "node src/cli.mjs produce"
  assert package["exports"]["."] == "./src/index.mjs"
  producer = (PACKAGE / "src/producer.mjs").read_text(encoding="utf-8")
  package_sdk = (PACKAGE / "src/package.mjs").read_text(encoding="utf-8")
  cli = (PACKAGE / "src/cli.mjs").read_text(encoding="utf-8")
  assert "new Context()" in producer
  assert "root.plugin" in producer
  assert "runtime/compose" in producer
  assert "root.fiber.dispose()" in producer
  assert "root.effect" in producer
  assert "finally" in producer
  assert "default_compatibility_manifest.requested.json" in cli
  assert "admitted_catalog_lock.v1.json" in cli
  assert "runtime_profile_projection.v1.json" in cli
  assert "request_lock_binding" in cli
  assert "lowerDefaultManifest" in cli
  assert "defineRuntimePackage" in package_sdk
  assert "resolveRuntimePackage" in package_sdk
  assert "applyConfigurationOverlays" in package_sdk
  assert "buildRuntimePackageProvenance" in package_sdk
  assert "buildRuntimePackageDiagnostics" in package_sdk
  assert "PRODUCER_PACKAGE_NAME = '@echelon-forge/cordis-runtime'" in package_sdk
  assert "PRODUCER_PACKAGE_VERSION = '0.1.0'" in package_sdk
  assert "runtime_package_provenance.v1.json" in cli
  assert "runtime_package_diagnostics.v1.json" in cli


def test_cordis_package_maturation_contracts_are_strict_and_owner_bounded() -> None:
  descriptor = json.loads(PACKAGE_DESCRIPTOR.read_text(encoding="utf-8"))
  overlay = json.loads(DEFAULT_OVERLAY.read_text(encoding="utf-8"))
  profile_bundle_path = PACKAGE / "profiles/default-compatibility.bundle.json"
  profile_bundle = json.loads(profile_bundle_path.read_text(encoding="utf-8"))
  pairs = (
    ("cordis_runtime_package.v1.schema.json", descriptor),
    ("cordis_runtime_configuration_overlay.v1.schema.json", overlay),
  )
  for schema_name, document in pairs:
    schema = json.loads((PACKAGE_CONTRACTS / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(document)

  assert descriptor["package_id"] == "builtin.default_compatibility.package"
  assert descriptor["profile"] == {
    "profile_id": "builtin.default_compatibility",
    "profile_version": "1.0.0",
    "module_dependency_id": "profile.module",
    "bundle_dependency_id": "profile.bundle",
  }
  assert descriptor["cordis_dependency_id"] == "cordis.runtime"
  dependencies = {entry["dependency_id"]: entry for entry in descriptor["dependencies"]}
  assert dependencies["cordis.runtime"]["version"] == "4.0.0-rc.8"
  for dependency in dependencies.values():
    if dependency["kind"] == "repository_artifact":
      path = PACKAGE / dependency["path"]
      assert hashlib.sha256(path.read_bytes()).hexdigest() == dependency["sha256"]
  assert len(descriptor["overlays"]) == 1
  overlay_reference = descriptor["overlays"][0]
  assert hashlib.sha256(DEFAULT_OVERLAY.read_bytes()).hexdigest() == overlay_reference["sha256"]
  assert overlay_reference["overlay_id"] == overlay["overlay_id"]
  assert overlay["configuration_patch"] == {"seed": 42, "time_step_ns": 16666667}

  attributes = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
  for pattern in (
    "packages/cordis-runtime/packages/*.json -text",
    "packages/cordis-runtime/overlays/*.json -text",
    "packages/cordis-runtime/profiles/*.json -text",
    "packages/cordis-runtime/profiles/*.mjs -text",
    "packages/cordis-runtime/package-lock.json -text",
  ):
    assert pattern in attributes
  for artifact in profile_bundle["artifacts"].values():
    artifact_path = REPO_ROOT / artifact["path"]
    artifact_bytes = artifact_path.read_bytes()
    assert b"\r\n" not in artifact_bytes
    assert hashlib.sha256(artifact_bytes).hexdigest() == artifact["sha256"]
    assert f'{artifact["path"]} -text' in attributes

  forbidden_truth_keys = {
    "backend_request",
    "component_contributions",
    "provider_catalog",
    "provider_contributions",
    "system_contributions",
    "system_registration_order",
  }
  assert forbidden_truth_keys.isdisjoint(descriptor)
  assert forbidden_truth_keys.isdisjoint(overlay)


def test_native_conformance_seam_revalidates_projection_and_ingests_low_level_artifacts() -> None:
  cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
  source = NATIVE_CONFORMANCE.read_text(encoding="utf-8")
  assert "ef_cordis_runtime_conformance_test" in cmake
  assert "validate_runtime_composition_projection_json" in source
  assert "parse_simulation_composition_manifest_json" in source
  assert "parse_resolved_composition_json" in source
  assert "SimulationKernel kernel(resolved_manifest)" in source
  assert "requested.value() == resolved.value().manifest" in source
  assert "profile_projection_matches_artifacts" in source
  assert "canonical_sha256_hex" in source
  assert "builtin.default_compatibility" in source
  assert "default_runtime_profile_projection.v1.json" in cmake


def test_cordis_producer_matches_frozen_request_lock_and_manifest() -> None:
  node = shutil.which("node")
  dependency = PACKAGE / "node_modules/cordis/package.json"
  if node is None or not dependency.is_file():
    pytest.skip("Cordis npm dependency is not installed in the local package workspace")
  output = PACKAGE / "build/test-default-profile"
  output.mkdir(parents=True, exist_ok=True)
  subprocess.run(
    [node, "src/cli.mjs", "produce", "--out", str(output)],
    cwd=PACKAGE,
    check=True,
    capture_output=True,
    text=True,
  )
  fixture_names = {
    "runtime_composition_request.v1.json": "default_runtime_composition_request.v1.json",
    "admitted_catalog_lock.v1.json": "default_admitted_catalog_lock.v1.json",
    "default_compatibility_manifest.requested.json": "default_compatibility_manifest.requested.json",
    "default_compatibility_manifest.resolved.json": "default_compatibility_manifest.resolved.json",
    "runtime_profile_projection.v1.json": "default_runtime_profile_projection.v1.json",
    "runtime_package_provenance.v1.json": "default_runtime_package_provenance.v1.json",
    "runtime_package_diagnostics.v1.json": "default_runtime_package_diagnostics.v1.json",
  }
  for output_name, fixture_name in fixture_names.items():
    assert json.loads((output / output_name).read_text(encoding="utf-8")) == json.loads(
      (FIXTURES / fixture_name).read_text(encoding="utf-8")
    )
  metadata = json.loads((output / "producer_metadata.json").read_text(encoding="utf-8"))
  lock = json.loads((output / "admitted_catalog_lock.v1.json").read_text(encoding="utf-8"))
  assert metadata["request_sha256"] == lock["request_sha256"]
  assert metadata["request_lock_binding"] == "validated"
  assert metadata["profile_projection_sha256"] == json.loads(
    (output / "runtime_profile_projection.v1.json").read_text(encoding="utf-8")
  )["projection_sha256"]
  assert metadata["cordis_version"] == "4.0.0-rc.8"
  assert metadata["package_lock_sha256"] == hashlib.sha256(
    (PACKAGE / "package-lock.json").read_bytes()
  ).hexdigest()
  assert metadata["profile_bundle_sha256"] == hashlib.sha256(
    (PACKAGE / "profiles/default-compatibility.bundle.json").read_bytes()
  ).hexdigest()
  assert metadata["profile_module_sha256"] == hashlib.sha256(
    (PACKAGE / "profiles/default-compatibility.mjs").read_bytes()
  ).hexdigest()
  assert metadata["runtime_package_descriptor_sha256"] == hashlib.sha256(
    PACKAGE_DESCRIPTOR.read_bytes()
  ).hexdigest()
  assert metadata["runtime_package_id"] == "builtin.default_compatibility.package"
  assert metadata["runtime_package_version"] == "1.0.0"
  assert metadata["applied_configuration_overlays"] == [
    "builtin.default_compatibility.overlay.default"
  ]
  assert metadata["artifact_source"] == "repository_fixture_bundle"

  provenance = json.loads(
    (output / "runtime_package_provenance.v1.json").read_text(encoding="utf-8")
  )
  diagnostics = json.loads(
    (output / "runtime_package_diagnostics.v1.json").read_text(encoding="utf-8")
  )
  for schema_name, document in (
    ("cordis_runtime_package_provenance.v1.schema.json", provenance),
    ("cordis_runtime_package_diagnostics.v1.schema.json", diagnostics),
  ):
    schema = json.loads((PACKAGE_CONTRACTS / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(document)
  provenance_payload = {
    key: value
    for key, value in provenance.items()
    if key not in {"canonical_json", "provenance_sha256"}
  }
  canonical_provenance = json.dumps(
    provenance_payload,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
  )
  assert provenance["canonical_json"] == canonical_provenance
  assert provenance["provenance_sha256"] == hashlib.sha256(
    canonical_provenance.encode("utf-8")
  ).hexdigest()
  assert metadata["runtime_package_dependency_graph_sha256"] == provenance[
    "dependency_resolution"
  ]["graph_sha256"]
  assert metadata["runtime_package_provenance_sha256"] == provenance["provenance_sha256"]
  assert provenance["runtime_artifacts"] == {
    "request_sha256": metadata["request_sha256"],
    "lock_sha256": metadata["lock_sha256"],
    "profile_projection_sha256": metadata["profile_projection_sha256"],
  }
  assert provenance["producer"]["package_name"] == "@echelon-forge/cordis-runtime"
  assert provenance["producer"]["package_version"] == "0.1.0"
  assert diagnostics["status"] == "ready_for_native_validation"
  assert diagnostics["summary"]["request_lock_binding"] == "validated"
  assert diagnostics["summary"]["provenance_sha256"] == provenance["provenance_sha256"]
  assert str(PACKAGE) not in json.dumps(diagnostics)

  binary = _native_conformance_binary()
  if binary is None:
    if os.environ.get("CI", "").lower() == "true":
      pytest.fail("CI built no ef_cordis_runtime_conformance executable")
    return
  result = subprocess.run(
    [
      str(binary),
      str(output / "runtime_composition_request.v1.json"),
      str(output / "admitted_catalog_lock.v1.json"),
      str(output / "owner_authority_registry.v1.json"),
      str(output / "default_compatibility_manifest.requested.json"),
      str(output / "default_compatibility_manifest.resolved.json"),
      str(output / "runtime_profile_projection.v1.json"),
    ],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )
  assert result.returncode == 0, result.stderr
  assert "native projection and low-level manifest conformance passed" in result.stdout


def test_native_conformance_seam_rejects_tampered_artifacts(tmp_path: Path) -> None:
  node = shutil.which("node")
  binary = _native_conformance_binary()
  dependency = PACKAGE / "node_modules/cordis/package.json"
  if node is None or binary is None or not dependency.is_file():
    if os.environ.get("CI", "").lower() == "true":
      pytest.fail("CI lacks Cordis package or native conformance binary")
    pytest.skip("Cordis package or native conformance binary is not available locally")

  output = tmp_path / "default-profile"
  subprocess.run(
    [node, "src/cli.mjs", "produce", "--out", str(output)],
    cwd=PACKAGE,
    check=True,
    capture_output=True,
    text=True,
  )
  def run_conformance(
    lock_path: Path,
    requested_path: Path,
    resolved_path: Path,
    projection_path: Path | None = None,
  ) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
      [
        str(binary),
        str(output / "runtime_composition_request.v1.json"),
        str(lock_path),
        str(output / "owner_authority_registry.v1.json"),
        str(requested_path),
        str(resolved_path),
        str(projection_path or output / "runtime_profile_projection.v1.json"),
      ],
      cwd=REPO_ROOT,
      check=False,
      capture_output=True,
      text=True,
    )

  def rewrite_projection_identity(candidate: dict, path: Path) -> None:
    payload = {
      key: value
      for key, value in candidate.items()
      if key not in {"canonical_json", "projection_sha256"}
    }
    canonical_json = json.dumps(
      payload,
      ensure_ascii=False,
      separators=(",", ":"),
      sort_keys=True,
    )
    candidate["canonical_json"] = canonical_json
    candidate["projection_sha256"] = hashlib.sha256(
      canonical_json.encode("utf-8")
    ).hexdigest()
    path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")

  lock = json.loads((output / "admitted_catalog_lock.v1.json").read_text(encoding="utf-8"))
  lock["lock_version"] = "not-semver"
  tampered_lock = tmp_path / "tampered-lock.json"
  tampered_lock.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
  result = run_conformance(
    tampered_lock,
    output / "default_compatibility_manifest.requested.json",
    output / "default_compatibility_manifest.resolved.json",
  )
  assert result.returncode != 0
  assert "projection.invalid_version" in result.stderr

  requested = json.loads((output / "default_compatibility_manifest.requested.json").read_text(encoding="utf-8"))
  requested["backend_request"]["provider_id"] = "attacker.unadmitted"
  tampered_requested = tmp_path / "tampered-requested-manifest.json"
  tampered_requested.write_text(json.dumps(requested, indent=2) + "\n", encoding="utf-8")
  result = run_conformance(
    output / "admitted_catalog_lock.v1.json",
    tampered_requested,
    output / "default_compatibility_manifest.resolved.json",
  )
  assert result.returncode != 0
  assert "requested and resolved manifest payloads differ" in result.stderr

  profile_projection = json.loads(
    (output / "runtime_profile_projection.v1.json").read_text(encoding="utf-8")
  )
  profile_projection["compatibility_claims"][0] = "attacker.claim"
  tampered_projection = tmp_path / "tampered-profile-projection.json"
  tampered_projection.write_text(
    json.dumps(profile_projection, indent=2) + "\n", encoding="utf-8"
  )
  result = run_conformance(
    output / "admitted_catalog_lock.v1.json",
    output / "default_compatibility_manifest.requested.json",
    output / "default_compatibility_manifest.resolved.json",
    tampered_projection,
  )
  assert result.returncode != 0
  assert "profile projection compatibility claims mismatch" in result.stderr

  profile_projection = json.loads(
    (output / "runtime_profile_projection.v1.json").read_text(encoding="utf-8")
  )
  profile_projection["canonical_json"] = "{}"
  tampered_projection = tmp_path / "tampered-profile-canonical-json.json"
  tampered_projection.write_text(
    json.dumps(profile_projection, indent=2) + "\n", encoding="utf-8"
  )
  result = run_conformance(
    output / "admitted_catalog_lock.v1.json",
    output / "default_compatibility_manifest.requested.json",
    output / "default_compatibility_manifest.resolved.json",
    tampered_projection,
  )
  assert result.returncode != 0
  assert "profile projection canonical bytes mismatch" in result.stderr

  profile_projection = json.loads(
    (output / "runtime_profile_projection.v1.json").read_text(encoding="utf-8")
  )
  profile_projection["projection_sha256"] = "0" * 64
  tampered_projection = tmp_path / "tampered-profile-identity.json"
  tampered_projection.write_text(
    json.dumps(profile_projection, indent=2) + "\n", encoding="utf-8"
  )
  result = run_conformance(
    output / "admitted_catalog_lock.v1.json",
    output / "default_compatibility_manifest.requested.json",
    output / "default_compatibility_manifest.resolved.json",
    tampered_projection,
  )
  assert result.returncode != 0
  assert "profile projection identity mismatch" in result.stderr

  profile_projection = json.loads(
    (output / "runtime_profile_projection.v1.json").read_text(encoding="utf-8")
  )
  profile_projection["catalog_entries"].reverse()
  tampered_projection = tmp_path / "tampered-profile-catalog-order.json"
  rewrite_projection_identity(profile_projection, tampered_projection)
  result = run_conformance(
    output / "admitted_catalog_lock.v1.json",
    output / "default_compatibility_manifest.requested.json",
    output / "default_compatibility_manifest.resolved.json",
    tampered_projection,
  )
  assert result.returncode != 0
  assert "profile projection catalog admission mismatch" in result.stderr

  profile_projection = json.loads(
    (output / "runtime_profile_projection.v1.json").read_text(encoding="utf-8")
  )
  system_entry = next(
    entry for entry in profile_projection["catalog_entries"] if entry["category"] == "system"
  )
  system_entry["capabilities"].reverse()
  tampered_projection = tmp_path / "tampered-profile-capability-order.json"
  rewrite_projection_identity(profile_projection, tampered_projection)
  result = run_conformance(
    output / "admitted_catalog_lock.v1.json",
    output / "default_compatibility_manifest.requested.json",
    output / "default_compatibility_manifest.resolved.json",
    tampered_projection,
  )
  assert result.returncode != 0
  assert "profile projection catalog admission mismatch" in result.stderr

  request = json.loads((output / "runtime_composition_request.v1.json").read_text(encoding="utf-8"))
  request["requested_profile"]["profile_version"] = "2.0.0"
  lock = json.loads((output / "admitted_catalog_lock.v1.json").read_text(encoding="utf-8"))
  lock["request_sha256"] = request_contract.request_identity(request)
  normalized_lock = request_contract.normalize_lock(lock)
  lock_payload = request_contract._lock_payload(normalized_lock)
  lock["canonical_json"] = composition_contract.canonical_json_bytes(lock_payload).decode("utf-8")
  lock["lock_sha256"] = composition_contract.canonical_sha256(lock_payload)
  requested = json.loads(
    (output / "default_compatibility_manifest.requested.json").read_text(encoding="utf-8")
  )
  requested["requested_profile"]["profile_version"] = "2.0.0"
  requested = composition_contract.normalize_manifest(requested)
  resolved = composition_contract.resolve_manifest(requested)
  profile_projection = json.loads(
    (output / "runtime_profile_projection.v1.json").read_text(encoding="utf-8")
  )
  profile_projection["requested_profile"]["profile_version"] = "2.0.0"
  profile_projection["request_sha256"] = lock["request_sha256"]
  profile_projection["lock_sha256"] = lock["lock_sha256"]
  tampered_request = tmp_path / "tampered-profile-version-request.json"
  tampered_lock = tmp_path / "tampered-profile-version-lock.json"
  tampered_requested = tmp_path / "tampered-profile-version-requested.json"
  tampered_resolved = tmp_path / "tampered-profile-version-resolved.json"
  tampered_projection = tmp_path / "tampered-profile-version-projection.json"
  tampered_request.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
  tampered_lock.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
  tampered_requested.write_text(json.dumps(requested, indent=2) + "\n", encoding="utf-8")
  tampered_resolved.write_text(json.dumps(resolved, indent=2) + "\n", encoding="utf-8")
  rewrite_projection_identity(profile_projection, tampered_projection)
  result = subprocess.run(
    [
      str(binary),
      str(tampered_request),
      str(tampered_lock),
      str(output / "owner_authority_registry.v1.json"),
      str(tampered_requested),
      str(tampered_resolved),
      str(tampered_projection),
    ],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )
  assert result.returncode != 0
  assert "profile" in result.stderr

  resolved = json.loads((output / "default_compatibility_manifest.resolved.json").read_text(encoding="utf-8"))
  resolved["resolved_manifest_sha256"] = "0" * 64
  tampered_resolved = tmp_path / "tampered-resolved-manifest.json"
  tampered_resolved.write_text(json.dumps(resolved, indent=2) + "\n", encoding="utf-8")
  result = run_conformance(
    output / "admitted_catalog_lock.v1.json",
    output / "default_compatibility_manifest.requested.json",
    tampered_resolved,
  )
  assert result.returncode != 0
