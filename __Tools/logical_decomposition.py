"""
logical_decomposition.py — LA-02 Logical Block Decomposition

Reports the part def hierarchy across all Core::Logical packages and
generates a Graphviz diagram of the decomposition.

Usage: python __Tools/logical_decomposition.py <model_dir> [--output DIR]
"""
import sys
import re
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_unnamed_doc,
    md_heading, md_table, write_report, collapse_doc,
)
try:
    import syside
except ImportError:
    pass

FONT = "Helvetica"


def get_parent_def_names(part_def) -> list:
    """Return names of specialised (parent) defs."""
    parents = []
    try:
        for sp in part_def.specialization.collect():
            general = getattr(sp, "general", None)
            if general:
                name = get_declared_name(general)
                if name:
                    parents.append(name)
    except Exception:
        pass
    return parents


def get_part_usages_in_def(part_def) -> list:
    """Return owned part usages within a part def, excluding connectors and interfaces."""
    usages = []
    try:
        for m in part_def.owned_members.collect():
            if not m.isinstance(syside.PartUsage.STD):
                continue
            # ConnectionUsage :> PartUsage in SysML v2 — exclude interface/connect usages
            try:
                if m.isinstance(syside.ConnectionUsage.STD):
                    continue
            except Exception:
                pass
            usages.append(m.cast(syside.PartUsage.STD))
    except Exception:
        pass
    return usages


def get_usage_type_name(part_usage) -> str:
    try:
        for typ in part_usage.types.collect():
            return get_declared_name(typ)
    except Exception:
        pass
    return ""


def in_logical_pkg(element) -> bool:
    try:
        owner = element.owner
        while owner is not None:
            n = get_declared_name(owner)
            if n and any(k in n for k in ("Logical", "Feature", "CoreSystem",
                                           "LogicalArch", "Interface")):
                return True
            owner = getattr(owner, "owner", None)
    except Exception:
        pass
    return False


def render_decomposition(part_defs, diagrams_dir) -> str | None:
    safe_name = re.compile(r"[^A-Za-z0-9_]")

    def nid(name):
        return "n_" + safe_name.sub("_", name)

    nodes = []
    edges = []
    for pd in part_defs:
        name = get_declared_name(pd)
        doc  = collapse_doc(get_unnamed_doc(pd))[:60]
        label = f"{name}\\n{doc}" if doc else name
        label = label.replace('"', '\\"')
        nodes.append(
            f'    {nid(name)} [label="{label}" shape="box" '
            f'style="rounded,filled" fillcolor="#ABD9E9" '
            f'fontname="{FONT}" fontsize="10"]'
        )
        # Specialization edges
        for parent in get_parent_def_names(pd):
            edges.append(
                f'    {nid(parent)} -> {nid(name)} '
                f'[style="dashed" arrowhead="empty" color="#666666"]'
            )
        # Composition edges
        for usage in get_part_usages_in_def(pd):
            typ_name = get_usage_type_name(usage)
            u_name   = get_declared_name(usage)
            if typ_name:
                label_e = u_name or ""
                edges.append(
                    f'    {nid(name)} -> {nid(typ_name)} '
                    f'[label="{label_e}" fontname="{FONT}" fontsize="9"]'
                )

    dot = "\n".join([
        "digraph LogicalDecomposition {",
        f'    graph [rankdir="TB" fontname="{FONT}" pad="0.4" splines="spline"]',
        f'    edge  [arrowhead="open"]',
        "",
    ] + nodes + [""] + edges + ["}"])

    out = diagrams_dir / "logical_decomposition.png"
    dot_file = out.with_suffix(".dot")
    dot_file.write_text(dot, encoding="utf-8")
    try:
        subprocess.run(["dot", "-Tpng", str(dot_file), "-o", str(out)],
                       check=True, capture_output=True, timeout=30)
        dot_file.unlink(missing_ok=True)
        return str(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        dot_file.unlink(missing_ok=True)
        return None


def main():
    args = parse_args("LA-02 Logical Block Decomposition")

    with load_model(args.model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        all_defs = []
        for top in iter_user_elements(model, args.model_dir):
            collect_typed(top, syside.PartDefinition.STD, all_defs)

        # Filter to logical layer
        logical_defs = [d for d in all_defs if in_logical_pkg(d)]

        lines = [
            md_heading("Logical Block Decomposition (LA-02)"),
            f"**Model:** `{args.model_dir}`\n",
            f"**Logical part defs found:** {len(logical_defs)}\n",
        ]

        if not logical_defs:
            lines.append("> No logical part definitions found.\n")
        else:
            # Summary table
            lines.append(md_heading("Part Definition Summary", 2))
            rows = []
            for pd in sorted(logical_defs, key=get_declared_name):
                name    = get_declared_name(pd)
                doc     = collapse_doc(get_unnamed_doc(pd))[:80]
                parents = get_parent_def_names(pd)
                usages  = get_part_usages_in_def(pd)
                rows.append([
                    name,
                    ", ".join(parents) if parents else "—",
                    str(len(usages)),
                    doc or "—",
                ])
            lines.append(md_table(
                ["Part Def", "Specializes", "Owned Parts", "Description"], rows))

            # Decomposition details
            lines.append(md_heading("Decomposition Details", 2))
            for pd in sorted(logical_defs, key=get_declared_name):
                name = get_declared_name(pd)
                usages = get_part_usages_in_def(pd)
                if usages:
                    lines.append(md_heading(name, 3))
                    usage_rows = []
                    for u in usages:
                        u_name  = get_declared_name(u)
                        u_type  = get_usage_type_name(u)
                        u_doc   = collapse_doc(get_unnamed_doc(u))[:80]
                        usage_rows.append([u_name, u_type or "—", u_doc or "—"])
                    lines.append(md_table(["Usage", "Type", "Description"], usage_rows))

            # Diagram
            diagram_path = render_decomposition(logical_defs, args.diagrams_dir)
            if diagram_path:
                rel = Path(diagram_path).relative_to(args.output)
                lines.append(md_heading("Decomposition Diagram", 2))
                lines.append("Solid arrows = composition  Dashed arrows = specialization\n")
                lines.append(f"![Logical Decomposition]({rel})\n")
            else:
                lines.append("> *Install graphviz to generate decomposition diagram.*\n")

        write_report(args.output / "logical_decomposition.md", "\n".join(lines), "LA-02")


if __name__ == "__main__":
    main()
