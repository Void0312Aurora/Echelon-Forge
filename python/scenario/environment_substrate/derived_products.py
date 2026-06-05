from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable

from .components import HELD_CAPABILITY_CLAIMS
from .manifest import EnvironmentManifest, EnvironmentObject
from .projection import project_manifest_to_compatibility_setup
from .validation import validate_environment_manifest


ENVIRONMENT_SUBSTRATE_DERIVED_PRODUCT_CONTRACT_VERSION = (
    "environment_substrate.g0_m.derived_products.v1"
)

ENVIRONMENT_DERIVED_PRODUCT_KINDS = (
    "surface_zone_index",
    "occlusion_candidate_index",
)

HELD_DERIVED_PRODUCT_KINDS = (
    "road_graph",
    "movement_cost_grid",
    "passability_mask",
    "los_occlusion_index",
    "cover_concealment_index",
    "tactical_area_graph",
)


def _clone(value: Any) -> Any:
    return deepcopy(value)


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


def _finite_float(value: Any) -> float | None:
    try:
        coerced = float(value)
    except Exception:
        return None
    if not math.isfinite(coerced):
        return None
    return coerced


@dataclass(frozen=True)
class EnvironmentDerivedProductRequest:
    request_id: str
    product_kinds: tuple[str, ...]
    source_projection_profile_id: str = ""
    capability_claims: tuple[str, ...] = ()
    no_held_capability_release: bool = True
    contract_version: str = ENVIRONMENT_SUBSTRATE_DERIVED_PRODUCT_CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _normalized_text(self.request_id))
        object.__setattr__(self, "product_kinds", _normalized_unique_texts(self.product_kinds))
        object.__setattr__(
            self,
            "source_projection_profile_id",
            _normalized_text(self.source_projection_profile_id),
        )
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
        object.__setattr__(
            self,
            "contract_version",
            _normalized_text(self.contract_version),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "contract_version": self.contract_version,
            "product_kinds": list(self.product_kinds),
            "source_projection_profile_id": self.source_projection_profile_id,
            "capability_claims": list(self.capability_claims),
            "no_held_capability_release": bool(self.no_held_capability_release),
        }


@dataclass(frozen=True)
class EnvironmentDerivedProduct:
    product_id: str
    product_kind: str
    source_manifest_id: str
    entries: tuple[dict[str, Any], ...]
    evidence: dict[str, Any]
    contract_version: str = ENVIRONMENT_SUBSTRATE_DERIVED_PRODUCT_CONTRACT_VERSION
    no_held_capability_release: bool = True

    def to_metadata(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_kind": self.product_kind,
            "contract_version": self.contract_version,
            "source_manifest_id": self.source_manifest_id,
            "entries": [_clone(entry) for entry in self.entries],
            "evidence": _clone(self.evidence),
            "no_held_capability_release": bool(self.no_held_capability_release),
        }


@dataclass(frozen=True)
class EnvironmentDerivedProductBundle:
    request: EnvironmentDerivedProductRequest
    source_manifest_id: str
    products: tuple[EnvironmentDerivedProduct, ...]
    no_runtime_consumer_release: bool = True

    def to_metadata(self) -> dict[str, Any]:
        return {
            "contract_version": ENVIRONMENT_SUBSTRATE_DERIVED_PRODUCT_CONTRACT_VERSION,
            "source_manifest_id": self.source_manifest_id,
            "request": self.request.to_metadata(),
            "products": [product.to_metadata() for product in self.products],
            "no_runtime_consumer_release": bool(self.no_runtime_consumer_release),
            "no_held_capability_release": True,
        }


@dataclass(frozen=True)
class EnvironmentDerivedProductResult:
    valid: bool
    fail_closed: bool
    rejection_reason: str
    errors: tuple[str, ...]
    bundle: EnvironmentDerivedProductBundle | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "valid": bool(self.valid),
            "fail_closed": bool(self.fail_closed),
            "rejection_reason": self.rejection_reason,
            "errors": list(self.errors),
            "bundle": self.bundle.to_metadata() if self.bundle else None,
        }


def _failure(reason: str, message: str) -> EnvironmentDerivedProductResult:
    return EnvironmentDerivedProductResult(
        valid=False,
        fail_closed=True,
        rejection_reason=reason,
        errors=(message,),
    )


def _component_map(item: EnvironmentObject) -> dict[str, Any]:
    return {component.family: component for component in item.components}


def _rect_bounds_from_object(item: EnvironmentObject) -> dict[str, float] | None:
    if item.geometry.geometry_type != "rect":
        return None
    coords = item.geometry.coordinates
    x = _finite_float(coords.get("x"))
    y = _finite_float(coords.get("y"))
    width = _finite_float(coords.get("width"))
    length = _finite_float(coords.get("length"))
    heading = _finite_float(coords.get("heading", 0.0))
    if x is None or y is None or width is None or length is None or heading is None:
        return None
    if width <= 0.0 or length <= 0.0:
        return None
    return {
        "x": float(x),
        "y": float(y),
        "width": float(width),
        "length": float(length),
        "heading": float(heading),
    }


def _polygon_bounds_from_object(item: EnvironmentObject) -> dict[str, float] | None:
    if item.geometry.geometry_type != "polygon":
        return None
    points = item.geometry.coordinates.get("points")
    if not isinstance(points, list) or not points:
        return None
    xs: list[float] = []
    ys: list[float] = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            return None
        x = _finite_float(point[0])
        y = _finite_float(point[1])
        if x is None or y is None:
            return None
        xs.append(x)
        ys.append(y)
    return {
        "min_x": min(xs),
        "min_y": min(ys),
        "max_x": max(xs),
        "max_y": max(ys),
    }


def _surface_zone_index(
    manifest: EnvironmentManifest,
    request: EnvironmentDerivedProductRequest,
) -> EnvironmentDerivedProductResult | EnvironmentDerivedProduct:
    if not request.source_projection_profile_id:
        return _failure(
            "environment_substrate_derived_projection_profile_required",
            "surface_zone_index requires a source projection profile",
        )
    projection = project_manifest_to_compatibility_setup(
        manifest,
        profile_id=request.source_projection_profile_id,
    )
    if not projection.valid:
        return EnvironmentDerivedProductResult(
            valid=False,
            fail_closed=True,
            rejection_reason=projection.rejection_reason,
            errors=projection.errors,
        )
    if projection.evidence is None or projection.evidence.dropped_attributes:
        return _failure(
            "environment_substrate_derived_projection_evidence_required",
            "surface_zone_index requires no-dropped-attribute projection evidence",
        )
    entries = []
    for index, zone in enumerate(projection.zones):
        entries.append(
            {
                "index": index,
                "source_object_id": zone.source_object_id,
                "zone_name": zone.name,
                "surface": zone.surface,
                "rect": {
                    "x": float(zone.x),
                    "y": float(zone.y),
                    "width": float(zone.width),
                    "length": float(zone.length),
                    "heading": float(zone.heading),
                },
                "runtime_consumer_release": False,
            }
        )
    return EnvironmentDerivedProduct(
        product_id=f"{manifest.manifest_id}:surface_zone_index",
        product_kind="surface_zone_index",
        source_manifest_id=manifest.manifest_id,
        entries=tuple(entries),
        evidence={
            "profile_id": projection.evidence.profile_id,
            "target": projection.evidence.target,
            "source_object_ids": list(projection.evidence.source_object_ids),
            "no_runtime_consumer_release": True,
            "no_held_capability_release": True,
        },
    )


def _occlusion_candidate_index(
    manifest: EnvironmentManifest,
) -> EnvironmentDerivedProduct:
    entries: list[dict[str, Any]] = []
    for item in manifest.objects:
        components = _component_map(item)
        candidate_component = None
        for family in ("occlusion", "structure", "vegetation"):
            if family in components:
                candidate_component = components[family]
                break
        if candidate_component is None:
            continue
        bounds = _rect_bounds_from_object(item)
        bounds_kind = "rect"
        if bounds is None:
            bounds = _polygon_bounds_from_object(item)
            bounds_kind = "aabb"
        if bounds is None:
            continue
        attrs = candidate_component.attributes
        height = _finite_float(attrs.get("height_m"))
        opacity = _finite_float(attrs.get("opacity"))
        entry: dict[str, Any] = {
            "source_object_id": item.object_id,
            "catalog_ref": item.catalog_ref,
            "component_id": candidate_component.component_id,
            "component_family": candidate_component.family,
            "bounds_kind": bounds_kind,
            "bounds": bounds,
            "layer_membership": list(item.layer_membership),
            "runtime_consumer_release": False,
        }
        if height is not None:
            entry["height_m"] = float(height)
        if opacity is not None:
            entry["opacity"] = float(opacity)
        entries.append(entry)
    return EnvironmentDerivedProduct(
        product_id=f"{manifest.manifest_id}:occlusion_candidate_index",
        product_kind="occlusion_candidate_index",
        source_manifest_id=manifest.manifest_id,
        entries=tuple(sorted(entries, key=lambda entry: entry["source_object_id"])),
        evidence={
            "candidate_component_families": ["occlusion", "structure", "vegetation"],
            "no_los_runtime_release": True,
            "no_cover_runtime_release": True,
            "no_held_capability_release": True,
        },
    )


def build_environment_derived_products(
    manifest: EnvironmentManifest,
    request: EnvironmentDerivedProductRequest,
) -> EnvironmentDerivedProductResult:
    if not isinstance(manifest, EnvironmentManifest):
        raise TypeError("manifest must be an EnvironmentManifest")
    if not isinstance(request, EnvironmentDerivedProductRequest):
        raise TypeError("request must be an EnvironmentDerivedProductRequest")

    validation = validate_environment_manifest(manifest)
    if not validation.valid:
        return EnvironmentDerivedProductResult(
            valid=False,
            fail_closed=True,
            rejection_reason=validation.rejection_reason,
            errors=validation.errors,
        )
    if request.contract_version != ENVIRONMENT_SUBSTRATE_DERIVED_PRODUCT_CONTRACT_VERSION:
        return _failure(
            "environment_substrate_derived_contract_mismatch",
            "derived product request uses an unsupported contract version",
        )
    if not request.request_id:
        return _failure(
            "environment_substrate_derived_request_id_required",
            "derived product request_id is required",
        )
    if not request.product_kinds:
        return _failure(
            "environment_substrate_derived_product_kind_required",
            "at least one derived product kind is required",
        )
    unsupported = sorted(
        kind
        for kind in request.product_kinds
        if kind not in ENVIRONMENT_DERIVED_PRODUCT_KINDS
        and kind not in HELD_DERIVED_PRODUCT_KINDS
    )
    if unsupported:
        return _failure(
            "environment_substrate_derived_product_kind_unknown",
            f"unknown derived product kinds {unsupported}",
        )
    held_products = sorted(
        kind for kind in request.product_kinds if kind in HELD_DERIVED_PRODUCT_KINDS
    )
    held_claims = sorted(
        claim for claim in request.capability_claims if claim in HELD_CAPABILITY_CLAIMS
    )
    if held_products or held_claims or not request.no_held_capability_release:
        return _failure(
            "environment_substrate_derived_product_held_capability",
            f"derived product request crosses held boundary products={held_products} claims={held_claims}",
        )

    products: list[EnvironmentDerivedProduct] = []
    for kind in request.product_kinds:
        if kind == "surface_zone_index":
            product = _surface_zone_index(manifest, request)
            if isinstance(product, EnvironmentDerivedProductResult):
                return product
            products.append(product)
        elif kind == "occlusion_candidate_index":
            products.append(_occlusion_candidate_index(manifest))

    bundle = EnvironmentDerivedProductBundle(
        request=request,
        source_manifest_id=manifest.manifest_id,
        products=tuple(sorted(products, key=lambda product: product.product_kind)),
    )
    return EnvironmentDerivedProductResult(
        valid=True,
        fail_closed=False,
        rejection_reason="",
        errors=(),
        bundle=bundle,
    )


__all__ = [
    "ENVIRONMENT_DERIVED_PRODUCT_KINDS",
    "ENVIRONMENT_SUBSTRATE_DERIVED_PRODUCT_CONTRACT_VERSION",
    "HELD_DERIVED_PRODUCT_KINDS",
    "EnvironmentDerivedProduct",
    "EnvironmentDerivedProductBundle",
    "EnvironmentDerivedProductRequest",
    "EnvironmentDerivedProductResult",
    "build_environment_derived_products",
]
