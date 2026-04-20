"""
concerns_matrix.py

Generates a Concern → Requirement traceability matrix from a SysML v2 model.

Usage:
    # Core model only (default)
    python __Tools/concerns_matrix.py .

    # Core + Program A
    python __Tools/concerns_matrix.py . --program Program_A

    # Core + Program B
    python __Tools/concerns_matrix.py . --program Program_B

Output:
    - ASCII matrix printed to stdout
    - If --program is given, a second program-specific matrix is shown after core
    - CSV written to __Tools/concern_req_matrix[_<program>].csv

Each program can have its own stakeholders, concerns, and requirement defs
that are entirely separate from (and in addition to) the core model elements.
"""

import sys
import csv
import argparse
from pathlib import Path
import syside
from syside.preview import open_model


def get_name(element) -> str:
    name = element.declared_name
    if name:
        return name
    qn = element.qualified_name
    return str(qn) if qn else "<unnamed>"


def collect_typed(root, std_type: type, results: list):
    """Depth-first collection of all elements matching std_type."""
    if root.isinstance(std_type):
        results.append(root.cast(std_type))
    if root.isinstance(syside.Namespace.STD):
        ns = root.cast(syside.Namespace.STD)
        for member in ns.owned_members.collect():
            collect_typed(member, std_type, results)


def framed_concern_names(req_def) -> set[str]:
    """
    Return the set of concern names framed by this requirement def.
    In SysIDE 0.8.x, `frame concern X` is stored as a ConcernUsage
    with declared_name = 'X'.
    """
    names: set[str] = set()
    for member in req_def.owned_members.collect():
        if member.isinstance(syside.ConcernUsage.STD):
            n = member.cast(syside.ConcernUsage.STD).declared_name
            if n:
                names.add(n)
    return names


def print_matrix(label: str,
                 concern_names: list[str],
                 req_names: list[str],
                 req_frames: dict[str, set[str]]) -> list[str]:
    """Print one ASCII matrix section. Returns the list of gap concern names."""
    if not concern_names or not req_names:
        print(f"\n[{label}] Nothing to show — no concerns or requirements found.\n")
        return []

    row_w = max(len(n) for n in concern_names + ["Concern"])
    col_w = max(len(n) for n in req_names)

    print(f"\n{'═' * 4} {label} {'═' * max(0, 60 - len(label))}")
    header = f"{'Concern':<{row_w}} | " + " | ".join(f"{r:<{col_w}}" for r in req_names)
    print(header)
    print("-" * len(header))

    gaps = []
    for concern in concern_names:
        cells = " | ".join(
            f"{'X':^{col_w}}" if concern in req_frames.get(r, set()) else f"{' ':^{col_w}}"
            for r in req_names
        )
        covered = any(concern in req_frames.get(r, set()) for r in req_names)
        gap_marker = "  ← GAP" if not covered else ""
        if not covered:
            gaps.append(concern)
        print(f"{concern:<{row_w}} | {cells}{gap_marker}")

    print()
    if gaps:
        print(f"⚠  {len(gaps)} concern(s) with no requirement:")
        for g in gaps:
            print(f"   - {g}")
    else:
        print(f"✓  All {len(concern_names)} concern(s) have at least one requirement.")

    return gaps


def write_csv(csv_path: Path,
              concern_names: list[str],
              req_names: list[str],
              req_frames: dict[str, set[str]]):
    csv_path.parent.mkdir(exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Concern"] + req_names + ["COVERED?"])
        for concern in concern_names:
            covered = any(concern in req_frames.get(r, set()) for r in req_names)
            row = [concern] + ["X" if concern in req_frames.get(r, set()) else ""
                               for r in req_names]
            row.append("YES" if covered else "NO — GAP")
            writer.writerow(row)


def collect_for_dir(model, target_dir: Path) -> tuple[list, list]:
    """Collect concerns and req defs from a specific directory."""
    concerns: list = []
    req_defs: list = []
    for top in model.top_elements_from(target_dir):
        collect_typed(top, syside.ConcernDefinition.STD,     concerns)
        collect_typed(top, syside.RequirementDefinition.STD, req_defs)
    req_defs = [r for r in req_defs
                if not r.isinstance(syside.ConcernDefinition.STD)]
    return concerns, req_defs


def build_matrix(model_dir: Path, program: str | None, output_dir: Path):

    print(f"Loading model from: {model_dir}")
    if program:
        print(f"Program filter:     {program}\n")
    else:
        print()

    with open_model(model_dir) as model:

        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        # ── Core collection ───────────────────────────────────────────────
        # Exclude program directories from the core pass
        programs_dir = model_dir / "04_Programs"
        core_concerns: list = []
        core_req_defs: list = []

        for top in model.top_elements_from(model_dir):
            # Skip elements that belong to any program subdirectory
            skip = False
            if programs_dir.exists():
                for prog_dir in programs_dir.iterdir():
                    if prog_dir.is_dir():
                        try:
                            elems = list(model.top_elements_from(prog_dir))
                            if top in elems:
                                skip = True
                                break
                        except Exception:
                            pass
            if not skip:
                collect_typed(top, syside.ConcernDefinition.STD,     core_concerns)
                collect_typed(top, syside.RequirementDefinition.STD, core_req_defs)

        core_req_defs = [r for r in core_req_defs
                         if not r.isinstance(syside.ConcernDefinition.STD)]

        core_concern_names = sorted(get_name(c) for c in core_concerns)
        core_req_names     = sorted(get_name(r) for r in core_req_defs)
        core_req_frames    = {get_name(r): framed_concern_names(r) for r in core_req_defs}

        core_gaps = print_matrix(
            "CORE — Concern → Requirement",
            core_concern_names,
            core_req_names,
            core_req_frames,
        )

        # Write core CSV
        csv_path = output_dir / "concern_req_matrix.csv"
        write_csv(csv_path, core_concern_names, core_req_names, core_req_frames)
        print(f"\nCSV written to: {csv_path}")

        # ── Program collection ────────────────────────────────────────────
        if not program:
            return

        prog_dir = programs_dir / program
        if not prog_dir.is_dir():
            print(f"\nERROR: Program directory not found: {prog_dir}", file=sys.stderr)
            print(f"Available programs: {[d.name for d in programs_dir.iterdir() if d.is_dir()]}")
            return

        prog_concerns, prog_req_defs = collect_for_dir(model, prog_dir)

        prog_concern_names = sorted(get_name(c) for c in prog_concerns)
        prog_req_names     = sorted(get_name(r) for r in prog_req_defs)
        prog_req_frames    = {get_name(r): framed_concern_names(r) for r in prog_req_defs}

        print_matrix(
            f"{program} — Concern → Requirement",
            prog_concern_names,
            prog_req_names,
            prog_req_frames,
        )

        # Write program CSV
        prog_csv = output_dir / f"concern_req_matrix_{program}.csv"
        write_csv(prog_csv, prog_concern_names, prog_req_names, prog_req_frames)
        print(f"\nCSV written to: {prog_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Concern → Requirement traceability matrix."
    )
    parser.add_argument("model_dir", help="Path to model root directory")
    parser.add_argument(
        "--program", "-p",
        default=None,
        help="Program subdirectory name (e.g. Program_A) to include after core"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: __output in current working directory)"
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir).resolve()
    if not model_dir.is_dir():
        print(f"Error: '{model_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output).resolve() if args.output else Path.cwd() / "__output"
    output_dir.mkdir(parents=True, exist_ok=True)

    build_matrix(model_dir, args.program, output_dir)
