from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from .catalog import (
    EnvironmentCatalogDescriptor,
    default_environment_catalog_descriptors,
    validate_environment_catalog_admission,
    validate_environment_catalog_descriptors,
)
from .components import HELD_CAPABILITY_CLAIMS
from .manifest import (
    EnvironmentComponent,
    EnvironmentGenerationMetadata,
    EnvironmentGeometry,
    EnvironmentManifest,
    EnvironmentObject,
    EnvironmentRegionExtent,
)
from .validation import validate_environment_manifest


ENVIRONMENT_SUBSTRATE_GENERATOR_CONTRACT_VERSION = (
    "environment_substrate.g0_k.generator_catalog.v1"
)

ENVIRONMENT_GENERATION_KINDS = ("environment_manifest",)


def _normalized_text(value: Any) -> str:
    return str(value or "").strip()


def _normalized_unique_texts(values: Iterable[Any]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        text = _normalized_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return tuple(sorted(normalized))


def canonical_environment_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


@dataclass(frozen=True)
class EnvironmentGeneratorEvidenceRef:
    ref_id: str
    evidence_kind: str
    provenance_label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref_id", _normalized_text(self.ref_id))
        object.__setattr__(self, "evidence_kind", _normalized_text(self.evidence_kind))
        object.__setattr__(
            self,
            "provenance_label",
            _normalized_text(self.provenance_label),
        )

    def to_metadata(self) -> dict[str, str]:
        return {
            "ref_id": self.ref_id,
            "evidence_kind": self.evidence_kind,
            "provenance_label": self.provenance_label,
        }


@dataclass(frozen=True)
class EnvironmentTileScheme:
    tile_scheme_id: str
    origin_x: float
    origin_y: float
    tile_width_m: float
    tile_height_m: float
    columns: int
    rows: int
    halo_m: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile_scheme_id", _normalized_text(self.tile_scheme_id))
        object.__setattr__(self, "origin_x", float(self.origin_x))
        object.__setattr__(self, "origin_y", float(self.origin_y))
        object.__setattr__(self, "tile_width_m", float(self.tile_width_m))
        object.__setattr__(self, "tile_height_m", float(self.tile_height_m))
        object.__setattr__(self, "columns", int(self.columns))
        object.__setattr__(self, "rows", int(self.rows))
        object.__setattr__(self, "halo_m", float(self.halo_m))

    def tile_id(self, row: int, column: int) -> str:
        return f"tile:{self.tile_scheme_id}:r{int(row):04d}:c{int(column):04d}"

    def tile_ids(self) -> tuple[str, ...]:
        return tuple(
            self.tile_id(row, column)
            for row in range(self.rows)
            for column in range(self.columns)
        )

    def tile_extent(self, tile_id: str) -> EnvironmentRegionExtent:
        prefix = f"tile:{self.tile_scheme_id}:"
        if not tile_id.startswith(prefix):
            raise ValueError("tile_id does not belong to this tile scheme")
        parts = tile_id.removeprefix(prefix).split(":")
        if len(parts) != 2 or not parts[0].startswith("r") or not parts[1].startswith("c"):
            raise ValueError("tile_id must include row and column tokens")
        row = int(parts[0].removeprefix("r"))
        column = int(parts[1].removeprefix("c"))
        if row < 0 or column < 0 or row >= self.rows or column >= self.columns:
            raise ValueError("tile_id is outside this tile scheme")
        min_x = self.origin_x + column * self.tile_width_m
        min_y = self.origin_y + row * self.tile_height_m
        return EnvironmentRegionExtent(
            min_x,
            min_y,
            min_x + self.tile_width_m,
            min_y + self.tile_height_m,
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "tile_scheme_id": self.tile_scheme_id,
            "origin_x": float(self.origin_x),
            "origin_y": float(self.origin_y),
            "tile_width_m": float(self.tile_width_m),
            "tile_height_m": float(self.tile_height_m),
            "columns": int(self.columns),
            "rows": int(self.rows),
            "halo_m": float(self.halo_m),
            "tile_ids": list(self.tile_ids()) if self.columns > 0 and self.rows > 0 else [],
        }


@dataclass(frozen=True)
class EnvironmentGeneratorRequest:
    request_id: str
    generator_id: str
    generator_version: str
    deterministic_seed: int
    coordinate_frame: str
    region_extent: EnvironmentRegionExtent
    tile_scheme: EnvironmentTileScheme
    catalog_refs: tuple[str, ...]
    evidence_refs: tuple[EnvironmentGeneratorEvidenceRef, ...]
    output_manifest_id: str
    generation_kind: str = "environment_manifest"
    request_version: str = "1"
    contract_version: str = ENVIRONMENT_SUBSTRATE_GENERATOR_CONTRACT_VERSION
    branch_scope: tuple[str, ...] = ("terrain",)
    realism_target: str = "G1"
    constraints: dict[str, Any] = field(default_factory=dict)
    source_inputs: tuple[str, ...] = ()
    capability_claims: tuple[str, ...] = ()
    no_held_capability_release: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _normalized_text(self.request_id))
        object.__setattr__(self, "generator_id", _normalized_text(self.generator_id))
        object.__setattr__(
            self,
            "generator_version",
            _normalized_text(self.generator_version),
        )
        object.__setattr__(self, "deterministic_seed", int(self.deterministic_seed))
        object.__setattr__(
            self,
            "coordinate_frame",
            _normalized_text(self.coordinate_frame),
        )
        extent = self.region_extent
        if isinstance(extent, dict):
            extent = EnvironmentRegionExtent(**extent)
        if not isinstance(extent, EnvironmentRegionExtent):
            raise TypeError("region_extent must be EnvironmentRegionExtent or dict")
        object.__setattr__(self, "region_extent", extent)
        tile_scheme = self.tile_scheme
        if isinstance(tile_scheme, dict):
            tile_scheme = EnvironmentTileScheme(**tile_scheme)
        if not isinstance(tile_scheme, EnvironmentTileScheme):
            raise TypeError("tile_scheme must be EnvironmentTileScheme or dict")
        object.__setattr__(self, "tile_scheme", tile_scheme)
        object.__setattr__(self, "catalog_refs", _normalized_unique_texts(self.catalog_refs))
        evidence_refs = []
        for ref in self.evidence_refs:
            if isinstance(ref, EnvironmentGeneratorEvidenceRef):
                evidence_refs.append(ref)
            elif isinstance(ref, dict):
                evidence_refs.append(EnvironmentGeneratorEvidenceRef(**ref))
            else:
                raise TypeError(
                    "evidence_refs entries must be EnvironmentGeneratorEvidenceRef or dict"
                )
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(
                sorted(
                    evidence_refs,
                    key=lambda ref: (
                        ref.evidence_kind,
                        ref.ref_id,
                        ref.provenance_label,
                    ),
                )
            ),
        )
        object.__setattr__(
            self,
            "output_manifest_id",
            _normalized_text(self.output_manifest_id),
        )
        object.__setattr__(
            self,
            "generation_kind",
            _normalized_text(self.generation_kind),
        )
        object.__setattr__(
            self,
            "request_version",
            _normalized_text(self.request_version),
        )
        object.__setattr__(
            self,
            "contract_version",
            _normalized_text(self.contract_version),
        )
        object.__setattr__(self, "branch_scope", _normalized_unique_texts(self.branch_scope))
        object.__setattr__(self, "realism_target", _normalized_text(self.realism_target))
        object.__setattr__(self, "constraints", json.loads(json.dumps(self.constraints)))
        object.__setattr__(self, "source_inputs", _normalized_unique_texts(self.source_inputs))
        object.__setattr__(
            self,
            "capability_claims",
            _normalized_unique_texts(self.capability_claims),
        )
        object.__setattr__(
            self,
            "no_held_capability_release",
            bool(self.no_held_capability_release),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "request_version": self.request_version,
            "contract_version": self.contract_version,
            "generation_kind": self.generation_kind,
            "generator_id": self.generator_id,
            "generator_version": self.generator_version,
            "deterministic_seed": int(self.deterministic_seed),
            "coordinate_frame": self.coordinate_frame,
            "region_extent": self.region_extent.to_metadata(),
            "tile_scheme": self.tile_scheme.to_metadata(),
            "branch_scope": list(self.branch_scope),
            "catalog_refs": list(self.catalog_refs),
            "realism_target": self.realism_target,
            "constraints": json.loads(json.dumps(self.constraints, sort_keys=True)),
            "source_inputs": list(self.source_inputs),
            "evidence_refs": [ref.to_metadata() for ref in self.evidence_refs],
            "output_manifest_id": self.output_manifest_id,
            "capability_claims": list(self.capability_claims),
            "no_held_capability_release": bool(self.no_held_capability_release),
        }


@dataclass(frozen=True)
class EnvironmentGeneratorValidationResult:
    valid: bool
    fail_closed: bool
    rejection_reason: str
    errors: tuple[str, ...]


def _first_failure(failures: list[tuple[str, str]]) -> EnvironmentGeneratorValidationResult:
    if not failures:
        return EnvironmentGeneratorValidationResult(
            valid=True,
            fail_closed=False,
            rejection_reason="",
            errors=(),
        )
    return EnvironmentGeneratorValidationResult(
        valid=False,
        fail_closed=True,
        rejection_reason=failures[0][0],
        errors=tuple(message for _, message in failures),
    )


def _finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def validate_environment_generator_request(
    request: EnvironmentGeneratorRequest,
    catalogs: Iterable[EnvironmentCatalogDescriptor] = (),
) -> EnvironmentGeneratorValidationResult:
    if not isinstance(request, EnvironmentGeneratorRequest):
        raise TypeError("request must be an EnvironmentGeneratorRequest")

    failures: list[tuple[str, str]] = []
    if not request.request_id:
        failures.append(
            (
                "environment_substrate_generator_request_id_required",
                "request_id is required",
            )
        )
    if not request.contract_version:
        failures.append(
            (
                "environment_substrate_generator_contract_version_required",
                "contract_version is required",
            )
        )
    if request.generation_kind not in ENVIRONMENT_GENERATION_KINDS:
        failures.append(
            (
                "environment_substrate_generator_kind_required",
                "generation_kind must be environment_manifest",
            )
        )
    if not request.generator_id:
        failures.append(
            ("environment_substrate_generator_id_required", "generator_id is required")
        )
    if not request.generator_version:
        failures.append(
            (
                "environment_substrate_generator_version_required",
                "generator_version is required",
            )
        )
    if type(request.deterministic_seed) is not int or request.deterministic_seed < 0:
        failures.append(
            (
                "environment_substrate_generator_seed_required",
                "deterministic_seed must be a non-negative integer",
            )
        )
    if not request.coordinate_frame:
        failures.append(
            (
                "environment_substrate_coordinate_frame_required",
                "coordinate_frame is required",
            )
        )
    if not request.output_manifest_id:
        failures.append(
            (
                "environment_substrate_manifest_id_required",
                "output_manifest_id is required",
            )
        )
    if not request.source_inputs:
        failures.append(
            (
                "environment_substrate_generator_provenance_required",
                "source_inputs are required",
            )
        )
    if not request.evidence_refs:
        failures.append(
            (
                "environment_substrate_generator_evidence_required",
                "evidence_refs are required",
            )
        )
    for ref in request.evidence_refs:
        if not ref.ref_id or not ref.evidence_kind or not ref.provenance_label:
            failures.append(
                (
                    "environment_substrate_generator_evidence_required",
                    "evidence refs require ref_id, evidence_kind, and provenance_label",
                )
            )
            break
    if not request.catalog_refs:
        failures.append(
            (
                "environment_substrate_catalog_ref_unknown",
                "catalog_refs must not be empty",
            )
        )
    if not request.branch_scope:
        failures.append(
            (
                "environment_substrate_generator_branch_scope_required",
                "branch_scope must not be empty",
            )
        )
    catalog_map = {catalog.catalog_id: catalog for catalog in catalogs}
    if catalog_map:
        unknown_catalogs = sorted(set(request.catalog_refs) - set(catalog_map))
        if unknown_catalogs:
            failures.append(
                (
                    "environment_substrate_catalog_ref_unknown",
                    f"request references unknown catalogs {unknown_catalogs}",
                )
            )
        requested_catalogs = [
            catalog_map[catalog_ref]
            for catalog_ref in request.catalog_refs
            if catalog_ref in catalog_map
        ]
        out_of_scope = sorted(
            {
                membership.branch_id
                for catalog in requested_catalogs
                for membership in catalog.branch_membership
                if membership.branch_id not in request.branch_scope
            }
        )
        if out_of_scope:
            failures.append(
                (
                    "environment_substrate_generator_branch_scope_mismatch",
                    f"catalogs require branches outside request scope {out_of_scope}",
                )
            )
    if not request.tile_scheme.tile_scheme_id:
        failures.append(
            (
                "environment_substrate_tile_scheme_required",
                "tile_scheme_id is required",
            )
        )
    if (
        request.tile_scheme.columns <= 0
        or request.tile_scheme.rows <= 0
        or request.tile_scheme.tile_width_m <= 0
        or request.tile_scheme.tile_height_m <= 0
    ):
        failures.append(
            (
                "environment_substrate_tile_scheme_required",
                "tile dimensions and grid dimensions must be positive",
            )
        )
    extent_values = (
        request.region_extent.min_x,
        request.region_extent.min_y,
        request.region_extent.max_x,
        request.region_extent.max_y,
        request.tile_scheme.origin_x,
        request.tile_scheme.origin_y,
    )
    if not all(_finite_number(value) for value in extent_values):
        failures.append(
            (
                "environment_substrate_tile_extent_invalid",
                "region and tile coordinates must be finite",
            )
        )
    else:
        expected_max_x = (
            request.tile_scheme.origin_x
            + request.tile_scheme.columns * request.tile_scheme.tile_width_m
        )
        expected_max_y = (
            request.tile_scheme.origin_y
            + request.tile_scheme.rows * request.tile_scheme.tile_height_m
        )
        if (
            not math.isclose(request.region_extent.min_x, request.tile_scheme.origin_x)
            or not math.isclose(request.region_extent.min_y, request.tile_scheme.origin_y)
            or not math.isclose(request.region_extent.max_x, expected_max_x)
            or not math.isclose(request.region_extent.max_y, expected_max_y)
        ):
            failures.append(
                (
                    "environment_substrate_tile_extent_invalid",
                    "tile grid must exactly cover region_extent",
                )
            )
    held_claims = sorted(
        claim for claim in request.capability_claims if claim in HELD_CAPABILITY_CLAIMS
    )
    if held_claims or not request.no_held_capability_release:
        failures.append(
            (
                "environment_substrate_held_capability_claim",
                f"request claims held capabilities {held_claims}",
            )
        )

    return _first_failure(failures)


def derive_environment_seed(
    request: EnvironmentGeneratorRequest,
    *,
    stage_id: str,
    tile_id: str,
    catalog_ref: str,
    local_key: str,
) -> int:
    seed_material = {
        "request": request.to_metadata(),
        "stage_id": _normalized_text(stage_id),
        "tile_id": _normalized_text(tile_id),
        "catalog_ref": _normalized_text(catalog_ref),
        "local_key": _normalized_text(local_key),
    }
    digest = hashlib.sha256(canonical_environment_bytes(seed_material)).hexdigest()
    return int(digest[:16], 16)


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-")


def _geometry_for_catalog(
    geometry_type: str,
    tile_extent: EnvironmentRegionExtent,
    local_seed: int,
) -> EnvironmentGeometry:
    span_x = tile_extent.max_x - tile_extent.min_x
    span_y = tile_extent.max_y - tile_extent.min_y
    frac_x = 0.25 + ((local_seed % 1000) / 1000.0) * 0.5
    frac_y = 0.25 + (((local_seed // 1000) % 1000) / 1000.0) * 0.5
    x = tile_extent.min_x + span_x * frac_x
    y = tile_extent.min_y + span_y * frac_y
    size_x = max(1.0, min(span_x * 0.1, 80.0))
    size_y = max(1.0, min(span_y * 0.1, 80.0))
    if geometry_type == "rect":
        return EnvironmentGeometry(
            "rect",
            {
                "x": round(x, 6),
                "y": round(y, 6),
                "width": round(size_x, 6),
                "length": round(size_y, 6),
                "heading": float(local_seed % 360),
            },
        )
    if geometry_type == "polygon":
        half_x = size_x / 2.0
        half_y = size_y / 2.0
        return EnvironmentGeometry(
            "polygon",
            {
                "points": [
                    [round(x - half_x, 6), round(y - half_y, 6)],
                    [round(x + half_x, 6), round(y - half_y, 6)],
                    [round(x + half_x, 6), round(y + half_y, 6)],
                    [round(x - half_x, 6), round(y + half_y, 6)],
                ]
            },
        )
    if geometry_type == "line":
        return EnvironmentGeometry(
            "line",
            {
                "points": [
                    [round(x - size_x / 2.0, 6), round(y, 6)],
                    [round(x + size_x / 2.0, 6), round(y, 6)],
                ]
            },
        )
    return EnvironmentGeometry("point", {"x": round(x, 6), "y": round(y, 6)})


def build_deterministic_generated_environment_manifest(
    request: EnvironmentGeneratorRequest,
    catalogs: Iterable[EnvironmentCatalogDescriptor] = (),
) -> EnvironmentManifest:
    catalog_tuple = tuple(catalogs or default_environment_catalog_descriptors())
    catalog_validation = validate_environment_catalog_descriptors(catalog_tuple)
    if not catalog_validation.valid:
        raise ValueError(catalog_validation.rejection_reason)
    request_validation = validate_environment_generator_request(request, catalog_tuple)
    if not request_validation.valid:
        raise ValueError(request_validation.rejection_reason)

    catalog_map = {catalog.catalog_id: catalog for catalog in catalog_tuple}
    tile_ids = request.tile_scheme.tile_ids()
    objects: list[EnvironmentObject] = []
    for index, catalog_ref in enumerate(request.catalog_refs):
        catalog = catalog_map[catalog_ref]
        tile_id = tile_ids[index % len(tile_ids)]
        local_seed = derive_environment_seed(
            request,
            stage_id="g0-k-fixture",
            tile_id=tile_id,
            catalog_ref=catalog_ref,
            local_key=str(index),
        )
        tile_extent = request.tile_scheme.tile_extent(tile_id)
        catalog_slug = _slug(catalog_ref.removeprefix("catalog:"))
        object_id = f"envobj:{_slug(request.request_id)}:{catalog_slug}:{tile_id.split(':')[-2]}-{tile_id.split(':')[-1]}"
        copied_components = []
        for component in catalog.component_templates:
            copied_components.append(
                EnvironmentComponent(
                    component_id=f"component:{object_id}:{_slug(component.family)}",
                    family=component.family,
                    schema_version=component.schema_version,
                    attributes=component.attributes,
                )
            )
        provenance = {
            "request_id": request.request_id,
            "generator_id": request.generator_id,
            "generator_version": request.generator_version,
            "root_seed": int(request.deterministic_seed),
            "derived_seed": int(local_seed),
            "tile_id": tile_id,
            "covered_tile_ids": [tile_id],
            "catalog_ref": catalog.catalog_id,
            "catalog_schema_version": catalog.schema_version,
            "stage_id": "g0-k-fixture",
            "source_inputs": list(request.source_inputs),
            "evidence_refs": [ref.to_metadata() for ref in request.evidence_refs],
            "no_held_capability_release": True,
        }
        objects.append(
            EnvironmentObject(
                object_id=object_id,
                catalog_ref=catalog.catalog_id,
                geometry=_geometry_for_catalog(
                    catalog.geometry_types[0],
                    tile_extent,
                    local_seed,
                ),
                branch_membership=catalog.branch_membership,
                components=tuple(copied_components),
                layer_membership=catalog.layer_membership,
                projection_profile_ids=catalog.projection_profile_refs,
                properties={},
                provenance=provenance,
            )
        )

    manifest = EnvironmentManifest(
        manifest_id=request.output_manifest_id,
        schema_version="1",
        coordinate_frame=request.coordinate_frame,
        region_extent=request.region_extent,
        generation=EnvironmentGenerationMetadata(
            generator_id=request.generator_id,
            generator_version=request.generator_version,
            deterministic_seed=request.deterministic_seed,
            source_inputs=tuple(
                list(request.source_inputs)
                + [ref.ref_id for ref in request.evidence_refs]
            ),
        ),
        catalogs=request.catalog_refs,
        objects=tuple(sorted(objects, key=lambda item: item.object_id)),
        validation_evidence=(
            {
                "kind": "environment_generator_request",
                "request_id": request.request_id,
                "contract_version": request.contract_version,
                "tile_scheme": request.tile_scheme.to_metadata(),
                "no_held_capability_release": True,
            },
        ),
        capability_claims=(),
    )
    manifest_validation = validate_environment_manifest(manifest)
    if not manifest_validation.valid:
        raise ValueError(manifest_validation.rejection_reason)
    admission_validation = validate_environment_catalog_admission(manifest, catalog_tuple)
    if not admission_validation.valid:
        raise ValueError(admission_validation.rejection_reason)
    return manifest


__all__ = [
    "ENVIRONMENT_GENERATION_KINDS",
    "ENVIRONMENT_SUBSTRATE_GENERATOR_CONTRACT_VERSION",
    "EnvironmentGeneratorEvidenceRef",
    "EnvironmentGeneratorRequest",
    "EnvironmentGeneratorValidationResult",
    "EnvironmentTileScheme",
    "build_deterministic_generated_environment_manifest",
    "canonical_environment_bytes",
    "derive_environment_seed",
    "validate_environment_generator_request",
]
