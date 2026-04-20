"""
satisfaction_matrix.py

Generates a Requirement → Architecture satisfaction matrix from a SysML v2 model.

Usage:
    # Core model only (default)
    python __Tools/satisfaction_matrix.py .

    # Core + Program A
    python __Tools/satisfaction_matrix.py . --program Program_A

    # Core + Program B
    python __Tools/satisfaction_matrix.py . --program Program_B

Output:
    - ASCII matrix printed to stdout
    - If --program is given, a second program-specific matrix is shown after core
    - CSV written to __Tools/satisfaction_matrix[_<program>].csv

The tool reads `satisfy requirement X` statements inside verification blocks.
Each block also declares `subject Y : SomeArchType`, which becomes the column.
No separate package-level `satisfy X by Y` statements are needed.
"""

import sys
import csv
import argparse
from pathlib import Path
import syside
from syside.preview import open_model


def get_name(element) -> str:
    if element is None:
        return "<none>"
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


def subject_type_name(verification: syside.VerificationCaseUsage) -> str:
    """
    Return the architectural element type name from a verification's subject.
    Prefers the type classifier name (e.g. FeatureA_Component) over the
    usage name (e.g. featureA_Subject).
    """
    subj = verification.subject_parameter
    if subj is None:
        return "<no subject>"
    for typing in subj.types.collect():
        name = get_name(typing)
        if name and name not in ("<none>", "<unnamed>"):
            return name
    name = get_name(subj)
    return name if name and name not in ("<none>", "<unnamed>") else "<unknown>"


def req_name_from_satisfy(satisfy: syside.SatisfyRequirementUsage) -> str:
    """Return the requirement name from a satisfy link."""
    req = satisfy.satisfied_requirement
    if req is None:
        return "<unresolved>"
    name = get_name(req)
    if name and name not in ("<unnamed>", "<none>"):
        return name
    if req.isinstance(syside.RequirementUsage.STD):
        req_def = req.cast(syside.RequirementUsage.STD).requirement_definition
        if req_def is not None:
            def_name = get_name(req_def)
            if def_name and def_name not in ("<unnamed>", "<none>"):
                return def_name
    return "<unnamed>"


def build_satisfaction_map(req_usages: list,
                            verifications: list) -> dict[str, set[str]]:
    """
    Build satisfaction[req_name] = set of arch element type names
    by reading each verification block's satisfy + subject declarations.
    """
    satisfaction: dict[str, set[str]] = {get_name(r): set() for r in req_usages}

    for v in verifications:
        arch_name = subject_type_name(v)
        for member in v.owned_members.collect():
            if not member.isinstance(syside.SatisfyRequirementUsage.STD):
                continue
            req_name = req_name_from_satisfy(
                member.cast(syside.SatisfyRequirementUsage.STD)
            )
            if req_name not in satisfaction:
                satisfaction[req_name] = set()
            satisfaction[req_name].add(arch_name)

    return satisfaction


def print_matrix(label: str,
                 satisfaction: dict[str, set[str]]) -> list[str]:
    """Print one ASCII matrix section. Returns gap requirement names."""
    req_names  = sorted(satisfaction.keys())
    arch_names = sorted({n for names in satisfaction.values() for n in names})

    if not req_names:
        print(f"\n[{label}] No requirements found.\n")
        return []

    if not arch_names:
        arch_names = ["(no arch elements)"]

    row_w = max(len(n) for n in req_names + ["Requirement"])
    col_w = max(len(n) for n in arch_names)

    print(f"\n{'═' * 4} {label} {'═' * max(0, 60 - len(label))}")
    header = f"{'Requirement':<{row_w}} | " + " | ".join(
        f"{a:<{col_w}}" for a in arch_names
    )
    print(header)
    print("-" * len(header))

    gaps = []
    for req in req_names:
        sat = satisfaction.get(req, set())
        cells = " | ".join(
            f"{'X':^{col_w}}" if a in sat else f"{' ':^{col_w}}"
            for a in arch_names
        )
        gap_marker = "  ← GAP" if not sat else ""
        if not sat:
            gaps.append(req)
        print(f"{req:<{row_w}} | {cells}{gap_marker}")

    print()
    if gaps:
        print(f"⚠  {len(gaps)} unsatisfied requirement(s):")
        for g in gaps:
            print(f"   - {g}")
    else:
        print(f"✓  All {len(req_names)} requirement(s) have at least one satisfying element.")

    return gaps


def write_csv(csv_path: Path, satisfaction: dict[str, set[str]]):
    req_names  = sorted(satisfaction.keys())
    arch_names = sorted({n for names in satisfaction.values() for n in names})
    if not arch_names:
        arch_names = ["(no arch elements)"]
    csv_path.parent.mkdir(exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Requirement"] + arch_names + ["SATISFIED?"])
        for req in req_names:
            sat = satisfaction.get(req, set())
            row = [req] + ["X" if a in sat else "" for a in arch_names]
            row.append("YES" if sat else "NO — GAP")
            writer.writerow(row)


def collect_for_dir(model, target_dir: Path) -> tuple[list, list]:
    """Collect requirement usages and verifications from a directory."""
    req_usages:   list = []
    verifications: list = []
    for top in model.top_elements_from(target_dir):
        collect_typed(top, syside.RequirementUsage.STD,      req_usages)
        collect_typed(top, syside.VerificationCaseUsage.STD, verifications)
    req_usages = [
        r for r in req_usages
        if not r.isinstance(syside.SatisfyRequirementUsage.STD)
        and not r.isinstance(syside.ConcernUsage.STD)
    ]
    return req_usages, verifications


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
        # Collect from model_dir but exclude any program subdirectories
        programs_dir = model_dir / "04_Programs"
        core_req_usages:   list = []
        core_verifications: list = []

        for top in model.top_elements_from(model_dir):
            skip = False
            if programs_dir.exists():
                for prog_dir in programs_dir.iterdir():
                    if prog_dir.is_dir():
                        try:
                            if top in list(model.top_elements_from(prog_dir)):
                                skip = True
                                break
                        except Exception:
                            pass
            if not skip:
                collect_typed(top, syside.RequirementUsage.STD,      core_req_usages)
                collect_typed(top, syside.VerificationCaseUsage.STD, core_verifications)

        core_req_usages = [
            r for r in core_req_usages
            if not r.isinstance(syside.SatisfyRequirementUsage.STD)
            and not r.isinstance(syside.ConcernUsage.STD)
        ]

        core_satisfaction = build_satisfaction_map(core_req_usages, core_verifications)
        print_matrix("CORE — Requirement → Architecture", core_satisfaction)

        csv_path = output_dir / "satisfaction_matrix.csv"
        write_csv(csv_path, core_satisfaction)
        print(f"\nCSV written to: {csv_path}")

        # ── Program collection ────────────────────────────────────────────
        if not program:
            return

        prog_dir = programs_dir / program
        if not prog_dir.is_dir():
            print(f"\nERROR: Program directory not found: {prog_dir}", file=sys.stderr)
            print(f"Available: {[d.name for d in programs_dir.iterdir() if d.is_dir()]}")
            return

        prog_req_usages, prog_verifications = collect_for_dir(model, prog_dir)
        prog_satisfaction = build_satisfaction_map(prog_req_usages, prog_verifications)

        print_matrix(f"{program} — Requirement → Architecture", prog_satisfaction)

        prog_csv = output_dir / f"satisfaction_matrix_{program}.csv"
        write_csv(prog_csv, prog_satisfaction)
        print(f"\nCSV written to: {prog_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Requirement → Architecture satisfaction matrix."
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
