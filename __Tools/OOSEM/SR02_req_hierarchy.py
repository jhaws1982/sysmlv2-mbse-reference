"""
req_hierarchy.py — SR-02 Requirements Hierarchy / Decomposition

Generates a Markdown report and Graphviz PNG diagrams showing the requirement
decomposition tree. One PNG per node in every root tree.

Usage: python __Tools/req_hierarchy.py <model_dir> [--output DIR]

Diagram style matches req_report.py:
  - Navy filled box  (#1F4E79, white text)  = focal (highlighted) node
  - Light blue box   (#DDEEFF, black text)  = all other visible nodes
  - HTML-like TABLE labels: ID bold on top, doc preview in 9pt below (when enabled)
  - rankdir=LR, splines=spline, white background, Helvetica font
  - Uses the graphviz Python library (not subprocess dot)

Visibility rule per diagram (same as req_report):
  - All ancestors of the focal node up to the tree root
  - All siblings at every ancestor level
  - Direct children of the focal node only (no grandchildren)

Requirement text in diagrams is hidden by default (ID-only nodes).
To show requirement text, set show_doc=True in script_config or pass
show_doc=True to render_diagram() / render_all() when calling from
another tool (e.g. sys_req_spec.py).
"""
import sys
import re
import textwrap
from pathlib import Path
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_short_name, get_unnamed_doc, get_def_type_name,
    md_heading, md_table, write_report, collapse_doc, is_plain_req,
)
try:
    import syside
except ImportError:
    pass


# ── Natural sort ──────────────────────────────────────────────────────────────

def natural_sort_key(s: str) -> list:
    """
    Sort key that orders embedded integers numerically.
    BL.2 < BL.10,  REQ-1 < REQ-10.
    """
    return [int(p) if p.isdigit() else p.lower()
            for p in re.split(r'(\d+)', s)]

# ── Palette & font (matches req_report.py) ────────────────────────────────────

HIGHLIGHT_FILL  = "#1F4E79"
HIGHLIGHT_FONT  = "white"
DEFAULT_FILL    = "#DDEEFF"
DEFAULT_FONT    = "black"
FONT            = "Helvetica"


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ReqNode:
    req_id:   str
    name:     str
    doc:      str
    def_type: str
    children: list = field(default_factory=list)
    parent:   "ReqNode | None" = field(default=None, repr=False)

    @property
    def label(self):
        return self.req_id if self.req_id else self.name

    @property
    def node_id(self):
        return "n_" + re.sub(r"[^A-Za-z0-9_]", "_", self.req_id or self.name)


# ── Tree construction ─────────────────────────────────────────────────────────

def build_node(req, parent=None) -> ReqNode:
    node = ReqNode(
        req_id=get_short_name(req), name=get_declared_name(req),
        doc=collapse_doc(get_unnamed_doc(req)), def_type=get_def_type_name(req),
        parent=parent,
    )
    try:
        for m in req.owned_members.collect():
            if m.isinstance(syside.RequirementUsage.STD) and is_plain_req(m):
                node.children.append(
                    build_node(m.cast(syside.RequirementUsage.STD), parent=node)
                )
    except Exception:
        pass
    return node


def collect_roots(model, model_dir) -> list:
    all_reqs = []
    for top in iter_user_elements(model, model_dir):
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


def flatten(node: ReqNode, depth: int = 0) -> list[tuple[int, "ReqNode"]]:
    """Pre-order (depth, node) pairs for the subtree rooted at node."""
    result = [(depth, node)]
    for child in node.children:
        result.extend(flatten(child, depth + 1))
    return result


# ── Graphviz diagram (req_report style) ───────────────────────────────────────

def _html_label(node: ReqNode, show_doc: bool = False) -> str:
    """
    HTML-like TABLE label: ID bold on top row, truncated doc in 9pt below.

    When show_doc is False (the default) only the bold ID is rendered.
    When show_doc is True and the node has doc text, a second row with a
    48-character preview is added beneath the ID.
    """
    if show_doc and node.doc:
        preview = textwrap.shorten(node.doc, width=48, placeholder="…")
        preview_esc = (
            preview.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
        )
        body = (
            f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">'
            f'<TR><TD><B>{node.label}</B></TD></TR>'
            f'<TR><TD><FONT POINT-SIZE="9">{preview_esc}</FONT></TD></TR>'
            f'</TABLE>'
        )
    else:
        body = f'<B>{node.label}</B>'
    return f"<{body}>"


def _build_parent_map(root: ReqNode) -> dict[str, ReqNode]:
    """Map node_id → parent ReqNode for the whole subtree."""
    parent_map: dict[str, ReqNode] = {}

    def _index(n: ReqNode, parent: ReqNode | None = None):
        if parent is not None:
            parent_map[n.node_id] = parent
        for c in n.children:
            _index(c, n)

    _index(root)
    return parent_map


def _ancestors(node: ReqNode, parent_map: dict[str, ReqNode]) -> list[ReqNode]:
    """Return ancestor chain from immediate parent up to tree root."""
    chain: list[ReqNode] = []
    cur = parent_map.get(node.node_id)
    while cur is not None:
        chain.append(cur)
        cur = parent_map.get(cur.node_id)
    return chain


def render_diagram(
    root: ReqNode,
    highlight: ReqNode,
    out_path: Path,
    show_doc: bool = False,
) -> bool:
    """
    Render one PNG diagram for the given highlight node within root's tree.

    Uses the graphviz Python library to match req_report.py's rendering path.
    Returns True on success, False if graphviz is unavailable.

    show_doc — when True, each node box includes a 48-char doc text preview
               beneath the bold ID.  Defaults to False (ID-only nodes).
    """
    try:
        import graphviz
    except ImportError:
        return False

    parent_map  = _build_parent_map(root)
    anc_list    = _ancestors(highlight, parent_map)
    ancestor_ids = {a.node_id for a in anc_list}
    ancestor_ids.add(root.node_id)

    # Siblings at every ancestor level (all children of each ancestor + root)
    sibling_ids: set[str] = set()
    for anc_node in [root] + anc_list:
        for c in anc_node.children:
            sibling_ids.add(c.node_id)

    # Direct children of highlight only
    child_ids = {c.node_id for c in highlight.children}

    visible_ids = ancestor_ids | sibling_ids | child_ids | {highlight.node_id}

    dot = graphviz.Digraph(
        graph_attr={
            "rankdir":  "LR",
            "splines":  "spline",
            "bgcolor":  "white",
            "fontname": FONT,
            "pad":      "0.5",
        },
        node_attr={
            "shape":    "box",
            "style":    "filled",
            "fontname": FONT,
            "fontsize": "10",
        },
        edge_attr={
            "color":     "#555555",
            "arrowhead": "open",
            "fontname":  FONT,
            "fontsize":  "9",
        },
    )

    def _add_subtree(n: ReqNode, parent_id: str | None = None):
        if n.node_id not in visible_ids:
            return
        is_hi = n.node_id == highlight.node_id
        dot.node(
            n.node_id,
            label=_html_label(n, show_doc=show_doc),
            fillcolor=HIGHLIGHT_FILL if is_hi else DEFAULT_FILL,
            fontcolor=HIGHLIGHT_FONT if is_hi else DEFAULT_FONT,
        )
        if parent_id:
            dot.edge(parent_id, n.node_id)
        for child in n.children:
            _add_subtree(child, n.node_id)

    _add_subtree(root)

    # out_path already includes the .png suffix; strip it for graphviz.render()
    stem = str(out_path.with_suffix(""))
    try:
        dot.render(stem, format="png", cleanup=True)
        return True
    except Exception:
        return False


def diagram_filename(label: str) -> str:
    """
    Canonical diagram filename for a requirement label.
    Single source of truth used by both req_hierarchy and sys_req_spec,
    so both tools always reference the same files on disk.

    All characters outside [A-Za-z0-9_-] (e.g. dots in 'A.1') are
    replaced with underscores.  Hyphens are preserved so that IDs like
    'SYS-001' stay readable.

    Example: 'A.1' -> 'req_A_1.png',  'SYS-001' -> 'req_SYS-001.png'
    """
    safe = re.sub(r"[^A-Za-z0-9_\-]", "_", label)
    return f"req_{safe}.png"


def render_all(
    roots: list[ReqNode],
    diagrams_dir: Path,
    show_doc: bool = False,
) -> dict[str, Path]:
    """
    Render one diagram per node across all root trees.
    Returns {node.label: png_path} for every successfully rendered diagram.
    Keyed by label (short req ID or name) so callers can look up by req ID.

    show_doc — passed through to render_diagram; defaults to False (ID-only).
    """
    rendered: dict[str, Path] = {}

    for root in roots:
        for _, node in flatten(root):
            out = diagrams_dir / diagram_filename(node.label or node.name)
            if render_diagram(root, node, out, show_doc=show_doc):
                rendered[node.label] = out

    return rendered


# ── Markdown helpers ──────────────────────────────────────────────────────────

def md_tree(node: ReqNode, depth: int = 0) -> list[str]:
    indent  = "  " * depth
    id_part = f"**{node.label}**" if node.label else ""
    nm_part = f" `{node.name}`" if node.name != node.label else ""
    ty_part = f" *{node.def_type}*" if node.def_type else ""
    dc_part = f" — {node.doc[:100]}" if node.doc else ""
    lines   = [f"{indent}- {id_part}{nm_part}{ty_part}{dc_part}"]
    for child in node.children:
        lines.extend(md_tree(child, depth + 1))
    return lines


def count_nodes(node: ReqNode) -> int:
    return 1 + sum(count_nodes(c) for c in node.children)


# ── Entry point ───────────────────────────────────────────────────────────────

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
            for root in sorted(roots, key=lambda r: natural_sort_key(r.label)):
                lines.extend(md_tree(root))
            lines.append("")

            lines.append(md_heading("Root Requirements", 2))
            rows = [
                [r.label, r.name, r.def_type or "—", str(len(r.children)),
                 (r.doc[:70] + "...") if len(r.doc) > 70 else r.doc or "—"]
                for r in sorted(roots, key=lambda r: natural_sort_key(r.label))
            ]
            lines.append(md_table(["ID", "Name", "Type", "Subreqs", "Description"], rows))

            # Diagrams — one per node across all trees
            # show_doc defaults False (ID-only); set show_doc=true in
            # script_config to include the requirement text preview.
            show_doc     = bool(cfg.get("show_doc", False))
            diagrams_dir = args.diagrams_dir
            diagrams_dir.mkdir(parents=True, exist_ok=True)
            rendered = render_all(roots, diagrams_dir, show_doc=show_doc)

            if rendered:
                lines.append(md_heading("Diagrams", 2))
                lines.append(
                    "Navy = focal node  |  Light blue = ancestors, siblings & direct children\n"
                )
                # Show one representative diagram per root (the root node itself)
                for root in sorted(roots, key=lambda r: natural_sort_key(r.label)):
                    if root.label in rendered:
                        rel = rendered[root.label].relative_to(args.output)
                        lines.append(f"**{root.label}** — `{root.name}`\n")
                        lines.append(f"![{root.label}]({rel})\n")
            else:
                lines.append(
                    "> *Graphviz not available — install the graphviz Python package "
                    "(`pip install graphviz`) and the Graphviz system package to generate diagrams.*\n"
                )

        write_report(args.output / "req_hierarchy.md", "\n".join(lines), "SR-02")


if __name__ == "__main__":
    main()
