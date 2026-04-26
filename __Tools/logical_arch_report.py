"""
logical_arch_report.py — LA-01 Logical Architecture Description

Generates a narrative description of the logical architecture from
part defs in LogicalArchDefs, LogicalArchModel, and related packages.

Usage: python __Tools/logical_arch_report.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_unnamed_doc,
    md_heading, md_table, write_report, collapse_doc, pdf_attempt,
)
try:
    import syside
except ImportError:
    pass


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
    args = parse_args("LA-01 Logical Architecture Description")
    model_dir = args.model_dir
    project = model_dir.name

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        part_defs = []
        part_usages = []
        for top in iter_user_elements(model, model_dir):
            collect_typed(top, syside.PartDefinition.STD, part_defs)
            collect_typed(top, syside.PartUsage.STD, part_usages)

        # Separate subsystem defs from feature component defs
        subsystem_defs = [p for p in part_defs
                          if in_pkg(p, "LogicalArchDef") and
                          not in_pkg(p, "CommonDefinition", "StakeholderDef")]
        feature_defs   = [p for p in part_defs
                          if in_pkg(p, "Feature", "CoreSystem") and
                          not in_pkg(p, "LogicalArchDef")]

        lines = [
            md_heading("Logical Architecture Description (LA-01)"),
            f"**Project:** {project}\n",
            "---\n",
            md_heading("1. Introduction", 2),
            f"This document describes the logical architecture of **{project}**: "
            "the decomposition of the system into subsystems, their responsibilities, "
            "and behavioral assignments. The logical architecture is technology-independent "
            "and maps to physical components in program-specific deployments.\n",
        ]

        # Logical subsystems
        lines.append(md_heading("2. Logical Subsystems", 2))
        if subsystem_defs:
            rows = []
            for pd in sorted(subsystem_defs, key=get_declared_name):
                name = get_declared_name(pd)
                doc  = collapse_doc(get_unnamed_doc(pd))
                rows.append([name, doc[:120] or "—"])
            lines.append(md_table(["Subsystem", "Description"], rows))
            lines.append("")
            # Narrative for each
            for pd in sorted(subsystem_defs, key=get_declared_name):
                name = get_declared_name(pd)
                doc  = get_unnamed_doc(pd)
                lines.append(md_heading(name, 3))
                lines.append(f"{doc or '*No description.*'}\n")
        else:
            lines.append("> No logical subsystem definitions found in LogicalArchDefs.\n")

        # Feature components
        lines.append(md_heading("3. Feature Components", 2))
        if feature_defs:
            rows = []
            for pd in sorted(feature_defs, key=get_declared_name):
                name = get_declared_name(pd)
                doc  = collapse_doc(get_unnamed_doc(pd))
                rows.append([name, doc[:120] or "—"])
            lines.append(md_table(["Component", "Description"], rows))
        else:
            lines.append("> No feature component definitions found.\n")

        # Architecture instances
        arch_instances = [u for u in part_usages
                          if in_pkg(u, "LogicalArchModel")]
        if arch_instances:
            lines.append(md_heading("4. Architecture Instances", 2))
            rows = []
            for u in sorted(arch_instances, key=get_declared_name):
                name = get_declared_name(u)
                doc  = collapse_doc(get_unnamed_doc(u))
                rows.append([name, doc[:100] or "—"])
            lines.append(md_table(["Instance", "Description"], rows))

    md_content = "\n".join(lines)
    md_path = args.output / "logical_arch_report.md"
    write_report(md_path, md_content, "LA-01 MD")
    pdf_attempt(md_content, args.output / "logical_arch_report.pdf", "LA-01", number_sections=False)


if __name__ == "__main__":
    main()
