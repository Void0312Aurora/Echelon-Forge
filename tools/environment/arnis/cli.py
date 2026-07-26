from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Sequence


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from tools.environment.arnis.bootstrap import (  # type: ignore[no-redef]
        ArnisBootstrapError,
        prepare_arnis,
    )
else:
    from .bootstrap import ArnisBootstrapError, prepare_arnis


_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_LOCK_PATH = Path(__file__).resolve().parent / "upstream.lock.json"


class ArnisCliError(RuntimeError):
    pass


def _sha256(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArnisCliError(f"failed to read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ArnisCliError(f"{path} must contain a JSON object")
    return value


def _pinned_patch_sha256() -> str:
    lock = _load_json(_LOCK_PATH)
    patch = lock.get("patch")
    digest = patch.get("sha256") if isinstance(patch, dict) else None
    if not isinstance(digest, str) or not _HEX64.fullmatch(digest):
        raise ArnisCliError("Arnis upstream lock requires a valid patch SHA-256")
    return digest


def _resolve_from_request(request_path: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ArnisCliError("request source path must be a non-empty string")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = request_path.parent / path
    return path.resolve()


def _phase1_export_command(
    request_path: Path,
    output_dir: Path,
    binary: Path,
) -> list[str]:
    request = _load_json(request_path)
    if request.get("contract_version") != "arnis_cmo_phase1_request.v1":
        raise ArnisCliError("unsupported Arnis phase 1 request contract")
    source = request.get("source_input")
    bbox = request.get("bbox_wgs84")
    options = request.get("options")
    required = request.get("required_actual_sources")
    if not all(isinstance(value, dict) for value in (source, bbox, options, required)):
        raise ArnisCliError(
            "request requires source_input, bbox_wgs84, options, and required_actual_sources"
        )
    source_path = _resolve_from_request(request_path, source["path"])
    actual_sha, actual_size = _sha256(source_path)
    if actual_sha != source.get("sha256") or actual_size != source.get("byte_length"):
        raise ArnisCliError("frozen OSM input does not match request checksum or byte length")
    expected_options = {
        "terrain": True,
        "projection": "web_mercator",
        "scale": 1.0,
        "rotation_deg": 0.0,
        "overture": False,
    }
    for key, expected in expected_options.items():
        if options.get(key) != expected:
            raise ArnisCliError(f"phase 1 request requires options.{key}={expected!r}")
    provider = str(required.get("elevation_provider") or "").strip()
    if not provider:
        raise ArnisCliError("phase 1 request requires an actual elevation provider")
    bbox_text = ",".join(str(bbox[key]) for key in ("min_lat", "min_lon", "max_lat", "max_lon"))
    return [
        str(binary),
        "--bbox",
        bbox_text,
        "--file",
        str(source_path),
        "--cmo-output-dir",
        str(output_dir),
        "--cmo-require-elevation-provider",
        provider,
        "--cmo-exporter-patch-sha256",
        _pinned_patch_sha256(),
        "--terrain",
        "--projection",
        "web_mercator",
        "--scale",
        "1",
        "--rotation",
        "0",
        "--overture=false",
        "--no-3d",
    ]


def _safe_checksum_path(root: Path, relative_path: str) -> Path:
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts or "\\" in relative_path:
        raise ArnisCliError(f"unsafe checksum path: {relative_path!r}")
    resolved = root.joinpath(*pure.parts).resolve(strict=True)
    root_resolved = root.resolve(strict=True)
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ArnisCliError(f"checksum path escapes bundle: {relative_path!r}")
    return resolved


def _verify_checksums(bundle_root: Path) -> dict[str, str]:
    checksum_path = bundle_root / "checksums.sha256"
    try:
        lines = checksum_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ArnisCliError(f"failed to read {checksum_path}: {exc}") from exc
    if not lines:
        raise ArnisCliError("checksums.sha256 is empty")
    verified: dict[str, str] = {}
    for line in lines:
        digest, separator, relative_path = line.partition("  ")
        if not separator or not _HEX64.fullmatch(digest) or not relative_path:
            raise ArnisCliError(f"invalid checksum line: {line!r}")
        path = _safe_checksum_path(bundle_root, relative_path)
        actual, _ = _sha256(path)
        if actual != digest:
            raise ArnisCliError(f"checksum mismatch: {relative_path}")
        if relative_path in verified:
            raise ArnisCliError(f"duplicate checksum path: {relative_path}")
        verified[relative_path] = digest
    return verified


def _verify_bundle(bundle_root: Path) -> dict[str, Any]:
    checksums = _verify_checksums(bundle_root)
    bundle = _load_json(bundle_root / "bundle.json")
    lineage = bundle.get("lineage")
    if not isinstance(lineage, dict) or lineage.get("contract") != "arnis_continuous_metric.v1":
        raise ArnisCliError("CMO bundle is missing required continuous metric lineage")
    generator = bundle.get("generator")
    if not isinstance(generator, dict):
        raise ArnisCliError("CMO bundle is missing generator identity")
    if generator.get("exporter_patch_id") != "0001-cmo-continuous-bundle-export-v1":
        raise ArnisCliError("CMO bundle was not produced by the continuous exporter patch")
    if generator.get("exporter_patch_sha256") != _pinned_patch_sha256():
        raise ArnisCliError("CMO bundle exporter patch SHA-256 does not match the pinned adapter")
    from python.scenario.environment_substrate import import_arnis_environment_bundle

    result = import_arnis_environment_bundle(bundle_root)
    if not result.valid or result.manifest is None:
        message = result.errors[0] if result.errors else result.rejection_reason
        raise ArnisCliError(f"CMO bundle contract rejection: {message}")
    counts = Counter(item.catalog_ref for item in result.manifest.objects)
    return {
        "bundle_digest_sha256": result.bundle_digest_sha256,
        "catalog_counts": dict(sorted(counts.items())),
        "checksum_file_count": len(checksums),
        "manifest_id": result.manifest.manifest_id,
        "object_count": len(result.manifest.objects),
        "valid": True,
    }


def _verify_request_expectations(
    request_path: Path,
    bundle_root: Path,
    verification: dict[str, Any],
) -> None:
    request = _load_json(request_path)
    bundle = _load_json(bundle_root / "bundle.json")
    expected_generator = request.get("generator")
    if isinstance(expected_generator, dict):
        actual_generator = bundle.get("generator")
        if not isinstance(actual_generator, dict):
            raise ArnisCliError("generated bundle is missing generator identity")
        for key in (
            "id",
            "version",
            "upstream_revision",
            "exporter_version",
            "exporter_patch_id",
            "exporter_patch_sha256",
        ):
            if key in expected_generator and actual_generator.get(key) != expected_generator[key]:
                raise ArnisCliError(f"generated bundle generator mismatch for {key}")
    expected = request.get("expected")
    if not isinstance(expected, dict):
        return
    expected_digest = expected.get("bundle_manifest_sha256")
    if expected_digest and verification["bundle_digest_sha256"] != expected_digest:
        raise ArnisCliError("generated bundle does not match the request's retained bundle SHA-256")
    expected_counts = expected.get("feature_counts")
    if isinstance(expected_counts, dict):
        catalog_counts = verification["catalog_counts"]
        actual_counts = {
            "buildings": catalog_counts.get("catalog:arnis_building", 0),
            "hydrology": catalog_counts.get("catalog:arnis_hydrology", 0),
            "roads": catalog_counts.get("catalog:arnis_road", 0),
        }
        if actual_counts != expected_counts:
            raise ArnisCliError(
                f"generated feature counts differ from retained expectations: {actual_counts}"
            )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, run, and verify the pinned Arnis CMO adapter"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="build and install pinned arnis-cmo")
    prepare.add_argument("--source-dir", type=Path)
    prepare.add_argument("--build-dir", type=Path)
    prepare.add_argument("--install-dir", type=Path)
    prepare.add_argument("--command-link", type=Path)
    export = subparsers.add_parser("export", help="export a frozen phase 1 request")
    export.add_argument("--request", type=Path, required=True)
    export.add_argument("--output-dir", type=Path, required=True)
    export.add_argument(
        "--binary",
        type=Path,
        default=Path.home() / ".local" / "bin" / "arnis-cmo",
    )
    verify = subparsers.add_parser("verify", help="verify checksums and import contract")
    verify.add_argument("--bundle", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            payload = prepare_arnis(
                source_dir=args.source_dir,
                build_dir=args.build_dir,
                install_dir=args.install_dir,
                command_link=args.command_link,
            )
        elif args.command == "export":
            request = args.request.expanduser().resolve()
            output = args.output_dir.expanduser().resolve()
            binary = args.binary.expanduser().resolve()
            if not binary.is_file():
                raise ArnisCliError(f"arnis-cmo binary is missing: {binary}")
            if output.exists() and (not output.is_dir() or any(output.iterdir())):
                raise ArnisCliError(f"output directory must be absent or empty: {output}")
            command = _phase1_export_command(request, output, binary)
            subprocess.run(command, check=True)
            payload = _verify_bundle(output)
            _verify_request_expectations(request, output, payload)
        else:
            payload = _verify_bundle(args.bundle.expanduser().resolve())
    except (ArnisBootstrapError, ArnisCliError, OSError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
