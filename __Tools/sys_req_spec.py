"""
sys_req_spec.py — SR-01 System Requirements Specification (SRS)

Produces a structured SRS document from all requirement usages in the model,
organized by requirement type. Attempts PDF generation via pandoc.

Usage: python __Tools/sys_req_spec.py <model_dir> [--output DIR]
"""
import sys
import subprocess
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed,
    get_declared_name, get_short_name, get_unnamed_doc, get_named_doc,
    get_def_type_name, md_heading, md_table, write_report,
    collapse_doc, is_plain_req,
)
import syside

# DI-IPSC-81433A section mapping
TYPE_SECTION = {
    "CapabilityRequirement":       "3.2 Capability Requirements",
    "PerformanceAspect":           "3.2 Capability Requirements",
    "InterfaceRequirement":        "3.3 Interface Requirements",
    "InterfaceAspect":             "3.3 Interface Requirements",
    "DataRequirement":             "3.5 Data Requirements",
    "DataAspect":                  "3.5 Data Requirements",
    "SafetyRequirement":           "3.7 Safety Requirements",
    "SecurityRequirement":         "3.8 Security Requirements",
    "QualityRequirement":          "3.11 Quality Requirements",
    "DesignConstraintRequirement": "3.12 Design Constraint Requirements",
    "EnvironmentalRequirement":    "3.9 Environmental Requirements",
    "ResourceRequirement":         "3.10 Resource Requirements",
    "AdaptationRequirement":       "3.6 Adaptation Requirements",
    "COTSRequirement":             "3.10.3 COTS Requirements",
}
SECTION_ORDER = [
    "3.2 Capability Requirements",
    "3.3 Interface Requirements",
    "3.5 Data Requirements",
    "3.6 Adaptation Requirements",
    "3.7 Safety Requirements",
    "3.8 Security Requirements",
    "3.9 Environmental Requirements",
    "3.10 Resource Requirements",
    "3.10.3 COTS Requirements",
    "3.11 Quality Requirements",
    "3.12 Design Constraint Requirements",
    "Other",
]


def get_attr_value(req, attr_name: str) -> str:
    try:
        for member in req.nested_attributes.collect():
            name = getattr(member, "declared_name", None)
            if not name:
                try:
                    rf = member.referenced_feature
                    if rf:
                        name = rf.declared_name
                except Exception:
                    pass
            if name == attr_name:
                try:
                    expr = member.feature_value_expression
                    if expr:
                        val = getattr(expr, "value", None)
                        if val is not None:
                            return str(val).strip("\"'")
                except Exception:
                    pass
    except Exception:
        pass
    return ""


def is_root(req) -> bool:
    try:
        owner = req.owner
        if owner and owner.isinstance(syside.RequirementUsage.STD):
            return False
    except Exception:
        pass
    return True


def get_subreqs(req) -> list:
    subs = []
    try:
        for m in req.owned_members.collect():
            if m.isinstance(syside.RequirementUsage.STD) and is_plain_req(m):
                subs.append(m.cast(syside.RequirementUsage.STD))
    except Exception:
        pass
    return subs


def format_req(req, depth=0) -> list[str]:
    req_id = get_short_name(req) or get_declared_name(req)
    req_name = get_declared_name(req)
    doc = get_unnamed_doc(req)
    rationale = get_named_doc(req, "Rationale")
    level = min(3 + depth, 6)
    lines = []
    lines.append(md_heading(f"{req_id}  `{req_name}`", level))
    lines.append(f"{doc or '*No requirement text.*'}\n")
    if rationale:
        lines.append(f"**Rationale:** {rationale}\n")
    for sub in get_subreqs(req):
        lines.extend(format_req(sub, depth + 1))
    return lines


def pdf_attempt(md_content, pdf_path, artifact_id):
    tmp = pdf_path.with_suffix(".md.tmp")
    tmp.write_text(md_content, encoding="utf-8")
    try:
        subprocess.run(
            ["pandoc", str(tmp), "-o", str(pdf_path),
             "--pdf-engine=xelatex", "-V", "geometry:margin=1in",
             "-V", "fontsize=11pt", "--toc", "--number-sections"],
            check=True, capture_output=True, timeout=120)
        print(f"  [{artifact_id} PDF] → {pdf_path}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pdf_path.with_suffix(".pdf.txt").write_text(
            f"PDF requires pandoc + xelatex. Markdown at {pdf_path.stem}.md\n")
        print(f"  [{artifact_id} PDF] ⚠ pandoc not available — see {pdf_path.stem}.md")
    finally:
        tmp.unlink(missing_ok=True)


def main():
    args = parse_args("SR-01 System Requirements Specification")
    model_dir = args.model_dir
    project = model_dir.name

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        all_reqs = []
        for top in model.top_elements_from(str(model_dir)):
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)

        root_reqs = [r for r in all_reqs if is_plain_req(r) and is_root(r)]

        # Bucket by type
        buckets: dict[str, list] = defaultdict(list)
        for req in root_reqs:
            section = TYPE_SECTION.get(get_def_type_name(req), "Other")
            buckets[section].append(req)

        lines = [
            md_heading("System Requirements Specification (SRS)"),
            f"**Project:** {project}\n",
            "---\n",
            md_heading("1. Introduction", 2),
            f"This document specifies the system-level requirements for **{project}**. "
            f"Requirements are identified by unique short-name identifiers.\n",
            f"**Total requirements:** {len(root_reqs)}\n",
        ]

        for section in SECTION_ORDER:
            reqs = buckets.get(section, [])
            if not reqs:
                continue
            lines.append(md_heading(section, 2))
            for req in sorted(reqs, key=lambda r: get_short_name(r)):
                lines.extend(format_req(req))

        # Index appendix
        lines.append(md_heading("Appendix A — Requirements Index", 2))
        rows = []
        for req in sorted(root_reqs, key=lambda r: get_short_name(r)):
            rows.append([
                get_short_name(req) or "—",
                get_declared_name(req),
                TYPE_SECTION.get(get_def_type_name(req), "Other"),
                collapse_doc(get_unnamed_doc(req))[:80] or "—",
            ])
        if rows:
            lines.append(md_table(["ID", "Name", "Type", "Summary"], rows))

    md_content = "\n".join(lines)
    md_path = args.output / "sys_req_spec.md"
    write_report(md_path, md_content, "SR-01 MD")
    pdf_attempt(md_content, args.output / "sys_req_spec.pdf", "SR-01")


if __name__ == "__main__":
    main()
