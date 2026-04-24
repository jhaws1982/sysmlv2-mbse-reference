"""
req_validate.py

Validates SysML v2 requirements against SRS_Definitions.sysml structural rules.

Checks performed on every RequirementUsage found in the model:

  Doc Convention Checks (replaces the former HasID / HasText / HasRationale
  attribute constraints, which no longer exist in SRS_Definitions):
    INVALID  — no short-name ID (<'REQ-NNN'>) declared
    INVALID  — no unnamed doc block (normative requirement text missing)
    INVALID  — no 'doc Rationale' annotation

  Attribute Checks (derived from the definition type):
    INVALID  — required attribute present on the def is missing or empty at
               the usage site
    WARNING  — optional attribute ([0..1]) is absent (informational only)

  Cross-requirement Checks:
    INVALID  — short-name ID is duplicated across two or more requirements
    INVALID  — requirement text (unnamed doc, whitespace-normalised) is
               duplicated (copy-paste guard)

  Criteria Checks (when a VerificationCriteria part is present):
    INVALID  — verificationMethod is missing or empty
    INVALID  — verification method violates the type-specific constraint
               (e.g. CapabilityRequirement must use Test or Analysis)

Usage:
    python __Tools/req_validate.py <model_dir>
    python __Tools/req_validate.py <model_dir> --program Program_A
    python __Tools/req_validate.py <model_dir> --output ./reports

Exit codes:
    0 — all checks passed (no INVALID results)
    1 — one or more INVALID results found
"""

import sys
import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

import syside
from syside.preview import open_model


# ── Severity ──────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    INVALID  = "INVALID"
    WARNING  = "WARNING"
    VALID    = "VALID"


@dataclass
class Violation:
    severity: Severity
    field:    str
    message:  str


@dataclass
class RequirementResult:
    req_id:    str        # short-name ID string (may be "" if missing)
    name:      str        # declared_name
    qual_name: str        # qualified_name for location reporting
    req_text:  str        # unnamed doc body (whitespace-normalised) for dup check
    violations: list[Violation] = field(default_factory=list)

    @property
    def status(self) -> Severity:
        if any(v.severity == Severity.INVALID for v in self.violations):
            return Severity.INVALID
        if any(v.severity == Severity.WARNING for v in self.violations):
            return Severity.WARNING
        return Severity.VALID


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_name(element) -> str:
    if element is None:
        return ""
    name = element.declared_name
    return str(name) if name else ""


def get_qual_name(element) -> str:
    try:
        qn = element.qualified_name
        return str(qn) if qn else get_name(element)
    except Exception:
        return get_name(element)


def get_req_id(req: syside.RequirementUsage) -> str:
    """Return the <'X'> short-name string, or '' if not set."""
    try:
        rid = req.req_id
        if rid:
            return str(rid).strip("'\"")
    except Exception:
        pass
    try:
        sn = req.short_name
        if sn:
            return str(sn).strip("'\"")
    except Exception:
        pass
    return ""


def _strip_doc_markers(body: str) -> str:
    """Remove /* */ markers and leading * from continuation lines."""
    text = str(body).strip()
    text = re.sub(r"^/\*+\s*", "", text)
    text = re.sub(r"\s*\*+/$", "", text)
    lines = text.splitlines()
    return "\n".join(re.sub(r"^\s*\*\s?", "", ln) for ln in lines).strip()


def get_all_docs(req: syside.RequirementUsage) -> dict[str | None, str]:
    """
    Return all doc annotations as {name_or_None: cleaned_body}.
    None key = unnamed doc (normative requirement text).
    'Rationale' key = doc Rationale block.
    Last-wins for duplicate names (unusual but safe).
    """
    docs: dict[str | None, str] = {}
    try:
        for doc in req.documentation.collect():
            body = doc.body
            if not body:
                continue
            cleaned = _strip_doc_markers(body)
            if not cleaned:
                continue
            doc_name = getattr(doc, "declared_name", None) or None
            docs[doc_name] = cleaned
    except Exception:
        pass
    return docs


def get_feature_value(attr_usage) -> str:
    """
    Return the string value of an attribute usage's feature_value, or ''.
    Handles LiteralString and other literal types.
    """
    try:
        fv = attr_usage.feature_value
        if fv is None:
            return ""
        val = fv.value
        if val is None:
            return ""
        # LiteralString: .value is the raw string (may include quotes)
        sv = str(val).strip().strip('"\'')
        return sv
    except Exception:
        return ""


def get_attr_value(req: syside.RequirementUsage, attr_name: str) -> str:
    """Walk owned_members for an AttributeUsage named attr_name and return its value."""
    try:
        for member in req.owned_members.collect():
            if type(member).__name__ != "AttributeUsage":
                continue
            if member.declared_name == attr_name:
                return get_feature_value(member)
    except Exception:
        pass
    return ""


def collect_typed(root, std_type, results: list):
    """Depth-first collection of all elements matching std_type."""
    if root.isinstance(std_type):
        results.append(root.cast(std_type))
    if root.isinstance(syside.Namespace.STD):
        ns = root.cast(syside.Namespace.STD)
        for member in ns.owned_members.collect():
            collect_typed(member, std_type, results)


def is_plain_req(r) -> bool:
    return (
        not r.isinstance(syside.SatisfyRequirementUsage.STD)
        and not r.isinstance(syside.ConcernUsage.STD)
    )


# ── Definition introspection ──────────────────────────────────────────────────

# Attributes defined on SRS_Requirement itself that are always present on
# every usage (inherited). We skip checking these by name in subtype
# attribute discovery — they are covered separately or are structural-only.
_BASE_SKIP = frozenset({"source", "priority", "criticality"})

# Attributes with [0..1] multiplicity (optional) per the SRS_Definitions model.
# These are checked at WARNING level only.
_KNOWN_OPTIONAL = frozenset({
    "source", "priority", "criticality",
    "performance", "timing", "throughput", "latency", "accuracy",
    "format", "units", "protocol", "messageFormat", "additionalEntities",
    "threshold",
})


def _attrs_from_def(req_def, exclude: set[str]) -> tuple[list[str], list[str]]:
    """
    Return (required_attrs, optional_attrs) declared directly on req_def,
    excluding any names in the exclude set.

    Classification:
      - If declared_multiplicity is not None → optional ([0..1] or [*])
      - If name is in _KNOWN_OPTIONAL → optional
      - Otherwise → required (default [1])
    """
    required: list[str] = []
    optional: list[str] = []
    try:
        for member in req_def.owned_members.collect():
            if type(member).__name__ != "AttributeUsage":
                continue
            name = member.declared_name
            if not name or name in exclude or name in _BASE_SKIP:
                continue
            mult = member.declared_multiplicity
            if mult is not None or name in _KNOWN_OPTIONAL:
                optional.append(name)
            else:
                required.append(name)
    except Exception:
        pass
    return required, optional


def _find_criteria_part_def(req_def):
    """
    Walk the definition's owned_members looking for a PartUsage named 'criteria'.
    Returns the PartDefinition of criteria, or None.
    """
    try:
        for member in req_def.owned_members.collect():
            if type(member).__name__ != "PartUsage":
                continue
            if member.declared_name == "criteria":
                for typing in member.types.collect():
                    return typing
    except Exception:
        pass
    return None


# Allowed verificationMethod values per type — keyed by definition simple name.
# These mirror the assert constraints in SRS_Definitions.sysml.
_ALLOWED_METHODS: dict[str, set[str]] = {
    "CapabilityRequirement":     {"Test", "Analysis"},
    "InterfaceRequirement":      {"Test", "Inspection", "Demonstration"},
    "DataRequirement":           {"Analysis", "Inspection"},
    "SafetyRequirement":         {"Analysis", "Test", "Inspection"},
    "SecurityRequirement":       {"Analysis", "Test"},
    "EnvironmentalRequirement":  {"Test", "Analysis"},
    "ResourceRequirement":       {"Analysis", "Inspection"},
    "QualityRequirement":        {"Test", "Analysis"},
    "DesignConstraintRequirement": {"Inspection", "Analysis"},
    "AdaptationRequirement":     {"Test", "Analysis"},
    "COTSRequirement":           {"Inspection", "Analysis"},
}


def _req_type_name(req: syside.RequirementUsage) -> str:
    """Return the most-derived definition type name for this usage."""
    try:
        types = list(req.types.collect())
        if types:
            return get_name(types[0]) or ""
    except Exception:
        pass
    return ""


# ── Validation ────────────────────────────────────────────────────────────────

def _check_doc_convention(
    req: syside.RequirementUsage,
    req_id_str: str,
    docs: dict[str | None, str],
    violations: list[Violation],
) -> str:
    """
    Validate the three doc-convention requirements. Returns the whitespace-
    normalised req text for duplicate detection (empty string if absent).
    """
    # 1. Short-name ID
    if not req_id_str:
        violations.append(Violation(
            Severity.INVALID,
            "id",
            "No short-name ID declared. Add <'REQ-NNN'> before the requirement name.",
        ))

    # 2. Unnamed doc (normative text)
    req_text = docs.get(None, "")
    normalised_text = " ".join(req_text.split())
    if not req_text:
        violations.append(Violation(
            Severity.INVALID,
            "doc (text)",
            "Missing unnamed doc block — the normative requirement statement. "
            "Add: doc /* The CSCI shall ... */",
        ))

    # 3. doc Rationale
    # Case-insensitive search for a doc named 'Rationale'
    rationale_found = any(
        k is not None and k.lower() == "rationale"
        for k in docs
    )
    if not rationale_found:
        violations.append(Violation(
            Severity.INVALID,
            "doc Rationale",
            "Missing 'doc Rationale' annotation. "
            "Add: doc Rationale /* <why this requirement exists> */",
        ))

    return normalised_text


def _check_attributes(
    req: syside.RequirementUsage,
    violations: list[Violation],
):
    """
    Check required and optional typed attributes inherited from the definition.
    """
    type_name = _req_type_name(req)
    req_def = None
    try:
        types = list(req.types.collect())
        if types:
            req_def = types[0]
    except Exception:
        pass

    if req_def is None:
        return

    required_attrs, optional_attrs = _attrs_from_def(req_def, exclude=set())

    for attr in required_attrs:
        val = get_attr_value(req, attr)
        if not val:
            violations.append(Violation(
                Severity.INVALID,
                attr,
                f"Required attribute '{attr}' is missing or empty.",
            ))

    for attr in optional_attrs:
        val = get_attr_value(req, attr)
        if not val:
            violations.append(Violation(
                Severity.WARNING,
                attr,
                f"Optional attribute '{attr}' is not set.",
            ))

    # Criteria checks
    criteria_val = get_attr_value(req, "criteria")
    # criteria is a part usage — check if it's present via owned_members
    criteria_present = False
    criteria_method = ""
    try:
        for member in req.owned_members.collect():
            if type(member).__name__ == "PartUsage" and member.declared_name == "criteria":
                criteria_present = True
                # Try to get verificationMethod from its own members
                for sub in member.owned_members.collect():
                    if (type(sub).__name__ == "AttributeUsage"
                            and sub.declared_name == "verificationMethod"):
                        criteria_method = get_feature_value(sub)
                break
    except Exception:
        pass

    if criteria_present:
        if not criteria_method:
            violations.append(Violation(
                Severity.INVALID,
                "verificationMethod",
                "A VerificationCriteria part is defined but verificationMethod is missing.",
            ))
        else:
            allowed = _ALLOWED_METHODS.get(type_name)
            if allowed and criteria_method not in allowed:
                violations.append(Violation(
                    Severity.INVALID,
                    "verificationMethod",
                    f"verificationMethod '{criteria_method}' is not valid for "
                    f"{type_name}. Allowed: {', '.join(sorted(allowed))}.",
                ))


def validate_requirement(req: syside.RequirementUsage) -> RequirementResult:
    req_id_str = get_req_id(req)
    name       = get_name(req)
    qual_name  = get_qual_name(req)
    docs       = get_all_docs(req)
    violations: list[Violation] = []

    req_text_normalised = _check_doc_convention(req, req_id_str, docs, violations)
    _check_attributes(req, violations)

    return RequirementResult(
        req_id=req_id_str,
        name=name,
        qual_name=qual_name,
        req_text=req_text_normalised,
        violations=violations,
    )


def check_cross_requirement_uniqueness(results: list[RequirementResult]):
    """
    Add INVALID violations for duplicate IDs and duplicate requirement texts.
    Mutates results in place.
    """
    # Duplicate IDs
    id_to_results: dict[str, list[RequirementResult]] = {}
    for r in results:
        if r.req_id:
            id_to_results.setdefault(r.req_id, []).append(r)
    for req_id, group in id_to_results.items():
        if len(group) > 1:
            others_by = ", ".join(
                g.qual_name for g in group if g is not group[0]
            )
            for r in group:
                others = ", ".join(
                    g.qual_name for g in group if g is not r
                )
                r.violations.append(Violation(
                    Severity.INVALID,
                    "id",
                    f"Duplicate ID '{req_id}' — also used by: {others}.",
                ))

    # Duplicate requirement texts (copy-paste guard)
    text_to_results: dict[str, list[RequirementResult]] = {}
    for r in results:
        if r.req_text:
            text_to_results.setdefault(r.req_text, []).append(r)
    for text, group in text_to_results.items():
        if len(group) > 1:
            preview = text[:80] + ("…" if len(text) > 80 else "")
            for r in group:
                others = ", ".join(
                    g.qual_name for g in group if g is not r
                )
                r.violations.append(Violation(
                    Severity.INVALID,
                    "doc (text)",
                    f"Duplicate requirement text '{preview}' — also used by: {others}.",
                ))


# ── Output formatting ─────────────────────────────────────────────────────────

_ICON = {
    Severity.INVALID: "❌",
    Severity.WARNING: "⚠️ ",
    Severity.VALID:   "✅",
}


def print_results(results: list[RequirementResult]):
    total   = len(results)
    invalid = sum(1 for r in results if r.status == Severity.INVALID)
    warning = sum(1 for r in results if r.status == Severity.WARNING)
    valid   = sum(1 for r in results if r.status == Severity.VALID)

    for r in results:
        icon = _ICON[r.status]
        label = r.req_id or r.name or r.qual_name
        print(f"\n{icon}  {label}  ({r.qual_name})")
        if r.status == Severity.VALID:
            print("      All checks passed.")
        else:
            for v in r.violations:
                sev_tag = f"[{v.severity.value}]"
                print(f"    {sev_tag:<10} {v.field}: {v.message}")

    print(f"\n{'─' * 60}")
    print(f"  Total: {total}  |  ❌ Invalid: {invalid}  |  "
          f"⚠️  Warnings: {warning}  |  ✅ Valid: {valid}")
    print(f"{'─' * 60}")


# ── Main ──────────────────────────────────────────────────────────────────────

def run(model_dir: Path, program: str | None, output_dir: Path | None):
    print(f"Opening model at: {model_dir}")
    with open_model(str(model_dir)) as model:
        all_reqs: list[syside.RequirementUsage] = []
        for element in model.top_elements_from(str(model_dir)):
            collect_typed(element, syside.RequirementUsage.STD, all_reqs)

        if program:
            prog_dir = model_dir / program
            if prog_dir.is_dir():
                for element in model.top_elements_from(str(prog_dir)):
                    collect_typed(element, syside.RequirementUsage.STD, all_reqs)

        plain_reqs = [r for r in all_reqs if is_plain_req(r)]
        print(f"Found {len(plain_reqs)} requirement usage(s).\n")

        results = [validate_requirement(r) for r in plain_reqs]
        check_cross_requirement_uniqueness(results)
        print_results(results)

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / "req_validation.txt"
            # Redirect stdout to file as well
            import io
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            print_results(results)
            sys.stdout = old_stdout
            out_path.write_text(buf.getvalue(), encoding="utf-8")
            print(f"Validation report written to: {out_path}")

    invalid_count = sum(1 for r in results if r.status == Severity.INVALID)
    return invalid_count


def main():
    parser = argparse.ArgumentParser(
        description="Validate SysML v2 requirements against SRS_Definitions rules."
    )
    parser.add_argument("model_dir", help="Path to the SysML v2 model directory.")
    parser.add_argument(
        "--program", "-p",
        default=None,
        help="Optional program sub-directory to include (e.g. Program_A).",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory for validation report file (default: stdout only).",
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir).resolve()
    if not model_dir.is_dir():
        print(f"Error: model directory not found: {model_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output).resolve() if args.output else None
    invalid_count = run(model_dir, args.program, output_dir)
    sys.exit(0 if invalid_count == 0 else 1)


if __name__ == "__main__":
    main()
