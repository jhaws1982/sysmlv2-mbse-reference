"""
result_matrix.py

Generates a Requirement → Test Result matrix by joining:
  - The SysML v2 model  (requirement → verification name mapping)
  - A CTest JUnit XML   (verification name → pass/fail/skip result)

This keeps design intent (the model) and execution evidence (CI results)
cleanly separated.  The model is never modified to record test results.

NAMING CONVENTION (required):
  Verification names in the model MUST exactly match test names in the
  CTest XML.  e.g. `verification testA { ... }` matches `<testcase name="testA">`.

Usage:
    python __Tools/result_matrix.py . --xml path/to/ctest.xml
    python __Tools/result_matrix.py . --xml ctest.xml --program Program_A

    # Use bundled sample data for demo:
    python __Tools/result_matrix.py . --xml __Tools/sample_data/ctest_core.xml

Output:
    - ASCII table: Requirement | Verification | Result | Message
    - Summary counts
    - CSV written to __Tools/result_matrix[_<program>].csv

Result states (derived from JUnit XML):
    PASS     — testcase present, no <failure> or <error> child
    FAIL     — testcase has <failure> or <error> child
    SKIP     — testcase has <skipped> child
    NOT_RUN  — verification exists in model but no matching testcase in XML
    NO_TEST  — requirement exists but has no verification in the model (gap)
"""

import sys
import csv
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET
import syside
from syside.preview import open_model


# ── Result state definitions ──────────────────────────────────────────────────

RESULT_ORDER = ["FAIL", "SKIP", "NOT_RUN", "NO_TEST", "PASS"]

STATUS_MARKERS = {
    "PASS":    "✓ PASS",
    "FAIL":    "✗ FAIL",
    "SKIP":    "↷ SKIP",
    "NOT_RUN": "— NOT_RUN",
    "NO_TEST": "⚠ NO_TEST",
}


# ── CTest XML parsing ─────────────────────────────────────────────────────────

def parse_ctest_xml(xml_path: Path) -> dict[str, dict]:
    """
    Parse a CTest JUnit XML file.

    Returns dict: test_name → {status, message}
    Status is one of: PASS, FAIL, SKIP
    """
    results: dict[str, dict] = {}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"ERROR: Could not parse XML file {xml_path}: {e}", file=sys.stderr)
        return results
    except FileNotFoundError:
        print(f"ERROR: XML file not found: {xml_path}", file=sys.stderr)
        return results

    # Handle both <testsuites><testsuite> and bare <testsuite> roots
    suites = (root.findall(".//testsuite")
              if root.tag == "testsuites"
              else [root] if root.tag == "testsuite"
              else root.findall(".//testsuite"))

    for suite in suites:
        for tc in suite.findall("testcase"):
            name = tc.get("name", "").strip()
            if not name:
                continue

            if tc.find("failure") is not None:
                status  = "FAIL"
                message = tc.find("failure").get("message", "")
            elif tc.find("error") is not None:
                status  = "FAIL"
                message = tc.find("error").get("message", "")
            elif tc.find("skipped") is not None:
                status  = "SKIP"
                message = tc.find("skipped").get("message", "")
            else:
                status  = "PASS"
                message = ""

            results[name] = {"status": status, "message": message}

    return results


# ── Model traversal ───────────────────────────────────────────────────────────

def get_name(element) -> str:
    if element is None:
        return "<none>"
    name = element.declared_name
    if name:
        return name
    qn = element.qualified_name
    return str(qn) if qn else "<unnamed>"


def collect_typed(root, std_type: type, results: list):
    if root.isinstance(std_type):
        results.append(root.cast(std_type))
    if root.isinstance(syside.Namespace.STD):
        ns = root.cast(syside.Namespace.STD)
        for member in ns.owned_members.collect():
            collect_typed(member, std_type, results)


def req_names_for_verification(v: syside.VerificationCaseUsage) -> list[str]:
    """Return requirement names covered by a verification block."""
    names = []
    try:
        for req in v.verified_requirements.collect():
            n = get_name(req)
            if n and n not in ("<none>", "<unnamed>"):
                names.append(n)
    except Exception:
        pass
    if not names:
        for member in v.owned_members.collect():
            if member.isinstance(syside.SatisfyRequirementUsage.STD):
                req = member.cast(syside.SatisfyRequirementUsage.STD).satisfied_requirement
                if req is not None:
                    n = get_name(req)
                    if n and n not in ("<none>", "<unnamed>"):
                        names.append(n)
    return sorted(set(names))


def collect_req_usages(model, dirs: list[Path]) -> list:
    """Collect plain requirement usages (not satisfy/concern) from a list of dirs."""
    req_usages = []
    for d in dirs:
        for top in model.top_elements_from(d):
            collect_typed(top, syside.RequirementUsage.STD, req_usages)
    return [
        r for r in req_usages
        if not r.isinstance(syside.SatisfyRequirementUsage.STD)
        and not r.isinstance(syside.ConcernUsage.STD)
    ]


def collect_verifications(model, dirs: list[Path]) -> list:
    """Collect VerificationCaseUsage elements from a list of dirs."""
    verifications = []
    for d in dirs:
        for top in model.top_elements_from(d):
            collect_typed(top, syside.VerificationCaseUsage.STD, verifications)
    return verifications


# ── Matrix construction ───────────────────────────────────────────────────────

def build_records(req_usages: list,
                  verifications: list,
                  ctest_results: dict[str, dict]) -> list[dict]:
    """
    Join model data with CTest results to produce row records.

    Each record: {requirement, verification, status, message}
    One row per (requirement, verification) pair.
    Requirements with no verification get a NO_TEST row.
    """
    # Build map: req_name → list of verification names
    req_to_verifs: dict[str, list[str]] = {get_name(r): [] for r in req_usages}

    for v in verifications:
        v_name = get_name(v)
        for req_name in req_names_for_verification(v):
            if req_name not in req_to_verifs:
                req_to_verifs[req_name] = []
            req_to_verifs[req_name].append(v_name)

    records = []
    for req_name in sorted(req_to_verifs):
        verif_names = sorted(req_to_verifs[req_name])
        if not verif_names:
            records.append({
                "requirement":  req_name,
                "verification": "(none)",
                "status":       "NO_TEST",
                "message":      "",
            })
        else:
            for v_name in verif_names:
                result  = ctest_results.get(v_name, {})
                status  = result.get("status",  "NOT_RUN")
                message = result.get("message", "")
                records.append({
                    "requirement":  req_name,
                    "verification": v_name,
                    "status":       status,
                    "message":      message,
                })

    # Sort by status severity, then requirement name
    records.sort(key=lambda r: (
        RESULT_ORDER.index(r["status"]) if r["status"] in RESULT_ORDER else 99,
        r["requirement"]
    ))
    return records


# ── Output ────────────────────────────────────────────────────────────────────

def print_table(label: str, records: list[dict], ctest_path: Path | None):
    if not records:
        print(f"\n[{label}] No data.\n")
        return

    req_w   = max(len(r["requirement"])  for r in records + [{"requirement": "Requirement"}])
    verif_w = max(len(r["verification"]) for r in records + [{"verification": "Verification"}])
    stat_w  = max(len(STATUS_MARKERS.get(r["status"], r["status"]))
                  for r in records + [{"status": "Status"}])
    msg_w   = min(
        max(len(r["message"]) for r in records),
        55
    )
    msg_w   = max(msg_w, len("Message"))

    src = f" (XML: {ctest_path.name})" if ctest_path else " (no XML — all NOT_RUN)"
    print(f"\n{'═' * 4} {label}{src} {'═' * max(0, 55 - len(label))}")

    header = (f"{'Requirement':<{req_w}} | "
              f"{'Verification':<{verif_w}} | "
              f"{'Status':<{stat_w}} | "
              f"{'Message':<{msg_w}}")
    print(header)
    print("-" * len(header))

    for r in records:
        marker = STATUS_MARKERS.get(r["status"], r["status"])
        msg    = r["message"][:msg_w] if r["message"] else ""
        print(f"{r['requirement']:<{req_w}} | "
              f"{r['verification']:<{verif_w}} | "
              f"{marker:<{stat_w}} | "
              f"{msg:<{msg_w}}")

    # Summary
    print()
    counts = {s: sum(1 for r in records if r["status"] == s) for s in RESULT_ORDER}
    parts  = [f"{STATUS_MARKERS[s]}: {counts[s]}" for s in RESULT_ORDER if counts[s] > 0]
    print(f"Summary ({len(records)} row(s)): {' | '.join(parts)}")

    failures = [r for r in records if r["status"] == "FAIL"]
    no_test  = [r for r in records if r["status"] == "NO_TEST"]
    not_run  = [r for r in records if r["status"] == "NOT_RUN"]

    if failures:
        print(f"\n✗  {len(failures)} FAILED test(s):")
        for r in failures:
            suffix = f" — {r['message']}" if r["message"] else ""
            print(f"   [{r['requirement']}] {r['verification']}{suffix}")
    if no_test:
        print(f"\n⚠  {len(no_test)} requirement(s) with NO verification in model:")
        for r in no_test:
            print(f"   - {r['requirement']}")
    if not_run:
        print(f"\n—  {len(not_run)} verification(s) not found in XML (NOT_RUN):")
        for r in not_run:
            print(f"   - {r['verification']} (covers: {r['requirement']})")


def write_csv(csv_path: Path, records: list[dict]):
    csv_path.parent.mkdir(exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Requirement", "Verification", "Status", "Message"])
        for r in records:
            writer.writerow([r["requirement"], r["verification"],
                             r["status"], r["message"]])


# ── Main ──────────────────────────────────────────────────────────────────────

def build_matrix(model_dir: Path, xml_path: Path | None, program: str | None, output_dir: Path):

    print(f"Loading model from: {model_dir}")
    if program:
        print(f"Program filter:     {program}")
    if xml_path:
        print(f"CTest XML:          {xml_path}")
    else:
        print("CTest XML:          (none — all verifications will show NOT_RUN)")
    print()

    ctest_results = parse_ctest_xml(xml_path) if xml_path else {}
    if xml_path and ctest_results:
        print(f"Parsed {len(ctest_results)} test result(s) from XML.")

    with open_model(model_dir) as model:

        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        programs_dir = model_dir / "04_Programs"

        # ── Determine directories to scan ─────────────────────────────────
        # Core dirs: everything under model_dir except 04_Programs
        def is_prog_element(top) -> bool:
            if not programs_dir.exists():
                return False
            for pd in programs_dir.iterdir():
                if pd.is_dir():
                    try:
                        if top in list(model.top_elements_from(pd)):
                            return True
                    except Exception:
                        pass
            return False

        # Core collection
        core_req_usages    = []
        core_verifications = []
        for top in model.top_elements_from(model_dir):
            if not is_prog_element(top):
                collect_typed(top, syside.RequirementUsage.STD,      core_req_usages)
                collect_typed(top, syside.VerificationCaseUsage.STD, core_verifications)

        core_req_usages = [
            r for r in core_req_usages
            if not r.isinstance(syside.SatisfyRequirementUsage.STD)
            and not r.isinstance(syside.ConcernUsage.STD)
        ]

        core_records = build_records(core_req_usages, core_verifications, ctest_results)
        print_table("CORE — Requirement → Result", core_records, xml_path)

        csv_path = output_dir / "result_matrix.csv"
        write_csv(csv_path, core_records)
        print(f"\nCSV written to: {csv_path}")

        if not program:
            return

        # ── Program collection ────────────────────────────────────────────
        prog_dir = programs_dir / program
        if not prog_dir.is_dir():
            print(f"\nERROR: Program directory not found: {prog_dir}", file=sys.stderr)
            print(f"Available: {[d.name for d in programs_dir.iterdir() if d.is_dir()]}")
            return

        prog_req_usages    = []
        prog_verifications = []
        for top in model.top_elements_from(prog_dir):
            collect_typed(top, syside.RequirementUsage.STD,      prog_req_usages)
            collect_typed(top, syside.VerificationCaseUsage.STD, prog_verifications)

        prog_req_usages = [
            r for r in prog_req_usages
            if not r.isinstance(syside.SatisfyRequirementUsage.STD)
            and not r.isinstance(syside.ConcernUsage.STD)
        ]

        prog_records = build_records(prog_req_usages, prog_verifications, ctest_results)
        print_table(f"{program} — Requirement → Result", prog_records, xml_path)

        prog_csv = output_dir / f"result_matrix_{program}.csv"
        write_csv(prog_csv, prog_records)
        print(f"\nCSV written to: {prog_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Requirement → Result matrix from model + CTest XML."
    )
    parser.add_argument("model_dir",
                        help="Path to model root directory")
    parser.add_argument("--xml", "-x",
                        default=None,
                        help="Path to CTest JUnit XML results file")
    parser.add_argument("--program", "-p",
                        default=None,
                        help="Program subdirectory name (e.g. Program_A)")
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

    xml_path = Path(args.xml).resolve() if args.xml else None
    if xml_path and not xml_path.exists():
        print(f"Error: XML file not found: {xml_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output).resolve() if args.output else Path.cwd() / "__output"
    output_dir.mkdir(parents=True, exist_ok=True)

    build_matrix(model_dir, xml_path, args.program, output_dir)
