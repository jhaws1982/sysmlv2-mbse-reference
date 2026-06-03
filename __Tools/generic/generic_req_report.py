"""
req_report.py

Generates a requirements table and hierarchy diagrams from a SysML v2 model.

Outputs:
  1. requirements.md  — Markdown table with columns:
       ID | Requirement Text | Rationale | Satisfied By | Derived From
     "Satisfied By" lists the short IDs (or names) of elements that carry a
     «satisfy» relationship to this requirement.
     "Derived From" lists the short IDs (or names) of requirements from which
     this requirement is derived via «derive» / nested-parent relationships.

  2. req_hierarchy_<ID>.png — one Graphviz LR diagram per node, showing the
     full hierarchy with the current node highlighted.

Usage:
    python __Tools/req_report.py <model_dir>
    python __Tools/req_report.py <model_dir> --format xlsx
    python __Tools/req_report.py <model_dir> --output ./reports
    python __Tools/req_report.py <model_dir> --package NetworkRequirements
    python __Tools/req_report.py <model_dir> --format xlsx --sections

Dependencies:
    pip install graphviz openpyxl   (openpyxl only needed for --format xlsx)
    graphviz system package must also be installed:
      Linux:  sudo apt install graphviz
      macOS:  brew install graphviz
      Windows: https://graphviz.org/download/

SysIDE API notes (SysIDE 0.8.x / SysML v2 2025-07):
  - RequirementUsage.req_id         -> the <'A.1'> short-name identifier string
  - RequirementUsage.nested_requirements -> subrequirements (from Usage)
  - element.documentation           -> list of Documentation elements
  - doc.declared_name               -> the name after 'doc', or None for unnamed
  - doc.body                        -> the /* ... */ text content
  - top_elements_from(path) scopes to user model files only

Doc Convention (SRS_Definitions.sysml):
  Every requirement usage must carry:
    doc           /* <normative "shall" text> */
    doc Rationale /* <rationale prose> */
  Plus a short-name ID:  requirement <'REQ-001'> myReq : SomeReqDef { ... }
  These are validated by req_validate.py; this tool reports them as-found.
"""

import sys
import re
import argparse
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _tool_utils import iter_user_elements, collect_user_sysml_files
from dataclasses import dataclass, field
import syside
from syside.preview import open_model


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class DocEntry:
    """A single doc annotation: a name (or None) and its body text."""
    name: str | None   # None for unnamed doc; 'Rationale' for doc Rationale
    body: str          # stripped body text, leading /* */ removed


@dataclass
class ReqNode:
    """A single requirement with its ID, name, doc annotations, and children."""
    req_id:       str               # e.g. "A", "A.1", "A.2.1"
    name:         str               # declared_name, e.g. "requirementA"
    docs:         list[DocEntry]    # all doc annotations in declaration order
    satisfied_by: list[str] = field(default_factory=list)  # short IDs of satisfying elements
    derived_from: list[str] = field(default_factory=list)  # short IDs of source requirements
    children:     list["ReqNode"] = field(default_factory=list)

    @property
    def req_text(self) -> str:
        """The unnamed doc body — the normative requirement statement."""
        for d in self.docs:
            if d.name is None:
                return d.body
        return ""

    @property
    def rationale(self) -> str:
        """The 'doc Rationale' body."""
        for d in self.docs:
            if d.name and d.name.lower() == "rationale":
                return d.body
        return ""

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


def get_short_label(element) -> str:
    """
    Return the shortest useful label for a related element:
    req_id / short_name if available, else declared_name, else qualified_name tail.
    """
    if element is None:
        return ""
    # Try req_id (for RequirementUsage)
    try:
        rid = element.req_id
        if rid:
            return str(rid).strip("'\"")
    except Exception:
        pass
    # Try short_name
    try:
        sn = element.short_name
        if sn:
            return str(sn).strip("'\"")
    except Exception:
        pass
    # Try declared_name
    try:
        dn = element.declared_name
        if dn:
            return dn
    except Exception:
        pass
    # Fall back to tail of qualified_name
    try:
        qn = element.qualified_name
        if qn:
            parts = str(qn).split("::")
            return parts[-1]
    except Exception:
        pass
    return ""


def _strip_doc_markers(body: str) -> str:
    """Remove /* */ comment markers and normalize leading * on continuation lines."""
    text = str(body).strip()
    # Strip opening /* with any number of asterisks
    text = re.sub(r"^/\*+\s*", "", text)
    # Strip closing */ with any number of asterisks
    text = re.sub(r"\s*\*+/$", "", text)
    # Remove leading ' * ' on interior lines (JavaDoc / SysML style)
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        cleaned.append(re.sub(r"^\s*\*\s?", "", line))
    return "\n".join(cleaned).strip()


def get_all_docs(req: syside.RequirementUsage) -> list[DocEntry]:
    """
    Return all doc annotations on this requirement, in declaration order.
    Each DocEntry carries:
      name — the declared name after 'doc' (e.g. 'Rationale'), or None for unnamed
      body — the cleaned text content
    """
    entries: list[DocEntry] = []
    try:
        for doc in req.documentation.collect():
            body = doc.body
            if not body:
                continue
            cleaned = _strip_doc_markers(body)
            if not cleaned:
                continue
            doc_name = getattr(doc, "declared_name", None) or None
            entries.append(DocEntry(name=doc_name, body=cleaned))
    except Exception:
        pass
    return entries


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


# ── Relationship extraction ───────────────────────────────────────────────────

def get_satisfied_by(req: syside.RequirementUsage) -> list[str]:
    """
    Return short labels for elements that satisfy this requirement via
    SatisfyRequirementUsage relationships anywhere in the model.

    SatisfyRequirementUsage is a RequirementUsage that references both
    the requirement being satisfied and the satisfying feature.  We search
    the already-collected global satisfy list (injected at call time), but
    here we query the requirement's own owned relationships as a fallback.

    Primary strategy: inspect owned members for SatisfyRequirementUsage
    whose satisfied requirement points back to this req.
    """
    labels: list[str] = []
    try:
        # satisfaction_subject gives the elements that satisfy this requirement
        for feat in req.satisfied_by_features.collect():
            lbl = get_short_label(feat)
            if lbl and lbl not in labels:
                labels.append(lbl)
    except Exception:
        pass
    return labels


def get_derived_from(req: syside.RequirementUsage, parent_label: str | None) -> list[str]:
    """
    Return short labels for requirements that this requirement is derived from.

    Two sources:
      1. The parent ReqNode (nesting implies derivation in SysML v2).
      2. DeriveRequirementUsage owned members (explicit «derive» annotations).
    """
    labels: list[str] = []
    if parent_label:
        labels.append(parent_label)

    # Explicit derive usages (DeriveRequirementUsage inside this req's body)
    try:
        for member in req.owned_members.collect():
            try:
                if member.isinstance(syside.DeriveRequirementUsage.STD):
                    derive = member.cast(syside.DeriveRequirementUsage.STD)
                    # The source requirement(s) are the required constraints' subjects
                    try:
                        for src in derive.derived_requirements.collect():
                            lbl = get_short_label(src)
                            if lbl and lbl not in labels:
                                labels.append(lbl)
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass

    return labels


def get_global_satisfied_by(
    req: syside.RequirementUsage,
    satisfy_usages: list,
) -> list[str]:
    """
    Search the global list of SatisfyRequirementUsage instances for any that
    reference this requirement as the satisfied requirement.

    This is necessary because satisfy statements are often declared in the
    architecture package, not inside the requirement itself.
    """
    labels: list[str] = []
    req_id_str = get_req_id(req)
    req_name = get_name(req)

    for su in satisfy_usages:
        try:
            # The requirement being satisfied
            satisfied_req = su.satisfied_requirement
            if satisfied_req is None:
                continue
            sr_id   = get_req_id(satisfied_req) if hasattr(satisfied_req, "req_id") else ""
            sr_name = get_name(satisfied_req)
            if (req_id_str and sr_id == req_id_str) or (req_name and sr_name == req_name):
                # The satisfying feature
                try:
                    feat = su.satisfying_feature
                    if feat is not None:
                        lbl = get_short_label(feat)
                        if lbl and lbl not in labels:
                            labels.append(lbl)
                except Exception:
                    pass
                # Also try the owning namespace (the part/block that declares the satisfy)
                try:
                    owner = su.owning_namespace
                    if owner is not None:
                        lbl = get_short_label(owner)
                        if lbl and lbl not in labels:
                            labels.append(lbl)
                except Exception:
                    pass
        except Exception:
            continue

    return labels


def build_req_tree(
    req: syside.RequirementUsage,
    satisfy_usages: list,
    parent_label: str | None = None,
) -> ReqNode:
    """Recursively build a ReqNode tree from a RequirementUsage."""
    req_id = get_req_id(req)
    node = ReqNode(
        req_id=req_id,
        name=get_name(req),
        docs=get_all_docs(req),
        satisfied_by=get_global_satisfied_by(req, satisfy_usages),
        derived_from=get_derived_from(req, parent_label),
    )
    try:
        for child in req.nested_requirements.collect():
            if not child.isinstance(syside.RequirementUsage.STD):
                continue
            child_req = child.cast(syside.RequirementUsage.STD)
            if is_plain_req(child_req):
                node.children.append(
                    build_req_tree(child_req, satisfy_usages, parent_label=node.label)
                )
    except Exception:
        pass
    return node


def flatten(node: ReqNode, depth: int = 0) -> list[tuple[int, ReqNode]]:
    """Return (depth, node) pairs in pre-order."""
    result = [(depth, node)]
    for child in node.children:
        result.extend(flatten(child, depth + 1))
    return result


# ── Package filter ────────────────────────────────────────────────────────────

def _req_in_package(req: syside.RequirementUsage, package_name: str) -> bool:
    """
    Return True if `req` lives inside a package whose declared_name matches
    `package_name` (case-insensitive), searching all ancestor namespaces.
    """
    try:
        ns = req.owning_namespace
        while ns is not None:
            try:
                dn = ns.declared_name
                if dn and dn.lower() == package_name.lower():
                    return True
            except Exception:
                pass
            try:
                ns = ns.owning_namespace
            except Exception:
                break
    except Exception:
        pass
    return False


# ── Markdown output ───────────────────────────────────────────────────────────

def _md_escape(text: str) -> str:
    """Escape pipe characters and collapse newlines for Markdown table cells."""
    return " ".join(text.split()).replace("|", "\\|")


def write_markdown(roots: list[ReqNode], output_dir: Path) -> Path:
    """
    Write a flat Markdown table with columns:
      ID | Requirement Text | Rationale | Satisfied By | Derived From
    """
    out = output_dir / "requirements.md"
    lines = [
        "# Requirements\n",
        "\n",
        "| ID | Requirement Text | Rationale | Satisfied By | Derived From |\n",
        "|:---|:-----------------|:----------|:-------------|:-------------|\n",
    ]

    for root in roots:
        for _depth, node in flatten(root):
            req_id      = _md_escape(node.label)
            req_text    = _md_escape(node.req_text)    if node.req_text    else "_—_"
            rationale   = _md_escape(node.rationale)   if node.rationale   else "_—_"
            sat_by      = ", ".join(node.satisfied_by) if node.satisfied_by else "_—_"
            derived_frm = ", ".join(node.derived_from) if node.derived_from else "_—_"

            lines.append(
                f"| {req_id} | {req_text} | {rationale} | {sat_by} | {derived_frm} |\n"
            )

    out.write_text("".join(lines), encoding="utf-8")
    return out


# ── Excel output ──────────────────────────────────────────────────────────────

def _section_label(name: str) -> str:
    """
    Convert a SysML declared_name to a human-readable section heading.
    Underscores become spaces; result is sentence-case (first word capitalised,
    remainder lower-cased, unless a word is an acronym-like all-caps token).

    Examples:
        "networkRequirements"      -> "Network requirements"
        "DDIL_transport_layer"     -> "DDIL transport layer"
        "security_and_crypto_reqs" -> "Security and crypto reqs"
    """
    # Insert a space before each upper-case letter that follows a lower-case letter
    # (handles camelCase names)
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    # Replace underscores / hyphens with spaces and collapse runs
    spaced = re.sub(r"[_\-]+", " ", spaced).strip()
    words = spaced.split()
    if not words:
        return name
    # Sentence-case: capitalise only the first word; leave subsequent words as-is
    # so that acronyms (DDIL, TCP, ICD) keep their capitalisation.
    result = words[0].capitalize() + (" " + " ".join(words[1:]) if len(words) > 1 else "")
    return result


def write_xlsx(roots: list[ReqNode], output_dir: Path, sections: bool = False) -> Path:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("openpyxl not installed. Run: pip install openpyxl", file=sys.stderr)
        sys.exit(1)

    wb = Workbook()
    ws = wb.active
    ws.title = "Requirements"

    header_font    = Font(bold=True, color="FFFFFF")
    header_fill    = PatternFill("solid", fgColor="1F4E79")
    # L0: dark gray banner — strong visual break between top-level groups
    section_l0_font  = Font(bold=True, color="000000")
    section_l0_fill  = PatternFill("solid", fgColor="BFBFBF")
    # L1: lighter gray — sub-section divider, clearly subordinate to L0
    section_l1_font  = Font(bold=True, color="000000")
    section_l1_fill  = PatternFill("solid", fgColor="E2E2E2")
    wrap_align     = Alignment(wrap_text=True, vertical="top")
    section_align  = Alignment(wrap_text=False, vertical="center")

    NUM_COLS = 6
    headers = ["ID", "Requirement Text", "Rationale", "Satisfied By", "Derived From", "Comments"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = wrap_align

    row_num = 2
    for root in roots:
        for depth, node in flatten(root):
            # ── Optional section-header rows (L0 and L1) ──────────────────────
            if sections and depth in (0, 1):
                heading = _section_label(node.name or node.label)
                s_font  = section_l0_font if depth == 0 else section_l1_font
                s_fill  = section_l0_fill if depth == 0 else section_l1_fill
                for col in range(1, NUM_COLS + 1):
                    cell = ws.cell(row=row_num, column=col, value=heading if col == 1 else "")
                    cell.font      = s_font
                    cell.fill      = s_fill
                    cell.alignment = section_align
                ws.merge_cells(
                    start_row=row_num, start_column=1,
                    end_row=row_num,   end_column=NUM_COLS,
                )
                row_num += 1

            ws.cell(row=row_num, column=1, value=node.label).alignment         = wrap_align
            ws.cell(row=row_num, column=2, value=node.req_text).alignment       = wrap_align
            ws.cell(row=row_num, column=3, value=node.rationale).alignment      = wrap_align
            ws.cell(row=row_num, column=4,
                    value=", ".join(node.satisfied_by)).alignment               = wrap_align
            ws.cell(row=row_num, column=5,
                    value=", ".join(node.derived_from)).alignment               = wrap_align
            ws.cell(row=row_num, column=6, value="").alignment                  = wrap_align
            row_num += 1

    col_widths = [18, 70, 50, 30, 30, 40]
    for col, width in enumerate(col_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = width

    out = output_dir / "requirements.xlsx"
    wb.save(out)
    return out


# ── Graphviz diagrams ─────────────────────────────────────────────────────────

def _graphviz_label(node: ReqNode, highlight: bool) -> str:
    """Build an HTML-like Graphviz label: ID on top, short doc preview below."""
    req_text = node.req_text
    if req_text:
        preview = textwrap.shorten(req_text, width=48, placeholder="…")
        preview_escaped = (
            preview.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
        )
        body = (
            f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">'
            f'<TR><TD><B>{node.label}</B></TD></TR>'
            f'<TR><TD><FONT POINT-SIZE="9">{preview_escaped}</FONT></TD></TR>'
            f'</TABLE>'
        )
    else:
        body = f'<B>{node.label}</B>'
    return f"<{body}>"


def write_diagram(root: ReqNode, highlight: ReqNode, output_dir: Path) -> Path | None:
    """
    Render one hierarchy diagram for `root`, highlighting the `highlight` node.

    Visibility rule:
      - All ancestors of `highlight` up to `root`
      - All siblings at every ancestor level
      - Direct children of `highlight` only (no grandchildren)
    """
    try:
        import graphviz
    except ImportError:
        print("graphviz Python package not installed. Run: pip install graphviz",
              file=sys.stderr)
        return None

    # Build parent map for the whole subtree under root
    parent_map: dict[str, ReqNode] = {}

    def _index(n: ReqNode, parent: ReqNode | None = None):
        if parent is not None:
            parent_map[n.node_id] = parent
        for c in n.children:
            _index(c, n)

    _index(root)

    # Ancestors of highlight (not including highlight itself)
    def ancestors(n: ReqNode) -> list[ReqNode]:
        chain: list[ReqNode] = []
        cur = parent_map.get(n.node_id)
        while cur is not None:
            chain.append(cur)
            cur = parent_map.get(cur.node_id)
        return chain

    anc_list = ancestors(highlight)
    ancestor_ids = {a.node_id for a in anc_list}
    ancestor_ids.add(root.node_id)

    # Siblings at every ancestor level — all children of each ancestor node
    # FIX: iterate anc_list (list[ReqNode]) and root directly, not flatten() tuples
    sibling_ids: set[str] = set()
    for anc_node in [root] + anc_list:
        for c in anc_node.children:
            sibling_ids.add(c.node_id)

    # Direct children of highlight
    child_ids = {c.node_id for c in highlight.children}

    visible_ids = ancestor_ids | sibling_ids | child_ids | {highlight.node_id}

    dot = graphviz.Digraph(
        graph_attr={
            "rankdir": "LR",
            "splines": "spline",
            "bgcolor": "white",
            "fontname": "Helvetica",
        },
        node_attr={
            "shape": "box",
            "style": "filled",
            "fontname": "Helvetica",
            "fontsize": "10",
        },
        edge_attr={"color": "#555555"},
    )

    def add_nodes_edges(n: ReqNode, parent_id: str | None = None):
        if n.node_id not in visible_ids:
            return
        is_highlight = n.node_id == highlight.node_id
        dot.node(
            n.node_id,
            label=_graphviz_label(n, is_highlight),
            fillcolor="#1F4E79" if is_highlight else "#DDEEFF",
            fontcolor="white" if is_highlight else "black",
        )
        if parent_id:
            dot.edge(parent_id, n.node_id)
        for child in n.children:
            add_nodes_edges(child, n.node_id)

    add_nodes_edges(root)

    safe_id = re.sub(r"[^A-Za-z0-9_\-]", "_", highlight.label)
    out_path = output_dir / f"req_hierarchy_{safe_id}"
    dot.render(str(out_path), format="png", cleanup=True)
    return Path(str(out_path) + ".png")


# ── Main ──────────────────────────────────────────────────────────────────────

def run(model_dir: Path, fmt: str, output_dir: Path,
        package_filter: str | None = None, sections: bool = False):
    print(f"Opening model at: {model_dir}")
    if package_filter:
        print(f"  Package filter: '{package_filter}'")
    with open_model(collect_user_sysml_files(model_dir), allow_errors=True) as model:
        all_reqs: list[syside.RequirementUsage] = []
        all_satisfy: list = []

        for element in iter_user_elements(model, model_dir):
            collect_typed(element, syside.RequirementUsage.STD, all_reqs)

        # Separate plain reqs from satisfy usages
        plain_reqs = []
        for r in all_reqs:
            if r.isinstance(syside.SatisfyRequirementUsage.STD):
                all_satisfy.append(r.cast(syside.SatisfyRequirementUsage.STD))
            elif is_plain_req(r):
                plain_reqs.append(r)

        # Apply package filter if requested
        if package_filter:
            plain_reqs = [r for r in plain_reqs if _req_in_package(r, package_filter)]

        print(f"Found {len(plain_reqs)} requirement usage(s), "
              f"{len(all_satisfy)} satisfy relationship(s).")

        # Identify top-level requirements (not nested inside another req)
        nested_ids: set[int] = set()
        for r in plain_reqs:
            try:
                for child in r.nested_requirements.collect():
                    if child.isinstance(syside.RequirementUsage.STD):
                        nested_ids.add(id(child.cast(syside.RequirementUsage.STD)))
            except Exception:
                pass
        top_level = [r for r in plain_reqs if id(r) not in nested_ids]

        roots = [build_req_tree(r, all_satisfy) for r in top_level]

        output_dir.mkdir(parents=True, exist_ok=True)

        if fmt == "xlsx":
            out = write_xlsx(roots, output_dir, sections=sections)
        else:
            out = write_markdown(roots, output_dir)
        print(f"  Written: {out}")

        # Diagrams — one per node in every tree
        for root in roots:
            for _, node in flatten(root):
                png = write_diagram(root, node, output_dir)
                if png:
                    print(f"  Diagram: {png.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SysML v2 requirements table and hierarchy diagrams."
    )
    parser.add_argument(
        "model_dir",
        help="Path to the SysML v2 model directory.",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["md", "xlsx"],
        default="md",
        help="Output format: md (default) or xlsx.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: __output in current working directory).",
    )
    parser.add_argument(
        "--package", "-p",
        default=None,
        metavar="PACKAGE_NAME",
        help=(
            "Restrict output to requirements inside this package (and its "
            "sub-packages). Matched case-insensitively against declared_name."
        ),
    )
    parser.add_argument(
        "--sections",
        action="store_true",
        default=False,
        help=(
            "Excel only: insert a gray section-header row above each top-level "
            "requirement.  The header is the human-readable form of the "
            "requirement's declared name (underscores removed, sentence case)."
        ),
    )
    args = parser.parse_args()

    if args.sections and args.format != "xlsx":
        parser.error("--sections is only valid with --format xlsx")

    model_dir = Path(args.model_dir).resolve()
    if not model_dir.is_dir():
        print(f"Error: model directory not found: {model_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output).resolve() if args.output else Path.cwd() / "__output"
    output_dir.mkdir(parents=True, exist_ok=True)

    run(model_dir, args.format, output_dir,
        package_filter=args.package, sections=args.sections)


if __name__ == "__main__":
    main()