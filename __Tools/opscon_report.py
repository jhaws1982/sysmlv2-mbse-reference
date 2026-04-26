"""
opscon_report.py — SN-04 Operational Concept Description (OpsCon)

Extracts narrative content from SystemContext and OperationalConcept packages
to produce a structured Operational Concept Description document.

Usage: python __Tools/opscon_report.py <model_dir> [--output DIR]
"""
import html as _html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_unnamed_doc,
    write_report,
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
    args    = parse_args("SN-04 Operational Concept Description")
    config  = load_report_config(args.script_config)
    model_dir = args.model_dir
    project   = model_dir.name

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

        builder = ReportBuilder(
            config,
            doc_title  = "Operational Concept Description",
            doc_number = "SN-04",
            project    = project,
        )

        # 1. Introduction
        builder.add(
            "<h2>1. Introduction</h2>"
            f"<p>This document describes the operational concept for the "
            f"<strong>{_esc(project)}</strong> system: "
            "the operational environment, system purpose, primary user community, "
            "and key operational scenarios.</p>"
        )

        # 2. System Context
        builder.add("<h2>2. System Context</h2>")
        context_found = False
        for p in sorted(context_parts, key=get_declared_name):
            name = get_declared_name(p)
            doc  = get_unnamed_doc(p)
            if name.endswith("Assembly") or not doc:
                continue
            builder.add(f"<h3>{_esc(name)}</h3><p>{_esc(doc)}</p>")
            context_found = True
        if not context_found:
            builder.add(
                "<p><em>Populate <code>02_Core/Context/system_context.sysml</code> "
                "with system and actor descriptions.</em></p>"
            )

        # 3. Operational Concept Summary
        builder.add("<h2>3. Operational Concept Summary</h2>")
        summary_found = False
        for p in concept_parts:
            name = get_declared_name(p)
            doc  = get_unnamed_doc(p)
            if "Summary" in name and doc:
                builder.add(f"<p>{_esc(doc)}</p>")
                summary_found = True
        if not summary_found:
            builder.add(
                "<p><em>Populate <code>OperationalConceptSummary</code> in "
                "<code>02_Core/Context/operational_concept.sysml</code>.</em></p>"
            )

        # 4. Missions
        missions = [p for p in concept_parts if "Mission" in get_declared_name(p)]
        if missions:
            builder.add("<h2>4. Missions</h2>")
            for m in sorted(missions, key=get_declared_name):
                name = get_declared_name(m)
                doc  = get_unnamed_doc(m)
                builder.add(
                    f"<h3>{_esc(name)}</h3>"
                    f"<p>{_esc(doc) if doc else '<em>No description.</em>'}</p>"
                )

        # 5. Operational Scenarios
        scenarios = [p for p in concept_parts if "Scenario" in get_declared_name(p)]
        if scenarios:
            builder.add("<h2>5. Operational Scenarios</h2>")
            for s in sorted(scenarios, key=get_declared_name):
                name = get_declared_name(s)
                doc  = get_unnamed_doc(s)
                builder.add(
                    f"<h3>{_esc(name)}</h3>"
                    f"<p>{_esc(doc) if doc else '<em>No description.</em>'}</p>"
                )

    # Markdown fallback
    md_lines = [
        "# Operational Concept Description\n",
        f"**Project:** {project}\n",
        "## 1. Introduction\n",
        f"Operational concept description for **{project}**.\n",
    ]
    write_report(args.output / "opscon_report.md", "\n".join(md_lines), "SN-04 MD")
    builder.render_pdf(args.output / "opscon_report.pdf")


if __name__ == "__main__":
    main()
