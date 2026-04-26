"""
risk_report.py — Risk Register Report

Traverses the model for all @RiskItem metadata annotations and produces
a risk register table sorted by exposure (highest first) plus a validation
gap report.

Usage: python __Tools/risk_report.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name,
    md_heading, md_table, write_report,
    ValidationIssue, format_issues_md, issues_summary,
)
try:
    import syside
except ImportError:
    pass

EXPOSURE_RED    = 6
EXPOSURE_YELLOW = 3
REQUIRES_MITIGATION = {"Open", "Mitigated"}


def get_metadata_attr(meta, attr_name):
    try:
        for member in meta.owned_members.collect():
            # In syside 0.8.x, metadata member names are on .name (not .declared_name)
            name = getattr(member, "name", None) or getattr(member, "declared_name", None)
            if name != attr_name:
                continue
            try:
                expr = member.feature_value_expression
                if expr is not None:
                    # LiteralString, LiteralInteger, LiteralBoolean, etc.
                    val = getattr(expr, "value", None)
                    if val is not None:
                        return str(val).strip("\"'")
                    # FeatureReferenceExpression (enum literals like RiskCategory::Technical)
                    referent = getattr(expr, "referent", None)
                    if referent is not None:
                        ref_name = getattr(referent, "declared_name", None)
                        if ref_name:
                            return str(ref_name)
                    s = str(expr).strip("\"'")
                    if s and not s.startswith("<"):
                        return s
            except Exception:
                pass
            return ""
    except Exception:
        pass
    return ""


def get_annotated_element_name(meta):
    try:
        for el in meta.annotated_elements.collect():
            name = get_declared_name(el)
            if name:
                return name
    except Exception:
        pass
    return "<unknown>"


def collect_risk_annotations(model, model_dir):
    results = []
    try:
        all_meta = []
        for top in iter_user_elements(model, model_dir):
            collect_typed(top, syside.MetadataUsage.STD, all_meta)
        for meta in all_meta:
            try:
                defn = meta.metadata_definition
                if defn and get_declared_name(defn) == "RiskItem":
                    results.append((meta, get_annotated_element_name(meta)))
            except Exception:
                pass
    except Exception:
        pass
    return results


def exposure_color(score):
    if score >= EXPOSURE_RED:
        return "RED"
    if score >= EXPOSURE_YELLOW:
        return "YELLOW"
    if score > 0:
        return "GREEN"
    return "UNDEFINED"


def status_short(s):
    return s.split("::")[-1].strip() if "::" in s else s


def validate_risk(meta, element_name):
    issues = []
    risk_id     = get_metadata_attr(meta, "riskId")
    title       = get_metadata_attr(meta, "title")
    description = get_metadata_attr(meta, "description")
    mitigation  = get_metadata_attr(meta, "mitigation")
    status      = status_short(get_metadata_attr(meta, "status"))
    probability = get_metadata_attr(meta, "probability")
    impact      = get_metadata_attr(meta, "impact")
    owner       = get_metadata_attr(meta, "owner")
    contingency = get_metadata_attr(meta, "contingency")
    label = risk_id or element_name or "<unknown>"

    if not risk_id:
        issues.append(ValidationIssue("INVALID", "", label, "RiskIdSet",
            "riskId is empty."))
    if not title:
        issues.append(ValidationIssue("INVALID", risk_id, label, "RiskTitleSet",
            "title is empty."))
    if not description:
        issues.append(ValidationIssue("INVALID", risk_id, label, "RiskDescSet",
            "description is empty."))
    if status in REQUIRES_MITIGATION and not mitigation:
        issues.append(ValidationIssue("INVALID", risk_id, label, "OpenRiskHasMitigation",
            f"Status '{status}' but mitigation is empty."))
    prob_val = probability.split("::")[-1].strip() if "::" in probability else probability
    imp_val  = impact.split("::")[-1].strip() if "::" in impact else impact
    if prob_val in ("", "Undefined") or imp_val in ("", "Undefined"):
        issues.append(ValidationIssue("WARNING", risk_id, label, "ExposureUndefined",
            "probability or impact is Undefined."))
    if not owner:
        issues.append(ValidationIssue("WARNING", risk_id, label, "OwnerNotSet",
            "owner is not set."))
    try:
        exp_val = int(get_metadata_attr(meta, "exposure"))
        if exp_val >= EXPOSURE_RED and not contingency:
            issues.append(ValidationIssue("WARNING", risk_id, label, "HighExposureNoContingency",
                f"Exposure {exp_val} >= {EXPOSURE_RED} — contingency recommended."))
    except (ValueError, TypeError):
        pass
    return issues


def main():
    args = parse_args("Risk Register Report")

    with load_model(args.model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        risks = collect_risk_annotations(model, args.model_dir)

        all_issues = []
        risk_rows  = []

        for meta, element_name in risks:
            risk_id      = get_metadata_attr(meta, "riskId")
            title        = get_metadata_attr(meta, "title")
            category     = status_short(get_metadata_attr(meta, "category"))
            status       = status_short(get_metadata_attr(meta, "status"))
            probability  = status_short(get_metadata_attr(meta, "probability"))
            impact       = status_short(get_metadata_attr(meta, "impact"))
            owner        = get_metadata_attr(meta, "owner") or "—"
            mitigation   = get_metadata_attr(meta, "mitigation")
            exposure_str = get_metadata_attr(meta, "exposure")

            try:
                exp_val = int(exposure_str) if exposure_str else 0
            except (ValueError, TypeError):
                exp_val = 0

            color = exposure_color(exp_val)
            exp_display = f"[{color}] {exp_val}" if exp_val else f"[{color}] —"

            risk_rows.append((exp_val, [
                risk_id or "—",
                title or "—",
                category or "—",
                status or "—",
                probability or "—",
                impact or "—",
                exp_display,
                owner,
                element_name,
                (mitigation[:60] + "...") if len(mitigation) > 60 else (mitigation or "—"),
            ]))

            all_issues.extend(validate_risk(meta, element_name))

        risk_rows.sort(key=lambda r: r[0], reverse=True)
        table_rows = [r for _, r in risk_rows]

        invalid, warns = issues_summary(all_issues)

        lines = [
            md_heading("Risk Register Report"),
            f"**Model:** `{args.model_dir}`  \n",
            f"**Risks found:** {len(risks)}  |  "
            f"**INVALID:** {invalid}  |  **WARNING:** {warns}\n",
            "> Risks sorted by exposure score (highest first).\n",
            "> [RED] = High (6-9)  [YELLOW] = Moderate (3-5)  [GREEN] = Low (1-2)  [UNDEFINED] = Not assessed\n",
        ]

        if not risks:
            lines.append("> *No @RiskItem annotations found.*\n")
        else:
            lines.append(md_heading("Risk Register", 2))
            lines.append(md_table(
                ["ID", "Title", "Category", "Status", "Prob", "Impact",
                 "Exposure", "Owner", "Attached To", "Mitigation (summary)"],
                table_rows,
            ))

            lines.append(md_heading("Validation", 2))
            if not all_issues:
                lines.append("All risk annotations pass validation.\n")
            else:
                by_check: dict = {}
                for issue in all_issues:
                    by_check.setdefault(issue.check, []).append(issue)
                for check, check_issues in sorted(by_check.items()):
                    lines.append(md_heading(check, 3))
                    lines.append(format_issues_md(check_issues, check))

            lines.append(md_heading("Summary by Category", 2))
            by_cat: dict = defaultdict(list)
            for meta, element_name in risks:
                cat = status_short(get_metadata_attr(meta, "category")) or "Unknown"
                by_cat[cat].append(meta)
            cat_rows = [[cat, str(len(items))]
                        for cat, items in sorted(by_cat.items())]
            lines.append(md_table(["Category", "Count"], cat_rows))

        write_report(args.output / "risk_report.md", "\n".join(lines), "RISK")
        if invalid > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
