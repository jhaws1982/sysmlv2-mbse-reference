"""
sys_req_spec.py — SR-01 System Requirements Specification (SRS)

Produces a structured SRS document from all requirement usages in the model,
organized by requirement type. Generates a formatted PDF with title page,
TOC, per-requirement tables, and ID-only traceability diagrams.

Usage: python __Tools/sys_req_spec.py <model_dir> [--output DIR]
"""
import re
import sys
import html as _html
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_short_name, get_unnamed_doc, get_named_doc,
    get_def_type_name, write_report, collapse_doc, is_plain_req,
)
from report_builder import ReportBuilder, load_report_config
from req_hierarchy import build_node, render_diagram

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

# Diagram config: ID-only nodes (show_doc=False)
DIAG_CFG = {
    "diagram_format": "png",
    "rankdir": "LR",
    "spline": "spline",
    "node_doc_max_chars": 0,
    "show_children": True,
    "show_doc": False,
}


# ── Attribute extraction ──────────────────────────────────────────────────────

def _member_name(m) -> str:
    return getattr(m, "name", None) or getattr(m, "declared_name", None) or ""


def _feature_value_str(attr_usage) -> str:
    try:
        fv = attr_usage.feature_value
        if fv is None:
            return ""
        val = fv.value
        if val is not None:
            return str(val).strip().strip('"\'')
    except Exception:
        pass
    return ""


def get_attr_value(req, attr_name: str) -> str:
    """Return the string value of a named owned AttributeUsage."""
    try:
        for m in req.owned_members.collect():
            if type(m).__name__ == "AttributeUsage" and _member_name(m) == attr_name:
                return _feature_value_str(m)
    except Exception:
        pass
    return ""


def get_criteria_attrs(req) -> tuple[str, str]:
    """Return (verificationMethod, threshold) from the nested criteria part."""
    ver_method = threshold = ""
    try:
        for m in req.owned_members.collect():
            if type(m).__name__ == "PartUsage" and _member_name(m) == "criteria":
                for sub in m.owned_members.collect():
                    if type(sub).__name__ != "AttributeUsage":
                        continue
                    n = _member_name(sub)
                    if n == "verificationMethod":
                        ver_method = _feature_value_str(sub)
                    elif n == "threshold":
                        threshold = _feature_value_str(sub)
                break
    except Exception:
        pass
    return ver_method, threshold


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


# ── Diagram generation ────────────────────────────────────────────────────────

def _safe_id(req_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", req_id)


def generate_diagrams(root_reqs: list, diagrams_dir: Path) -> dict[str, Path]:
    """Build ReqNode trees for all root reqs and render ID-only diagrams.
    Returns dict: req_id → diagram_path (only for successfully rendered diagrams)."""
    rendered: dict[str, Path] = {}

    def _render_tree(node):
        out = diagrams_dir / f"req_{_safe_id(node.label)}.png"
        if render_diagram(node, out, DIAG_CFG):
            rendered[node.label] = out
        for child in node.children:
            _render_tree(child)

    for req in root_reqs:
        _render_tree(build_node(req))

    return rendered


# ── HTML requirement table ────────────────────────────────────────────────────

def _esc(s: str) -> str:
    return _html.escape(s or "")


def _row2(label1: str, val1: str, label2: str, val2: str) -> str:
    return (f'<tr><th class="req-field">{_esc(label1)}</th>'
            f'<td>{_esc(val1) or "—"}</td>'
            f'<th class="req-field">{_esc(label2)}</th>'
            f'<td>{_esc(val2) or "—"}</td></tr>')


def _row_full(label: str, value: str, *, is_header: bool = False) -> str:
    if is_header:
        return f'<tr><th class="section-header" colspan="4">{_esc(label)}</th></tr>'
    return f'<tr><td colspan="4">{_esc(value) or "<em>—</em>"}</td></tr>'


def _row1(label: str, value: str) -> str:
    return (f'<tr><th class="req-field">{_esc(label)}</th>'
            f'<td colspan="3">{_esc(value) or "—"}</td></tr>')


def format_req_html(req, depth: int, diagrams: dict[str, Path],
                    out_dir: Path) -> str:
    req_id   = get_short_name(req) or get_declared_name(req)
    req_name = get_declared_name(req)
    doc      = get_unnamed_doc(req)
    rationale= get_named_doc(req, "Rationale")
    source   = get_attr_value(req, "source")
    priority = get_attr_value(req, "priority")
    criticality = get_attr_value(req, "criticality")
    def_type = get_def_type_name(req)
    ver_method, threshold = get_criteria_attrs(req)

    # Build table
    colgroup = ('<colgroup>'
                '<col style="width:14%"><col style="width:36%">'
                '<col style="width:14%"><col style="width:36%">'
                '</colgroup>')
    rows = [
        colgroup,
        (f'<tr><th class="req-field">ID</th>'
         f'<td><span class="req-id-text">{_esc(req_id)}</span></td>'
         f'<th class="req-field">Name</th>'
         f'<td>{_esc(req_name)}</td></tr>'),
        _row2("Type", def_type, "Priority", priority),
    ]
    if criticality:
        rows.append(_row2("Criticality", criticality, "Source", source))
    elif source:
        rows.append(_row1("Source", source))

    rows += [
        _row_full("Requirement Text", "", is_header=True),
        _row_full("", doc or "No requirement text."),
    ]
    if rationale:
        rows += [
            _row_full("Rationale", "", is_header=True),
            _row_full("", rationale),
        ]
    if ver_method or threshold:
        rows.append(_row2("Verification Method", ver_method,
                          "Threshold", threshold))

    table_html = f'<table class="req-table">{"".join(rows)}</table>'

    # Diagram
    diag_html = ""
    diag_path = diagrams.get(req_id)
    if diag_path and diag_path.exists():
        try:
            rel = diag_path.relative_to(out_dir)
            diag_html = (
                '<div class="req-diagram">'
                f'<img src="{rel}" alt="{_esc(req_id)} traceability">'
                f'<div class="req-diagram-caption">'
                f'Requirement hierarchy for {_esc(req_id)}</div>'
                '</div>'
            )
        except ValueError:
            pass

    # Children
    children_html = ""
    subs = get_subreqs(req)
    if subs:
        child_parts = [format_req_html(sub, depth + 1, diagrams, out_dir)
                       for sub in subs]
        children_html = '<div class="req-children">' + "\n".join(child_parts) + "</div>"

    heading_level = min(3 + depth, 6)
    safe = _safe_id(req_id).lower()
    heading = (f'<h{heading_level} id="req-{safe}">'
               f'{_esc(req_id)} <code>{_esc(req_name)}</code>'
               f'</h{heading_level}>')

    return (f"{heading}"
            f'<div class="req-block">'
            f"{table_html}"
            f"{diag_html}"
            f"{children_html}"
            "</div>")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args    = parse_args("SR-01 System Requirements Specification")
    config  = load_report_config(args.script_config)
    model_dir = args.model_dir
    project   = model_dir.name

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        all_reqs = []
        for top in iter_user_elements(model, model_dir):
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)

        root_reqs = [r for r in all_reqs if is_plain_req(r) and is_root(r)]

        # Generate ID-only diagrams for all requirements
        diagrams = generate_diagrams(root_reqs, args.diagrams_dir)

        # Bucket root reqs by DI-IPSC section
        buckets: dict[str, list] = defaultdict(list)
        for req in root_reqs:
            section = TYPE_SECTION.get(get_def_type_name(req), "Other")
            buckets[section].append(req)

        builder = ReportBuilder(
            config,
            doc_title  = "System Requirements Specification",
            doc_number = "SR-01",
            project    = project,
        )

        # Introduction
        builder.add(
            "<h2>1. Introduction</h2>"
            f"<p>This document specifies the system-level requirements for "
            f"<strong>{_esc(project)}</strong>. Requirements are identified "
            "by unique short-name identifiers and organized per DI-IPSC-81433A.</p>"
            f"<p><strong>Total root requirements:</strong> {len(root_reqs)}</p>"
        )

        # Sections
        for section in SECTION_ORDER:
            reqs = buckets.get(section, [])
            if not reqs:
                continue
            builder.add(f"<h2>{_esc(section)}</h2>")
            for req in sorted(reqs, key=lambda r: get_short_name(r)):
                builder.add(format_req_html(req, 0, diagrams, args.output))

        # Appendix — requirements index
        builder.add("<h2>Appendix A — Requirements Index</h2>")
        index_rows = []
        for req in sorted(root_reqs, key=lambda r: get_short_name(r)):
            rid = get_short_name(req) or "—"
            safe = _safe_id(rid).lower()
            index_rows.append(
                f'<tr>'
                f'<td><a href="#req-{safe}">{_esc(rid)}</a></td>'
                f'<td>{_esc(get_declared_name(req))}</td>'
                f'<td>{_esc(TYPE_SECTION.get(get_def_type_name(req), "Other"))}</td>'
                f'<td>{_esc(collapse_doc(get_unnamed_doc(req))[:80])}</td>'
                f'</tr>'
            )
        builder.add(
            '<table>'
            '<thead><tr><th>ID</th><th>Name</th><th>Type</th><th>Summary</th></tr></thead>'
            '<tbody>' + "\n".join(index_rows) + '</tbody>'
            '</table>'
        )

    # Also write Markdown (for non-PDF consumers)
    import html as _h
    md_lines = [
        "# System Requirements Specification (SRS)\n",
        f"**Project:** {project}\n",
        f"**Total requirements:** {len(root_reqs)}\n",
    ]
    for section in SECTION_ORDER:
        reqs = buckets.get(section, [])
        if not reqs:
            continue
        md_lines.append(f"## {section}\n")
        for req in sorted(reqs, key=lambda r: get_short_name(r)):
            req_id   = get_short_name(req) or get_declared_name(req)
            req_name = get_declared_name(req)
            doc      = get_unnamed_doc(req)
            rationale= get_named_doc(req, "Rationale")
            md_lines.append(f"### {req_id}  `{req_name}`\n")
            md_lines.append(f"{doc or '*No requirement text.*'}\n")
            if rationale:
                md_lines.append(f"**Rationale:** {rationale}\n")
    write_report(args.output / "sys_req_spec.md", "\n".join(md_lines), "SR-01 MD")

    builder.render_pdf(args.output / "sys_req_spec.pdf")


if __name__ == "__main__":
    main()
