#!/usr/bin/env python3
"""
req_validate.py — SRS Requirement Validator
============================================
Validates SRS_Definitions-typed requirements in a SysML v2 model against two
rule levels:

  VALID    — all assert constraint conditions from SRS_Definitions are met:
               • id is set (non-empty)
               • text is set (non-empty)
               • type-specific attributes are populated
               • verificationMethod is valid for the requirement type (if criteria present)

  COMPLETE — all non-optional/recommended attributes are populated:
               • rationale, source, priority, criticality set
               • criteria part present with all fields populated
               • type-specific optional attributes set

Usage:
  python req_validate.py <model_dir> [options]

Options:
  -o, --output <dir>    Output directory (default: ./__output)
  -f, --format <fmt>    Output format: text (default), markdown, json
  --level <level>       Minimum level to report: valid (default), complete, all
  --package <name>      Filter to a specific package name
  --fail-on-invalid     Exit code 1 if any INVALID requirements found
  --fail-on-incomplete  Exit code 1 if any INCOMPLETE requirements found
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import syside
from syside.preview import open_model


# ---------------------------------------------------------------------------
# Constraint overlay — rules that cannot be inferred from model structure
#
# The model tells us WHICH attributes exist on each requirement def.
# It does NOT tell us:
#   - which verification methods are valid per type (from assert constraints)
#   - which [0..1] attributes are semantically required vs truly optional
#   - which attributes form a "performance group" (at-least-one rule)
#
# This overlay is keyed by unqualified type name. Any type found in
# SRS_Definitions that is NOT listed here gets default rules (no method
# restriction, all non-base attrs treated as optional).
#
# When you add a new requirement def to SRS_Definitions.sysml, you only
# need to add an entry here if it has non-default verification method
# restrictions or a performance-group rule.
# ---------------------------------------------------------------------------

CONSTRAINT_OVERLAY: dict[str, dict] = {
    "SRS_Requirement": {
        "valid_methods":     None,   # no restriction on base type
        "performance_attrs": [],
    },
    "PerformanceAspect": {
        "valid_methods":     None,
        "performance_attrs": ["performance", "timing", "throughput", "latency", "accuracy"],
    },
    "CapabilityRequirement": {
        "valid_methods":     {"Test", "Analysis"},
        "performance_attrs": ["performance", "timing", "throughput", "latency", "accuracy"],
    },
    "DataAspect": {
        "valid_methods":     None,
        "performance_attrs": [],
    },
    "DataRequirement": {
        "valid_methods":     {"Analysis", "Inspection"},
        "performance_attrs": [],
    },
    "InterfaceAspect": {
        "valid_methods":     None,
        "performance_attrs": [],
    },
    "InterfaceRequirement": {
        "valid_methods":     {"Test", "Inspection", "Demonstration"},
        "performance_attrs": [],
    },
    "SafetyRequirement": {
        "valid_methods":     {"Analysis", "Test", "Inspection"},
        "performance_attrs": [],
    },
    "SecurityRequirement": {
        "valid_methods":     {"Analysis", "Test"},
        "performance_attrs": [],
    },
    "EnvironmentalRequirement": {
        "valid_methods":     {"Test", "Analysis"},
        "performance_attrs": [],
    },
    "ResourceRequirement": {
        "valid_methods":     {"Analysis", "Inspection"},
        "performance_attrs": [],
    },
    "QualityRequirement": {
        "valid_methods":     {"Test", "Analysis"},
        "performance_attrs": [],
    },
    "DesignConstraintRequirement": {
        "valid_methods":     {"Inspection", "Analysis"},
        "performance_attrs": [],
    },
    "AdaptationRequirement": {
        "valid_methods":     {"Test", "Analysis"},
        "performance_attrs": [],
    },
    "COTSRequirement": {
        "valid_methods":     {"Inspection", "Analysis"},
        "performance_attrs": [],
    },
}

# Default SRS_Definitions package name — overridden by --srs-package CLI arg.
_SRS_DEFS_PACKAGE = "SRS_Definitions"

# All of the following are populated at runtime by build_req_type_config().
# They are declared here as mutable module-level state so that validate_requirement
# and render functions can reference them without threading extra arguments.

# REQ_TYPE_CONFIG — per-type validation rules, keyed by unqualified type name.
REQ_TYPE_CONFIG: dict[str, dict] = {}

# _BASE_ATTR_NAMES — attribute names declared on the base RequirementDefinition;
# excluded from per-type attr discovery so they don't appear as type-specific attrs.
_BASE_ATTR_NAMES: set[str] = set()

# BASE_REQUIRED_ATTRS — [1]-multiplicity attributes on the base type (VALID checks).
BASE_REQUIRED_ATTRS: list[str] = []

# BASE_COMPLETE_ATTRS — [0..1]-multiplicity attributes on the base type (COMPLETE checks).
BASE_COMPLETE_ATTRS: list[str] = []

# _CRITERIA_PART_NAME — declared name of the criteria part on the base type.
_CRITERIA_PART_NAME: str = "criteria"

# CRITERIA_COMPLETE_ATTRS — attributes on the VerificationCriteria part def (COMPLETE checks).
CRITERIA_COMPLETE_ATTRS: list[str] = []


# ---------------------------------------------------------------------------
# Runtime config builder — reads SRS_Definitions from the model
# ---------------------------------------------------------------------------

def _humanize(name: str) -> str:
    """Convert CamelCase or snake_case name to a readable display label."""
    # Insert space before uppercase letters following lowercase
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    # Replace underscores with spaces
    return spaced.replace("_", " ")


def _collect_req_defs(root, results: list):
    """Depth-first collection of RequirementDefinition elements."""
    if root.isinstance(syside.RequirementDefinition.STD):
        results.append(root.cast(syside.RequirementDefinition.STD))
    if root.isinstance(syside.Namespace.STD):
        ns = root.cast(syside.Namespace.STD)
        for member in ns.owned_members.collect():
            _collect_req_defs(member, results)


def _is_base_type(rd, all_type_names: set[str]) -> bool:
    """
    Return True if rd has no specialization parents within the SRS_Definitions
    package. The base RequirementDefinition is the one whose owned_specializations
    all point outside the package (i.e., to standard library types only).
    """
    try:
        for spec in rd.owned_specializations.collect():
            try:
                general = spec.general
                if general is not None:
                    gname = general.declared_name or ""
                    if gname in all_type_names and gname != rd.declared_name:
                        return False
            except Exception:
                pass
    except Exception:
        pass
    return True


def _is_optional_multiplicity(mult) -> bool:
    """
    Return True if the MultiplicityRange represents an optional feature
    ([0..1] or [0..*]), False if it represents a required feature ([1]).

    Confirmed ground truth from req_debug output:
      [0..1]  → lower_bound = LiteralInteger(0),  upper_bound = LiteralInteger(1)
      [1]     → lower_bound = None,               upper_bound = LiteralInteger(1)
      [*]     → lower_bound = None,               upper_bound = None (or LiteralInfinity)
      None    → no MultiplicityRange at all       → default [1] → required

    Rule: optional if and only if lower_bound is a LiteralInteger with value == 0.
    Every other case (lower_bound None, lower_bound >= 1) is required.
    """
    if mult is None:
        return False
    try:
        lb = mult.lower_bound
        if lb is None:
            # No lower bound object → [1] or [*] default → required
            return False
        val = getattr(lb, 'value', None)
        if val is not None:
            return int(val) == 0
        # lower_bound present but no direct .value — try owned_members one level
        try:
            for child in lb.owned_members.collect():
                val = getattr(child, 'value', None)
                if val is not None:
                    return int(val) == 0
        except Exception:
            pass
    except Exception:
        pass
    # Could not read lower bound — conservative: treat as required
    return False


def _attrs_from_def(req_def, exclude: set[str]) -> tuple[list[str], list[str]]:
    """
    Return (required_attrs, optional_attrs) declared directly on req_def,
    excluding any names in the exclude set.

    Uses owned_members filtered to AttributeUsage only.

    Multiplicity strategy (confirmed from req_debug output):
      - declared_multiplicity is None   → default [1]       → required
      - declared_multiplicity is present, lower bound == 0  → [0..1] or [0..*] → optional
      - declared_multiplicity is present, lower bound >= 1  → [1] explicit      → required
      - declared_multiplicity present but lower unreadable  → fall back to
        Has<AttrName> constraint presence, then default required

    Also cross-references AssertConstraintUsage names of the form Has<AttrName>
    as a secondary signal that an attribute is required (belt-and-suspenders for
    attributes that use the default multiplicity with an explicit constraint).
    """
    # First pass: collect Has<AttrName> constraint names → required signals
    has_constrained: set[str] = set()
    try:
        for member in req_def.owned_members.collect():
            if type(member).__name__ != 'AssertConstraintUsage':
                continue
            cname = member.declared_name or ""
            if cname.startswith("Has") and len(cname) > 3:
                attr = cname[3:]
                attr = attr[0].lower() + attr[1:]
                has_constrained.add(attr)
    except Exception:
        pass

    # Second pass: classify each AttributeUsage
    required: list[str] = []
    optional: list[str] = []
    try:
        for member in req_def.owned_members.collect():
            if type(member).__name__ != 'AttributeUsage':
                continue
            name = member.declared_name
            if not name or name in exclude:
                continue
            mult = member.declared_multiplicity
            if mult is None:
                # No explicit multiplicity — default [1], required
                required.append(name)
            elif _is_optional_multiplicity(mult):
                # Lower bound is 0 → [0..1] or [0..*] → optional
                optional.append(name)
            else:
                # Explicit multiplicity with lower bound None or >= 1 → required
                required.append(name)
    except Exception:
        pass
    return required, optional


def _criteria_attrs_from_part_def(part_def) -> list[str]:
    """
    Return all attribute names declared on a PartDefinition (e.g. VerificationCriteria).
    Uses owned_members filtered to AttributeUsage — nested_attributes does not
    exist on PartDefinition (confirmed from req_debug output).
    """
    names: list[str] = []
    try:
        for member in part_def.owned_members.collect():
            if type(member).__name__ != 'AttributeUsage':
                continue
            name = member.declared_name
            if name:
                names.append(name)
    except Exception:
        pass
    return names


def _find_criteria_part_def(base_rd):
    """
    Walk the base RequirementDefinition's owned_members to find the optional
    [0..1] PartUsage (the criteria part). Return the PartDefinition it is typed
    by, or None if not found.

    Uses owned_members filtered to PartUsage — nested_parts does not exist on
    RequirementDefinition (confirmed from req_debug output).
    """
    try:
        for member in base_rd.owned_members.collect():
            if type(member).__name__ != 'PartUsage':
                continue
            mult = member.declared_multiplicity
            if mult is not None and "0" in str(mult):
                # This is the [0..1] criteria part — get its type
                try:
                    for typing in member.owned_typings.collect():
                        td = getattr(typing, "type", None)
                        if td is not None and td.isinstance(syside.PartDefinition.STD):
                            return td.cast(syside.PartDefinition.STD)
                except Exception:
                    pass
    except Exception:
        pass
    return None


def build_req_type_config(model_dir: Path, srs_package: str = _SRS_DEFS_PACKAGE) -> dict[str, dict]:
    """
    Build REQ_TYPE_CONFIG and populate all derived runtime constants by reading
    the SRS_Definitions package from the model.

    Derives from the model:
      - Which RequirementDefinition is the base (no intra-package specialization parents)
      - _BASE_ATTR_NAMES, BASE_REQUIRED_ATTRS, BASE_COMPLETE_ATTRS from base type attrs
      - _CRITERIA_PART_NAME from the base type's [0..1] nested part
      - CRITERIA_COMPLETE_ATTRS from the VerificationCriteria PartDefinition attrs
      - Per-type required/optional attrs for all specializations
      - valid_methods and performance_attrs from CONSTRAINT_OVERLAY

    Returns the populated config dict.
    """
    global _BASE_ATTR_NAMES, BASE_REQUIRED_ATTRS, BASE_COMPLETE_ATTRS
    global _CRITERIA_PART_NAME, CRITERIA_COMPLETE_ATTRS

    config: dict[str, dict] = {}

    with open_model(model_dir) as model:
        for top in model.top_elements_from(model_dir):
            if not top.isinstance(syside.Namespace.STD):
                continue
            if top.declared_name != srs_package:
                continue

            # Collect all RequirementDefinitions in the package
            req_defs: list = []
            _collect_req_defs(top, req_defs)
            if not req_defs:
                break

            all_type_names = {rd.declared_name for rd in req_defs if rd.declared_name}

            # Identify the base type
            base_rd = None
            for rd in req_defs:
                if _is_base_type(rd, all_type_names):
                    base_rd = rd
                    break

            if base_rd is None:
                print(f"[WARN] Could not identify base RequirementDefinition in "
                      f"'{srs_package}'. Using empty base attr lists.",
                      file=sys.stderr)
                base_required: list[str] = []
                base_optional: list[str] = []
            else:
                base_required, base_optional = _attrs_from_def(base_rd, exclude=set())
                if base_rd.declared_name:
                    print(f"[INFO] Base RequirementDefinition: '{base_rd.declared_name}' "
                          f"(required: {base_required}, optional: {base_optional})")

            # Populate global base attr constants from the model
            _BASE_ATTR_NAMES  = set(base_required) | set(base_optional)
            BASE_REQUIRED_ATTRS[:] = base_required
            BASE_COMPLETE_ATTRS[:] = base_optional

            # Find and populate criteria attrs from the base type's [0..1] part
            if base_rd is not None:
                criteria_part_def = _find_criteria_part_def(base_rd)
                if criteria_part_def is not None:
                    cname = criteria_part_def.declared_name
                    # Find the declared name of the criteria part usage itself
                    try:
                        for part in base_rd.owned_members.collect():
                            if type(part).__name__ != 'PartUsage':
                                continue
                            mult = part.declared_multiplicity
                            if mult is not None and "0" in str(mult):
                                if part.declared_name:
                                    _CRITERIA_PART_NAME = part.declared_name
                                break
                    except Exception:
                        pass
                    criteria_attrs = _criteria_attrs_from_part_def(criteria_part_def)
                    CRITERIA_COMPLETE_ATTRS[:] = criteria_attrs
                    print(f"[INFO] Criteria part: '{_CRITERIA_PART_NAME}' "
                          f"typed by '{cname}' "
                          f"(attrs: {criteria_attrs})")

            # Build per-type config for all requirement defs
            for rd in req_defs:
                type_name = rd.declared_name
                if not type_name:
                    continue

                required_attrs, optional_attrs = _attrs_from_def(rd, exclude=_BASE_ATTR_NAMES)
                overlay = CONSTRAINT_OVERLAY.get(type_name, {})

                config[type_name] = {
                    "display":             _humanize(type_name),
                    "valid_methods":       overlay.get("valid_methods", None),
                    "performance_attrs":   overlay.get("performance_attrs", []),
                    "required_type_attrs": required_attrs,
                    "optional_type_attrs": optional_attrs,
                }

            break  # Found and processed the package — no need to continue

    if not config:
        print(f"[WARN] No RequirementDefinition elements found in package "
              f"'{srs_package}'. Falling back to empty config — "
              f"all requirements will appear UNTYPED.", file=sys.stderr)

    return config


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class ValidationLevel(Enum):
    VALID    = "VALID"
    COMPLETE = "COMPLETE"


class RuleCategory(Enum):
    BASE        = "base"
    TYPE        = "type-specific"
    PERFORMANCE = "performance"
    CRITERIA    = "criteria"


@dataclass
class RuleViolation:
    level:      ValidationLevel   # which level this violation belongs to
    category:   RuleCategory
    attribute:  str               # attribute or feature name involved
    message:    str


@dataclass
class RequirementResult:
    element_id:    str
    short_id:      str            # the <'ID'> declared identifier, if any
    qualified_name: str
    req_type:      str            # unqualified type name
    package:       str
    violations:    list[RuleViolation] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(v.level == ValidationLevel.VALID for v in self.violations)

    @property
    def is_complete(self) -> bool:
        return self.is_valid and not any(v.level == ValidationLevel.COMPLETE for v in self.violations)

    @property
    def status(self) -> str:
        if not self.is_valid:
            return "INVALID"
        if not self.is_complete:
            return "INCOMPLETE"
        return "COMPLETE"


# ---------------------------------------------------------------------------
# Model parsing (SysIDE Automator API)
# ---------------------------------------------------------------------------

def _req_type_name(element) -> Optional[str]:
    """
    Return the unqualified type name of a requirement usage element,
    matched against REQ_TYPE_CONFIG keys.

    Tries three accessors in order (confirmed from dir() dump):
      1. requirement_definition — direct typed definition accessor on RequirementUsage
      2. owned_typings.collect() — the owned FeatureTyping relationships
      3. types.collect() — broader type collection fallback
    """
    # Attempt 1: requirement_definition (direct accessor, cleanest)
    try:
        rd = element.requirement_definition
        if rd is not None:
            name = rd.declared_name or ""
            short = name.split("::")[-1]
            if short in REQ_TYPE_CONFIG:
                return short
    except Exception:
        pass

    # Attempt 2: owned_typings (FeatureTyping relationships)
    try:
        for typing in element.owned_typings.collect():
            # Each FeatureTyping has a .type pointing to the definition
            td = getattr(typing, "type", None)
            if td is None:
                continue
            name = td.declared_name or ""
            short = name.split("::")[-1]
            if short in REQ_TYPE_CONFIG:
                return short
    except Exception:
        pass

    # Attempt 3: types (broader collection)
    try:
        for td in element.types.collect():
            name = td.declared_name or ""
            short = name.split("::")[-1]
            if short in REQ_TYPE_CONFIG:
                return short
    except Exception:
        pass

    return None


def _short_id(element) -> str:
    """
    Extract the <'ID'> declared short identifier.
    The <'AUT.1'> syntax sets req_id / short_name on RequirementUsage.
    """
    try:
        rid = element.req_id
        if rid:
            return str(rid).strip("'\"")
    except Exception:
        pass
    try:
        sn = element.short_name
        if sn:
            return str(sn).strip("'\"")
    except Exception:
        pass
    return ""


def _package_name(element) -> str:
    """Return the name of the nearest owning namespace/package."""
    try:
        ns = element.owning_namespace
        if ns is not None:
            return ns.declared_name or "<unnamed>"
    except Exception:
        pass
    return "<unknown>"


def _feature_value(member) -> Optional[str]:
    """
    Extract the string value from a feature's FeatureValue relationship.

    Confirmed access path from req_debug output:
      feature_value_expression  → LiteralString object
      feature_value_expression.value → the actual string (e.g. 'AUT.1')

    Fallback: walk owned_members for a LiteralString sub-element with .value.
    Returns the literal text stripped of surrounding quotes, or None.
    """
    # Primary: feature_value_expression.value (LiteralString)
    try:
        expr = member.feature_value_expression
        if expr is not None:
            val = getattr(expr, 'value', None)
            if val is not None:
                return str(val).strip('"\'')
            # expr itself might be a plain string in some cases
            s = str(expr).strip('"\'')
            if s and not s.startswith('<'):   # exclude object reprs like <syside.core...>
                return s
    except Exception:
        pass
    # Fallback: owned_members — look for a LiteralString or element with .value
    try:
        for sub in member.owned_members.collect():
            val = getattr(sub, 'value', None)
            if val is not None:
                return str(val).strip('"\'')
    except Exception:
        pass
    return None


def _iter_attribute_members(element):
    """
    Yield all attribute-like members of a requirement usage, covering both
    directly owned attributes and nested_attributes (which is where :>> redefinitions
    appear in the Automator API).
    """
    # nested_attributes covers :>> attribute redefinitions
    try:
        for m in element.nested_attributes.collect():
            yield m
    except Exception:
        pass
    # owned_members as fallback for any remaining direct members
    try:
        for m in element.owned_members.collect():
            yield m
    except Exception:
        pass


def _member_name(member) -> Optional[str]:
    """
    Return the effective attribute name for a member.

    For direct declarations:  declared_name is set (e.g. 'missionPlanningTime')
    For :>> redefinitions:    declared_name is None; the redefined feature name
                              is on referenced_feature.declared_name
                              (confirmed from req_debug output: AUT.1 id redefinition
                               has declared_name=None, value on fve.value)
    """
    # Direct name
    name = member.declared_name
    if name:
        return name
    # Redefinition — walk referenced_feature chain
    try:
        rf = member.referenced_feature
        if rf is not None:
            return rf.declared_name or None
    except Exception:
        pass
    # Also try owned_redefinitions
    try:
        for redef in member.owned_redefinitions.collect():
            try:
                redefed = redef.redefined_feature
                if redefed is not None:
                    return redefed.declared_name or None
            except Exception:
                pass
    except Exception:
        pass
    return None


def _attr_value(element, attr_name: str) -> Optional[str]:
    """
    Return the string value of a named attribute on a requirement usage.

    Searches nested_attributes first (where :>> redefinitions live),
    then falls back to owned_members. Matches on both declared_name (direct
    declarations) and referenced_feature.declared_name (:>> redefinitions).
    Returns None if the attribute is not present at all.
    Returns empty string if found but no value is assigned.
    """
    seen_ids: set = set()
    for member in _iter_attribute_members(element):
        eid = getattr(member, 'element_id', None)
        if eid and eid in seen_ids:
            continue
        if eid:
            seen_ids.add(eid)
        if _member_name(member) == attr_name:
            val = _feature_value(member)
            return val if val is not None else ""
    return None


def _criteria_attrs(element) -> dict:
    """
    Find the 'criteria' part redefinition and extract its sub-attribute values.
    Searches nested_parts (where :>> part redefinitions live) then owned_members.
    Returns a dict of {attr_name: value_or_empty_string}.
    An empty dict means no criteria part is present.
    """
    result: dict = {}

    # Find the criteria part — lives in nested_parts for :>> redefinitions
    criteria_member = None
    try:
        for m in element.nested_parts.collect():
            if m.declared_name == 'criteria':
                criteria_member = m
                break
    except Exception:
        pass
    if criteria_member is None:
        try:
            for m in element.owned_members.collect():
                if m.declared_name == 'criteria':
                    criteria_member = m
                    break
        except Exception:
            pass
    if criteria_member is None:
        return result

    # Extract sub-attributes from the criteria part
    for sub in _iter_attribute_members(criteria_member):
        name = sub.declared_name
        if name:
            val = _feature_value(sub)
            result[name] = val if val is not None else ""
    return result


def _collect_typed(root, std_type, results: list):
    """Depth-first collection of all elements matching std_type."""
    if root.isinstance(std_type):
        results.append(root.cast(std_type))
    if root.isinstance(syside.Namespace.STD):
        ns = root.cast(syside.Namespace.STD)
        for member in ns.owned_members.collect():
            _collect_typed(member, std_type, results)


def collect_requirements(model_dir: Path) -> tuple[list, list]:
    """
    Walk the model and collect RequirementUsage elements.
    Returns:
      typed   — list of (element, req_type_name) for SRS_Definitions-typed requirements
      untyped — list of elements with no recognised SRS_Definitions type
    """
    raw_usages = []
    with open_model(model_dir) as model:
        for top in model.top_elements_from(model_dir):
            _collect_typed(top, syside.RequirementUsage.STD, raw_usages)

    typed   = []
    untyped = []
    for element in raw_usages:
        # Exclude SatisfyRequirementUsage — these are satisfy statements, not
        # declared requirements, and should never be flagged as untyped.
        if element.isinstance(syside.SatisfyRequirementUsage.STD):
            continue
        req_type = _req_type_name(element)
        if req_type is None:
            untyped.append(element)
        else:
            typed.append((element, req_type))
    return typed, untyped


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

def validate_requirement(element, req_type: str) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    cfg = REQ_TYPE_CONFIG.get(req_type, {})

    # -----------------------------------------------------------------------
    # VALID rules — base attributes
    # -----------------------------------------------------------------------
    for attr in BASE_REQUIRED_ATTRS:
        val = _attr_value(element, attr)
        if val is None or val.strip() == "":
            violations.append(RuleViolation(
                level=ValidationLevel.VALID,
                category=RuleCategory.BASE,
                attribute=attr,
                message=f"Required attribute '{attr}' is missing or empty.",
            ))

    # -----------------------------------------------------------------------
    # VALID rules — type-specific required attributes
    # -----------------------------------------------------------------------
    for attr in cfg.get("required_type_attrs", []):
        val = _attr_value(element, attr)
        if val is None or val.strip() == "":
            violations.append(RuleViolation(
                level=ValidationLevel.VALID,
                category=RuleCategory.TYPE,
                attribute=attr,
                message=f"Required attribute '{attr}' for {req_type} is missing or empty.",
            ))

    # -----------------------------------------------------------------------
    # VALID rules — PerformanceDefined (at least one performance attr set)
    # -----------------------------------------------------------------------
    perf_attrs = cfg.get("performance_attrs", [])
    if perf_attrs:
        perf_values = [_attr_value(element, a) for a in perf_attrs]
        any_set = any(v is not None and v.strip() != "" for v in perf_values)
        if not any_set:
            violations.append(RuleViolation(
                level=ValidationLevel.VALID,
                category=RuleCategory.PERFORMANCE,
                attribute="performance/timing/throughput/latency/accuracy",
                message=f"At least one performance attribute must be set "
                        f"({', '.join(perf_attrs)}).",
            ))

    # -----------------------------------------------------------------------
    # VALID rules — verificationMethod valid for type (if criteria present)
    # -----------------------------------------------------------------------
    valid_methods = cfg.get("valid_methods")
    if valid_methods is not None:
        criteria = _criteria_attrs(element)
        if criteria:  # criteria part is present
            method_val = criteria.get("verificationMethod", "")
            if method_val is None or method_val.strip() == "":
                violations.append(RuleViolation(
                    level=ValidationLevel.VALID,
                    category=RuleCategory.CRITERIA,
                    attribute="criteria.verificationMethod",
                    message=f"'criteria.verificationMethod' is required when criteria "
                            f"is defined.",
                ))
            else:
                # Strip enum qualifier if present (e.g. "VerificationMethodKind::Test" → "Test")
                method_short = method_val.split("::")[-1].strip()
                if method_short not in valid_methods:
                    violations.append(RuleViolation(
                        level=ValidationLevel.VALID,
                        category=RuleCategory.CRITERIA,
                        attribute="criteria.verificationMethod",
                        message=f"Verification method '{method_short}' is not valid for "
                                f"{req_type}. Allowed: {sorted(valid_methods)}.",
                    ))

            # passFailLogic must be non-empty when criteria is present
            pfl = criteria.get("passFailLogic", "")
            if pfl is None or pfl.strip() == "":
                violations.append(RuleViolation(
                    level=ValidationLevel.VALID,
                    category=RuleCategory.CRITERIA,
                    attribute="criteria.passFailLogic",
                    message="'criteria.passFailLogic' is required when criteria is defined.",
                ))

    # -----------------------------------------------------------------------
    # COMPLETE rules — base optional attributes
    # -----------------------------------------------------------------------
    for attr in BASE_COMPLETE_ATTRS:
        val = _attr_value(element, attr)
        if val is None or val.strip() == "":
            violations.append(RuleViolation(
                level=ValidationLevel.COMPLETE,
                category=RuleCategory.BASE,
                attribute=attr,
                message=f"Recommended attribute '{attr}' is not set.",
            ))

    # -----------------------------------------------------------------------
    # COMPLETE rules — criteria recommended when it is meaningful
    # -----------------------------------------------------------------------
    if valid_methods is not None:  # type has a verification method constraint
        criteria = _criteria_attrs(element)
        if not criteria:
            violations.append(RuleViolation(
                level=ValidationLevel.COMPLETE,
                category=RuleCategory.CRITERIA,
                attribute="criteria",
                message="Verification criteria are not defined. Consider adding a "
                        "'criteria' part with method, pass/fail logic, and threshold.",
            ))
        else:
            for attr in CRITERIA_COMPLETE_ATTRS:
                val = criteria.get(attr)
                if val is None or val.strip() == "":
                    violations.append(RuleViolation(
                        level=ValidationLevel.COMPLETE,
                        category=RuleCategory.CRITERIA,
                        attribute=f"criteria.{attr}",
                        message=f"Recommended criteria attribute '{attr}' is not set.",
                    ))

    # -----------------------------------------------------------------------
    # COMPLETE rules — type-specific optional attributes
    # -----------------------------------------------------------------------
    for attr in cfg.get("optional_type_attrs", []):
        val = _attr_value(element, attr)
        if val is None or val.strip() == "":
            violations.append(RuleViolation(
                level=ValidationLevel.COMPLETE,
                category=RuleCategory.TYPE,
                attribute=attr,
                message=f"Optional attribute '{attr}' for {req_type} is not set.",
            ))

    return violations


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

STATUS_EMOJI = {"COMPLETE": "✅", "INCOMPLETE": "⚠️", "INVALID": "❌"}
STATUS_ORDER = {"INVALID": 0, "INCOMPLETE": 1, "COMPLETE": 2}


def _summary_stats(results: list[RequirementResult]) -> dict:
    total    = len(results)
    invalid  = sum(1 for r in results if not r.is_valid)
    incomplete = sum(1 for r in results if r.is_valid and not r.is_complete)
    complete = sum(1 for r in results if r.is_complete)
    return dict(total=total, invalid=invalid, incomplete=incomplete, complete=complete)


def render_text(results: list[RequirementResult], min_level: str) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("SRS Requirement Validation Report")
    lines.append("=" * 72)

    show_incomplete = min_level in ("complete", "all")
    show_complete   = min_level == "all"

    sorted_results = sorted(results, key=lambda r: (STATUS_ORDER[r.status], r.qualified_name))

    for r in sorted_results:
        if r.status == "COMPLETE" and not show_complete:
            continue
        if r.status == "INCOMPLETE" and not show_incomplete:
            continue

        emoji = STATUS_EMOJI[r.status]
        lines.append(f"\n{emoji} [{r.status}] {r.qualified_name}")
        lines.append(f"   Type:    {REQ_TYPE_CONFIG.get(r.req_type, {}).get('display', r.req_type)}")
        lines.append(f"   ShortID: {r.short_id or '(none)'}")
        lines.append(f"   Package: {r.package}")

        valid_viols    = [v for v in r.violations if v.level == ValidationLevel.VALID]
        complete_viols = [v for v in r.violations if v.level == ValidationLevel.COMPLETE]

        if valid_viols:
            lines.append("   ── VALIDITY violations ──────────────────────────────")
            for v in valid_viols:
                lines.append(f"   ❌  [{v.category.value}] {v.attribute}")
                lines.append(f"       {v.message}")

        if complete_viols and show_incomplete:
            lines.append("   ── COMPLETENESS gaps ────────────────────────────────")
            for v in complete_viols:
                lines.append(f"   ⚠️   [{v.category.value}] {v.attribute}")
                lines.append(f"       {v.message}")

    lines.append("\n" + "=" * 72)
    stats = _summary_stats(results)
    lines.append(f"Summary: {stats['total']} requirements checked")
    lines.append(f"  ❌ INVALID:    {stats['invalid']}")
    lines.append(f"  ⚠️  INCOMPLETE: {stats['incomplete']}")
    lines.append(f"  ✅ COMPLETE:   {stats['complete']}")
    lines.append("=" * 72)
    return "\n".join(lines)


def render_markdown(results: list[RequirementResult], min_level: str,
                    untyped_names: list[str] | None = None) -> str:
    lines = []
    lines.append("# SRS Requirement Validation Report\n")

    stats = _summary_stats(results)
    untyped_count = len(untyped_names) if untyped_names else 0
    lines.append(f"| Status | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| ❌ INVALID | {stats['invalid']} |")
    lines.append(f"| ⚠️ INCOMPLETE | {stats['incomplete']} |")
    lines.append(f"| ✅ COMPLETE | {stats['complete']} |")
    if untyped_count:
        lines.append(f"| 🔷 UNTYPED | {untyped_count} |")
    lines.append(f"| **Total** | **{stats['total'] + untyped_count}** |\n")

    show_incomplete = min_level in ("complete", "all")
    show_complete   = min_level == "all"

    sorted_results = sorted(results, key=lambda r: (STATUS_ORDER[r.status], r.qualified_name))

    for r in sorted_results:
        if r.status == "COMPLETE" and not show_complete:
            continue
        if r.status == "INCOMPLETE" and not show_incomplete:
            continue

        emoji = STATUS_EMOJI[r.status]
        lines.append(f"## {emoji} `{r.qualified_name}`\n")
        lines.append(f"- **Status:** {r.status}")
        lines.append(f"- **Type:** {REQ_TYPE_CONFIG.get(r.req_type, {}).get('display', r.req_type)}")
        lines.append(f"- **Short ID:** `{r.short_id or '(none)'}`")
        lines.append(f"- **Package:** `{r.package}`\n")

        valid_viols    = [v for v in r.violations if v.level == ValidationLevel.VALID]
        complete_viols = [v for v in r.violations if v.level == ValidationLevel.COMPLETE]

        if valid_viols:
            lines.append("### Validity Violations\n")
            lines.append("| Attribute | Category | Issue |")
            lines.append("|-----------|----------|-------|")
            for v in valid_viols:
                lines.append(f"| `{v.attribute}` | {v.category.value} | {v.message} |")
            lines.append("")

        if complete_viols:
            lines.append("### Completeness Gaps\n")
            lines.append("| Attribute | Category | Gap |")
            lines.append("|-----------|----------|-----|")
            for v in complete_viols:
                lines.append(f"| `{v.attribute}` | {v.category.value} | {v.message} |")
            lines.append("")

    # Untyped requirements section — after all typed entries
    if untyped_names:
        lines.append("## 🔷 Untyped Requirements\n")
        lines.append("The following requirements are not typed by any `SRS_Definitions` "
                     "requirement type. They will not be validated until a type is assigned.\n")
        lines.append("| Qualified Name |")
        lines.append("|----------------|")
        for name in sorted(untyped_names):
            lines.append(f"| `{name}` |")
        lines.append("")

    return "\n".join(lines)


def render_json(results: list[RequirementResult]) -> str:
    out = []
    for r in results:
        out.append({
            "element_id":    r.element_id,
            "short_id":      r.short_id,
            "qualified_name": r.qualified_name,
            "req_type":      r.req_type,
            "package":       r.package,
            "status":        r.status,
            "violations": [
                {
                    "level":     v.level.value,
                    "category":  v.category.value,
                    "attribute": v.attribute,
                    "message":   v.message,
                }
                for v in r.violations
            ],
        })
    return json.dumps(out, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Validate SRS_Definitions-typed requirements in a SysML v2 model."
    )
    p.add_argument("model_dir", help="Directory containing .sysml model files")
    p.add_argument("-o", "--output", default=None,
                   help="Output directory (default: <cwd>/__output)")
    p.add_argument("-f", "--format", choices=["text", "markdown", "json"],
                   default="markdown", help="Output format (default: markdown)")
    p.add_argument("--level", choices=["valid", "complete", "all"],
                   default="all",
                   help="Minimum violation level to include in report "
                        "(valid=INVALID only, complete=INVALID+INCOMPLETE, all=everything (default))")
    p.add_argument("--package", default=None,
                   help="Filter to requirements in a specific package")
    p.add_argument("--srs-package", default=_SRS_DEFS_PACKAGE,
                   help=f"Name of the SRS definitions package in the model "
                        f"(default: '{_SRS_DEFS_PACKAGE}')")
    p.add_argument("--fail-on-invalid", action="store_true",
                   help="Exit with code 1 if any INVALID requirements are found")
    p.add_argument("--fail-on-incomplete", action="store_true",
                   help="Exit with code 1 if any INCOMPLETE requirements are found")
    return p.parse_args()


def main():
    args = parse_args()

    model_dir = Path(args.model_dir).resolve()
    if not model_dir.is_dir():
        print(f"[ERROR] Model directory not found: {model_dir}", file=sys.stderr)
        sys.exit(2)

    output_dir = Path(args.output).resolve() if args.output else Path.cwd() / "__output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # Collect and validate requirements
    # -----------------------------------------------------------------------
    print(f"[INFO] Loading model from: {model_dir}")

    # Build type config from SRS_Definitions package before collecting
    global REQ_TYPE_CONFIG
    REQ_TYPE_CONFIG = build_req_type_config(model_dir, srs_package=args.srs_package)
    if REQ_TYPE_CONFIG:
        print(f"[INFO] Found {len(REQ_TYPE_CONFIG)} requirement type(s) "
              f"in {args.srs_package}: {', '.join(sorted(REQ_TYPE_CONFIG))}")

    raw, untyped = collect_requirements(model_dir)

    if not raw:
        print("[WARN] No SRS_Definitions-typed requirements found in model.")
        sys.exit(0)

    print(f"[INFO] Found {len(raw)} SRS-typed requirement(s). Validating...")

    results: list[RequirementResult] = []
    for element, req_type in raw:
        pkg = _package_name(element)
        if args.package and pkg != args.package:
            continue

        qname = str(element.qualified_name or element.declared_name or "<unnamed>")
        eid   = element.element_id or ""
        sid   = _short_id(element)

        violations = validate_requirement(element, req_type)

        results.append(RequirementResult(
            element_id=eid,
            short_id=sid,
            qualified_name=qname,
            req_type=req_type,
            package=pkg,
            violations=violations,
        ))

    # Build untyped names list for report (resolve to strings now, outside open_model context)
    untyped_names = [
        str(el.qualified_name or el.declared_name or "<unnamed>")
        for el in untyped
    ]

    # -----------------------------------------------------------------------
    # Console output — print problems as they are found
    # -----------------------------------------------------------------------
    # --level controls which requirements appear (by status).
    # All violations (both ❌ and ⚠️) are always shown for any requirement
    # that passes the level filter — an INVALID requirement shows its
    # completeness gaps too, so the author can fix everything in one pass.
    show_incomplete = args.level in ("complete", "all")
    show_complete   = args.level == "all"

    for r in sorted(results, key=lambda x: (STATUS_ORDER[x.status], str(x.qualified_name))):
        if r.status == "COMPLETE" and not show_complete:
            continue
        if r.status == "INCOMPLETE" and not show_incomplete:
            continue

        emoji = STATUS_EMOJI[r.status]
        sid_label = f" <{r.short_id}>" if r.short_id else ""
        print(f"\n{emoji} [{r.status}] {r.qualified_name}{sid_label}")

        valid_viols    = [v for v in r.violations if v.level == ValidationLevel.VALID]
        complete_viols = [v for v in r.violations if v.level == ValidationLevel.COMPLETE]

        for v in valid_viols:
            print(f"   ❌  {v.attribute}: {v.message}")
        for v in complete_viols:
            print(f"   ⚠️   {v.attribute}: {v.message}")

    # Untyped requirements — printed last, after all validation results
    if untyped_names:
        print()
        for name in sorted(untyped_names):
            print(f"🔷 [UNTYPED] {name} — not typed by any SRS_Definitions requirement type")

    # -----------------------------------------------------------------------
    # Render and write output
    # -----------------------------------------------------------------------
    fmt = args.format
    if fmt == "text":
        content  = render_text(results, args.level)
        filename = "req_validation_report.txt"
    elif fmt == "markdown":
        content  = render_markdown(results, args.level, untyped_names)
        filename = "req_validation_report.md"
    else:
        content  = render_json(results)
        filename = "req_validation_report.json"

    out_path = output_dir / filename
    out_path.write_text(content, encoding="utf-8")
    print(f"[INFO] Report written to: {out_path}")

    # Also print summary to stdout
    stats = _summary_stats(results)
    print(f"\nResults: {stats['total']} requirements — "
          f"{stats['invalid']} INVALID, "
          f"{stats['incomplete']} INCOMPLETE, "
          f"{stats['complete']} COMPLETE")

    # -----------------------------------------------------------------------
    # Exit codes for CI/CD integration
    # -----------------------------------------------------------------------
    exit_code = 0
    if args.fail_on_invalid and stats['invalid'] > 0:
        print(f"[FAIL] {stats['invalid']} INVALID requirement(s) found.", file=sys.stderr)
        exit_code = 1
    if args.fail_on_incomplete and (stats['invalid'] + stats['incomplete']) > 0:
        print(f"[FAIL] {stats['invalid'] + stats['incomplete']} INVALID/INCOMPLETE "
              f"requirement(s) found.", file=sys.stderr)
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
