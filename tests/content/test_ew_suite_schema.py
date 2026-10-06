"""EW suite templates and the maintained source fixture share one schema contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver


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


if __name__ == "__main__":
    unittest.main()
