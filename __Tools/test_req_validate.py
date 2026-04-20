#!/usr/bin/env python3
"""
test_req_validate.py — Unit tests for req_validate.py helper functions.

Tests are written against the actual Automator proxy API using MagicMock
to simulate the object shapes returned by syside. Once req_debug.py
confirms the correct attribute access path for feature values, the
mock structure here matches that exact shape.

Run with:
    pytest __Tools/test_req_validate.py -v

Or against a specific test:
    pytest __Tools/test_req_validate.py::test_attr_value_finds_redefined_id -v
"""

import sys
import re
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock
from typing import Optional

import pytest

# ---------------------------------------------------------------------------
# Import the functions under test directly from req_validate.
# Since req_validate imports syside at module level, we mock it first.
# ---------------------------------------------------------------------------
import unittest.mock as mock

# Stub out syside before importing req_validate so the import doesn't fail
# in environments where syside isn't installed (e.g. CI without a licence).
syside_stub = MagicMock()
sys.modules.setdefault('syside', syside_stub)
sys.modules.setdefault('syside.preview', MagicMock())

# Now import the functions we want to test.
# Adjust the path if your __Tools directory is not on sys.path.
_tools_dir = Path(__file__).parent
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from req_validate import (
    _feature_value,
    _attr_value,
    _criteria_attrs,
    _req_type_name,
    _short_id,
    _package_name,
    validate_requirement,
    REQ_TYPE_CONFIG,
    ValidationLevel,
    BASE_REQUIRED_ATTRS,
)


# ---------------------------------------------------------------------------
# Helpers — build mock elements that match the Automator proxy shape.
#
# NOTE: The exact shape of these mocks (especially _make_attr_member) must
# match what req_debug.py reveals for your version of syside.
# Update _make_attr_member once you have confirmed the correct access path.
# ---------------------------------------------------------------------------

def _collect_mock(items):
    """Return a mock with a .collect() that yields items."""
    m = MagicMock()
    m.collect.return_value = iter(items)
    return m


def _make_attr_member(name: str, value: Optional[str],
                      as_redefinition: bool = False) -> MagicMock:
    """
    Build a mock AttributeUsage member with a given name and value.

    Confirmed from req_debug output (syside 0.8.x):
      - Direct declarations:   declared_name = name
      - :>> redefinitions:     declared_name = None,
                               referenced_feature.declared_name = name
      - Value access:          feature_value_expression.value = the string
                               owned_members[0].value = the string (fallback)

    Set as_redefinition=True to simulate a :>> redefined attribute
    (declared_name=None, name on referenced_feature).
    """
    m = MagicMock()
    m.element_id = f"mock-id-{name}"

    if as_redefinition:
        # :>> redefinition — declared_name is None
        m.declared_name = None
        rf = MagicMock()
        rf.declared_name = name
        m.referenced_feature = rf
        # owned_redefinitions path (secondary)
        redef = MagicMock()
        redef_feat = MagicMock()
        redef_feat.declared_name = name
        redef.redefined_feature = redef_feat
        m.owned_redefinitions = _collect_mock([redef])
    else:
        # Direct declaration — declared_name is set
        m.declared_name = name
        m.referenced_feature = None
        m.owned_redefinitions = _collect_mock([])

    # feature_value_expression is a LiteralString object with .value
    if value is not None:
        lit = MagicMock()
        lit.value = value
        m.feature_value_expression = lit
    else:
        m.feature_value_expression = None

    # Fallback: owned_members contains a LiteralString-like sub
    if value is not None:
        sub = MagicMock()
        sub.value = value
        m.owned_members = _collect_mock([sub])
    else:
        m.owned_members = _collect_mock([])

    # Multiplicity: default [1] (required)
    m.declared_multiplicity = None
    return m


def _make_optional_attr_member(name: str, value: Optional[str]) -> MagicMock:
    """Like _make_attr_member but with [0..1] multiplicity."""
    m = _make_attr_member(name, value)
    m.declared_multiplicity = MagicMock()
    m.declared_multiplicity.__str__ = lambda self: "0..1"
    return m


def _make_requirement(
    type_name: str,
    attrs: dict[str, Optional[str]],
    criteria_attrs: Optional[dict[str, str]] = None,
    short_id: str = "",
    pkg_name: str = "TestPackage",
    qname: str = "TestPackage::testReq",
) -> MagicMock:
    """
    Build a mock RequirementUsage with the given type, attributes, and criteria.
    """
    el = MagicMock()
    el.declared_name = qname.split("::")[-1]
    el.qualified_name = qname
    el.element_id = "mock-element-id"

    # req_id / short_name for _short_id
    el.req_id = short_id or None
    el.short_name = short_id or None
    el.declared_short_name = short_id or None

    # owning_namespace for _package_name
    ns = MagicMock()
    ns.declared_name = pkg_name
    el.owning_namespace = ns

    # feature_typing / owned_typings / types / requirement_definition
    # for _req_type_name
    rd = MagicMock()
    rd.declared_name = type_name
    el.requirement_definition = rd

    owned_typing = MagicMock()
    owned_typing.type = rd
    el.owned_typings = _collect_mock([owned_typing])
    el.types = _collect_mock([rd])

    # nested_attributes — the :>> redefined attributes
    attr_members = [_make_attr_member(k, v) for k, v in attrs.items()]
    el.nested_attributes = _collect_mock(attr_members)

    # nested_parts — the criteria part if provided
    if criteria_attrs is not None:
        criteria_part = MagicMock()
        criteria_part.declared_name = "criteria"
        criteria_attr_members = [
            _make_attr_member(k, v) for k, v in criteria_attrs.items()
        ]
        criteria_part.nested_attributes = _collect_mock(criteria_attr_members)
        criteria_part.owned_members = _collect_mock([])
        el.nested_parts = _collect_mock([criteria_part])
    else:
        el.nested_parts = _collect_mock([])

    # owned_members fallback (empty — nested_attributes is primary)
    el.owned_members = _collect_mock([])

    # isinstance checks — always return False for SatisfyRequirementUsage
    el.isinstance = MagicMock(return_value=False)

    return el


# ---------------------------------------------------------------------------
# Populate REQ_TYPE_CONFIG for tests (normally built at runtime from model)
# ---------------------------------------------------------------------------

REQ_TYPE_CONFIG.update({
    "SRS_Requirement": {
        "display": "SRS Requirement",
        "valid_methods": None,
        "performance_attrs": [],
        "required_type_attrs": [],
        "optional_type_attrs": [],
    },
    "CapabilityRequirement": {
        "display": "Capability Requirement",
        "valid_methods": {"Test", "Analysis"},
        "performance_attrs": ["performance", "timing", "throughput", "latency", "accuracy"],
        "required_type_attrs": ["capabilityName"],
        "optional_type_attrs": [],
    },
    "SafetyRequirement": {
        "display": "Safety Requirement",
        "valid_methods": {"Analysis", "Test", "Inspection"},
        "performance_attrs": [],
        "required_type_attrs": ["hazard", "mitigation"],
        "optional_type_attrs": [],
    },
    "DataRequirement": {
        "display": "Data Requirement",
        "valid_methods": {"Analysis", "Inspection"},
        "performance_attrs": [],
        "required_type_attrs": ["dataName", "dataType"],
        "optional_type_attrs": ["format", "units"],
    },
})


# ---------------------------------------------------------------------------
# _feature_value tests
# ---------------------------------------------------------------------------

class TestFeatureValue:

    def test_returns_string_from_feature_value_expression(self):
        m = MagicMock()
        m.feature_value_expression = "AUT.1"
        m.owned_members = _collect_mock([])
        assert _feature_value(m) == "AUT.1"

    def test_strips_quotes_from_feature_value_expression(self):
        m = MagicMock()
        m.feature_value_expression = '"AUT.1"'
        m.owned_members = _collect_mock([])
        assert _feature_value(m) == "AUT.1"

    def test_falls_back_to_owned_member_value(self):
        m = MagicMock()
        m.feature_value_expression = None
        sub = MagicMock()
        sub.value = "fallback_value"
        m.owned_members = _collect_mock([sub])
        assert _feature_value(m) == "fallback_value"

    def test_returns_none_when_no_value(self):
        m = MagicMock()
        m.feature_value_expression = None
        m.owned_members = _collect_mock([])
        assert _feature_value(m) is None

    def test_returns_none_when_expression_raises(self):
        m = MagicMock()
        type(m).feature_value_expression = PropertyMock(side_effect=AttributeError)
        m.owned_members = _collect_mock([])
        assert _feature_value(m) is None


# ---------------------------------------------------------------------------
# _attr_value tests
# ---------------------------------------------------------------------------

class TestAttrValue:

    def test_finds_attribute_in_nested_attributes(self):
        el = _make_requirement("SRS_Requirement", {"id": "AUT.1", "text": "The system shall..."})
        assert _attr_value(el, "id") == "AUT.1"

    def test_finds_attribute_text(self):
        el = _make_requirement("SRS_Requirement", {"id": "AUT.1", "text": "The system shall..."})
        assert _attr_value(el, "text") == "The system shall..."

    def test_returns_none_for_absent_attribute(self):
        el = _make_requirement("SRS_Requirement", {"id": "AUT.1"})
        assert _attr_value(el, "rationale") is None

    def test_returns_empty_string_for_member_with_no_value(self):
        el = _make_requirement("SRS_Requirement", {"id": None})
        assert _attr_value(el, "id") == ""

    def test_does_not_confuse_different_attribute_names(self):
        el = _make_requirement("SRS_Requirement", {"id": "AUT.1", "text": "desc"})
        assert _attr_value(el, "text") == "desc"
        assert _attr_value(el, "id") == "AUT.1"

    def test_finds_redefined_attribute_with_none_declared_name(self):
        """
        Simulates :>> id = "AUT.1" where declared_name is None and the name
        is on referenced_feature.declared_name — confirmed from req_debug output.
        """
        el = MagicMock()
        el.element_id = "mock-req"
        # Build redefined id member (declared_name=None, name via referenced_feature)
        id_member = _make_attr_member("id", "AUT.1", as_redefinition=True)
        el.nested_attributes = _collect_mock([id_member])
        el.owned_members = _collect_mock([])
        assert _attr_value(el, "id") == "AUT.1"

    def test_feature_value_reads_literal_string_value_not_repr(self):
        """
        feature_value_expression is a LiteralString object — we must read
        .value, not str(expr), which would give the object repr.
        """
        from req_validate import _feature_value
        member = MagicMock()
        lit = MagicMock()
        lit.value = "AUT.1"
        # Ensure str(lit) would give an unhelpful repr
        lit.__str__ = lambda self: "<syside.core.LiteralString object at 0x...>"
        member.feature_value_expression = lit
        member.owned_members = _collect_mock([])
        assert _feature_value(member) == "AUT.1"


# ---------------------------------------------------------------------------
# _criteria_attrs tests
# ---------------------------------------------------------------------------

class TestCriteriaAttrs:

    def test_returns_empty_dict_when_no_criteria(self):
        el = _make_requirement("SRS_Requirement", {}, criteria_attrs=None)
        assert _criteria_attrs(el) == {}

    def test_returns_method_and_logic(self):
        el = _make_requirement(
            "CapabilityRequirement",
            {"id": "AUT.1", "text": "desc", "capabilityName": "Cap",
             "latency": "50ms"},
            criteria_attrs={
                "verificationMethod": "Test",
                "passFailLogic": "PASS if latency <= 50ms",
            },
        )
        result = _criteria_attrs(el)
        assert result.get("verificationMethod") == "Test"
        assert result.get("passFailLogic") == "PASS if latency <= 50ms"

    def test_returns_empty_string_for_unset_criteria_attr(self):
        el = _make_requirement(
            "CapabilityRequirement",
            {"id": "AUT.1", "text": "desc"},
            criteria_attrs={"verificationMethod": "Test", "passFailLogic": None},
        )
        result = _criteria_attrs(el)
        assert result.get("passFailLogic") == ""


# ---------------------------------------------------------------------------
# _req_type_name tests
# ---------------------------------------------------------------------------

class TestReqTypeName:

    def test_finds_type_from_requirement_definition(self):
        el = _make_requirement("CapabilityRequirement", {})
        assert _req_type_name(el) == "CapabilityRequirement"

    def test_returns_none_for_unknown_type(self):
        el = _make_requirement("UnknownType", {})
        # UnknownType is not in REQ_TYPE_CONFIG
        assert _req_type_name(el) is None

    def test_strips_package_qualifier(self):
        el = _make_requirement("CapabilityRequirement", {})
        rd = MagicMock()
        rd.declared_name = "SRSREQ::CapabilityRequirement"
        el.requirement_definition = rd
        assert _req_type_name(el) == "CapabilityRequirement"


# ---------------------------------------------------------------------------
# validate_requirement — integration-level tests
# ---------------------------------------------------------------------------

class TestValidateRequirement:

    def _valid_capability(self, extra_attrs=None, criteria=None):
        """Build a minimally valid CapabilityRequirement."""
        attrs = {
            "id":             "550e8400-e29b-41d4-a716-446655440000",
            "text":           "The system shall process messages within 50ms.",
            "capabilityName": "MessageProcessing",
            "latency":        "50ms",
        }
        if extra_attrs:
            attrs.update(extra_attrs)
        return _make_requirement(
            "CapabilityRequirement", attrs,
            criteria_attrs=criteria,
            short_id="AUT.1",
        )

    def test_valid_capability_no_violations(self):
        el = self._valid_capability()
        viols = validate_requirement(el, "CapabilityRequirement")
        valid_viols = [v for v in viols if v.level == ValidationLevel.VALID]
        assert valid_viols == [], f"Unexpected VALID violations: {valid_viols}"

    def test_missing_id_is_invalid(self):
        el = self._valid_capability(extra_attrs={"id": ""})
        viols = validate_requirement(el, "CapabilityRequirement")
        attrs = [v.attribute for v in viols if v.level == ValidationLevel.VALID]
        assert "id" in attrs

    def test_missing_text_is_invalid(self):
        el = self._valid_capability(extra_attrs={"text": ""})
        viols = validate_requirement(el, "CapabilityRequirement")
        attrs = [v.attribute for v in viols if v.level == ValidationLevel.VALID]
        assert "text" in attrs

    def test_non_uuid_id_is_valid(self):
        """id only needs to be non-empty — no UUID format enforcement."""
        el = self._valid_capability(extra_attrs={"id": "AUT.1"})
        viols = validate_requirement(el, "CapabilityRequirement")
        id_viols = [v for v in viols
                    if v.level == ValidationLevel.VALID and v.attribute == "id"]
        assert id_viols == [], f"Unexpected id violations: {id_viols}"

    def test_missing_capability_name_is_invalid(self):
        el = self._valid_capability(extra_attrs={"capabilityName": ""})
        viols = validate_requirement(el, "CapabilityRequirement")
        attrs = [v.attribute for v in viols if v.level == ValidationLevel.VALID]
        assert "capabilityName" in attrs

    def test_no_performance_attr_is_invalid(self):
        el = self._valid_capability(extra_attrs={
            "latency": "", "performance": "", "timing": "",
            "throughput": "", "accuracy": "",
        })
        viols = validate_requirement(el, "CapabilityRequirement")
        attrs = [v.attribute for v in viols if v.level == ValidationLevel.VALID]
        assert any("performance" in a for a in attrs)

    def test_invalid_verification_method_for_capability(self):
        el = self._valid_capability(
            criteria={"verificationMethod": "Inspection", "passFailLogic": "PASS if..."},
        )
        viols = validate_requirement(el, "CapabilityRequirement")
        attrs = [v.attribute for v in viols if v.level == ValidationLevel.VALID]
        assert "criteria.verificationMethod" in attrs

    def test_valid_verification_method_for_capability(self):
        el = self._valid_capability(
            criteria={"verificationMethod": "Test", "passFailLogic": "PASS if latency <= 50ms"},
        )
        viols = validate_requirement(el, "CapabilityRequirement")
        valid_viols = [v for v in viols if v.level == ValidationLevel.VALID]
        assert valid_viols == [], f"Unexpected violations: {valid_viols}"

    def test_missing_pass_fail_logic_is_invalid(self):
        el = self._valid_capability(
            criteria={"verificationMethod": "Test", "passFailLogic": ""},
        )
        viols = validate_requirement(el, "CapabilityRequirement")
        attrs = [v.attribute for v in viols if v.level == ValidationLevel.VALID]
        assert "criteria.passFailLogic" in attrs

    def test_missing_rationale_is_incomplete_not_invalid(self):
        el = self._valid_capability()
        viols = validate_requirement(el, "CapabilityRequirement")
        valid_viols    = [v for v in viols if v.level == ValidationLevel.VALID]
        complete_viols = [v for v in viols if v.level == ValidationLevel.COMPLETE]
        assert valid_viols == []
        assert any(v.attribute == "rationale" for v in complete_viols)

    def test_safety_req_requires_hazard_and_mitigation(self):
        el = _make_requirement(
            "SafetyRequirement",
            {"id": "550e8400-e29b-41d4-a716-446655440001",
             "text": "The system shall prevent inadvertent launch.",
             "hazard": "", "mitigation": ""},
        )
        viols = validate_requirement(el, "SafetyRequirement")
        attrs = [v.attribute for v in viols if v.level == ValidationLevel.VALID]
        assert "hazard" in attrs
        assert "mitigation" in attrs

    def test_safety_req_valid_when_all_set(self):
        el = _make_requirement(
            "SafetyRequirement",
            {"id": "550e8400-e29b-41d4-a716-446655440001",
             "text": "The system shall prevent inadvertent launch.",
             "hazard": "Inadvertent command", "mitigation": "Two-key enable"},
        )
        viols = validate_requirement(el, "SafetyRequirement")
        valid_viols = [v for v in viols if v.level == ValidationLevel.VALID]
        assert valid_viols == []
