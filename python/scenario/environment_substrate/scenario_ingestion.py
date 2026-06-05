from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .projection_setup import (
    ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_CONTRACT_VERSION,
    WORLD_ZONE_DEFINITION_SURFACE_CODES,
)


ENVIRONMENT_SUBSTRATE_SCENARIO_INGESTION_CONTRACT_VERSION = (
    "environment_substrate.g0_l.compiler_ingestion.v1"
)
ENVIRONMENT_SUBSTRATE_ENVIRONMENT_KEY = "environment_substrate"
ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_PAYLOADS_KEY = "projection_setup_payloads"
ENVIRONMENT_SUBSTRATE_INGESTION_EVIDENCE_KEY = "projection_ingestion_evidence"


def _clone(value: Any) -> Any:
    return deepcopy(value)


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _normalized_text(value: Any) -> str:
    return str(value or "").strip()


def _finite_float(value: Any) -> float | None:
    try:
        coerced = float(value)
    except Exception:
        return None
    if not math.isfinite(coerced):
        return None
    return coerced


@dataclass(frozen=True)
class EnvironmentProjectionScenarioIngestionResult:
    valid: bool
    fail_closed: bool
    rejection_reason: str
    errors: tuple[str, ...]
    scenario_data: dict[str, Any] | None = None
    ingested_zone_count: int = 0

    def to_metadata(self) -> dict[str, Any]:
        return {
            "valid": bool(self.valid),
            "fail_closed": bool(self.fail_closed),
            "rejection_reason": self.rejection_reason,
            "errors": list(self.errors),
            "ingested_zone_count": int(self.ingested_zone_count),
        }


def _failure(
    reason: str,
    message: str,
) -> EnvironmentProjectionScenarioIngestionResult:
    return EnvironmentProjectionScenarioIngestionResult(
        valid=False,
        fail_closed=True,
        rejection_reason=reason,
        errors=(message,),
    )


def _payloads_from_environment(
    env_cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool] | EnvironmentProjectionScenarioIngestionResult:
    substrate_cfg = env_cfg.get(ENVIRONMENT_SUBSTRATE_ENVIRONMENT_KEY, {})
    if ENVIRONMENT_SUBSTRATE_ENVIRONMENT_KEY not in env_cfg:
        return ([], False)
    if not isinstance(substrate_cfg, dict):
        return _failure(
            "environment_substrate_projection_ingestion_namespace_invalid",
            "environment.environment_substrate must be an object",
        )
    if ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_PAYLOADS_KEY not in substrate_cfg:
        return ([], False)
    payloads = substrate_cfg.get(ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_PAYLOADS_KEY)
    if not isinstance(payloads, list):
        return _failure(
            "environment_substrate_projection_ingestion_payloads_invalid",
            "environment_substrate.projection_setup_payloads must be a list",
        )
    for index, payload in enumerate(payloads):
        if not isinstance(payload, dict):
            return _failure(
                "environment_substrate_projection_ingestion_payload_invalid",
                f"projection setup payload {index} must be an object",
            )
    return (payloads, True)


def _validate_zone_payload(
    zone: dict[str, Any],
    *,
    payload_index: int,
    zone_index: int,
) -> dict[str, Any] | EnvironmentProjectionScenarioIngestionResult:
    if "world_index" in zone:
        return _failure(
            "environment_substrate_projection_ingestion_world_index_forbidden",
            "projection setup payload zones must remain world-index inert",
        )
    name = _normalized_text(zone.get("name"))
    if not name:
        return _failure(
            "environment_substrate_projection_ingestion_zone_invalid",
            f"payload {payload_index} zone {zone_index} requires name",
        )
    numbers: dict[str, float] = {}
    for key in ("x", "y", "width", "length", "heading"):
        value = _finite_float(zone.get(key))
        if value is None:
            return _failure(
                "environment_substrate_projection_ingestion_zone_invalid",
                f"payload {payload_index} zone {zone_index} requires finite {key}",
            )
        numbers[key] = value
    if numbers["width"] <= 0.0 or numbers["length"] <= 0.0:
        return _failure(
            "environment_substrate_projection_ingestion_zone_invalid",
            f"payload {payload_index} zone {zone_index} requires positive dimensions",
        )
    surface = _normalized_text(zone.get("surface"))
    if surface not in WORLD_ZONE_DEFINITION_SURFACE_CODES:
        return _failure(
            "environment_substrate_projection_ingestion_surface_invalid",
            f"payload {payload_index} zone {zone_index} surface {surface!r} is not accepted",
        )
    return {
        "name": name,
        "x": float(numbers["x"]),
        "y": float(numbers["y"]),
        "width": float(numbers["width"]),
        "length": float(numbers["length"]),
        "heading": float(numbers["heading"]),
        "surface": surface,
    }


def _validate_payload(
    payload: dict[str, Any],
    *,
    payload_index: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]] | EnvironmentProjectionScenarioIngestionResult:
    if payload.get("contract_version") != ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_CONTRACT_VERSION:
        return _failure(
            "environment_substrate_projection_ingestion_contract_mismatch",
            f"payload {payload_index} has unsupported projection setup contract",
        )
    if payload.get("target") != "world_zone_definition":
        return _failure(
            "environment_substrate_projection_ingestion_target_not_accepted",
            f"payload {payload_index} target must be world_zone_definition",
        )
    if not bool(payload.get("no_held_capability_release", False)):
        return _failure(
            "environment_substrate_projection_ingestion_held_claim",
            f"payload {payload_index} lacks no-held-capability evidence",
        )
    zones = payload.get("zones")
    if not isinstance(zones, list) or not zones:
        return _failure(
            "environment_substrate_projection_ingestion_zones_required",
            f"payload {payload_index} must include projected zones",
        )
    zone_evidence = payload.get("zone_evidence")
    if not isinstance(zone_evidence, list) or len(zone_evidence) != len(zones):
        return _failure(
            "environment_substrate_projection_ingestion_evidence_required",
            f"payload {payload_index} must include one evidence entry per zone",
        )
    projection_evidence = payload.get("projection_evidence")
    if not isinstance(projection_evidence, dict):
        return _failure(
            "environment_substrate_projection_ingestion_evidence_required",
            f"payload {payload_index} requires projection evidence",
        )
    if projection_evidence.get("target") != "world_zone_definition":
        return _failure(
            "environment_substrate_projection_ingestion_target_not_accepted",
            f"payload {payload_index} projection evidence target must be world_zone_definition",
        )
    if not bool(projection_evidence.get("no_held_capability_release", False)):
        return _failure(
            "environment_substrate_projection_ingestion_held_claim",
            f"payload {payload_index} projection evidence lacks no-held-capability flag",
        )
    if projection_evidence.get("dropped_attributes"):
        return _failure(
            "environment_substrate_projection_ingestion_derived_product_forbidden",
            f"payload {payload_index} cannot silently ingest dropped rich attributes",
        )

    normalized_zones: list[dict[str, Any]] = []
    source_object_ids: list[str] = []
    source_manifest_ids: set[str] = set()
    for zone_index, zone in enumerate(zones):
        if not isinstance(zone, dict):
            return _failure(
                "environment_substrate_projection_ingestion_zone_invalid",
                f"payload {payload_index} zone {zone_index} must be an object",
            )
        normalized = _validate_zone_payload(
            zone,
            payload_index=payload_index,
            zone_index=zone_index,
        )
        if isinstance(normalized, EnvironmentProjectionScenarioIngestionResult):
            return normalized
        evidence = zone_evidence[zone_index]
        if not isinstance(evidence, dict):
            return _failure(
                "environment_substrate_projection_ingestion_evidence_required",
                f"payload {payload_index} zone {zone_index} evidence must be an object",
            )
        if evidence.get("target") != "world_zone_definition":
            return _failure(
                "environment_substrate_projection_ingestion_target_not_accepted",
                f"payload {payload_index} zone {zone_index} evidence target must be world_zone_definition",
            )
        if evidence.get("profile_id") != payload.get("profile_id"):
            return _failure(
                "environment_substrate_projection_ingestion_evidence_required",
                f"payload {payload_index} zone {zone_index} profile evidence mismatch",
            )
        if not bool(evidence.get("no_held_capability_release", False)):
            return _failure(
                "environment_substrate_projection_ingestion_held_claim",
                f"payload {payload_index} zone {zone_index} lacks no-held-capability evidence",
            )
        source_object_id = _normalized_text(evidence.get("source_object_id"))
        source_manifest_id = _normalized_text(evidence.get("source_manifest_id"))
        if not source_object_id or not source_manifest_id:
            return _failure(
                "environment_substrate_projection_ingestion_evidence_required",
                f"payload {payload_index} zone {zone_index} requires source provenance",
            )
        source_object_ids.append(source_object_id)
        source_manifest_ids.add(source_manifest_id)
        normalized_zones.append(normalized)

    if tuple(projection_evidence.get("source_object_ids", ())) != tuple(source_object_ids):
        return _failure(
            "environment_substrate_projection_ingestion_evidence_required",
            f"payload {payload_index} projection evidence source IDs do not match zones",
        )
    payload_manifest_id = _normalized_text(payload.get("manifest_id"))
    if not payload_manifest_id or source_manifest_ids != {payload_manifest_id}:
        return _failure(
            "environment_substrate_projection_ingestion_evidence_required",
            f"payload {payload_index} source manifest evidence mismatch",
        )

    ingestion_evidence = {
        "contract_version": ENVIRONMENT_SUBSTRATE_SCENARIO_INGESTION_CONTRACT_VERSION,
        "payload_contract_version": payload.get("contract_version"),
        "payload_digest_sha256": _canonical_digest(payload),
        "manifest_id": payload_manifest_id,
        "profile_id": _normalized_text(payload.get("profile_id")),
        "target": "world_zone_definition",
        "zone_count": len(normalized_zones),
        "source_object_ids": source_object_ids,
        "no_runtime_setup_application": True,
        "no_held_capability_release": True,
    }
    return normalized_zones, ingestion_evidence


def ingest_projection_setup_payloads_into_scenario(
    scenario_data: dict[str, Any],
) -> EnvironmentProjectionScenarioIngestionResult:
    if not isinstance(scenario_data, dict):
        raise TypeError("scenario_data must be a dict")
    merged = _clone(scenario_data)
    env_cfg = merged.get("environment", {})
    if "environment" not in merged:
        return EnvironmentProjectionScenarioIngestionResult(
            valid=True,
            fail_closed=False,
            rejection_reason="",
            errors=(),
            scenario_data=merged,
            ingested_zone_count=0,
        )
    if not isinstance(env_cfg, dict):
        return _failure(
            "environment_substrate_projection_ingestion_environment_invalid",
            "environment must be an object",
        )

    payloads_result = _payloads_from_environment(env_cfg)
    if isinstance(payloads_result, EnvironmentProjectionScenarioIngestionResult):
        return payloads_result
    payloads, payload_key_present = payloads_result
    if not payload_key_present:
        return EnvironmentProjectionScenarioIngestionResult(
            valid=True,
            fail_closed=False,
            rejection_reason="",
            errors=(),
            scenario_data=merged,
            ingested_zone_count=0,
        )
    if not payloads:
        return _failure(
            "environment_substrate_projection_ingestion_payloads_invalid",
            "projection_setup_payloads must not be empty when declared",
        )

    existing_zones = env_cfg.get("zones", [])
    if "zones" in env_cfg and not isinstance(existing_zones, list):
        return _failure(
            "environment_substrate_projection_ingestion_existing_zones_invalid",
            "environment.zones must be a list before projection ingestion",
        )
    normalized_existing = list(_clone(existing_zones)) if isinstance(existing_zones, list) else []
    used_names = {
        _normalized_text(zone.get("name"))
        for zone in normalized_existing
        if isinstance(zone, dict) and _normalized_text(zone.get("name"))
    }

    ingested_zones: list[dict[str, Any]] = []
    ingestion_evidence: list[dict[str, Any]] = []
    for payload_index, payload in enumerate(payloads):
        payload_result = _validate_payload(payload, payload_index=payload_index)
        if isinstance(payload_result, EnvironmentProjectionScenarioIngestionResult):
            return payload_result
        zones, evidence = payload_result
        for zone in zones:
            if zone["name"] in used_names:
                return _failure(
                    "environment_substrate_projection_ingestion_zone_name_conflict",
                    f"projection zone {zone['name']!r} conflicts with an existing zone",
                )
            used_names.add(zone["name"])
        ingested_zones.extend(zones)
        ingestion_evidence.append(evidence)

    substrate_cfg = dict(env_cfg.get(ENVIRONMENT_SUBSTRATE_ENVIRONMENT_KEY, {}))
    substrate_cfg.pop(ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_PAYLOADS_KEY, None)
    substrate_cfg[ENVIRONMENT_SUBSTRATE_INGESTION_EVIDENCE_KEY] = ingestion_evidence
    env_cfg["zones"] = normalized_existing + ingested_zones
    env_cfg[ENVIRONMENT_SUBSTRATE_ENVIRONMENT_KEY] = substrate_cfg
    merged["environment"] = env_cfg

    return EnvironmentProjectionScenarioIngestionResult(
        valid=True,
        fail_closed=False,
        rejection_reason="",
        errors=(),
        scenario_data=merged,
        ingested_zone_count=len(ingested_zones),
    )


__all__ = [
    "ENVIRONMENT_SUBSTRATE_ENVIRONMENT_KEY",
    "ENVIRONMENT_SUBSTRATE_INGESTION_EVIDENCE_KEY",
    "ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_PAYLOADS_KEY",
    "ENVIRONMENT_SUBSTRATE_SCENARIO_INGESTION_CONTRACT_VERSION",
    "EnvironmentProjectionScenarioIngestionResult",
    "ingest_projection_setup_payloads_into_scenario",
]
