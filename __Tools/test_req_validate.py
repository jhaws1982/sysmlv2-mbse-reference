#!/usr/bin/env python3
"""
test_req_validate.py — Unit tests for req_validate.py helper functions.

Tests use mock objects shaped to match the syside Automator proxy API as
observed in syside 0.8.x.  Run with:

    pytest __Tools/test_req_validate.py -v
    pytest __Tools/test_req_validate.py::TestValidateRequirement -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# Stub syside before importing req_validate (needed in envs without a licence)
# ---------------------------------------------------------------------------
syside_stub = MagicMock()
sys.modules.setdefault("syside", syside_stub)
sys.modules.setdefault("syside.preview", MagicMock())

_tools_dir = Path(__file__).parent
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from req_validate import (
    get_feature_value,
    get_attr_value,
    get_all_docs,
    get_req_id,
    _req_type_name,
    validate_requirement,
    Severity,
    Violation,
    RequirementResult,
    _ALLOWED_METHODS,
)


# ---------------------------------------------------------------------------
# Mock-shape helpers
#
# The syside Automator proxy uses type(obj).__name__ for duck-typed dispatch,
# so we create named classes rather than plain MagicMocks for model elements.
# ---------------------------------------------------------------------------

# Named types used by req_validate's type().__name__ checks
_AttributeUsage = type("AttributeUsage", (), {})
_PartUsage      = type("PartUsage", (), {})


class _MultiCollect:
    """Collect mock that supports multiple iterations (owned_members called N times)."""
    def __init__(self, items):
        self._items = list(items)

    def collect(self):
        return iter(self._items)


def _fv(value: str):
    """Build a feature_value mock: attr_usage.feature_value.value == value."""
    fv = MagicMock()
    fv.value = value
    return fv


def _attr(name: str, value: str | None = None):
    """Build an AttributeUsage mock."""
    m = _AttributeUsage()
    m.declared_name = name
    m.declared_multiplicity = None        # required by default
    m.feature_value = _fv(value) if value is not None else None
    return m


def _optional_attr(name: str, value: str | None = None):
    m = _attr(name, value)
    m.declared_multiplicity = MagicMock() # non-None → optional
    return m


def _doc(name, body: str):
    d = MagicMock()
    d.declared_name = name
    d.body = body
    return d


def _criteria_part(method: str | None):
    """Build a PartUsage 'criteria' mock with the given verificationMethod."""
    c = _PartUsage()
    c.declared_name = "criteria"
    members = []
    if method is not None:
        vm = _attr("verificationMethod", method)
        members.append(vm)
    c.owned_members = _MultiCollect(members)
    return c


def _make_req(
    type_name: str,
    req_id: str = "REQ-001",
    req_text: str = "The CSCI shall do something.",
    rationale: str = "Because it is needed.",
    def_members: list | None = None,
    req_members: list | None = None,
):
    """
    Build a RequirementUsage mock.

    def_members  — AttributeUsage objects on the definition (for _attrs_from_def)
    req_members  — AttributeUsage / PartUsage objects on the usage (values + criteria)
    """
    el = MagicMock()
    el.declared_name = "testReq"
    el.qualified_name = f"TestPkg::testReq"

    # Short-name ID
    el.req_id    = req_id or None
    el.short_name = req_id or None

    # Documentation
    docs = []
    if req_text is not None:
        docs.append(_doc(None, f"/* {req_text} */"))
    if rationale is not None:
        docs.append(_doc("Rationale", f"/* {rationale} */"))
    el.documentation = _MultiCollect(docs)

    # Type / definition
    rd = MagicMock()
    rd.declared_name = type_name
    rd.owned_members = _MultiCollect(def_members or [])
    el.types = _MultiCollect([rd])

    # Owned members on the usage (attribute values + criteria)
    el.owned_members = _MultiCollect(req_members or [])

    return el


# ---------------------------------------------------------------------------
# get_feature_value
# ---------------------------------------------------------------------------

class TestGetFeatureValue:

    def test_returns_value_from_feature_value(self):
        m = _attr("x", "hello")
        assert get_feature_value(m) == "hello"

    def test_strips_surrounding_quotes(self):
        m = _attr("x", '"quoted"')
        assert get_feature_value(m) == "quoted"

    def test_returns_empty_when_feature_value_is_none(self):
        m = _attr("x")
        assert get_feature_value(m) == ""

    def test_returns_empty_on_exception(self):
        class _Broken:
            @property
            def feature_value(self):
                raise AttributeError("no feature_value")
        assert get_feature_value(_Broken()) == ""


# ---------------------------------------------------------------------------
# get_attr_value
# ---------------------------------------------------------------------------

class TestGetAttrValue:

    def test_finds_named_attribute(self):
        el = MagicMock()
        el.owned_members = _MultiCollect([_attr("capabilityName", "Processing")])
        assert get_attr_value(el, "capabilityName") == "Processing"

    def test_returns_empty_when_absent(self):
        el = MagicMock()
        el.owned_members = _MultiCollect([_attr("other", "val")])
        assert get_attr_value(el, "missing") == ""

    def test_skips_non_attribute_usage_members(self):
        crit = _PartUsage()
        crit.declared_name = "capabilityName"
        crit.feature_value = _fv("should_not_see")
        el = MagicMock()
        el.owned_members = _MultiCollect([crit])
        # PartUsage is not "AttributeUsage" — should not be found
        assert get_attr_value(el, "capabilityName") == ""


# ---------------------------------------------------------------------------
# get_req_id
# ---------------------------------------------------------------------------

class TestGetReqId:

    def test_reads_req_id_attr(self):
        el = MagicMock()
        el.req_id = "REQ-CAP-001"
        el.short_name = None
        assert get_req_id(el) == "REQ-CAP-001"

    def test_falls_back_to_short_name(self):
        el = MagicMock()
        el.req_id = None
        el.short_name = "'REQ-CAP-002'"
        assert get_req_id(el) == "REQ-CAP-002"

    def test_returns_empty_when_both_missing(self):
        el = MagicMock()
        el.req_id = None
        el.short_name = None
        assert get_req_id(el) == ""


# ---------------------------------------------------------------------------
# _req_type_name
# ---------------------------------------------------------------------------

class TestReqTypeName:

    def test_returns_declared_name_of_first_type(self):
        el = MagicMock()
        rd = MagicMock()
        rd.declared_name = "CapabilityRequirement"
        el.types = _MultiCollect([rd])
        assert _req_type_name(el) == "CapabilityRequirement"

    def test_returns_empty_when_no_types(self):
        el = MagicMock()
        el.types = _MultiCollect([])
        assert _req_type_name(el) == ""


# ---------------------------------------------------------------------------
# validate_requirement — integration tests
# ---------------------------------------------------------------------------

class TestValidateRequirement:

    def _valid_capability(self, **kwargs) -> MagicMock:
        """Minimally valid CapabilityRequirement (no def attrs checked — empty def)."""
        return _make_req("CapabilityRequirement", **kwargs)

    # ── doc convention ──────────────────────────────────────────────────────

    def test_valid_requirement_has_no_invalid_violations(self):
        el = self._valid_capability()
        result = validate_requirement(el)
        invalid = [v for v in result.violations if v.severity == Severity.INVALID]
        assert invalid == [], f"Unexpected INVALID violations: {invalid}"

    def test_missing_id_is_invalid(self):
        el = self._valid_capability(req_id="")
        result = validate_requirement(el)
        fields = [v.field for v in result.violations if v.severity == Severity.INVALID]
        assert "id" in fields

    def test_missing_req_text_is_invalid(self):
        el = self._valid_capability(req_text=None)
        result = validate_requirement(el)
        fields = [v.field for v in result.violations if v.severity == Severity.INVALID]
        assert any("doc" in f for f in fields)

    def test_missing_rationale_is_invalid(self):
        el = self._valid_capability(rationale=None)
        result = validate_requirement(el)
        fields = [v.field for v in result.violations if v.severity == Severity.INVALID]
        assert any("Rationale" in f for f in fields)

    # ── required def attributes ─────────────────────────────────────────────

    def test_missing_required_attr_is_invalid(self):
        # def declares capabilityName as required; usage omits it
        def_members = [_attr("capabilityName")]
        el = _make_req(
            "CapabilityRequirement",
            def_members=def_members,
            req_members=[],        # no value provided
        )
        result = validate_requirement(el)
        fields = [v.field for v in result.violations if v.severity == Severity.INVALID]
        assert "capabilityName" in fields

    def test_present_required_attr_has_no_violation(self):
        def_members = [_attr("capabilityName")]
        req_members = [_attr("capabilityName", "Processing")]
        el = _make_req(
            "CapabilityRequirement",
            def_members=def_members,
            req_members=req_members,
        )
        result = validate_requirement(el)
        fields = [v.field for v in result.violations if v.severity == Severity.INVALID]
        assert "capabilityName" not in fields

    def test_missing_optional_attr_is_warning_not_invalid(self):
        def_members = [_optional_attr("latency")]
        el = _make_req(
            "CapabilityRequirement",
            def_members=def_members,
            req_members=[],
        )
        result = validate_requirement(el)
        invalid = [v for v in result.violations
                   if v.severity == Severity.INVALID and v.field == "latency"]
        warnings = [v for v in result.violations
                    if v.severity == Severity.WARNING and v.field == "latency"]
        assert invalid == []
        assert warnings != []

    # ── criteria / verificationMethod ───────────────────────────────────────

    def test_valid_method_for_capability_has_no_violation(self):
        el = _make_req(
            "CapabilityRequirement",
            req_members=[_criteria_part("test")],
        )
        result = validate_requirement(el)
        method_viols = [v for v in result.violations
                        if v.severity == Severity.INVALID
                        and "verificationMethod" in v.field]
        assert method_viols == []

    def test_invalid_method_for_capability_is_invalid(self):
        # "inspect" is not allowed for CapabilityRequirement
        el = _make_req(
            "CapabilityRequirement",
            req_members=[_criteria_part("inspect")],
        )
        result = validate_requirement(el)
        method_viols = [v for v in result.violations
                        if v.severity == Severity.INVALID
                        and "verificationMethod" in v.field]
        assert method_viols != []

    def test_missing_method_in_criteria_is_invalid(self):
        el = _make_req(
            "CapabilityRequirement",
            req_members=[_criteria_part(None)],
        )
        result = validate_requirement(el)
        method_viols = [v for v in result.violations
                        if v.severity == Severity.INVALID
                        and "verificationMethod" in v.field]
        assert method_viols != []

    # ── _ALLOWED_METHODS content ─────────────────────────────────────────────

    def test_allowed_methods_uses_stdlib_names(self):
        # All values in _ALLOWED_METHODS should be stdlib lowercase names
        stdlib_names = {"test", "analyze", "inspect", "demo"}
        for req_type, methods in _ALLOWED_METHODS.items():
            unexpected = methods - stdlib_names
            assert unexpected == set(), \
                f"{req_type} has non-stdlib method names: {unexpected}"
