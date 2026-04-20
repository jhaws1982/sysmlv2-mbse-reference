"""
req_report.py

Generates a requirements list and hierarchy diagrams from a SysML v2 model.

Outputs:
  1. requirements.md  — flat list with IDs as enumerators, doc text included
  2. req_hierarchy_<ID>.png — one Graphviz LR diagram per top-level requirement,
     showing the full derivation tree with the current node highlighted

Usage:
    python req_report.py <model-path-or-file>
    python req_report.py <model-path-or-file> --format xlsx
    python req_report.py <model-path-or-file> --output-dir ./reports

Dependencies:
    pip install graphviz openpyxl   (openpyxl only needed for --format xlsx)
    graphviz system package must also be installed:
      Linux:  sudo apt install graphviz
      macOS:  brew install graphviz
      Windows: https://graphviz.org/download/

SysIDE API notes (SysIDE 0.8.x / SysML v2 2025-07):
  - RequirementUsage.req_id        -> the <'A.1'> short name identifier string
  - RequirementUsage.nested_requirements -> subrequirements (from Usage)
  - element.short_name             -> the <'X'> value (same as req_id source)
  - element.documentation          -> list of Documentation elements
  - doc.body                       -> the /* ... */ text content
  - top_elements_from(path) scopes to user model files only
"""

import sys
import re
import argparse
import textwrap
from pathlib import Path
from dataclasses import dataclass, field
import syside
from syside.preview import open_model


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ReqNode:
    """A single requirement with its ID, name, doc text, and children."""
    req_id:   str          # e.g. "A", "A.1", "A.2.1"
    name:     str          # declared_name, e.g. "requirementA"
    doc:      str          # first doc block body text, stripped
    children: list["ReqNode"] = field(default_factory=list)

    @property
    def label(self) -> str:
        """Short label for display: ID if present, else name."""
        return self.req_id if self.req_id else self.name

    @property
    def node_id(self) -> str:
        """Graphviz-safe node identifier (no spaces or special chars)."""
        safe = re.sub(r"[^A-Za-z0-9_]", "_", self.req_id or self.name)
        return f"n_{safe}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_name(element) -> str:
    if element is None:
        return ""
    name = element.declared_name
    if name:
        return name
    qn = element.qualified_name
    return str(qn) if qn else ""


def get_req_id(req: syside.RequirementUsage) -> str:
    """
    Return the requirement ID from req_id or short_name.
    The <'A.1'> syntax sets short_name; req_id is the spec accessor for it.
    Falls back to declared_name if neither is set.
    """
    try:
        rid = req.req_id
        if rid:
            return str(rid).strip("'\"")
    except Exception:
        pass
    try:
        sn = req.short_name
        if sn:
            return str(sn).strip("'\"")
    except Exception:
        pass
    return get_name(req)


def get_doc_text(req: syside.RequirementUsage) -> str:
    """Return the first doc block body, stripped of leading /* */ markers."""
    try:
        for doc in req.documentation.collect():
            body = doc.body
            if body:
                # Strip /* */ markers and normalize whitespace
                text = str(body).strip()
                text = re.sub(r"^/\*+\s*", "", text)
                text = re.sub(r"\s*\*+/$", "", text)
                return text.strip()
    except Exception:
        pass
    return ""


def collect_typed(root, std_type, results: list):
    """Depth-first collection of all elements matching std_type."""
    if root.isinstance(std_type):
        results.append(root.cast(std_type))
    if root.isinstance(syside.Namespace.STD):
        ns = root.cast(syside.Namespace.STD)
        for member in ns.owned_members.collect():
            collect_typed(member, std_type, results)


def is_plain_req(r) -> bool:
    """Filter to plain RequirementUsage — exclude satisfy, concern, viewpoint."""
    return (
        not r.isinstance(syside.SatisfyRequirementUsage.STD)
        and not r.isinstance(syside.ConcernUsage.STD)
    )


def build_req_tree(req: syside.RequirementUsage) -> ReqNode:
    """Recursively build a ReqNode tree from a RequirementUsage."""
    node = ReqNode(
        req_id=get_req_id(req),
        name=get_name(req),
        doc=get_doc_text(req),
    )
    try:
        for child in req.nested_requirements.collect():
            if not is_plain_req(child):
                continue
            child_req = child.cast(syside.RequirementUsage.STD)
            node.children.append(build_req_tree(child_req))
    except Exception:
        pass
    return node


def flatten(node: ReqNode, depth: int = 0) -> list[tuple[int, ReqNode]]:
    """Flatten a tree to a list of (depth, node) pairs in pre-order."""
    result = [(depth, node)]
    for child in node.children:
        result.extend(flatten(child, depth + 1))
    return result


# ── Markdown output ───────────────────────────────────────────────────────────

def _doc_for_markdown(doc: str) -> str:
    """
    Collapse a doc block to a single inline string safe for a Markdown list item.

    Blank lines inside a doc block would terminate the list item in Markdown,
    so we strip them and join all lines into one continuous paragraph.
    """
    if not doc:
        return ""
    # Split on newlines, discard blank lines, rejoin with a space
    cleaned = " ".join(line.strip() for line in doc.splitlines() if line.strip())
    return cleaned


def write_markdown(trees: list[ReqNode], output_path: Path):
    lines = []
    lines.append("# Requirements List\n")

    for tree in trees:
        for depth, node in flatten(tree):
            indent = "  " * depth
            # Use ID as the list marker when available
            label = f"**{node.req_id}**" if node.req_id else f"**{node.name}**"
            name_part = f" `{node.name}`" if node.name and node.name != node.req_id else ""
            # Collapse multiline doc to single line — blank lines break MD lists
            doc_single = _doc_for_markdown(node.doc)
            doc_part = f" — {doc_single}" if doc_single else ""
            lines.append(f"{indent}- {label}{name_part}{doc_part}")

        lines.append("")  # blank line between top-level trees

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown written to: {output_path}")


# ── Excel output ──────────────────────────────────────────────────────────────

def write_xlsx(trees: list[ReqNode], output_path: Path):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("ERROR: openpyxl not installed. Run: pip install openpyxl", file=sys.stderr)
        sys.exit(1)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Requirements"

    # Header
    headers = ["ID", "Name", "Depth", "Parent ID", "Description"]
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="2E4057")
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # Column widths
    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["B"].width = 25
    ws.column_dimensions["C"].width = 8
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 60

    # Alternating row fills
    fills = [PatternFill("solid", fgColor="F0F4F8"),
             PatternFill("solid", fgColor="FFFFFF")]

    row_num = 2
    for tree in trees:
        # Build parent map
        parent_map: dict[str, str] = {}
        def _build_parent(node: ReqNode, parent_id: str = ""):
            parent_map[node.req_id or node.name] = parent_id
            for child in node.children:
                _build_parent(child, node.req_id or node.name)
        _build_parent(tree)

        for depth, node in flatten(tree):
            key = node.req_id or node.name
            parent_id = parent_map.get(key, "")
            fill = fills[row_num % 2]
            row_data = [node.req_id, node.name, depth, parent_id, node.doc]
            for col, val in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col, value=val)
                cell.fill = fill
                cell.alignment = Alignment(wrap_text=(col == 5), vertical="top")
            row_num += 1

    ws.freeze_panes = "A2"
    wb.save(output_path)
    print(f"Excel written to: {output_path}")


# ── Graphviz diagram ──────────────────────────────────────────────────────────

def make_label(node: ReqNode, max_doc_width: int = 40) -> str:
    """Build a multi-line Graphviz HTML-like label for a node."""
    id_part   = node.req_id if node.req_id else ""
    name_part = node.name if node.name else ""
    # Wrap at max_doc_width but show ALL lines — no truncation
    doc_lines = textwrap.wrap(node.doc, max_doc_width) if node.doc else []

    # Build label: ID bold on first line, name italic, full doc below
    parts = []
    if id_part:
        parts.append(f"<B>{id_part}</B>")
    if name_part and name_part != id_part:
        parts.append(f"<I>{name_part}</I>")
    for line in doc_lines:
        # escape XML special chars
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts.append(safe)

    return "<" + "<BR/>".join(parts) + ">"


def find_node(tree: ReqNode, target_id: str) -> ReqNode | None:
    """Find a node in the tree by req_id or name."""
    if tree.req_id == target_id or tree.name == target_id:
        return tree
    for child in tree.children:
        result = find_node(child, target_id)
        if result:
            return result
    return None


def ancestor_ids(tree: ReqNode, target_id: str) -> set[str]:
    """
    Return the set of req_ids/names of all ancestors of target_id,
    including the target itself.
    """
    def _search(node: ReqNode, path: list[ReqNode]) -> list[ReqNode] | None:
        current_path = path + [node]
        key = node.req_id or node.name
        if key == target_id:
            return current_path
        for child in node.children:
            result = _search(child, current_path)
            if result:
                return result
        return None

    path = _search(tree, [])
    if not path:
        return set()
    return {n.req_id or n.name for n in path}


def visible_nodes(tree: ReqNode, highlight_id: str,
                  show_siblings: bool = True,
                  show_children: bool = True) -> set[str]:
    """
    Compute the set of node IDs that should be visible for a given highlight.

    Rules (always applied):
      - All ancestors up to root (full parent chain)
      - The highlighted node itself

    When show_siblings=True (default):
      - All siblings at EVERY level of the ancestor chain are also shown.

    When show_children=True (default):
      - Direct children of the highlighted node are shown (not grandchildren).
    """
    visible: set[str] = set()

    def _find_path(node: ReqNode, target: str,
                   path: list[ReqNode]) -> list[ReqNode] | None:
        current = path + [node]
        key = node.req_id or node.name
        if key == target:
            return current
        for child in node.children:
            result = _find_path(child, target, current)
            if result:
                return result
        return None

    path = _find_path(tree, highlight_id, [])
    if not path:
        # highlight_id not found — show full tree
        for _, node in flatten(tree):
            visible.add(node.req_id or node.name)
        return visible

    # All ancestors are always visible
    for node in path:
        visible.add(node.req_id or node.name)

    if show_siblings:
        # Siblings at every ancestor level: for each ancestor, expose all its
        # children. This makes every sibling at every depth of the path visible.
        for i in range(len(path) - 1):
            parent = path[i]
            for child in parent.children:
                visible.add(child.req_id or child.name)

    # Direct children of the highlighted node only (not grandchildren)
    if show_children:
        highlighted_node = path[-1]
        for child in highlighted_node.children:
            visible.add(child.req_id or child.name)

    return visible



def add_visible_nodes(dot_lines: list[str],
                      node: ReqNode,
                      highlight_id: str,
                      visible: set[str],
                      depth: int = 0):
    """
    Recursively emit Graphviz node and edge declarations,
    but only for nodes in the visible set.
    """
    key = node.req_id or node.name
    if key not in visible:
        return

    is_highlight = (node.req_id == highlight_id or node.name == highlight_id)

    if is_highlight:
        style = ('fillcolor="#E8A838" fontcolor="black" '
                 'style="filled,bold" penwidth="2.5"')
    elif depth == 0:
        style = 'fillcolor="#2E4057" fontcolor="white" style="filled"'
    else:
        style = 'fillcolor="#E8F4FD" fontcolor="black" style="filled"'

    label = make_label(node)
    dot_lines.append(f'  {node.node_id} [{style} label={label} shape="box" '
                     f'margin="0.15,0.1"];')

    for child in node.children:
        child_key = child.req_id or child.name
        if child_key in visible:
            dot_lines.append(f'  {node.node_id} -> {child.node_id} '
                             f'[color="#555555" arrowsize="0.8"];')
            add_visible_nodes(dot_lines, child, highlight_id, visible, depth + 1)


def render_diagram(tree: ReqNode,
                   highlight_id: str,
                   output_path: Path,
                   show_siblings: bool = True,
                   show_children: bool = True):
    """
    Render a hierarchy diagram as PNG using Graphviz.

    Shows: all ancestors of highlight_id, plus optionally siblings at every
    ancestor level (show_siblings) and direct children (show_children).
    The highlighted node is rendered in amber.
    """
    try:
        import graphviz
    except ImportError:
        print("ERROR: graphviz Python package not installed. "
              "Run: pip install graphviz", file=sys.stderr)
        return

    visible = visible_nodes(tree, highlight_id,
                            show_siblings=show_siblings,
                            show_children=show_children)

    dot_lines = [
        "digraph requirements {",
        '  rankdir="LR";',
        '  bgcolor="white";',
        '  splines="spline";',
        '  node [fontname="Helvetica" fontsize="11"];',
        '  edge [fontname="Helvetica" fontsize="9" arrowhead="normal"];',
        '  graph [pad="0.4" nodesep="0.5" ranksep="1.0"];',
    ]

    add_visible_nodes(dot_lines, tree, highlight_id, visible)
    dot_lines.append("}")

    dot_source = "\n".join(dot_lines)

    src = graphviz.Source(dot_source)
    src.render(
        filename=str(output_path.with_suffix("")),
        format="png",
        cleanup=True,
        quiet=True,
    )
    final = output_path if output_path.exists() else output_path.with_suffix(".png")
    print(f"  Diagram: {final}")


# ── Main ──────────────────────────────────────────────────────────────────────

def run(model_dir: Path, output_dir: Path, fmt: str,
        show_siblings: bool = True, show_children: bool = True):
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading model from: {model_dir}\n")

    with open_model(model_dir) as model:

        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")
        for msg in diags.warnings:
            print(f"  WARNING: {msg}")

        # Collect all RequirementUsage elements from the target scope
        all_reqs: list = []
        for top in model.top_elements_from(model_dir):
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)

        # Filter to plain requirement usages only
        all_reqs = [r for r in all_reqs if is_plain_req(r)]

        if not all_reqs:
            print("No requirements found.")
            return

        # Identify top-level requirements: those whose owning_usage is not
        # itself a RequirementUsage (i.e. not nested inside another requirement)
        top_level = []
        for r in all_reqs:
            try:
                owner = r.owning_usage
                if owner is None or not owner.isinstance(syside.RequirementUsage.STD):
                    top_level.append(r)
            except Exception:
                top_level.append(r)

        # Sort by req_id
        top_level.sort(key=lambda r: get_req_id(r))

        print(f"Found {len(top_level)} top-level requirement(s):")
        trees = []
        for r in top_level:
            tree = build_req_tree(r)
            trees.append(tree)
            child_count = len(flatten(tree)) - 1
            print(f"  [{tree.label}] {tree.name}  ({child_count} derived)")

        # ── Output 1: Requirements list ───────────────────────────────────
        print()
        if fmt == "xlsx":
            out_path = output_dir / "requirements.xlsx"
            write_xlsx(trees, out_path)
        else:
            out_path = output_dir / "requirements.md"
            write_markdown(trees, out_path)

        # ── Output 2: Hierarchy diagrams ──────────────────────────────────
        print("\nGenerating hierarchy diagrams...")
        for tree in trees:
            # One diagram per node in the tree, each highlighted in turn
            all_nodes = flatten(tree)
            for _, node in all_nodes:
                safe_id = re.sub(r"[^A-Za-z0-9_]", "_", node.req_id or node.name)
                png_name = f"req_hierarchy_{safe_id}.png"
                png_path = output_dir / png_name
                render_diagram(tree, node.req_id or node.name, png_path,
                               show_siblings=show_siblings,
                               show_children=show_children)

        print(f"\nDone. Output written to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate requirements list and hierarchy diagrams from SysML v2."
    )
    parser.add_argument(
        "model_dir",
        help="Path to model root directory"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["md", "xlsx"],
        default="md",
        help="Output format for requirements list: md (default) or xlsx"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: __output in current working directory)"
    )
    parser.add_argument(
        "--no-siblings",
        action="store_true",
        default=False,
        help="Hide sibling nodes in hierarchy diagrams — show only ancestors, "
             "highlighted node, and its direct children (default: siblings shown)"
    )
    parser.add_argument(
        "--no-children",
        action="store_true",
        default=False,
        help="Hide child nodes in hierarchy diagrams — show only ancestors "
             "and highlighted node (default: direct children shown)"
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir).resolve()
    if not model_dir.is_dir():
        print(f"Error: '{model_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output).resolve() if args.output else Path.cwd() / "__output"

    run(model_dir, output_dir, args.format,
        show_siblings=not args.no_siblings,
        show_children=not args.no_children)
