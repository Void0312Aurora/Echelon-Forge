"""EW suite templates and the maintained source fixture share one schema contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver, ValidationError


ROOT = Path(__file__).resolve().parents[2]
COMMON_SCHEMA = ROOT / "database" / "_templates" / "common.schema.json"
EW_SCHEMA = ROOT / "database" / "_templates" / "module" / "ew_suite.schema.json"
EW_TEMPLATE = ROOT / "database" / "_templates" / "module" / "ew_suite.template.json"
SOURCE_FIXTURE = (
    ROOT
    / "examples"
    / "config"
    / "database"
    / "aircraft"
    / "modules"
    / "ew_suites"
    / "gen4_standard.json"
)


class EwSuiteSchemaTests(unittest.TestCase):
    def test_template_and_source_fixture_validate_against_ew_schema(self) -> None:
        common = json.loads(COMMON_SCHEMA.read_text(encoding="utf-8"))
        schema = json.loads(EW_SCHEMA.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, resolver=RefResolver.from_schema(common))

        validator.validate(json.loads(EW_TEMPLATE.read_text(encoding="utf-8")))
        validator.validate(json.loads(SOURCE_FIXTURE.read_text(encoding="utf-8")))

    def test_explicit_rf_groups_require_complete_positive_inputs(self) -> None:
        common = json.loads(COMMON_SCHEMA.read_text(encoding="utf-8"))
        for definition, values in (
            ("Sensor", {"rf_eirp_watts": 100.0, "rf_frequency_mhz": 1000.0, "rf_bandwidth_mhz": 20.0}),
            ("Jammer", {"rf_eirp_watts": 100.0, "rf_frequency_mhz": 1000.0, "bandwidth_mhz": 20.0}),
        ):
            validator = Draft202012Validator(common["$defs"][definition])
            validator.validate({})
            validator.validate(values)
            for key in values:
                incomplete = dict(values)
                incomplete.pop(key)
                with self.subTest(definition=definition, key=key):
                    with self.assertRaises(ValidationError):
                        validator.validate(incomplete)
                    with self.assertRaises(ValidationError):
                        validator.validate({**values, key: 0.0})

        jammer_validator = Draft202012Validator(common["$defs"]["Jammer"])
        jammer_validator.validate({"max_continuous_transmit_s": 5.0, "cooldown_s": 0.0})
        for malformed in (
            {"max_continuous_transmit_s": 5.0},
            {"cooldown_s": 2.0},
            {"max_continuous_transmit_s": 0.0, "cooldown_s": 2.0},
            {"max_continuous_transmit_s": 5.0, "cooldown_s": -1.0},
        ):
            with self.subTest(budget=malformed):
                with self.assertRaises(ValidationError):
                    jammer_validator.validate(malformed)

    def test_receiver_schema_rejects_partial_bands_and_unretained_confirmations(self) -> None:
        common = json.loads(COMMON_SCHEMA.read_text(encoding="utf-8"))
        validator = Draft202012Validator(common["$defs"]["Esm"])
        validator.validate({"frequency_min_mhz": 900.0, "frequency_max_mhz": 1100.0,
                            "memory_s": 2.0, "confirmation_scans": 2, "require_rf_contract": True})
        for malformed in ({"frequency_min_mhz": 900.0}, {"confirmation_scans": 2},
                          {"memory_s": 0.0, "confirmation_scans": 2},
                          {"require_rf_contract": "true"}):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValidationError):
                    validator.validate(malformed)


if __name__ == "__main__":
    unittest.main()
