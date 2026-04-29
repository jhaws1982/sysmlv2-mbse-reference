"""
SR04_req_traceability_matrix.py — SR-04 Requirements Derivation Traceability Matrix

Produces a cross-reference matrix showing which system requirements are derived
from which parent requirements, combining two derivation sources recognized by
SysML v2:

  1. Nesting   — a requirement declared inside another requirement body.
                 The parent implicitly derives the child.
  2. Explicit  — a DeriveRequirementUsage (#derivation connection pattern
                 or an explicit 'derive' statement) linking requirements
                 that may live in different packages.

Matrix layout:
  Rows    = all requirement levels from start_level through (start_level + depth - 1)
  Columns = requirements at exactly level (start_level + depth)

  Requirements above start_level are excluded.
  Program requirements (04_Programs/*_Requirements packages) are always
  excluded unless --program is specified, in which case ONLY requirements
  from that program package are included.

  A ✓ cell means the column requirement is derived from the row requirement.

  depth=1  →  rows=L{start},               cols=L{start+1}
  depth=2  →  rows=L{start}..L{start+1},   cols=L{start+1}..L{start+2}
  depth=N  →  rows=L{start}..L{start+N-1}, cols=L{start+1}..L{start+N}

  Rows are ordered as a pre-order tree traversal — each parent is
  immediately followed by its children before the next sibling appears.

  Row levels are visually distinguished:
    L{start}   — bold, darkest background
    L{start+1} — normal weight, "  ↳ " indent prefix, lighter background
    L{start+2} — lighter still, "    ↳ " indent prefix
    etc.

Cell colouring (Excel):
  ✓  light blue  — derivation relationship exists
  Yellow row     — row requirement has no ✓ in any column (coverage gap)
  Red column     — column requirement has no ✓ in any row (orphaned)

Program filtering:
  By default, requirements from any 04_Programs/*_Requirements package
  are excluded from both rows and columns.

  --program Program_A  restricts to ONLY that program's requirements.
  Package name derived from directory name:
      Program_A  →  ProgramA_Requirements
      Program_B  →  ProgramB_Requirements
  Pass the package name directly if it doesn't follow this convention.

Usage:
    python __Tools/OOSEM/SR04_req_traceability_matrix.py <model_dir>
    python __Tools/OOSEM/SR04_req_traceability_matrix.py <model_dir> \\
        --start-level 0 --depth 2 --format xlsx
    python __Tools/OOSEM/SR04_req_traceability_matrix.py <model_dir> \\
        --program Program_A --depth 1

    # Via artifacts.yaml script_config:
    OOSEM/SR04_req_traceability_matrix:
      format: "both"
      start_level: 0
      depth: 1
      program: "Program_A"        # optional — omit for core reqs only
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent))   # __Tools/
sys.path.insert(0, str(Path(__file__).parent))           # __Tools/OOSEM/

from _tool_utils import (
    load_model, collect_typed, iter_user_elements,
    get_declared_name, get_short_name, get_unnamed_doc, collapse_doc,
    md_heading, md_table, write_report, is_plain_req,
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


# ── Program package helpers ───────────────────────────────────────────────────

# Matches any *_Requirements package that lives under a Programs namespace.
# Used to exclude all program requirements by default.
_PROGRAM_REQ_PKG_RE = re.compile(r'(?:^|::)[A-Za-z0-9]+_Requirements(?:::|$)')


def program_package_name(program: str) -> str:
    """
    Derive the SysML package name from a 04_Programs/ directory name.

        Program_A  →  ProgramA_Requirements
        Program_B  →  ProgramB_Requirements

    If the string already ends with _Requirements it is returned as-is.
    """
    if program.endswith("_Requirements"):
        return program
    return program.replace("_", "") + "_Requirements"


def is_program_req(qname: str) -> bool:
    """Return True if this qualified name belongs to any program requirements package."""
    return bool(_PROGRAM_REQ_PKG_RE.search(qname))


def matches_program(qname: str, pkg_name: str) -> bool:
    """Return True if qname contains pkg_name as a whole :: segment."""
    pattern = re.compile(r'(?:^|::)' + re.escape(pkg_name) + r'(?:::|$)')
    return bool(pattern.search(qname))


# ── Requirement helpers ───────────────────────────────────────────────────────

def req_label(req) -> str:
    sid = get_short_name(req)
    return sid if sid else get_declared_name(req)


def qualified_name(req) -> str:
    try:
        qn = req.qualified_name
        return str(qn) if qn else ""
    except Exception:
        return ""


# ── Requirement tree node ─────────────────────────────────────────────────────

@dataclass
class ReqNode:
    label:    str
    req:      object
    level:    int
    qname:    str
    children: list = field(default_factory=list)
    parent:   object = field(default=None, repr=False)


# ── Tree construction ─────────────────────────────────────────────────────────

def build_forest(plain_reqs: list) -> list[ReqNode]:
    """
    Build a forest of ReqNode trees. Level 0 = roots (no req-typed owner).
    """
    node_by_id: dict[int, ReqNode] = {}
    for req in plain_reqs:
        node_by_id[id(req)] = ReqNode(
            label=req_label(req),
            req=req,
            level=0,
            qname=qualified_name(req),
        )

    roots: list[ReqNode] = []
    for req in plain_reqs:
        node = node_by_id[id(req)]
        try:
            owner = req.owner
            if owner and owner.isinstance(syside.RequirementUsage.STD):
                parent_node = node_by_id.get(
                    id(owner.cast(syside.RequirementUsage.STD))
                )
                if parent_node:
                    node.parent = parent_node
                    parent_node.children.append(node)
                    continue
        except Exception:
            pass
        roots.append(node)

    # Assign levels via BFS
    queue = list(roots)
    while queue:
        n = queue.pop(0)
        for child in n.children:
            child.level = n.level + 1
            queue.append(child)

    return roots


def all_nodes(forest: list[ReqNode]) -> list[ReqNode]:
    result: list[ReqNode] = []

    def _walk(n: ReqNode):
        result.append(n)
        for c in n.children:
            _walk(c)

    for root in forest:
        _walk(root)
    return result


# ── Level-window + program selection ─────────────────────────────────────────

def select_rows_and_cols(
    forest: list[ReqNode],
    start_level: int,
    depth: int,
    program_pkg: str | None,
) -> tuple[list["ReqNode"], list["ReqNode"]]:
    """
    Return (row_nodes, col_nodes) for the requested level window.

    Row nodes — nodes at levels start_level .. start_level+depth-1, inclusive.
                Ordered by pre-order tree traversal so each parent is
                immediately followed by its children before the next sibling.
    Col nodes — nodes at levels start_level+1 .. start_level+depth, inclusive.
                Sorted by level then label.

    A requirement may appear in both rows and columns (e.g. with depth=2,
    L{start+1} requirements are row sources for L{start+2} and column
    targets derived from L{start}).

    Program filtering:
      - If program_pkg is set: keep ONLY nodes whose qname matches that package.
      - If program_pkg is None: exclude ALL nodes whose qname is a program req package.
    """
    nodes = all_nodes(forest)

    if program_pkg:
        nodes = [n for n in nodes if matches_program(n.qname, program_pkg)]
    else:
        nodes = [n for n in nodes if not is_program_req(n.qname)]

    node_set = set(id(n) for n in nodes)

    row_min = start_level
    row_max = start_level + depth - 1
    col_min = start_level + 1
    col_max = start_level + depth

    # Both rows and columns use a pre-order traversal of the same filtered
    # forest so derived requirements appear immediately after their parent
    # in both axes.
    row_nodes: list[ReqNode] = []
    col_nodes: list[ReqNode] = []

    def _collect(n: ReqNode):
        if id(n) not in node_set:
            return
        if row_min <= n.level <= row_max:
            row_nodes.append(n)
        if col_min <= n.level <= col_max:
            col_nodes.append(n)
        for child in sorted(n.children, key=lambda c: natural_sort_key(c.label)):
            _collect(child)

    for root in sorted(forest, key=lambda r: natural_sort_key(r.label)):
        _collect(root)

    return row_nodes, col_nodes


# ── Derivation pair collection ────────────────────────────────────────────────

def collect_all_pairs(plain_reqs: list) -> list[tuple[str, str]]:
    """
    Collect every (source_label, derived_label) pair in the model.
    Source 1: nesting. Source 2: explicit DeriveRequirementUsage.
    """
    pairs: list[tuple[str, str]] = []

    for req in plain_reqs:
        owner_label = req_label(req)

        # Nesting
        try:
            for member in req.owned_members.collect():
                if not member.isinstance(syside.RequirementUsage.STD):
                    continue
                child = member.cast(syside.RequirementUsage.STD)
                if not is_plain_req(child):
                    continue
                child_label = req_label(child)
                if child_label and owner_label:
                    pairs.append((owner_label, child_label))
        except Exception:
            pass

        # Explicit DeriveRequirementUsage
        try:
            for member in req.owned_members.collect():
                try:
                    if not member.isinstance(syside.DeriveRequirementUsage.STD):
                        continue
                    derive = member.cast(syside.DeriveRequirementUsage.STD)
                    try:
                        for src in derive.derived_requirements.collect():
                            src_label = req_label(src)
                            if src_label and owner_label:
                                pairs.append((src_label, owner_label))
                    except Exception:
                        pass
                    try:
                        for sup in derive.suppliers.collect():
                            sup_label = req_label(sup)
                            if sup_label and owner_label:
                                pairs.append((sup_label, owner_label))
                    except Exception:
                        pass
                except Exception:
                    continue
        except Exception:
            pass

    seen: set[tuple[str, str]] = set()
    unique: list[tuple[str, str]] = []
    for pair in pairs:
        if pair not in seen:
            seen.add(pair)
            unique.append(pair)
    return unique


def filter_pairs_to_window(
    all_pairs: list[tuple[str, str]],
    row_labels: set[str],
    col_labels: set[str],
) -> list[tuple[str, str]]:
    return [(s, d) for s, d in all_pairs
            if s in row_labels and d in col_labels]


# ── Markdown rendering ────────────────────────────────────────────────────────

def _indent_prefix(level: int, start_level: int) -> str:
    """Markdown indent prefix based on how deep below start_level this node is."""
    depth_from_start = level - start_level
    return "  " * depth_from_start + ("↳ " if depth_from_start > 0 else "")


def render_matrix_md(
    row_nodes: list[ReqNode],
    col_nodes: list[ReqNode],
    pairs: list[tuple[str, str]],
    start_level: int,
) -> str:
    pair_set  = set(pairs)
    derived   = [n.label for n in col_nodes]
    transpose = len(derived) > 12

    if not transpose:
        headers = ["Source \\ Derived"] + derived
        rows = []
        for rn in row_nodes:
            prefix = _indent_prefix(rn.level, start_level)
            rows.append(
                [prefix + rn.label] +
                ["✓" if (rn.label, drv) in pair_set else "" for drv in derived]
            )
    else:
        sources = [n.label for n in row_nodes]
        headers = ["Derived \\ Source"] + [
            _indent_prefix(rn.level, start_level) + rn.label
            for rn in row_nodes
        ]
        rows = [
            [cn.label] + ["✓" if (src, cn.label) in pair_set else "" for src in sources]
            for cn in col_nodes
        ]

    note = (
        "> Matrix transposed (more than 12 derived requirements): "
        "rows = derived, columns = sources.\n\n"
        if transpose else ""
    )
    return note + md_table(headers, rows)


# ── Excel output ──────────────────────────────────────────────────────────────

# Level shading: progressively lighter grey as depth from start increases.
# Index 0 = start_level (darkest), index 1 = start+1, etc.
_LEVEL_FILLS = ["E2E8F0", "F1F5F9", "F8FAFC"]  # slate-200, slate-100, slate-50


def write_xlsx(
    row_nodes: list[ReqNode],
    col_nodes: list[ReqNode],
    pairs: list[tuple[str, str]],
    plain_reqs: list,
    output_dir: Path,
    start_level: int,
    depth: int,
    program: str | None,
    col_range: str,
) -> Path:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.comments import Comment
    except ImportError:
        print("openpyxl not installed. Run: pip install openpyxl", file=sys.stderr)
        sys.exit(1)

    NAVY   = "1F4E79"
    LTBLUE = "DDEEFF"
    RED    = "FFCCCC"
    YELLOW = "FFFACD"
    CHECK  = "✓"

    pair_set  = set(pairs)
    row_labels = [n.label for n in row_nodes]
    col_labels = [n.label for n in col_nodes]

    doc_lookup: dict[str, str] = {}
    for req in plain_reqs:
        lbl = req_label(req)
        doc = collapse_doc(get_unnamed_doc(req))
        if lbl and doc:
            doc_lookup[lbl] = doc[:120] + ("…" if len(doc) > 120 else "")

    wb = Workbook()
    ws = wb.active
    ws.title = "SR-04 Matrix"

    hdr_font   = Font(bold=True, color="FFFFFF", size=10)
    hdr_fill   = PatternFill("solid", fgColor=NAVY)
    chk_fill   = PatternFill("solid", fgColor=LTBLUE)
    ctr_align  = Alignment(horizontal="center", vertical="center")
    lft_align  = Alignment(horizontal="left",   vertical="center")
    vert_align = Alignment(horizontal="center", vertical="bottom",
                           text_rotation=90, wrap_text=False)
    thin   = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    col_level = start_level + depth
    row_range_local = (f"L{start_level}"
                       if depth == 1
                       else f"L{start_level}–L{start_level+depth-1}")
    corner = ws.cell(
        row=1, column=1,
        value=f"{row_range_local} Source \\ {col_range} Derived"
    )
    corner.font      = hdr_font
    corner.fill      = hdr_fill
    corner.alignment = lft_align
    corner.border    = border
    ws.column_dimensions["A"].width = 26

    # Column headers — rotated 90°
    for ci, cn in enumerate(col_nodes, start=2):
        cell = ws.cell(row=1, column=ci, value=cn.label)
        cell.font      = hdr_font
        cell.fill      = hdr_fill
        cell.alignment = vert_align
        cell.border    = border
        ws.column_dimensions[cell.column_letter].width = 4
    ws.row_dimensions[1].height = (
        max(len(cn.label) * 5.5 for cn in col_nodes) if col_nodes else 80
    )

    # Pre-compute gap sets
    rows_no_check = {rn.label for rn in row_nodes
                     if not any((rn.label, cn.label) in pair_set for cn in col_nodes)}
    cols_no_check = {cn.label for cn in col_nodes
                     if not any((rn.label, cn.label) in pair_set for rn in row_nodes)}

    # Level-shading fills and indent strings for row headers
    def level_fill(level: int) -> PatternFill:
        idx = min(level - start_level, len(_LEVEL_FILLS) - 1)
        return PatternFill("solid", fgColor=_LEVEL_FILLS[idx])

    def level_font(level: int) -> Font:
        bold = (level == start_level)
        return Font(bold=bold, size=10)

    def level_indent(level: int) -> str:
        depth_from_start = level - start_level
        return "  " * depth_from_start + ("↳ " if depth_from_start > 0 else "")

    # Matrix body
    for ri, rn in enumerate(row_nodes, start=2):
        row_gap  = rn.label in rows_no_check
        gap_fill = PatternFill("solid", fgColor=YELLOW)
        base_fill = gap_fill if row_gap else level_fill(rn.level)

        indent   = level_indent(rn.level)
        row_hdr  = ws.cell(row=ri, column=1, value=indent + rn.label)
        row_hdr.font      = level_font(rn.level)
        row_hdr.alignment = lft_align
        row_hdr.border    = border
        row_hdr.fill      = base_fill
        if rn.label in doc_lookup:
            row_hdr.comment = Comment(doc_lookup[rn.label], "SR-04")

        for ci, cn in enumerate(col_nodes, start=2):
            col_gap = cn.label in cols_no_check
            cell   = ws.cell(row=ri, column=ci)
            cell.border    = border
            cell.alignment = ctr_align
            if (rn.label, cn.label) in pair_set:
                cell.value = CHECK
                cell.fill  = chk_fill
                cell.font  = Font(bold=True, color=NAVY, size=11)
            elif col_gap:
                cell.fill = PatternFill("solid", fgColor=RED)
            elif row_gap:
                cell.fill = gap_fill

    ws.freeze_panes = "B2"

    # Legend sheet
    ls = wb.create_sheet("Legend")
    ls.column_dimensions["A"].width = 22
    ls.column_dimensions["B"].width = 65

    legend_data = [
        ("SR-04",        "Requirements Derivation Traceability Matrix"),
        ("Start level",  f"L{start_level} — floor; requirements above excluded"),
        ("Row levels",   f"{row_range_local} — source requirements (derived FROM)"),
        ("Col levels",   f"{col_range} — derived requirements"),
        ("Program",      program if program else "Core only (all *_Requirements excluded)"),
        ("",             ""),
        ("✓",            "Derivation relationship exists"),
        ("Yellow row",   "Row requirement has no ✓ — not deriving anything at col level"),
        ("Red col",      "Col requirement has no ✓ — no source within row levels"),
        ("",             ""),
        ("Row shading",  "Darker = higher-level (closer to root); lighter = deeper"),
        ("Row indent",   "↳ prefix and indentation indicate levels below start"),
        ("",             ""),
        ("Derivation",   "Nesting (child req inside parent req body), or"),
        ("sources",      "explicit DeriveRequirementUsage (#derivation connection)"),
    ]
    swatch_fills = {
        "✓":          PatternFill("solid", fgColor=LTBLUE),
        "Yellow row": PatternFill("solid", fgColor=YELLOW),
        "Red col":    PatternFill("solid", fgColor=RED),
        "Row shading": level_fill(start_level),
    }
    for r, (k, v) in enumerate(legend_data, start=1):
        key_cell = ls.cell(row=r, column=1, value=k)
        key_cell.font = Font(bold=True)
        if k in swatch_fills:
            key_cell.fill = swatch_fills[k]
        ls.cell(row=r, column=2, value=v)

    out = output_dir / "SR04_req_traceability_matrix.xlsx"
    wb.save(out)
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="SR-04 Requirements Derivation Traceability Matrix"
    )
    parser.add_argument("model_dir", type=Path,
                        help="Path to the model root directory")
    parser.add_argument("--format", "-f", choices=["md", "xlsx", "both"],
                        default="md",
                        help="Output format: md (default), xlsx, or both")
    parser.add_argument("--start-level", type=int, default=None,
                        help="Floor level — requirements above this are excluded. "
                             "Default: 0.")
    parser.add_argument("--depth", type=int, default=None,
                        help="Number of levels to traverse from start-level. "
                             "Rows = L{start} to L{start+depth-1}. "
                             "Cols = L{start+depth}. Default: 1.")
    parser.add_argument("--program", type=str, default=None,
                        help="Include ONLY this program's requirements (both rows "
                             "and cols). Pass the 04_Programs/ subdirectory name, "
                             "e.g. Program_A. Without this flag, all program "
                             "requirements are excluded.")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output directory (default: __output/ under cwd)")
    parser.add_argument("--config-json", type=str, default=None,
                        help="JSON config string injected by generate_artifacts.py")
    args = parser.parse_args()

    if args.output is None:
        args.output = Path.cwd() / "__output"
    args.output.mkdir(parents=True, exist_ok=True)

    model_dir = Path(args.model_dir).resolve()

    # Merge script_config — explicit CLI args always win.
    script_config: dict = {}
    if args.config_json:
        import json as _json
        try:
            script_config = _json.loads(args.config_json)
        except Exception:
            pass

    if args.format == "md" and "format" in script_config:
        args.format = script_config["format"]
    if args.start_level is None:
        args.start_level = int(script_config.get("start_level", 0))
    if args.depth is None:
        args.depth = int(script_config.get("depth", 1))
    if args.program is None and "program" in script_config:
        args.program = script_config["program"]

    program_pkg: str | None = None
    if args.program:
        program_pkg = program_package_name(args.program)
        print(f"Program filter: {args.program} → package '{program_pkg}'")
    else:
        print("Program filter: none — all *_Requirements program packages excluded.")

    col_level = args.start_level + args.depth
    col_min   = args.start_level + 1
    row_range = (f"L{args.start_level}"
                 if args.depth == 1
                 else f"L{args.start_level}–L{args.start_level + args.depth - 1}")
    col_range = (f"L{col_level}"
                 if args.depth == 1
                 else f"L{col_min}–L{col_level}")

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        all_reqs: list = []
        for top in iter_user_elements(model, model_dir):
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)

        plain_reqs = [r for r in all_reqs if is_plain_req(r)]
        print(f"Found {len(plain_reqs)} requirement usage(s).")

        forest = build_forest(plain_reqs)
        row_nodes, col_nodes = select_rows_and_cols(
            forest, args.start_level, args.depth, program_pkg
        )
        print(f"Level window: rows={row_range}, cols={col_range} "
              f"→ {len(row_nodes)} row(s), {len(col_nodes)} column(s).")

        all_pairs = collect_all_pairs(plain_reqs)
        row_labels = {n.label for n in row_nodes}
        col_labels = {n.label for n in col_nodes}
        pairs      = filter_pairs_to_window(all_pairs, row_labels, col_labels)
        print(f"Found {len(pairs)} derivation pair(s) within window.")

        rows_no_check = [n for n in row_nodes
                         if not any(n.label == p[0] for p in pairs)]

        # ── Markdown ──────────────────────────────────────────────────────────
        prog_note = f"  |  **Program:** {args.program}" if args.program else ""
        lines = [
            md_heading("Requirements Derivation Traceability Matrix (SR-04)"),
            f"**Model:** `{model_dir}`{prog_note}\n",
            f"**Start level:** {args.start_level}  |  "
            f"**Depth:** {args.depth}  |  "
            f"**Row levels:** {row_range}  |  "
            f"**Col levels:** {col_range}  |  "
            f"**Pairs:** {len(pairs)}\n",
        ]

        if not row_nodes:
            lines.append(
                f"> No requirements found at levels {row_range}. "
                "Try adjusting --start-level or --depth.\n"
            )
        elif not col_nodes:
            lines.append(
                f"> No requirements found at levels {col_range}. "
                "Try increasing --depth.\n"
            )
        else:
            lines.append(md_heading("Derivation Matrix", 2))
            lines.append(
                f"Rows = {row_range} requirements (derived **from**).  "
                f"Columns = {col_range} requirements.  "
                "✓ = derivation relationship exists.  "
                "↳ prefix = deeper level within row range.\n"
            )
            lines.append(render_matrix_md(row_nodes, col_nodes, pairs, args.start_level))

            lines.append(md_heading("Derivation Pairs", 2))
            lines.append(md_table(
                [f"Source ({row_range})", f"Derived ({col_range})"],
                [[s, d] for s, d in sorted(pairs, key=lambda p: (natural_sort_key(p[0]), natural_sort_key(p[1])))],
            ))

        if rows_no_check:
            lines.append(md_heading("Coverage Gaps", 2))
            lines.append(
                f"**{len(rows_no_check)} requirement(s) in {row_range} have no "
                f"derived requirements in {col_range}:**\n"
            )
            gap_rows = []
            for n in rows_no_check:
                doc = ""
                for r in plain_reqs:
                    if req_label(r) == n.label:
                        doc = collapse_doc(get_unnamed_doc(r))[:80]
                        break
                gap_rows.append([f"L{n.level} {n.label}", doc or "—"])
            lines.append(md_table(
                ["Requirement ID", "Requirement Text (truncated)"], gap_rows
            ))

        md_path = args.output / "SR04_req_traceability_matrix.md"
        write_report(md_path, "\n".join(lines), "SR-04 MD")

        # ── Excel ─────────────────────────────────────────────────────────────
        if args.format in ("xlsx", "both"):
            if col_nodes:
                xlsx_path = write_xlsx(
                    row_nodes, col_nodes, pairs, plain_reqs,
                    args.output, args.start_level, args.depth,
                    args.program, col_range,
                )
                print(f"  [SR-04 XLSX] → {xlsx_path}")
            else:
                print("  [SR-04 XLSX] Skipped — no column requirements in window.")


if __name__ == "__main__":
    main()
