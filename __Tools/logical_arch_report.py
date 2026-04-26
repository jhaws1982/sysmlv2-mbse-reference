"""
logical_arch_report.py — LA-01 Logical Architecture Description

Generates a narrative description of the logical architecture from
part defs in LogicalArchDefs, LogicalArchModel, and related packages.

Usage: python __Tools/logical_arch_report.py <model_dir> [--output DIR]
"""
import html as _html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_unnamed_doc,
    write_report, collapse_doc,
)
from report_builder import ReportBuilder, load_report_config
try:
    import syside
except ImportError:
    pass


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
    args    = parse_args("LA-01 Logical Architecture Description")
    config  = load_report_config(args.script_config)
    model_dir = args.model_dir
    project   = model_dir.name

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        part_defs   = []
        part_usages = []
        for top in iter_user_elements(model, model_dir):
            collect_typed(top, syside.PartDefinition.STD, part_defs)
            collect_typed(top, syside.PartUsage.STD, part_usages)

        subsystem_defs = [p for p in part_defs
                          if in_pkg(p, "LogicalArchDef") and
                          not in_pkg(p, "CommonDefinition", "StakeholderDef")]
        feature_defs   = [p for p in part_defs
                          if in_pkg(p, "Feature", "CoreSystem") and
                          not in_pkg(p, "LogicalArchDef")]
        arch_instances = [u for u in part_usages if in_pkg(u, "LogicalArchModel")]

        builder = ReportBuilder(
            config,
            doc_title  = "Logical Architecture Description",
            doc_number = "LA-01",
            project    = project,
        )

        # 1. Introduction
        builder.add(
            "<h2>1. Introduction</h2>"
            f"<p>This document describes the logical architecture of "
            f"<strong>{_esc(project)}</strong>: the decomposition of the system "
            "into subsystems, their responsibilities, and behavioral assignments. "
            "The logical architecture is technology-independent and maps to physical "
            "components in program-specific deployments.</p>"
        )

        # 2. Logical Subsystems
        builder.add("<h2>2. Logical Subsystems</h2>")
        if subsystem_defs:
            # Summary table
            rows_html = "".join(
                f'<tr><td>{_esc(get_declared_name(pd))}</td>'
                f'<td>{_esc(collapse_doc(get_unnamed_doc(pd))[:140] or "—")}</td></tr>'
                for pd in sorted(subsystem_defs, key=get_declared_name)
            )
            builder.add(
                '<table><thead><tr><th>Subsystem</th><th>Description</th></tr></thead>'
                f'<tbody>{rows_html}</tbody></table>'
            )
            # Narrative
            for pd in sorted(subsystem_defs, key=get_declared_name):
                name = get_declared_name(pd)
                doc  = get_unnamed_doc(pd)
                builder.add(
                    f'<h3>{_esc(name)}</h3>'
                    f'<p>{_esc(doc) if doc else "<em>No description.</em>"}</p>'
                )
        else:
            builder.add(
                "<p><em>No logical subsystem definitions found in "
                "LogicalArchDefs.</em></p>"
            )

        # 3. Feature Components
        builder.add("<h2>3. Feature Components</h2>")
        if feature_defs:
            rows_html = "".join(
                f'<tr><td>{_esc(get_declared_name(pd))}</td>'
                f'<td>{_esc(collapse_doc(get_unnamed_doc(pd))[:140] or "—")}</td></tr>'
                for pd in sorted(feature_defs, key=get_declared_name)
            )
            builder.add(
                '<table><thead><tr><th>Component</th><th>Description</th></tr></thead>'
                f'<tbody>{rows_html}</tbody></table>'
            )
        else:
            builder.add("<p><em>No feature component definitions found.</em></p>")

        # 4. Architecture Instances
        if arch_instances:
            builder.add("<h2>4. Architecture Instances</h2>")
            rows_html = "".join(
                f'<tr><td>{_esc(get_declared_name(u))}</td>'
                f'<td>{_esc(collapse_doc(get_unnamed_doc(u))[:120] or "—")}</td></tr>'
                for u in sorted(arch_instances, key=get_declared_name)
            )
            builder.add(
                '<table><thead><tr><th>Instance</th><th>Description</th></tr></thead>'
                f'<tbody>{rows_html}</tbody></table>'
            )

    # Markdown fallback
    md_lines = ["# Logical Architecture Description (LA-01)\n",
                f"**Project:** {project}\n"]
    write_report(args.output / "logical_arch_report.md",
                 "\n".join(md_lines), "LA-01 MD")
    builder.render_pdf(args.output / "logical_arch_report.pdf")


if __name__ == "__main__":
    main()
