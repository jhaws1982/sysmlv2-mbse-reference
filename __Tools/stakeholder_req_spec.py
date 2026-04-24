"""
stakeholder_req_spec.py — SN-05 Stakeholder Requirements Specification (StRS)

Produces a structured StRS document from stakeholder defs, concerns, and
stakeholder-level requirement usages found in the model.

Usage: python __Tools/stakeholder_req_spec.py <model_dir> [--output DIR]
"""
import sys
import subprocess
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed,
    get_declared_name, get_short_name, get_unnamed_doc, get_named_doc,
    md_heading, md_table, write_report, collapse_doc, is_plain_req,
)
import syside


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
    args = parse_args("SN-05 Stakeholder Requirements Specification")
    model_dir = args.model_dir
    project = model_dir.name

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        part_defs, concern_defs, all_reqs = [], [], []
        for top in model.top_elements_from(str(model_dir)):
            collect_typed(top, syside.PartDefinition.STD, part_defs)
            collect_typed(top, syside.ConcernDefinition.STD, concern_defs)
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)

        stakeholders = [p for p in part_defs if in_pkg(p, "StakeholderDef")]
        strs_reqs = [r for r in all_reqs
                     if is_plain_req(r) and in_pkg(r, "StakeholderRequirement")]

        lines = [
            md_heading("Stakeholder Requirements Specification (StRS)"),
            f"**Project:** {project}\n",
            "---\n",
            md_heading("1. Introduction", 2),
            f"This document is the Stakeholder Requirements Specification for **{project}**. "
            "It identifies stakeholders, captures their concerns, and specifies the "
            "stakeholder-level requirements that constrain the system design.\n",
            md_heading("2. Stakeholder Register", 2),
        ]

        if stakeholders:
            rows = [[get_declared_name(s),
                     collapse_doc(get_unnamed_doc(s))[:100] or "—"]
                    for s in sorted(stakeholders, key=get_declared_name)]
            lines.append(md_table(["Stakeholder", "Description"], rows))
        else:
            lines.append("> No stakeholder definitions found.\n")

        lines.append(md_heading("3. Stakeholder Concerns", 2))
        if concern_defs:
            rows = [[get_declared_name(c),
                     collapse_doc(get_unnamed_doc(c))[:120] or "—"]
                    for c in sorted(concern_defs, key=get_declared_name)]
            lines.append(md_table(["Concern", "Description"], rows))
        else:
            lines.append("> No concern definitions found.\n")

        lines.append(md_heading("4. Stakeholder Requirements", 2))
        if strs_reqs:
            for req in sorted(strs_reqs, key=lambda r: get_short_name(r)):
                req_id = get_short_name(req) or get_declared_name(req)
                req_name = get_declared_name(req)
                doc = get_unnamed_doc(req)
                rationale = get_named_doc(req, "Rationale")
                lines.append(md_heading(f"{req_id}  `{req_name}`", 3))
                lines.append(f"{doc or '*No requirement text.*'}\n")
                if rationale:
                    lines.append(f"**Rationale:** {rationale}\n")
        else:
            lines.append("> No stakeholder requirements found.\n")
            lines.append("> Populate `requirements/stakeholder_requirements.sysml` or "
                         "tag requirements with stakeholder package names.\n")

    md_content = "\n".join(lines)
    md_path = args.output / "stakeholder_req_spec.md"
    write_report(md_path, md_content, "SN-05 MD")
    pdf_attempt(md_content, args.output / "stakeholder_req_spec.pdf", "SN-05")


if __name__ == "__main__":
    main()
