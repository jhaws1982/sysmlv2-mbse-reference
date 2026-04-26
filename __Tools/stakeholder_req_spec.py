"""
stakeholder_req_spec.py — SN-05 Stakeholder Requirements Specification (StRS)

Produces a structured StRS document from stakeholder defs, concerns, and
stakeholder-level requirement usages found in the model.

Usage: python __Tools/stakeholder_req_spec.py <model_dir> [--output DIR]
"""
import html as _html
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_short_name, get_unnamed_doc, get_named_doc,
    write_report, collapse_doc, is_plain_req,
)
from report_builder import ReportBuilder, load_report_config
import syside


def _esc(s: str) -> str:
    return _html.escape(s or "")


def in_pkg(element, *names) -> bool:
    try:
        owner = element.owner
        while owner is not None:
            n = get_declared_name(owner)
            if n and any(p.lower() in n.lower() for p in names):
                return True
            owner = getattr(owner, "owner", None)
    except Exception:
        pass
    return False


def main():
    args    = parse_args("SN-05 Stakeholder Requirements Specification")
    config  = load_report_config(args.script_config)
    model_dir = args.model_dir
    project   = model_dir.name

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        part_defs, concern_defs, all_reqs = [], [], []
        for top in iter_user_elements(model, model_dir):
            collect_typed(top, syside.PartDefinition.STD, part_defs)
            collect_typed(top, syside.ConcernDefinition.STD, concern_defs)
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)

        stakeholders = [p for p in part_defs if in_pkg(p, "StakeholderDef")]
        strs_reqs    = [r for r in all_reqs
                        if is_plain_req(r) and in_pkg(r, "StakeholderRequirement")]

        builder = ReportBuilder(
            config,
            doc_title  = "Stakeholder Requirements Specification",
            doc_number = "SN-05",
            project    = project,
        )

        # 1. Introduction
        builder.add(
            "<h2>1. Introduction</h2>"
            f"<p>This document is the Stakeholder Requirements Specification for "
            f"<strong>{_esc(project)}</strong>. It identifies stakeholders, captures "
            "their concerns, and specifies the stakeholder-level requirements that "
            "constrain the system design.</p>"
        )

        # 2. Stakeholder Register
        builder.add("<h2>2. Stakeholder Register</h2>")
        if stakeholders:
            rows_html = "".join(
                f'<tr><td>{_esc(get_declared_name(s))}</td>'
                f'<td>{_esc(collapse_doc(get_unnamed_doc(s))[:120] or "—")}</td></tr>'
                for s in sorted(stakeholders, key=get_declared_name)
            )
            builder.add(
                '<table><thead><tr><th>Stakeholder</th><th>Description</th></tr></thead>'
                f'<tbody>{rows_html}</tbody></table>'
            )
        else:
            builder.add("<p><em>No stakeholder definitions found.</em></p>")

        # 3. Stakeholder Concerns
        builder.add("<h2>3. Stakeholder Concerns</h2>")
        if concern_defs:
            rows_html = "".join(
                f'<tr><td>{_esc(get_declared_name(c))}</td>'
                f'<td>{_esc(collapse_doc(get_unnamed_doc(c))[:140] or "—")}</td></tr>'
                for c in sorted(concern_defs, key=get_declared_name)
            )
            builder.add(
                '<table><thead><tr><th>Concern</th><th>Description</th></tr></thead>'
                f'<tbody>{rows_html}</tbody></table>'
            )
        else:
            builder.add("<p><em>No concern definitions found.</em></p>")

        # 4. Stakeholder Requirements
        builder.add("<h2>4. Stakeholder Requirements</h2>")
        if strs_reqs:
            for req in sorted(strs_reqs, key=lambda r: get_short_name(r)):
                req_id   = get_short_name(req) or get_declared_name(req)
                req_name = get_declared_name(req)
                doc      = get_unnamed_doc(req)
                rationale= get_named_doc(req, "Rationale")
                builder.add(
                    f'<h3>{_esc(req_id)} <code>{_esc(req_name)}</code></h3>'
                    f'<p>{_esc(doc) if doc else "<em>No requirement text.</em>"}</p>'
                    + (f'<p><strong>Rationale:</strong> {_esc(rationale)}</p>'
                       if rationale else "")
                )
        else:
            builder.add(
                "<p><em>No stakeholder requirements found. "
                "Populate requirements tagged with stakeholder package names.</em></p>"
            )

    # Markdown fallback
    md_lines = ["# Stakeholder Requirements Specification (StRS)\n",
                f"**Project:** {project}\n"]
    write_report(args.output / "stakeholder_req_spec.md",
                 "\n".join(md_lines), "SN-05 MD")
    builder.render_pdf(args.output / "stakeholder_req_spec.pdf")


if __name__ == "__main__":
    main()
