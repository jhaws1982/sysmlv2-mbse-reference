"""
generic_concerns_matrix.py

Generates a Concern → Requirement traceability matrix as an Excel workbook.

Layout:
  Rows    = stakeholder concern definitions
  Columns = requirement usages that frame concerns (short ID, or name)
  Cell    = ✓ where the requirement frames the concern

Column headers are rotated 90° (vertical text) with narrow fixed width,
matching the SR-04 matrix style.

Program filtering:
  By default all program requirements and concerns (04_Programs/) are excluded.
  --program Program_A  restricts to ONLY that program's concerns and requirements.

Usage:
    python __Tools/generic/generic_concerns_matrix.py .
    python __Tools/generic/generic_concerns_matrix.py . --program Program_A
    python __Tools/generic/generic_concerns_matrix.py . --output ./reports
"""

import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))   # __Tools/
sys.path.insert(0, str(Path(__file__).parent))           # __Tools/generic/

from _tool_utils import iter_user_elements, collect_user_sysml_files, is_plain_req, _EXCLUDED_DIRS, get_unnamed_doc
import syside
from syside.preview import open_model


# ── Palette (matches SR-04 / SR-02 style) ────────────────────────────────────

NAVY   = "1F4E79"
LTBLUE = "DDEEFF"
RED    = "FFCCCC"
YELLOW = "FFFACD"
CHECK  = "✓"


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_name(element) -> str:
    name = element.declared_name
    if name:
        return name
    qn = element.qualified_name
    return str(qn) if qn else "<unnamed>"


def get_short_label(element) -> str:
    """Short-name ID if present, else declared name."""
    try:
        sn = element.short_name
        if sn:
            return str(sn).strip("'\"")
    except Exception:
        pass
    return get_name(element)


def qualified_name(element) -> str:
    try:
        qn = element.qualified_name
        return str(qn) if qn else ""
    except Exception:
        return ""


def collect_typed(root, std_type, results: list):
    if root.isinstance(std_type):
        results.append(root.cast(std_type))
    if root.isinstance(syside.Namespace.STD):
        ns = root.cast(syside.Namespace.STD)
        for member in ns.owned_members.collect():
            collect_typed(member, std_type, results)


def framed_concern_labels(req) -> set[str]:
    """
    Return the set of concern labels framed by this requirement usage.

    'frame concern X' is declared on the requirement *definition*, not the
    usage, so we walk from the usage to its definition (via .definition or
    .type) and collect ConcernUsage members from there.  We also check the
    usage's own members as a fallback for inline 'frame concern' statements.
    """
    labels: set[str] = set()

    def _collect_from(element):
        try:
            for member in element.owned_members.collect():
                if member.isinstance(syside.ConcernUsage.STD):
                    cu = member.cast(syside.ConcernUsage.STD)
                    n = cu.declared_name
                    if n:
                        labels.add(n)
        except Exception:
            pass

    # Check the usage itself (inline frame concern)
    _collect_from(req)

    # Walk to the requirement definition
    for attr in ("definition", "type"):
        try:
            defn = getattr(req, attr)
            if defn is None:
                continue
            # .type may return a collection — handle both
            try:
                for t in defn.collect():
                    _collect_from(t)
            except AttributeError:
                _collect_from(defn)
            break
        except Exception:
            continue

    return labels


# ── Program filtering ─────────────────────────────────────────────────────────

def natural_sort_key(s: str) -> list:
    """
    Sort key that orders embedded integers numerically.
    'BL.2' < 'BL.10',  'REQ-1' < 'REQ-10',  'A' < 'B'.
    """
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r'(\d+)', s)]
    """
    Derive the SysML package name prefix for a program directory name.
    Program_A → ProgramA  (used only for display; filtering is by directory path)
    """
    return program.replace("_", "")


# ── Collection ────────────────────────────────────────────────────────────────

def collect_elements(
    model,
    model_dir: Path,
    program: str | None,
) -> tuple[list, list]:
    """
    Collect (concern_defs, req_usages) scoped by directory.

    Concerns are ConcernDefinition; requirements are RequirementUsage
    filtered by is_plain_req().

    If program is set:  collect ONLY from 04_Programs/<program>/ subtree
                        using model.top_elements_from() scoped to that dir.
    If program is None: iterate model_dir exactly as iter_user_elements does,
                        but skip the 04_Programs/ directory entirely so no
                        program elements are ever visited.
    """
    programs_dir = model_dir / "04_Programs"
    all_concerns: list = []
    all_req_usages: list = []

    if program:
        prog_dir = programs_dir / program
        if not prog_dir.is_dir():
            available = ([d.name for d in programs_dir.iterdir() if d.is_dir()]
                         if programs_dir.is_dir() else [])
            print(f"ERROR: Program directory not found: {prog_dir}", file=sys.stderr)
            print(f"Available programs: {available}", file=sys.stderr)
            return [], []
        try:
            for top in model.top_elements_from(str(prog_dir)):
                collect_typed(top, syside.ConcernDefinition.STD, all_concerns)
                collect_typed(top, syside.RequirementUsage.STD,  all_req_usages)
        except Exception as e:
            print(f"WARNING: Could not scope to {prog_dir}: {e}", file=sys.stderr)
    else:
        # Mirror iter_user_elements but skip 04_Programs/ entirely
        for item in sorted(model_dir.iterdir()):
            if item.name.startswith('.'):
                continue
            # Skip the programs directory — we never want program elements here
            if item.resolve() == programs_dir.resolve():
                continue
            if item.name in _EXCLUDED_DIRS:
                continue
            if item.is_dir() or (item.is_file() and item.suffix == '.sysml'):
                try:
                    for top in model.top_elements_from(str(item)):
                        collect_typed(top, syside.ConcernDefinition.STD, all_concerns)
                        collect_typed(top, syside.RequirementUsage.STD,  all_req_usages)
                except Exception:
                    pass

    plain_req_usages = [r for r in all_req_usages if is_plain_req(r)]
    # Exclude base/organizational concern defs that have no doc block —
    # real stakeholder concerns always document what the concern is.
    documented_concerns = [c for c in all_concerns if get_unnamed_doc(c)]
    return documented_concerns, plain_req_usages


# ── Excel output ──────────────────────────────────────────────────────────────

def write_xlsx(
    concern_labels: list[str],
    req_labels: list[str],
    frames: dict[str, set[str]],
    output_path: Path,
    title: str,
) -> Path:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.comments import Comment
    except ImportError:
        print("openpyxl not installed. Run: pip install openpyxl", file=sys.stderr)
        sys.exit(1)

    wb = Workbook()
    ws = wb.active
    ws.title = "Concerns Matrix"

    hdr_font   = Font(bold=True, color="FFFFFF", size=10)
    hdr_fill   = PatternFill("solid", fgColor=NAVY)
    chk_fill   = PatternFill("solid", fgColor=LTBLUE)
    gap_fill   = PatternFill("solid", fgColor=YELLOW)
    red_fill   = PatternFill("solid", fgColor=RED)
    ctr_align  = Alignment(horizontal="center", vertical="center")
    lft_align  = Alignment(horizontal="left",   vertical="center")
    vert_align = Alignment(horizontal="center", vertical="bottom",
                           text_rotation=90, wrap_text=False)
    thin   = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Pre-compute gap sets
    concerns_no_req = {c for c in concern_labels
                       if not any(c in frames.get(r, set()) for r in req_labels)}
    reqs_no_concern = {r for r in req_labels
                       if not any(c in frames.get(r, set()) for c in concern_labels)}

    # Corner cell
    corner = ws.cell(row=1, column=1, value="Concern \\ Requirement")
    corner.font      = hdr_font
    corner.fill      = hdr_fill
    corner.alignment = lft_align
    corner.border    = border
    ws.column_dimensions["A"].width = 30

    # Column headers — requirement short IDs, rotated 90°
    for ci, req_lbl in enumerate(req_labels, start=2):
        cell = ws.cell(row=1, column=ci, value=req_lbl)
        cell.font      = hdr_font
        cell.fill      = hdr_fill
        cell.alignment = vert_align
        cell.border    = border
        ws.column_dimensions[cell.column_letter].width = 4
    ws.row_dimensions[1].height = (
        max(len(r) * 5.5 for r in req_labels) if req_labels else 80
    )

    # Matrix body
    for ri, concern in enumerate(concern_labels, start=2):
        row_gap = concern in concerns_no_req

        row_hdr = ws.cell(row=ri, column=1, value=concern)
        row_hdr.font      = Font(bold=True, size=10)
        row_hdr.alignment = lft_align
        row_hdr.border    = border
        row_hdr.fill      = red_fill if row_gap else PatternFill()

        for ci, req_lbl in enumerate(req_labels, start=2):
            col_gap = req_lbl in reqs_no_concern
            cell   = ws.cell(row=ri, column=ci)
            cell.border    = border
            cell.alignment = ctr_align
            if concern in frames.get(req_lbl, set()):
                cell.value = CHECK
                cell.fill  = chk_fill
                cell.font  = Font(bold=True, color=NAVY, size=11)
            elif row_gap:
                cell.fill = red_fill
            elif col_gap:
                cell.fill = gap_fill

    ws.freeze_panes = "B2"

    # Legend sheet
    ls = wb.create_sheet("Legend")
    ls.column_dimensions["A"].width = 20
    ls.column_dimensions["B"].width = 60

    legend_data = [
        ("Concerns Matrix", title),
        ("Rows",            "Stakeholder concern definitions"),
        ("Columns",         "Requirement usages that frame concerns (short ID or name)"),
        ("",                ""),
        ("✓",               "Requirement frames this concern"),
        ("Red row",         "Concern has no requirement framing it — uncovered concern (critical gap)"),
        ("Yellow column",   "Requirement frames no concerns — not tied to a stakeholder concern"),
        ("",                ""),
        ("Program filter",  "Core model only" if "Core" in title else title),
    ]
    swatch_fills = {
        "✓":             PatternFill("solid", fgColor=LTBLUE),
        "Red row":       PatternFill("solid", fgColor=RED),
        "Yellow column": PatternFill("solid", fgColor=YELLOW),
    }
    for r, (k, v) in enumerate(legend_data, start=1):
        key_cell = ls.cell(row=r, column=1, value=k)
        key_cell.font = Font(bold=True)
        if k in swatch_fills:
            key_cell.fill = swatch_fills[k]
        ls.cell(row=r, column=2, value=v)

    wb.save(output_path)
    return output_path


# ── Markdown summary ──────────────────────────────────────────────────────────

def write_markdown(
    concern_labels: list[str],
    req_labels: list[str],
    frames: dict[str, set[str]],
    output_path: Path,
    title: str,
):
    concerns_no_req = [c for c in concern_labels
                       if not any(c in frames.get(r, set()) for r in req_labels)]

    lines = [
        f"# {title}\n",
        f"**Concerns:** {len(concern_labels)}  |  "
        f"**Requirements:** {len(req_labels)}  |  "
        f"**Coverage gaps:** {len(concerns_no_req)}\n",
    ]

    if concerns_no_req:
        lines.append("## Coverage Gaps\n")
        lines.append("Concerns with no framing requirement:\n")
        for c in concerns_no_req:
            lines.append(f"- {c}\n")
        lines.append("")

    lines.append("## Concern × Requirement Matrix\n")
    header = "| Concern | " + " | ".join(req_labels) + " |"
    sep    = "|:--------|" + "|".join([":---:"] * len(req_labels)) + "|"
    lines.append(header + "\n")
    lines.append(sep + "\n")
    for concern in concern_labels:
        cells = " | ".join(
            CHECK if concern in frames.get(r, set()) else ""
            for r in req_labels
        )
        lines.append(f"| {concern} | {cells} |\n")

    output_path.write_text("".join(lines), encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate Concern → Requirement traceability matrix (Excel)."
    )
    parser.add_argument("model_dir", help="Path to model root directory")
    parser.add_argument(
        "--program", "-p", default=None,
        help="04_Programs/ subdirectory name (e.g. Program_A). "
             "Restricts to that program's concerns and requirements only. "
             "Without this flag, all program elements are excluded."
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output directory (default: __output/ under cwd)"
    )
    parser.add_argument(
        "--config-json", type=str, default=None,
        help="JSON config string injected by generate_artifacts.py"
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir).resolve()
    if not model_dir.is_dir():
        print(f"Error: '{model_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output).resolve() if args.output else Path.cwd() / "__output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Merge script_config
    script_config: dict = {}
    if args.config_json:
        import json as _json
        try:
            script_config = _json.loads(args.config_json)
        except Exception:
            pass
    if args.program is None and "program" in script_config:
        args.program = script_config["program"]

    if args.program:
        print(f"Program filter: {args.program}")
        title = f"Concern → Requirement Matrix — {args.program}"
        xlsx_name = f"concerns_matrix_{args.program}.xlsx"
        md_name   = f"concerns_matrix_{args.program}.md"
    else:
        print("Program filter: none — all program elements excluded (core only).")
        title = "Concern → Requirement Matrix — Core"
        xlsx_name = "concerns_matrix.xlsx"
        md_name   = "concerns_matrix.md"

    print(f"Loading model from: {model_dir}")

    with open_model(collect_user_sysml_files(model_dir), allow_errors=True) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        concerns, req_usages = collect_elements(model, model_dir, args.program)

        concern_labels = sorted((get_name(c) for c in concerns),    key=natural_sort_key)
        req_labels     = sorted((get_short_label(r) for r in req_usages), key=natural_sort_key)
        frames         = {get_short_label(r): framed_concern_labels(r) for r in req_usages}

        print(f"Found {len(concern_labels)} concern(s), {len(req_usages)} requirement usage(s).")

        concerns_no_req = [c for c in concern_labels
                           if not any(c in frames.get(r, set()) for r in req_labels)]
        if concerns_no_req:
            print(f"  ⚠  {len(concerns_no_req)} concern(s) with no framing requirement:")
            for c in concerns_no_req:
                print(f"     - {c}")
        else:
            print(f"  ✓  All {len(concern_labels)} concern(s) have at least one framing requirement.")

        if not concern_labels or not req_labels:
            print("Nothing to write — no concerns or requirement definitions found.")
            return

        xlsx_path = write_xlsx(
            concern_labels, req_labels, frames,
            output_dir / xlsx_name, title,
        )
        print(f"  XLSX → {xlsx_path}")

        md_path = output_dir / md_name
        write_markdown(concern_labels, req_labels, frames, md_path, title)
        print(f"  MD   → {md_path}")


if __name__ == "__main__":
    main()
