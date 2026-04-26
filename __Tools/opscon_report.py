"""
opscon_report.py — SN-04 Operational Concept Description (OpsCon)

Extracts narrative content from SystemContext and OperationalConcept packages
to produce a structured Operational Concept Description document.

Usage: python __Tools/opscon_report.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_unnamed_doc,
    md_heading, write_report, pdf_attempt,
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


def main():
    args = parse_args("SN-04 Operational Concept Description")
    model_dir = args.model_dir
    project = model_dir.name

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        part_defs = []
        for top in iter_user_elements(model, model_dir):
            collect_typed(top, syside.PartDefinition.STD, part_defs)

        context_parts = [p for p in part_defs if in_pkg(p, "SystemContext")]
        concept_parts = [p for p in part_defs if in_pkg(p, "OperationalConcept")]

        lines = [
            md_heading(f"Operational Concept Description"),
            f"**Project:** {project}\n",
            "---\n",
            md_heading("1. Introduction", 2),
            f"This document describes the operational concept for the **{project}** system: "
            "the operational environment, system purpose, primary user community, "
            "and key operational scenarios.\n",
        ]

        # System Context section
        lines.append(md_heading("2. System Context", 2))
        context_found = False
        for p in sorted(context_parts, key=get_declared_name):
            name = get_declared_name(p)
            doc = get_unnamed_doc(p)
            if name.endswith("Assembly") or not doc:
                continue
            lines.append(md_heading(name, 3))
            lines.append(f"{doc}\n")
            context_found = True
        if not context_found:
            lines.append("> Populate `02_Core/Context/system_context.sysml` with system "
                         "and actor descriptions.\n")

        # OpsCon Summary
        lines.append(md_heading("3. Operational Concept Summary", 2))
        summary_found = False
        for p in concept_parts:
            name = get_declared_name(p)
            doc = get_unnamed_doc(p)
            if "Summary" in name and doc:
                lines.append(f"{doc}\n")
                summary_found = True
        if not summary_found:
            lines.append("> Populate `OperationalConceptSummary` in "
                         "`02_Core/Context/operational_concept.sysml`.\n")

        # Missions
        missions = [p for p in concept_parts if "Mission" in get_declared_name(p)]
        if missions:
            lines.append(md_heading("4. Missions", 2))
            for m in sorted(missions, key=get_declared_name):
                name = get_declared_name(m)
                doc = get_unnamed_doc(m)
                lines.append(md_heading(name, 3))
                lines.append(f"{doc}\n" if doc else "> No description.\n")

        # Scenarios
        scenarios = [p for p in concept_parts if "Scenario" in get_declared_name(p)]
        if scenarios:
            lines.append(md_heading("5. Operational Scenarios", 2))
            for s in sorted(scenarios, key=get_declared_name):
                name = get_declared_name(s)
                doc = get_unnamed_doc(s)
                lines.append(md_heading(name, 3))
                lines.append(f"{doc}\n" if doc else "> No description.\n")

    md_content = "\n".join(lines)
    md_path = args.output / "opscon_report.md"
    write_report(md_path, md_content, "SN-04 MD")
    pdf_attempt(md_content, args.output / "opscon_report.pdf", "SN-04", number_sections=False)


if __name__ == "__main__":
    main()
