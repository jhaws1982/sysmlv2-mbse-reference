"""
req_hierarchy.py — SR-02 Requirements Hierarchy / Decomposition

Generates a Markdown report and Graphviz PNG diagrams showing the requirement
decomposition tree. One PNG per root requirement.

Usage: python __Tools/req_hierarchy.py <model_dir> [--output DIR]
"""
import sys
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed,
    get_declared_name, get_short_name, get_unnamed_doc, get_def_type_name,
    md_heading, md_table, write_report, collapse_doc, is_plain_req,
)
try:
    import syside
except ImportError:
    pass

COLORS = {
    "highlight": "#2C7BB6",
    "ancestor":  "#ABD9E9",
    "sibling":   "#FEE090",
    "child":     "#E8F4FD",
}
FONT = "Helvetica"


@dataclass
class ReqNode:
    req_id: str
    name: str
    doc: str
    def_type: str
    children: list = field(default_factory=list)

    @property
    def label(self):
        return self.req_id if self.req_id else self.name

    @property
    def node_id(self):
        return "n_" + re.sub(r"[^A-Za-z0-9_]", "_", self.req_id or self.name)


def build_node(req) -> ReqNode:
    node = ReqNode(
        req_id=get_short_name(req), name=get_declared_name(req),
        doc=collapse_doc(get_unnamed_doc(req)), def_type=get_def_type_name(req),
    )
    try:
        for m in req.owned_members.collect():
            if m.isinstance(syside.RequirementUsage.STD) and is_plain_req(m):
                node.children.append(build_node(m.cast(syside.RequirementUsage.STD)))
    except Exception:
        pass
    return node


def collect_roots(model, model_dir) -> list:
    all_reqs = []
    for top in model.top_elements_from(str(model_dir)):
        collect_typed(top, syside.RequirementUsage.STD, all_reqs)
    roots = []
    for req in [r for r in all_reqs if is_plain_req(r)]:
        try:
            owner = req.owner
            if owner and owner.isinstance(syside.RequirementUsage.STD):
                continue
        except Exception:
            pass
        roots.append(build_node(req))
    return roots


def _node_dot(node, color, max_chars):
    doc = (node.doc[:max_chars] + "...") if len(node.doc) > max_chars else node.doc
    doc = doc.replace("\\", "\\\\").replace('"', '\\"')
    lbl = node.label.replace("\\", "\\\\").replace('"', '\\"')
    label = f"{lbl}\\n{doc}" if doc else lbl
    return (f'    {node.node_id} [label="{label}" fillcolor="{color}" '
            f'style="rounded,filled" fontname="{FONT}" fontsize="10" shape="box"]')


def render_diagram(root, highlight, out_path, cfg):
    fmt     = cfg.get("diagram_format", "png")
    splines = cfg.get("spline", "spline")
    max_ch  = cfg.get("node_doc_max_chars", 120)

    def find_path(node, target):
        if node.node_id == target.node_id:
            return [node]
        for c in node.children:
            p = find_path(c, target)
            if p:
                return [node] + p
        return []

    path = find_path(root, highlight) or [root]
    ancestor_ids = {n.node_id for n in path[:-1]}
    dot_nodes, dot_edges = [], []

    def add_level(parent, current):
        siblings = parent.children if parent else [current]
        for sib in siblings:
            if sib.node_id == highlight.node_id:
                color = COLORS["highlight"]
            elif sib.node_id in ancestor_ids:
                color = COLORS["ancestor"]
            else:
                color = COLORS["sibling"]
            dot_nodes.append(_node_dot(sib, color, max_ch))
            if parent:
                dot_edges.append(f"    {parent.node_id} -> {sib.node_id}")
        if current.node_id == highlight.node_id:
            for child in current.children:
                dot_nodes.append(_node_dot(child, COLORS["child"], max_ch))
                dot_edges.append(f"    {current.node_id} -> {child.node_id}")

    for i, node in enumerate(path):
        add_level(path[i - 1] if i > 0 else None, node)

    dot = "\n".join([
        "digraph ReqHierarchy {",
        f'    graph [rankdir="TB" fontname="{FONT}" splines="{splines}" pad="0.5"]',
        f'    edge  [arrowhead="open" fontname="{FONT}" fontsize="9"]',
        "",
    ] + dot_nodes + [""] + dot_edges + ["}"])

    dot_file = out_path.with_suffix(".dot")
    dot_file.write_text(dot, encoding="utf-8")
    try:
        subprocess.run(["dot", f"-T{fmt}", str(dot_file), "-o", str(out_path)],
                       check=True, capture_output=True, timeout=30)
        dot_file.unlink(missing_ok=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        dot_file.unlink(missing_ok=True)
        return False


def render_all(roots, diagrams_dir, cfg):
    rendered = {}
    fmt = cfg.get("diagram_format", "png")

    def do_tree(root, node):
        safe = re.sub(r"[^A-Za-z0-9_]", "_", node.label or node.name)
        out = diagrams_dir / f"req_{safe}.{fmt}"
        if render_diagram(root, node, out, cfg):
            rendered[node.node_id] = out
        for child in node.children:
            do_tree(root, child)

    for root in roots:
        do_tree(root, root)
    return rendered


def md_tree(node, depth=0):
    indent  = "  " * depth
    id_part = f"**{node.label}**" if node.label else ""
    nm_part = f" `{node.name}`" if node.name != node.label else ""
    ty_part = f" *{node.def_type}*" if node.def_type else ""
    dc_part = f" — {node.doc[:100]}" if node.doc else ""
    lines   = [f"{indent}- {id_part}{nm_part}{ty_part}{dc_part}"]
    for child in node.children:
        lines.extend(md_tree(child, depth + 1))
    return lines


def count_nodes(node):
    return 1 + sum(count_nodes(c) for c in node.children)


def main():
    args = parse_args("SR-02 Requirements Hierarchy / Decomposition")
    cfg  = args.script_config

    with load_model(args.model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        roots = collect_roots(model, args.model_dir)
        total = sum(count_nodes(r) for r in roots)

        lines = [
            md_heading("Requirements Hierarchy / Decomposition (SR-02)"),
            f"**Model:** `{args.model_dir}`  \n",
            f"**Root requirements:** {len(roots)}  |  **Total requirements:** {total}\n",
        ]

        if not roots:
            lines.append("> *No requirements found.*\n")
        else:
            lines.append(md_heading("Requirement Tree", 2))
            for root in sorted(roots, key=lambda r: r.label):
                lines.extend(md_tree(root))
            lines.append("")

            lines.append(md_heading("Root Requirements", 2))
            rows = [[r.label, r.name, r.def_type or "—", str(len(r.children)),
                     (r.doc[:70] + "...") if len(r.doc) > 70 else r.doc or "—"]
                    for r in sorted(roots, key=lambda r: r.label)]
            lines.append(md_table(["ID", "Name", "Type", "Subreqs", "Description"], rows))

            rendered = render_all(roots, args.diagrams_dir, cfg)
            if rendered:
                lines.append(md_heading("Diagrams", 2))
                lines.append("Blue = focal node  Light blue = ancestors  "
                              "Amber = siblings  Pale blue = direct children\n")
                for root in sorted(roots, key=lambda r: r.label):
                    if root.node_id in rendered:
                        rel = rendered[root.node_id].relative_to(args.output)
                        lines.append(f"**{root.label}** — `{root.name}`\n")
                        lines.append(f"![{root.label}]({rel})\n")
            else:
                lines.append("> *Graphviz not available — install graphviz to generate diagrams.*\n")

        write_report(args.output / "req_hierarchy.md", "\n".join(lines), "SR-02")


if __name__ == "__main__":
    main()
