"""
coverage_matrix.py

Generates a Requirement → Verification coverage matrix from a SysML v2 model.
Uses the SysIDE Automator (syside) Python API.

The matrix answers: "Does every requirement have at least one verification
case planned to confirm it?"  Gaps (rows with no X) are requirements heading
into development with no test — the most common source of late-cycle escapes.

Usage:
    # Core model only (default)
    python __Tools/coverage_matrix.py .

    # Core + Program A
    python __Tools/coverage_matrix.py . --program Program_A

Output:
    - ASCII matrix (rows = requirements, cols = verification names)
    - Gap report: requirements with no verification
    - CSV written to __Tools/coverage_matrix[_<program>].csv

SysIDE API notes (confirmed against 0.8.x):
    - VerificationCaseUsage.verified_requirements is the spec property but
      may not resolve in SysIDE 0.8.x; we fall back to walking owned members
      for SatisfyRequirementUsage elements (confirmed working pattern).
    - req_name_from_satisfy uses satisfied_requirement.declared_name
    - top_elements_from(model_dir) scopes to user model files only
"""

import sys
import csv
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import iter_user_elements, collect_user_sysml_files
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


def req_name_from_satisfy(satisfy: syside.SatisfyRequirementUsage) -> str:
    """Return the requirement name from a SatisfyRequirementUsage."""
    req = satisfy.satisfied_requirement
    if req is None:
        return "<unresolved>"
    name = get_name(req)
    if name and name not in ("<unnamed>", "<none>"):
        return name
    # Fallback via requirement_definition
    if req.isinstance(syside.RequirementUsage.STD):
        req_def = req.cast(syside.RequirementUsage.STD).requirement_definition
        if req_def is not None:
            def_name = get_name(req_def)
            if def_name and def_name not in ("<unnamed>", "<none>"):
                return def_name
    return "<unnamed>"


def verified_req_names(v: syside.VerificationCaseUsage) -> set[str]:
    """
    Return the set of requirement names verified by a verification block.

    Tries verified_requirements first (spec property), then falls back to
    walking owned members for SatisfyRequirementUsage elements — the pattern
    confirmed working in SysIDE 0.8.x.
    """
    names: set[str] = set()

    # Primary: spec property
    try:
        for req in v.verified_requirements.collect():
            n = get_name(req)
            if n and n not in ("<none>", "<unnamed>"):
                names.add(n)
    except Exception:
        pass

    # Fallback: walk owned members (known-working pattern from satisfaction_matrix)
    if not names:
        for member in v.owned_members.collect():
            if member.isinstance(syside.SatisfyRequirementUsage.STD):
                n = req_name_from_satisfy(
                    member.cast(syside.SatisfyRequirementUsage.STD)
                )
                if n and n not in ("<unresolved>", "<unnamed>"):
                    names.add(n)

    return names


def build_coverage_map(req_usages: list,
                        verifications: list) -> dict[str, set[str]]:
    """
    Build coverage[req_name] = set of verification names covering it.
    """
    coverage: dict[str, set[str]] = {get_name(r): set() for r in req_usages}

    for v in verifications:
        v_name = get_name(v)
        for req_name in verified_req_names(v):
            if req_name not in coverage:
                coverage[req_name] = set()
            coverage[req_name].add(v_name)

    return coverage


def print_matrix(label: str,
                 coverage: dict[str, set[str]]) -> list[str]:
    """Print one ASCII matrix section. Returns gap requirement names."""
    req_names   = sorted(coverage.keys())
    verif_names = sorted({n for names in coverage.values() for n in names})

    if not req_names:
        print(f"\n[{label}] No requirements found.\n")
        return []

    if not verif_names:
        verif_names = ["(no verifications)"]

    row_w = max(len(n) for n in req_names + ["Requirement"])
    col_w = max(len(n) for n in verif_names)

    print(f"\n{'═' * 4} {label} {'═' * max(0, 60 - len(label))}")
    header = f"{'Requirement':<{row_w}} | " + " | ".join(
        f"{v:<{col_w}}" for v in verif_names
    )
    print(header)
    print("-" * len(header))

    gaps = []
    for req in req_names:
        covered = coverage.get(req, set())
        cells = " | ".join(
            f"{'X':^{col_w}}" if v in covered else f"{' ':^{col_w}}"
            for v in verif_names
        )
        gap_marker = "  ← GAP" if not covered else ""
        if not covered:
            gaps.append(req)
        print(f"{req:<{row_w}} | {cells}{gap_marker}")

    print()
    if gaps:
        print(f"⚠  {len(gaps)} uncovered requirement(s):")
        for g in gaps:
            print(f"   - {g}")
    else:
        print(f"✓  All {len(req_names)} requirement(s) have at least one verification.")

    return gaps


def write_csv(csv_path: Path, coverage: dict[str, set[str]]):
    req_names   = sorted(coverage.keys())
    verif_names = sorted({n for names in coverage.values() for n in names})
    if not verif_names:
        verif_names = ["(no verifications)"]
    csv_path.parent.mkdir(exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Requirement"] + verif_names + ["COVERED?"])
        for req in req_names:
            covered = coverage.get(req, set())
            row = [req] + ["X" if v in covered else "" for v in verif_names]
            row.append("YES" if covered else "NO — GAP")
            writer.writerow(row)


def collect_for_dir(model, target_dir: Path) -> tuple[list, list]:
    """Collect requirement usages and verifications from a specific directory."""
    req_usages:    list = []
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

    with open_model(collect_user_sysml_files(model_dir), allow_errors=True) as model:

        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        # ── Core collection ───────────────────────────────────────────────
        programs_dir = model_dir / "04_Programs"
        core_req_usages:    list = []
        core_verifications: list = []

        for top in iter_user_elements(model, model_dir):
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

        core_coverage = build_coverage_map(core_req_usages, core_verifications)
        print_matrix("CORE — Requirement → Verification", core_coverage)

        csv_path = output_dir / "coverage_matrix.csv"
        write_csv(csv_path, core_coverage)
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
        prog_coverage = build_coverage_map(prog_req_usages, prog_verifications)

        print_matrix(f"{program} — Requirement → Verification", prog_coverage)

        prog_csv = output_dir / f"coverage_matrix_{program}.csv"
        write_csv(prog_csv, prog_coverage)
        print(f"\nCSV written to: {prog_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Requirement → Verification coverage matrix."
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
